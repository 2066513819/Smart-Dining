"""
候选菜品生成器
用于为套餐推荐生成多种候选组合，支持权重评分筛选
"""
from typing import List, Dict, Any, Set, Optional, Tuple
import itertools
import random
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.menu_item import MenuItem
from app.utils.plan_scorer import PlanScorer


class CandidateGenerator:
    """候选菜品生成器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_candidates_by_category(
        self,
        category_rules: Dict[str, int],
        meal_type: str,
        meal: str,
        target_age_group: str,
        max_cost_per_meal: Optional[float] = None,
        max_candidates_per_category: int = 20,
        nutrition_targets: Optional[Dict[str, float]] = None,
        ingredient_prices: Optional[Dict[str, float]] = None,
        strict_mode: bool = False,
        flavor_filters: Optional[List[str]] = None,
        season_filters: Optional[List[str]] = None
    ) -> Dict[str, List[MenuItem]]:
        """
        按分类获取候选菜品列表
        
        Args:
            category_rules: 分类规则，如 {"素菜类": 2, "荤菜类": 1}
            meal_type: 餐次类型 (breakfast/lunch/dinner/snack)
            meal: 具体餐次名称
            target_age_group: 目标年龄段
            max_cost_per_meal: 每餐最大成本
            max_candidates_per_category: 每分类最大候选数量
            nutrition_targets: 营养目标
            ingredient_prices: 食材价格映射
            strict_mode: 严格模式
            flavor_filters: 口味过滤
            season_filters: 时令过滤
            
        Returns:
            Dict[str, List[MenuItem]]: 每个分类的候选菜品列表
        """
        candidates_by_category = {}
        
        for category, required_count in category_rules.items():
            if required_count <= 0:
                continue
                
            cat_trimmed = category.strip()
            
            # 构建基础查询
            query = self.db.query(MenuItem).filter(
                MenuItem.dish_type == meal_type,
                or_(
                    func.trim(MenuItem.category).like(f"%{cat_trimmed}%"),
                    MenuItem.category.like(f"%{cat_trimmed}%")
                )
            )
            
            # 应用基础过滤
            query = self._apply_base_filters(
                query, cat_trimmed, meal_type, target_age_group
            )
            
            # 应用营养过滤
            if nutrition_targets and nutrition_targets.get("target_calories", 0) > 0:
                max_calories_per_dish = nutrition_targets["target_calories"] * 1.2
                query = query.filter(MenuItem.total_calories <= max_calories_per_dish)
            
            # 应用口味过滤
            if flavor_filters:
                query = query.filter(MenuItem.flavor.in_(flavor_filters))
            
            # 应用时令过滤
            if season_filters:
                season_conditions = []
                for season in season_filters:
                    if season == "四季皆宜":
                        season_conditions.append(MenuItem.season.contains("四季皆宜"))
                    else:
                        season_conditions.append(MenuItem.season.contains(season))
                query = query.filter(or_(*season_conditions))
            
            # 成本过滤
            if max_cost_per_meal and max_cost_per_meal > 0:
                # 计算每个菜品的平均成本上限
                total_items = sum(category_rules.values())
                avg_item_cost = max_cost_per_meal / total_items
                query = query.filter(MenuItem.cost_price <= avg_item_cost * 1.2)
            
            # 推荐规则：只推荐有价格的菜品（无动态价格时在 SQL 层过滤）
            if not ingredient_prices:
                query = query.filter(MenuItem.cost_price > 0)

            # 获取候选菜品
            candidates = query.order_by(func.random()).limit(
                max_candidates_per_category
            ).all()

            # 有动态价格时按计算后的成本过滤掉无价菜品；严格模式也会过滤
            if ingredient_prices:
                from app.utils.cost_calculator import calculate_dynamic_cost
                for c in candidates:
                    c.cost_price = calculate_dynamic_cost(c.dish_recipe or "", ingredient_prices)
                candidates = [c for c in candidates if (c.cost_price or 0) > 0]
            if strict_mode:
                candidates = self._filter_strict_mode(candidates, ingredient_prices)

            candidates_by_category[category] = candidates
            
            print(f"DEBUG: 分类 [{category}] 找到 {len(candidates)} 个候选菜品")
        
        return candidates_by_category
    
    def _apply_base_filters(
        self,
        query,
        category: str,
        meal_type: str,
        target_age_group: str
    ):
        """应用基础过滤条件（MenuItem 无 age_group 字段，年龄段在评分阶段通过营养目标体现）"""
        # 分类精确匹配过滤
        query = query.filter(
            or_(
                MenuItem.category.like(f"%{category}%"),
                func.trim(MenuItem.category).like(f"%{category}%")
            )
        )
        
        return query
    
    def _filter_strict_mode(
        self,
        candidates: List[MenuItem],
        ingredient_prices: Optional[Dict[str, float]] = None
    ) -> List[MenuItem]:
        """严格模式过滤"""
        if not ingredient_prices:
            return candidates
        
        # 过滤掉价格缺失的菜品
        filtered = []
        for candidate in candidates:
            # 计算实际成本
            actual_cost = self._calculate_actual_cost(candidate, ingredient_prices)
            if actual_cost is not None and actual_cost > 0:
                filtered.append(candidate)
        
        return filtered
    
    def _calculate_actual_cost(
        self,
        dish: MenuItem,
        ingredient_prices: Dict[str, float]
    ) -> Optional[float]:
        """计算菜品实际成本：有价格表时按配方+价格表算，否则用数据库成本"""
        if ingredient_prices:
            from app.utils.cost_calculator import calculate_dynamic_cost
            return calculate_dynamic_cost(dish.dish_recipe or "", ingredient_prices)
        return float(dish.cost_price) if (dish.cost_price is not None and float(dish.cost_price) > 0) else None
    
    def generate_plan_combinations(
        self,
        candidates_by_category: Dict[str, List[MenuItem]],
        category_rules: Dict[str, int],
        max_combinations: int = 100
    ) -> List[List[MenuItem]]:
        """
        生成计划组合
        
        Args:
            candidates_by_category: 每个分类的候选菜品
            category_rules: 分类规则
            max_combinations: 最大组合数
            
        Returns:
            List[List[MenuItem]]: 菜品组合列表
        """
        combinations = []
        
        # 为每个分类生成选择列表
        selection_lists = []
        for category, required_count in category_rules.items():
            if required_count <= 0:
                continue
            
            candidates = candidates_by_category.get(category, [])
            if not candidates:
                continue
            
            # 从候选菜品中选择required_count个（可重复，但避免完全相同）
            category_selections = []
            for _ in range(min(10, len(candidates))):  # 每个分类最多10种选择
                selected = random.sample(candidates, min(required_count, len(candidates)))
                category_selections.append(selected)
            
            selection_lists.append(category_selections)
        
        # 如果只有一个分类，直接返回
        if len(selection_lists) == 1:
            return selection_lists[0]
        
        # 生成组合
        try:
            # 使用随机采样生成组合
            for _ in range(min(max_combinations, 50)):
                combination = []
                for selections in selection_lists:
                    if selections:
                        choice = random.choice(selections)
                        combination.extend(choice)
                if combination:
                    combinations.append(combination)
        except Exception as e:
            print(f"生成组合时出错: {e}")
        
        return combinations
    
    def generate_weighted_plans(
        self,
        category_rules: Dict[str, int],
        meal_type: str,
        meal: str,
        target_age_group: str,
        nutrition_targets: Dict[str, float],
        cost_budget: Optional[float] = None,
        max_combinations: int = 50,
        top_n: int = 5,
        ingredient_prices: Optional[Dict[str, float]] = None,
        strict_mode: bool = False,
        flavor_filters: Optional[List[str]] = None,
        season_filters: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成加权评分后的计划
        
        Args:
            各种参数...
            
        Returns:
            List[Dict[str, Any]]: 评分后的计划列表，按评分排序
        """
        print(f"\n=== 开始生成加权评分计划 ===")
        print(f"分类规则: {category_rules}")
        print(f"餐次: {meal} ({meal_type})")
        print(f"目标年龄段: {target_age_group}")
        print(f"营养目标: {nutrition_targets}")
        print(f"成本预算: {cost_budget}")
        
        # 1. 获取候选菜品
        candidates_by_category = self.get_candidates_by_category(
            category_rules=category_rules,
            meal_type=meal_type,
            meal=meal,
            target_age_group=target_age_group,
            max_cost_per_meal=cost_budget,
            nutrition_targets=nutrition_targets,
            ingredient_prices=ingredient_prices,
            strict_mode=strict_mode,
            flavor_filters=flavor_filters,
            season_filters=season_filters
        )
        
        # 2. 生成组合
        combinations = self.generate_plan_combinations(
            candidates_by_category=candidates_by_category,
            category_rules=category_rules,
            max_combinations=max_combinations
        )
        
        print(f"生成了 {len(combinations)} 个候选组合")
        
        # 3. 评分
        scorer = PlanScorer()
        scored_plans = []
        
        for i, combo in enumerate(combinations):
            if not combo:
                continue
                
            try:
                # 转换为字典格式供评分器使用
                dishes_dict = []
                for dish in combo:
                    dish_dict = {
                        "id": dish.id,
                        "dish_name": dish.dish_name,
                        "category": dish.category,
                        "dish_type": dish.dish_type,
                        "total_calories": dish.total_calories or 0,
                        "total_protein": dish.total_protein or 0,
                        "total_fat": dish.total_fat or 0,
                        "total_carbohydrates": dish.total_carbohydrates or 0,
                        "total_calcium": dish.total_calcium or 0,
                        "total_iron": dish.total_iron or 0,
                        "total_vitamin_c": dish.total_vitamin_c or 0,
                        "cost_price": dish.cost_price or 0,
                        "ingredient_count": dish.ingredient_count or 0,
                        "dish_recipe": dish.dish_recipe or "",
                        "season": dish.season or "",
                        "flavor": dish.flavor or "",
                        "age_group": target_age_group
                    }
                    dishes_dict.append(dish_dict)
                
                # 计算评分（返回 ScoredPlan 转成 dict 后再追加字段）
                scored_plan = scorer.score_plan(
                    dishes=dishes_dict,
                    nutrition_targets=nutrition_targets,
                    cost_budget=cost_budget,
                    age_group=target_age_group,
                    meal_type=meal_type
                )
                scored = scored_plan.to_dict()
                
                # 添加组合信息
                scored["combination_index"] = i
                scored["category_composition"] = {}
                for dish in combo:
                    cat = dish.category.strip() if dish.category else "未分类"
                    scored["category_composition"][cat] = scored["category_composition"].get(cat, 0) + 1
                
                # 权重用于下游展示
                w = scorer.weights
                scored["weight_nutrition"] = getattr(w, "WEIGHT_NUTRITION", 0.4)
                scored["weight_cost"] = getattr(w, "WEIGHT_COST", 0.35)
                scored["weight_variety"] = getattr(w, "WEIGHT_INGREDIENT_VARIETY", 0.25)
                
                scored_plans.append(scored)
                
                # 打印前几个组合的评分
                if i < 3:
                    print(f"组合 #{i+1} 评分: {scored['total_score']:.2f}")
                    print(f"  营养分: {scored['nutrition_score']:.2f}")
                    print(f"  成本分: {scored['cost_score']:.2f}")
                    print(f"  多样性分: {scored['variety_score']:.2f}")
                    print(f"  菜品: {[d.dish_name for d in combo[:3]]}...")
            
            except Exception as e:
                print(f"组合 #{i+1} 评分失败: {e}")
                continue
        
        if not scored_plans:
            print("警告: 没有生成任何有效评分计划")
            return []
        
        # 4. 排序和选择
        scored_plans.sort(key=lambda x: x["total_score"], reverse=True)
        selected_plans = scored_plans[:top_n]
        
        print(f"\n=== 评分结果 ===")
        print(f"总候选计划数: {len(scored_plans)}")
        print(f"选择前 {top_n} 个最佳计划")
        
        for i, plan in enumerate(selected_plans):
            print(f"计划 #{i+1} 总分: {plan['total_score']:.2f}")
            print(f"  权重分布 - 营养: {plan['weight_nutrition']*100:.1f}%, "
                  f"成本: {plan['weight_cost']*100:.1f}%, "
                  f"多样性: {plan['weight_variety']*100:.1f}%")
        
        return selected_plans