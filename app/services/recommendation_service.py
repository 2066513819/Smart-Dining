"""
餐饮推荐服务 - 重构版本
提供健壮的、可扩展的推荐功能，支持多种推荐策略和智能降级
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc, asc
import random
import math
from datetime import datetime
import logging
import traceback

from app.models.menu_item import MenuItem
from app.models.user import User
from app.config.guideline_meal_rules import get_guideline_meal_rules, get_default_meal_rules
from app.config.recommendation_weights import RecommendationWeights
from app.core.exceptions import RecommendationException
from app.utils.plan_scorer import PlanScorer, CombinationGenerator, select_best_plans, ScoredPlan
from app.config.guideline_nutrition_standards import get_nutrition_targets

logger = logging.getLogger(__name__)


def _console_step(step: int, message: str, detail: str = ""):
    """输出推荐过程到控制台，便于观察筛选与评分流程"""
    line = f"  [推荐过程] 步骤{step}: {message}"
    if detail:
        line += f" | {detail}"
    print(line, flush=True)


class RecommendationService:
    """餐饮推荐服务"""
    
    def __init__(self, db: Session, user: User = None):
        self.db = db
        self.user = user
        self.weights = RecommendationWeights()
        
    def recommend_by_meal_type(
        self,
        meal_type: str,
        count: int = 5,
        categories: List[str] = None,
        flavors: List[str] = None,
        seasons: List[str] = None,
        nutrition_requirements: List[str] = None,
        ingredients: List[str] = None,
        exclude_ids: List[int] = None,
        max_cost: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        根据餐次类型推荐菜品
        
        Args:
            meal_type: 餐次类型 (breakfast/lunch/dinner)
            count: 推荐数量
            categories: 菜品分类列表
            flavors: 口味列表
            seasons: 时令列表
            nutrition_requirements: 营养需求
            ingredients: 已有食材列表
            exclude_ids: 排除的菜品ID
            max_cost: 最大成本
            
        Returns:
            菜品推荐列表
        """
        try:
            # 基础查询
            query = self.db.query(MenuItem).filter(MenuItem.dish_type == meal_type)
            
            # 应用过滤条件
            query = self._apply_filters(
                query=query,
                categories=categories,
                flavors=flavors,
                seasons=seasons,
                exclude_ids=exclude_ids,
                max_cost=max_cost
            )
            
            # 获取符合条件的菜品总数
            total_count = query.count()
            
            if total_count == 0:
                logger.warning(f"没有找到符合条件的{meal_type}菜品")
                return []
            
            # 获取更多候选菜品用于评分
            sample_size = min(max(count * 10, 50), total_count)
            candidates = query.order_by(func.random()).limit(sample_size).all()
            
            # 如果有食材要求，进行匹配度评分
            if ingredients:
                candidates = self._score_by_ingredients(candidates, ingredients)
            
            # 如果有营养要求，应用营养筛选
            if nutrition_requirements:
                candidates = self._filter_by_nutrition(candidates, nutrition_requirements)
            
            # 最终选择
            selected = candidates[:count]
            
            # 转换为响应格式
            return self._format_menu_items(selected)
            
        except Exception as e:
            logger.error(f"餐次推荐失败: {str(e)}\n{traceback.format_exc()}")
            raise RecommendationException(f"餐次推荐失败: {str(e)}")
    
    def recommend_by_category_rules(
        self,
        meal_type: str,
        category_rules: Dict[str, int],
        flavors: List[str] = None,
        seasons: List[str] = None,
        ingredients: List[str] = None,
        exclude_ids: List[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        根据分类规则推荐菜品（用于严格的配餐规则）
        
        Args:
            meal_type: 餐次类型
            category_rules: 分类规则，格式: {"主食类": 2, "素菜类": 1, ...}
            flavors: 口味列表
            seasons: 时令列表
            ingredients: 已有食材列表
            exclude_ids: 排除的菜品ID
            
        Returns:
            按分类分组的菜品推荐
        """
        try:
            result = {}
            
            for category, required_count in category_rules.items():
                if required_count <= 0:
                    continue
                    
                # 查询该分类的菜品
                query = self.db.query(MenuItem).filter(
                    MenuItem.dish_type == meal_type,
                    MenuItem.category.like(f"%{category}%")
                )
                
                # 应用其他过滤条件
                if flavors:
                    query = query.filter(MenuItem.flavor.in_(flavors))
                if seasons:
                    query = query.filter(MenuItem.season.in_(seasons))
                if exclude_ids:
                    query = query.filter(MenuItem.id.not_in(exclude_ids))
                
                # 获取菜品
                candidates = query.order_by(func.random()).limit(required_count * 3).all()
                
                # 如果有食材要求，进行匹配度排序
                if ingredients and candidates:
                    candidates = self._score_by_ingredients(candidates, ingredients)
                
                # 选择指定数量的菜品
                selected = candidates[:required_count]
                
                # 转换为响应格式
                result[category] = self._format_menu_items(selected)
                
                # 更新排除ID，避免重复推荐
                if exclude_ids is not None:
                    exclude_ids.extend([item.id for item in selected])
            
            return result
            
        except Exception as e:
            logger.error(f"分类规则推荐失败: {str(e)}\n{traceback.format_exc()}")
            raise RecommendationException(f"分类规则推荐失败: {str(e)}")
    
    def recommend_meal_set(
        self,
        days: int = 1,
        meal_types: List[str] = None,
        category_rules: Dict[str, Dict[str, int]] = None,
        flavors: List[str] = None,
        seasons: List[str] = None,
        ingredients: List[str] = None,
        max_cost_per_meal: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        生成多日套餐推荐
        
        Args:
            days: 天数
            meal_types: 餐次类型列表
            category_rules: 分类规则，按餐次分组
            flavors: 口味列表
            seasons: 时令列表
            ingredients: 已有食材列表
            max_cost_per_meal: 各餐次最大成本
            
        Returns:
            套餐推荐计划
        """
        try:
            if not meal_types:
                meal_types = ["breakfast", "lunch", "dinner"]
            
            if not category_rules:
                # 获取默认的配餐规则
                meal_rules = get_guideline_meal_rules()
                category_rules = {
                    meal: meal_rules.get(meal, {})
                    for meal in meal_types
                }
            
            result = []
            all_excluded_ids = []
            
            for day in range(1, days + 1):
                day_plan = {
                    "day": day,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "meals": {}
                }
                
                total_day_cost = 0.0
                
                for meal_type in meal_types:
                    # 获取该餐次的分类规则
                    rules = category_rules.get(meal_type, {})
                    
                    if not rules:
                        # 如果没有规则，使用普通推荐
                        recommendations = self.recommend_by_meal_type(
                            meal_type=meal_type,
                            count=3,
                            flavors=flavors,
                            seasons=seasons,
                            ingredients=ingredients,
                            exclude_ids=all_excluded_ids,
                            max_cost=max_cost_per_meal.get(meal_type) if max_cost_per_meal else None
                        )
                    else:
                        # 使用分类规则推荐
                        category_results = self.recommend_by_category_rules(
                            meal_type=meal_type,
                            category_rules=rules,
                            flavors=flavors,
                            seasons=seasons,
                            ingredients=ingredients,
                            exclude_ids=all_excluded_ids
                        )
                        
                        # 平铺结果
                        recommendations = []
                        for category_items in category_results.values():
                            recommendations.extend(category_items)
                    
                    # 计算该餐次总成本
                    meal_cost = sum(item.get("cost_price", 0) for item in recommendations)
                    total_day_cost += meal_cost
                    
                    # 更新排除ID
                    all_excluded_ids.extend([item["id"] for item in recommendations])
                    
                    day_plan["meals"][meal_type] = {
                        "recommendations": recommendations,
                        "total_cost": round(meal_cost, 2),
                        "category_rules": rules if rules else None
                    }
                
                day_plan["total_cost"] = round(total_day_cost, 2)
                result.append(day_plan)
            
            return result
            
        except Exception as e:
            logger.error(f"套餐推荐失败: {str(e)}\n{traceback.format_exc()}")
            raise RecommendationException(f"套餐推荐失败: {str(e)}")
    
    def recommend_smart(
        self,
        request_data: Dict[str, Any],
        user: User = None
    ) -> Dict[str, Any]:
        """
        智能推荐 - 根据上下文自动选择最佳推荐策略
        
        Args:
            request_data: 请求数据
            user: 用户信息
            
        Returns:
            推荐结果和元数据
        """
        try:
            # 解析请求参数
            meal_type = request_data.get("meal_type", "lunch")
            count = request_data.get("count", 5)
            categories = request_data.get("categories", [])
            flavors = request_data.get("flavors", [])
            seasons = request_data.get("seasons", [])
            nutrition_requirements = request_data.get("nutrition_requirements", [])
            ingredients = request_data.get("ingredients", [])
            exclude_ids = request_data.get("exclude_ids", [])
            max_cost = request_data.get("max_cost")
            
            # 策略选择逻辑
            use_category_rules = bool(categories) and len(categories) > 0
            has_specific_requirements = any([
                nutrition_requirements,
                ingredients,
                max_cost is not None
            ])
            
            # 确定推荐策略
            strategy = "category_rules" if use_category_rules else "meal_type"
            
            if strategy == "category_rules":
                # 构建分类规则
                category_rules = {category: 1 for category in categories}
                category_results = self.recommend_by_category_rules(
                    meal_type=meal_type,
                    category_rules=category_rules,
                    flavors=flavors,
                    seasons=seasons,
                    ingredients=ingredients,
                    exclude_ids=exclude_ids
                )
                
                # 平铺结果
                recommendations = []
                for category_items in category_results.values():
                    recommendations.extend(category_items)
                
                recommendations = recommendations[:count]
                
            else:
                # 使用餐次类型推荐
                recommendations = self.recommend_by_meal_type(
                    meal_type=meal_type,
                    count=count,
                    flavors=flavors,
                    seasons=seasons,
                    nutrition_requirements=nutrition_requirements,
                    ingredients=ingredients,
                    exclude_ids=exclude_ids,
                    max_cost=max_cost
                )
            
            # 计算统计信息
            stats = self._calculate_recommendation_stats(recommendations)
            
            return {
                "success": True,
                "strategy": strategy,
                "recommendations": recommendations,
                "metadata": {
                    "total_recommended": len(recommendations),
                    "stats": stats,
                    "user_context": {
                        "has_ingredients": bool(ingredients),
                        "has_dietary_restrictions": bool(nutrition_requirements),
                        "has_cost_limit": max_cost is not None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"智能推荐失败: {str(e)}\n{traceback.format_exc()}")
            
            # 尝试降级到简单推荐
            try:
                recommendations = self._fallback_recommendation(
                    meal_type=request_data.get("meal_type", "lunch"),
                    count=request_data.get("count", 5)
                )
                
                return {
                    "success": True,
                    "strategy": "fallback",
                    "recommendations": recommendations,
                    "metadata": {
                        "total_recommended": len(recommendations),
                        "note": "使用降级推荐策略",
                        "error": str(e)
                    }
                }
            except Exception as fallback_error:
                logger.error(f"降级推荐也失败: {str(fallback_error)}")
                raise RecommendationException(f"所有推荐策略都失败: {str(e)}")
    
    def recommend_with_weighted_scoring(
        self,
        meal_type: str,
        age_group: str,
        category_rules: Dict[str, int],
        cost_budget: float,
        flavors: List[str] = None,
        seasons: List[str] = None,
        ingredients: List[str] = None,
        max_combinations: int = 100,
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        权重评分推荐 - 核心新方法
        
        算法流程：
        1. 根据配餐规则获取候选菜品
        2. 生成多种菜品组合方案
        3. 按权重计算每个方案的综合评分
           - 营养值达标率：40%
           - 成本控制：35%
           - 食材种类多样性：25%
        4. 选择评分最高的方案推荐给用户
        
        Args:
            meal_type: 餐次类型 (breakfast/lunch/dinner)
            age_group: 年龄段 (primary_low/junior_high/senior等)
            category_rules: 分类规则，如 {"主食类": 1, "荤菜类": 1, "素菜类": 2}
            cost_budget: 成本预算
            flavors: 口味列表
            seasons: 时令列表
            ingredients: 已有食材列表
            max_combinations: 最大评估组合数
            top_n: 返回的最佳计划数量
            
        Returns:
            Dict: 包含最佳推荐计划和所有评分的详细结果
        """
        try:
            print("", flush=True)
            print("========== 餐饮推荐 · 筛选与评分过程 ==========", flush=True)
            _console_step(1, "开始推荐", f"餐次={meal_type}, 年龄段={age_group}, 预算={cost_budget}元")
            _console_step(0, "分类规则", str(category_rules))
            logger.info(f"[权重评分推荐] 开始: meal={meal_type}, age={age_group}, budget={cost_budget}")
            logger.info(f"[权重评分推荐] 分类规则: {category_rules}")
            
            # 1. 获取营养目标
            try:
                nutrition_targets = get_nutrition_targets(age_group, meal_type)
                _console_step(2, "获取营养目标", f"热量目标≈{nutrition_targets.get('target_calories', 0):.0f}kcal 等")
                logger.info(f"[权重评分推荐] 营养目标: {nutrition_targets}")
            except Exception as e:
                logger.error(f"[权重评分推荐] 获取营养目标失败: {str(e)}")
                raise RecommendationException(f"获取营养目标失败: {str(e)}")
            
            # 2. 按分类获取候选菜品
            _console_step(3, "按分类拉取候选菜品", "查询数据库...")
            logger.info(f"[权重评分推荐] 开始获取候选菜品...")
            candidates_by_category = self._get_candidates_by_category(
                meal_type=meal_type,
                category_rules=category_rules,
                flavors=flavors,
                seasons=seasons,
                ingredients=ingredients
            )
            
            # 详细记录每个分类的候选数
            total_candidates = 0
            for category, items in candidates_by_category.items():
                count = len(items) if items else 0
                total_candidates += count
                _console_step(0, f"  分类「{category}」", f"候选数={count}")
                logger.info(f"[权重评分推荐] 分类 '{category}' 候选菜品数: {count}")
            _console_step(4, "候选汇总", f"共 {total_candidates} 个候选菜品")
            logger.info(f"[权重评分推荐] 候选菜品总数: {total_candidates}")
            
            if not candidates_by_category or total_candidates == 0:
                print("  [推荐过程] 未找到任何候选菜品，请检查数据库或分类规则。", flush=True)
                print("========== 推荐过程结束 ==========", flush=True)
                logger.warning(f"[权重评分推荐] 没有找到符合条件的候选菜品")
                logger.warning(f"[权重评分推荐]  meal_type={meal_type}, category_rules={category_rules}")
                return self._create_empty_result(
                    "没有找到符合条件的候选菜品",
                    context={
                        "meal_type": meal_type,
                        "category_rules": category_rules,
                        "flavors": flavors,
                        "seasons": seasons,
                        "candidates_by_category": {
                            cat: len(items) for cat, items in candidates_by_category.items()
                        } if candidates_by_category else {}
                    }
                )
            
            # 3. 生成多种组合方案
            _console_step(5, "生成组合方案", f"最多生成 {max_combinations} 种组合...")
            logger.info(f"[权重评分推荐] 开始生成组合方案...")
            try:
                generator = CombinationGenerator(candidates_by_category)
                combinations = generator.generate_combinations(
                    category_rules=category_rules,
                    max_combinations=max_combinations
                )
                _console_step(6, "组合生成完成", f"共 {len(combinations)} 种方案待评分")
                logger.info(f"[权重评分推荐] 生成了 {len(combinations)} 种组合方案")
            except Exception as e:
                logger.error(f"[权重评分推荐] 生成组合方案失败: {str(e)}")
                logger.error(traceback.format_exc())
                raise RecommendationException(f"生成组合方案失败: {str(e)}")
            
            if not combinations:
                print("  [推荐过程] 无法生成有效组合（某分类候选不足）。", flush=True)
                print("========== 推荐过程结束 ==========", flush=True)
                logger.warning(f"[权重评分推荐] 无法生成有效的菜品组合")
                return self._create_empty_result(
                    "无法生成有效的菜品组合",
                    context={
                        "candidates_summary": {
                            cat: len(items) for cat, items in candidates_by_category.items()
                        },
                        "category_rules": category_rules,
                        "meal_type": meal_type
                    }
                )
            
            # 4. 初始化评分器
            try:
                scorer = PlanScorer(self.weights)
                _console_step(7, "初始化评分器", "权重: 营养40% + 成本35% + 食材种类25%")
                logger.info(f"[权重评分推荐] 评分器初始化成功")
            except Exception as e:
                logger.error(f"[权重评分推荐] 评分器初始化失败: {str(e)}")
                raise RecommendationException(f"评分器初始化失败: {str(e)}")
            
            # 5. 对每个组合进行评分
            _console_step(8, "开始按权重评分", f"对 {len(combinations)} 个组合逐一评分...")
            logger.info(f"[权重评分推荐] 开始评分 {len(combinations)} 个组合...")
            scored_plans = []
            for i, combo in enumerate(combinations):
                try:
                    # 将菜品对象转换为字典格式
                    dishes = self._format_menu_items([d for d in combo if hasattr(d, 'dish_name')])
                    if not dishes:  # 如果已经是字典格式
                        dishes = combo
                    
                    if not dishes:
                        logger.warning(f"[权重评分推荐] 组合 {i} 没有有效菜品，跳过")
                        continue
                    
                    plan = scorer.score_plan(
                        dishes=dishes,
                        nutrition_targets=nutrition_targets,
                        cost_budget=cost_budget,
                        age_group=age_group,
                        meal_type=meal_type
                    )
                    scored_plans.append(plan)
                    
                    # 控制台：前5个组合打印详情，之后每10个打印进度
                    if i < 5:
                        _console_step(0, f"  组合{i+1} 评分", 
                                    f"综合={plan.total_score:.1f} (营养={plan.nutrition_score:.1f}, 成本={plan.cost_score:.1f}, 多样={plan.variety_score:.1f}) 成本={plan.total_cost:.2f}元")
                    elif (i + 1) % 10 == 0 or i == len(combinations) - 1:
                        print(f"  [推荐过程] 已评分 {i+1}/{len(combinations)} 个组合...", flush=True)
                    
                    if i < 3:  # 只记录前3个的详细信息
                        logger.info(f"[权重评分推荐] 组合 {i} 评分: total={plan.total_score:.2f}, "
                                  f"nutrition={plan.nutrition_score:.2f}, "
                                  f"cost={plan.cost_score:.2f}, "
                                  f"variety={plan.variety_score:.2f}")
                except Exception as e:
                    logger.error(f"[权重评分推荐] 评分组合 {i} 失败: {str(e)}")
                    # 继续评分其他组合，不中断
                    continue
            
            _console_step(9, "评分完成", f"成功 {len(scored_plans)}/{len(combinations)} 个组合")
            logger.info(f"[权重评分推荐] 成功评分 {len(scored_plans)}/{len(combinations)} 个组合")
            
            if not scored_plans:
                print("  [推荐过程] 所有组合评分均失败，请检查菜品数据格式或营养数据。", flush=True)
                print("========== 推荐过程结束 ==========", flush=True)
                logger.error(f"[权重评分推荐] 所有组合评分失败")
                return self._create_empty_result(
                    "所有组合评分失败",
                    context={
                        "total_combinations": len(combinations),
                        "sample_dish": combinations[0] if combinations else None,
                        "meal_type": meal_type,
                        "nutrition_targets": nutrition_targets
                    }
                )
            
            # 6. 选择评分最高的计划
            try:
                best_plans = select_best_plans(scored_plans, top_n=top_n)
                _console_step(10, "选出最佳方案", f"取前 {len(best_plans)} 名")
                if best_plans:
                    p = best_plans[0]
                    dish_names = [d.get("dish_name", getattr(d, "dish_name", "?")) for d in p.dishes]
                    print(f"  [推荐过程] 第1名: 综合分={p.total_score:.2f} 成本={p.total_cost:.2f}元 菜品: {dish_names}", flush=True)
                logger.info(f"[权重评分推荐] 选出 {len(best_plans)} 个最佳计划")
            except Exception as e:
                logger.error(f"[权重评分推荐] 选择最佳计划失败: {str(e)}")
                raise RecommendationException(f"选择最佳计划失败: {str(e)}")
            
            if not best_plans:
                print("  [推荐过程] 没有满足条件的推荐方案。", flush=True)
                print("========== 推荐过程结束 ==========", flush=True)
                logger.warning(f"[权重评分推荐] 没有满足条件的推荐方案")
                return self._create_empty_result(
                    "没有满足条件的推荐方案",
                    context={
                        "scored_plans_count": len(scored_plans),
                        "top_n": top_n,
                        "cost_budget": cost_budget,
                        "age_group": age_group,
                        "meal_type": meal_type
                    }
                )
            
            # 7. 构建返回结果
            result = {
                "success": True,
                "strategy": "weighted_scoring",
                "age_group": age_group,
                "meal_type": meal_type,
                "weights": {
                    "nutrition": self.weights.WEIGHT_NUTRITION,
                    "cost": self.weights.WEIGHT_COST,
                    "ingredient_variety": self.weights.WEIGHT_INGREDIENT_VARIETY
                },
                "nutrition_targets": nutrition_targets,
                "cost_budget": cost_budget,
                "best_plan": best_plans[0].to_dict() if best_plans else None,
                "alternative_plans": [p.to_dict() for p in best_plans[1:]] if len(best_plans) > 1 else [],
                "all_scored_plans": [p.to_dict() for p in scored_plans[:10]],  # 前10个供参考
                "metadata": {
                    "total_combinations_evaluated": len(combinations),
                    "total_plans_scored": len(scored_plans),
                    "best_score": round(best_plans[0].total_score, 2) if best_plans else 0,
                    "category_rules": category_rules
                }
            }
            
            logger.info(f"[权重评分推荐] 完成: 最佳评分={result['metadata']['best_score']}, "
                       f"评估了 {result['metadata']['total_combinations_evaluated']} 个组合")
            print("========== 推荐过程结束 ==========", flush=True)
            print("", flush=True)
            return result
            
        except Exception as e:
            print(f"  [推荐过程] 失败: {str(e)}", flush=True)
            print("========== 推荐过程结束 ==========", flush=True)
            logger.error(f"[权重评分推荐] 失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise RecommendationException(f"权重评分推荐失败: {str(e)}")
    
    def recommend_meal_plan_with_scoring(
        self,
        days: int,
        age_group: str,
        meal_types: List[str],
        cost_budget_per_meal: Dict[str, float],
        flavors: List[str] = None,
        seasons: List[str] = None,
        ingredients: List[str] = None
    ) -> Dict[str, Any]:
        """
        带权重评分的一日/多日餐饮计划推荐
        
        为每个餐次生成多个候选方案，选择评分最高的组合
        
        Args:
            days: 天数
            age_group: 年龄段
            meal_types: 餐次类型列表
            cost_budget_per_meal: 每餐成本预算
            flavors: 口味列表
            seasons: 时令列表
            ingredients: 已有食材列表
            
        Returns:
            Dict: 多日餐饮计划
        """
        try:
            # 获取默认配餐规则
            from app.config.guideline_meal_rules import get_guideline_meal_rules
            meal_rules = get_guideline_meal_rules(age_group)
            
            result_days = []
            
            for day in range(1, days + 1):
                day_plan = {
                    "day": day,
                    "meals": {}
                }
                
                for meal_type in meal_types:
                    # 获取该餐次的分类规则和预算
                    category_rules = meal_rules.get(meal_type, {})
                    budget = cost_budget_per_meal.get(meal_type, 20.0)
                    
                    if not category_rules:
                        # 没有规则时使用默认规则
                        category_rules = self._get_default_category_rules(meal_type)
                    
                    # 使用权重评分推荐
                    meal_result = self.recommend_with_weighted_scoring(
                        meal_type=meal_type,
                        age_group=age_group,
                        category_rules=category_rules,
                        cost_budget=budget,
                        flavors=flavors,
                        seasons=seasons,
                        ingredients=ingredients,
                        max_combinations=50,
                        top_n=1
                    )
                    
                    day_plan["meals"][meal_type] = meal_result
                
                result_days.append(day_plan)
            
            return {
                "success": True,
                "strategy": "weighted_scoring_meal_plan",
                "days": result_days,
                "metadata": {
                    "total_days": days,
                    "age_group": age_group,
                    "weights": {
                        "nutrition": self.weights.WEIGHT_NUTRITION,
                        "cost": self.weights.WEIGHT_COST,
                        "ingredient_variety": self.weights.WEIGHT_INGREDIENT_VARIETY
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"餐饮计划推荐失败: {str(e)}\n{traceback.format_exc()}")
            raise RecommendationException(f"餐饮计划推荐失败: {str(e)}")
    
    def _get_candidates_by_category(
        self,
        meal_type: str,
        category_rules: Dict[str, int],
        flavors: List[str] = None,
        seasons: List[str] = None,
        ingredients: List[str] = None
    ) -> Dict[str, List[MenuItem]]:
        """按分类获取候选菜品"""
        candidates = {}
        
        logger.info(f"[_get_candidates_by_category] 开始查询: meal_type={meal_type}, rules={category_rules}")
        
        for category, required_count in category_rules.items():
            if required_count <= 0:
                logger.info(f"[_get_candidates_by_category] 跳过分类 '{category}' (required_count={required_count})")
                continue
            
            try:
                # 查询该分类的菜品
                query = self.db.query(MenuItem).filter(
                    MenuItem.dish_type == meal_type,
                    MenuItem.category.like(f"%{category}%")
                )
                
                # 应用其他过滤条件
                if flavors:
                    query = query.filter(MenuItem.flavor.in_(flavors))
                    logger.debug(f"[_get_candidates_by_category] 应用口味过滤: {flavors}")
                if seasons:
                    query = query.filter(MenuItem.season.in_(seasons))
                    logger.debug(f"[_get_candidates_by_category] 应用时令过滤: {seasons}")
                
                # 获取足够多的候选
                sample_size = max(required_count * 5, 10)
                logger.info(f"[_get_candidates_by_category] 查询分类 '{category}': sample_size={sample_size}")
                
                items = query.order_by(func.random()).limit(sample_size).all()
                
                # 如果有食材要求，进行匹配度排序
                if ingredients and items:
                    items = self._score_by_ingredients(items, ingredients)
                    logger.debug(f"[_get_candidates_by_category] 对分类 '{category}' 应用食材匹配排序")
                
                candidates[category] = items
                logger.info(f"[_get_candidates_by_category] 分类 '{category}' 找到 {len(items)} 个候选菜品")
                
                if not items:
                    logger.warning(f"[_get_candidates_by_category] 警告: 分类 '{category}' 没有找到任何菜品! "
                                 f"meal_type={meal_type}, category_pattern=%{category}%")
                    
            except Exception as e:
                logger.error(f"[_get_candidates_by_category] 查询分类 '{category}' 失败: {str(e)}")
                logger.error(traceback.format_exc())
                candidates[category] = []
        
        total = sum(len(items) for items in candidates.values())
        logger.info(f"[_get_candidates_by_category] 完成: 共 {len(candidates)} 个分类, {total} 个候选菜品")
        
        return candidates
    
    def _get_default_category_rules(self, meal_type: str) -> Dict[str, int]:
        """获取默认分类规则"""
        defaults = {
            "breakfast": {
                "主食类": 1,
                "奶及奶制品类": 1,
                "蛋类或豆制品类": 1,
                "蔬菜水果类": 1
            },
            "lunch": {
                "主食类": 1,
                "荤菜类": 1,
                "素菜类": 2,
                "汤类": 1
            },
            "dinner": {
                "主食类": 1,
                "荤菜类": 1,
                "素菜类": 2,
                "汤类": 1
            }
        }
        return defaults.get(meal_type, {"主食类": 1, "荤菜类": 1, "素菜类": 1})
    
    def _create_empty_result(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建空结果，包含详细的诊断信息和解决建议"""
        
        # 根据错误类型提供解决建议
        suggestions = {
            "没有找到符合条件的候选菜品": [
                "1. 检查数据库中是否有菜品数据",
                "2. 检查菜品分类名称是否正确（如：主食类、荤菜类、素菜类、汤类）",
                "3. 检查菜品的餐次类型是否匹配（breakfast/lunch/dinner）",
                "4. 检查是否有过多的过滤条件（口味、时令等）"
            ],
            "无法生成有效的菜品组合": [
                "1. 某些分类的候选菜品数量不足",
                "2. 请增加各分类的菜品数量",
                "3. 尝试减少每个分类的需求数量"
            ],
            "所有组合评分失败": [
                "1. 菜品数据格式可能不正确",
                "2. 检查菜品的营养数据是否完整",
                "3. 查看日志获取详细的评分错误信息"
            ],
            "没有满足条件的推荐方案": [
                "1. 所有组合的评分都太低",
                "2. 尝试降低筛选条件或放宽预算",
                "3. 增加更多的候选菜品"
            ]
        }
        
        # 获取匹配的建议
        matched_suggestions = []
        for key, suggestion_list in suggestions.items():
            if key in message:
                matched_suggestions = suggestion_list
                break
        
        if not matched_suggestions:
            matched_suggestions = ["请查看应用日志 (app.log) 获取详细错误信息"]
        
        result = {
            "success": False,
            "strategy": "weighted_scoring",
            "error": {
                "type": "EmptyResult",
                "message": message,
                "suggestions": matched_suggestions,
                "context": context or {}
            },
            "diagnosis": {
                "possible_causes": [
                    "数据库菜品数据不足",
                    "分类名称不匹配",
                    "过滤条件过于严格",
                    "菜品营养数据缺失"
                ],
                "checklist": [
                    {"item": "检查menu_items表是否有数据", "command": "SELECT COUNT(*) FROM menu_items;"},
                    {"item": "检查各餐次菜品数量", "command": "SELECT dish_type, COUNT(*) FROM menu_items GROUP BY dish_type;"},
                    {"item": "检查各分类菜品数量", "command": "SELECT category, COUNT(*) FROM menu_items GROUP BY category;"},
                    {"item": "查看示例菜品", "command": "SELECT id, dish_name, dish_type, category FROM menu_items LIMIT 5;"}
                ]
            },
            "best_plan": None,
            "alternative_plans": [],
            "all_scored_plans": [],
            "metadata": {
                "total_combinations_evaluated": 0,
                "total_plans_scored": 0,
                "best_score": 0
            }
        }
        
        # 记录详细的空结果日志
        logger.warning(f"[权重评分推荐] 空结果: {message}")
        logger.warning(f"[权重评分推荐] 解决建议: {matched_suggestions}")
        if context:
            logger.warning(f"[权重评分推荐] 上下文: {context}")
        
        return result
    
    def _apply_filters(
        self,
        query,
        categories: List[str] = None,
        flavors: List[str] = None,
        seasons: List[str] = None,
        exclude_ids: List[int] = None,
        max_cost: Optional[float] = None
    ):
        """应用过滤条件到查询"""
        if categories:
            category_filters = [MenuItem.category.like(f"%{cat}%") for cat in categories]
            query = query.filter(or_(*category_filters))
        
        if flavors:
            query = query.filter(MenuItem.flavor.in_(flavors))
        
        if seasons:
            query = query.filter(MenuItem.season.in_(seasons))
        
        if exclude_ids:
            query = query.filter(MenuItem.id.not_in(exclude_ids))
        
        if max_cost is not None:
            query = query.filter(MenuItem.cost_price <= max_cost)
        
        return query
    
    def _score_by_ingredients(
        self,
        candidates: List[MenuItem],
        user_ingredients: List[str]
    ) -> List[MenuItem]:
        """根据食材匹配度评分和排序"""
        if not candidates or not user_ingredients:
            return candidates
        
        scored_items = []
        
        for item in candidates:
            score = 0
            
            # 从菜品描述中提取食材（简化实现）
            recipe_text = item.dish_recipe or ""
            
            # 检查用户食材是否出现在菜品描述中
            for ingredient in user_ingredients:
                if ingredient.lower() in recipe_text.lower():
                    score += self.weights.INGREDIENT_MATCH
            
            # 添加分数到临时对象
            scored_items.append((item, score))
        
        # 按分数降序排序
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, score in scored_items]
    
    def _filter_by_nutrition(
        self,
        candidates: List[MenuItem],
        requirements: List[str]
    ) -> List[MenuItem]:
        """根据营养需求筛选"""
        if not candidates or not requirements:
            return candidates
        
        filtered_items = []
        
        for item in candidates:
            meets_all_requirements = True
            
            for req in requirements:
                req_lower = req.lower()
                
                if "高蛋白" in req_lower and item.total_protein < 20:
                    meets_all_requirements = False
                    break
                elif "低脂肪" in req_lower and item.total_fat > 10:
                    meets_all_requirements = False
                    break
                elif "低热量" in req_lower and item.total_calories > 400:
                    meets_all_requirements = False
                    break
                elif "补钙" in req_lower and item.total_calcium < 100:
                    meets_all_requirements = False
                    break
                elif "补铁" in req_lower and item.total_iron < 5:
                    meets_all_requirements = False
                    break
                elif "维生素c" in req_lower and item.total_vitamin_c < 50:
                    meets_all_requirements = False
                    break
            
            if meets_all_requirements:
                filtered_items.append(item)
        
        return filtered_items
    
    def _fallback_recommendation(
        self,
        meal_type: str = "lunch",
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """降级推荐 - 最简单的推荐策略"""
        query = self.db.query(MenuItem).filter(MenuItem.dish_type == meal_type)
        
        # 随机选择
        candidates = query.order_by(func.random()).limit(count * 2).all()
        
        # 确保多样性：按分类分组
        by_category = {}
        for item in candidates:
            category = item.category or "其他"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(item)
        
        # 从每个分类中选择一个
        selected = []
        for category_items in by_category.values():
            if category_items:
                selected.append(random.choice(category_items))
                if len(selected) >= count:
                    break
        
        # 如果还不够，添加更多
        if len(selected) < count:
            remaining = [item for item in candidates if item not in selected]
            selected.extend(remaining[:count - len(selected)])
        
        return self._format_menu_items(selected)
    
    def _format_menu_items(self, menu_items: List[MenuItem]) -> List[Dict[str, Any]]:
        """格式化菜单项为响应格式"""
        result = []
        
        for item in menu_items:
            formatted = {
                "id": item.id,
                "dish_type": item.dish_type,
                "dish_name": item.dish_name,
                "category": item.category or "",
                "dish_recipe": item.dish_recipe or "",
                "total_calories": float(item.total_calories or 0),
                "total_carbohydrates": float(item.total_carbohydrates or 0),
                "total_fat": float(item.total_fat or 0),
                "total_protein": float(item.total_protein or 0),
                "total_calcium": float(item.total_calcium or 0),
                "total_iron": float(item.total_iron or 0),
                "total_vitamin_c": float(item.total_vitamin_c or 0),
                "ingredient_count": item.ingredient_count or 0,
                "matched_count": item.matched_count or 0,
                "season": item.season or "",
                "flavor": item.flavor or "",
                "cost_price": float(item.cost_price or 0),
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            }
            
            # 确保没有NaN或Inf值
            for key in [
                "total_calories", "total_carbohydrates", "total_fat",
                "total_protein", "total_calcium", "total_iron",
                "total_vitamin_c", "cost_price"
            ]:
                value = formatted[key]
                if value is None or math.isnan(value) or math.isinf(value):
                    formatted[key] = 0.0
            
            result.append(formatted)
        
        return result
    
    def _calculate_recommendation_stats(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算推荐结果的统计信息"""
        if not recommendations:
            return {
                "total_items": 0,
                "avg_calories": 0,
                "avg_protein": 0,
                "total_cost": 0,
                "category_distribution": {}
            }
        
        total_calories = sum(item["total_calories"] for item in recommendations)
        total_protein = sum(item["total_protein"] for item in recommendations)
        total_cost = sum(item["cost_price"] for item in recommendations)
        
        # 分类分布
        category_dist = {}
        for item in recommendations:
            category = item["category"] or "其他"
            category_dist[category] = category_dist.get(category, 0) + 1
        
        return {
            "total_items": len(recommendations),
            "avg_calories": round(total_calories / len(recommendations), 1),
            "avg_protein": round(total_protein / len(recommendations), 1),
            "total_cost": round(total_cost, 2),
            "avg_cost": round(total_cost / len(recommendations), 2),
            "category_distribution": category_dist
        }