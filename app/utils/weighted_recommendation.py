"""
加权推荐功能
实现真正的多计划权重评分筛选
"""

from typing import List, Dict, Any, Optional, Tuple
import copy
import json
from sqlalchemy.orm import Session
import traceback

from app.models.menu_item import MenuItem
from app.schemas.dish import MealSetRecommendationRequest
from app.utils.candidate_generator import CandidateGenerator
from app.utils.plan_scorer import PlanScorer
from app.config.guideline_portion_ratios import portion_ratio_for_meal
from app.config.guideline_nutrition_standards import get_nutrition_targets


class WeightedRecommendation:
    """加权推荐类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.candidate_generator = CandidateGenerator(db)
        self.plan_scorer = PlanScorer()
    
    def generate_weighted_meal_set(
        self,
        request: MealSetRecommendationRequest,
        meal_rules: Dict[str, Any],
        target_age_group: str,
        ingredient_prices: Optional[Dict[str, float]] = None,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        生成加权评分的套餐
        
        Args:
            request: 推荐请求
            meal_rules: 餐次规则
            target_age_group: 目标年龄段
            ingredient_prices: 食材价格映射
            strict_mode: 严格模式
            
        Returns:
            Dict[str, Any]: 加权评分的套餐结果
        """
        print(f"\n=== 开始加权套餐推荐 ===")
        print(f"天数: {request.days}")
        print(f"餐次类型: {getattr(request, 'meal_types', None) or ['breakfast', 'lunch', 'dinner']}")
        print(f"年龄段: {target_age_group}")
        
        # 存储每天的结果
        all_weighted_days = []
        
        # 为每天生成多个候选计划
        # 兼容两种规则结构：per_meal（旧）或顶层 breakfast/lunch/dinner（与 load_meal_rules 一致）
        per_meal = meal_rules.get("per_meal")
        if not per_meal or not isinstance(per_meal, dict):
            per_meal = {
                k: meal_rules[k] for k in ("breakfast", "lunch", "dinner")
                if k in meal_rules and isinstance(meal_rules.get(k), dict)
            }
        
        for day_idx in range(request.days):
            print(f"\n--- 生成第 {day_idx+1} 天加权计划 ---")
            
            # 对每个餐次生成加权计划
            day_weighted_plans = {}
            
            for meal, per_cat in per_meal.items():
                print(f"\n  餐次: {meal}")
                # 请求里可能是 meal_types 列表，这里按当前餐次用 meal 作为 meal_type
                meal_type_for_query = getattr(request, "meal_type", None) or meal
                
                # 获取营养目标（使用指南标准，与配置模块一致）
                nutrition_targets = get_nutrition_targets(target_age_group, meal)
                
                # 获取成本预算（支持 costs.breakfast / costs.lunch / costs.dinner）
                cost_budget = None
                if "max_cost_per_meal" in meal_rules:
                    cost_budget = meal_rules["max_cost_per_meal"]
                elif isinstance(meal_rules.get("costs"), dict):
                    cost_budget = meal_rules["costs"].get(meal)
                
                # 口味过滤（请求可能是 flavor 列表）
                flavor_filters = []
                if getattr(request, "flavor_preference", None):
                    flavor_filters = [request.flavor_preference]
                elif getattr(request, "flavor", None):
                    flavor_filters = request.flavor if isinstance(request.flavor, list) else [request.flavor]
                
                # 时令过滤
                season_filters = []
                if getattr(request, "season", None):
                    season_filters = request.season if isinstance(request.season, list) else [request.season]
                
                # 生成加权计划
                weighted_plans = self.candidate_generator.generate_weighted_plans(
                    category_rules=per_cat,
                    meal_type=meal_type_for_query,
                    meal=meal,
                    target_age_group=target_age_group,
                    nutrition_targets=nutrition_targets,
                    cost_budget=cost_budget,
                    max_combinations=30,  # 生成30个候选组合
                    top_n=3,  # 选择前3个最佳计划
                    ingredient_prices=ingredient_prices,
                    strict_mode=strict_mode,
                    flavor_filters=flavor_filters,
                    season_filters=season_filters
                )
                
                if weighted_plans:
                    # 选择最佳计划
                    best_plan = weighted_plans[0]
                    
                    # 格式化菜品信息
                    meal_items = self._format_dishes_for_meal(
                        dishes=best_plan.get("dishes", []),
                        request=request,
                        target_age_group=target_age_group,
                        meal=meal,
                        meal_rules=meal_rules
                    )
                    
                    # 添加评分信息
                    meal_summary = {
                        "weighted_score": best_plan.get("total_score", 0),
                        "nutrition_score": best_plan.get("nutrition_score", 0),
                        "cost_score": best_plan.get("cost_score", 0),
                        "variety_score": best_plan.get("variety_score", 0),
                        "weight_nutrition": best_plan.get("weight_nutrition", 0.4),
                        "weight_cost": best_plan.get("weight_cost", 0.35),
                        "weight_variety": best_plan.get("weight_variety", 0.25),
                        "candidate_plans_evaluated": len(weighted_plans),
                        "plan_rank": 1
                    }
                    
                    day_weighted_plans[meal] = {
                        "items": meal_items,
                        "summary": meal_summary
                    }
                    
                    print(f"  选择最佳计划: 总分 {best_plan['total_score']:.2f}")
                    print(f"    营养分: {best_plan['nutrition_score']:.2f}")
                    print(f"    成本分: {best_plan['cost_score']:.2f}")
                    print(f"    多样性分: {best_plan['variety_score']:.2f}")
                else:
                    print(f"  警告: 未生成有效加权计划")
                    day_weighted_plans[meal] = {
                        "items": [],
                        "summary": {
                            "weighted_score": 0,
                            "error": "无法生成加权评分计划"
                        }
                    }
            
            all_weighted_days.append(day_weighted_plans)
        
        # 生成最终结果
        result = {
            "weighted_recommendation": True,
            "days": all_weighted_days,
            "total_days": request.days,
            "meal_types": getattr(request, "meal_types", None) or ["breakfast", "lunch", "dinner"],
            "target_age_group": target_age_group,
            "evaluation_summary": self._generate_evaluation_summary(all_weighted_days)
        }
        
        return result
    
    def _format_dishes_for_meal(
        self,
        dishes: List[Dict[str, Any]],
        request: MealSetRecommendationRequest,
        target_age_group: str,
        meal: str,
        meal_rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """格式化菜品信息"""
        formatted_items = []
        
        for dish_data in dishes:
            # 获取菜品对象
            dish_id = dish_data.get("id")
            dish = self.db.query(MenuItem).filter(MenuItem.id == dish_id).first()
            
            if not dish:
                continue
            
            # 调整营养（按年龄段）
            base_nutrition = {
                "total_calories": dish.total_calories or 0,
                "total_carbohydrates": dish.total_carbohydrates or 0,
                "total_fat": dish.total_fat or 0,
                "total_protein": dish.total_protein or 0,
                "total_calcium": dish.total_calcium or 0,
                "total_iron": dish.total_iron or 0,
                "total_vitamin_c": dish.total_vitamin_c or 0,
            }
            
            # 调整配方克数
            portion_factor = portion_ratio_for_meal(target_age_group, meal)
            
            # 团餐模式调整
            if meal_rules.get("dining_style") == "团餐":
                portion_factor = float(portion_factor) * 1.2
            
            # 调整成本（cost_price 可能为 Decimal，需转 float 再与 1.2 运算）
            adjusted_cost = float(dish.cost_price or 0)
            if meal_rules.get("dining_style") == "团餐":
                adjusted_cost *= 1.2
            
            formatted_item = {
                "id": dish.id,
                "dish_type": dish.dish_type,
                "dish_name": dish.dish_name,
                "category": dish.category or "",
                "dish_recipe": dish.dish_recipe or "",
                "total_calories": round(base_nutrition["total_calories"], 2),
                "total_carbohydrates": round(base_nutrition["total_carbohydrates"], 2),
                "total_fat": round(base_nutrition["total_fat"], 2),
                "total_protein": round(base_nutrition["total_protein"], 2),
                "total_calcium": round(base_nutrition["total_calcium"], 2),
                "total_iron": round(base_nutrition["total_iron"], 2),
                "total_vitamin_c": round(base_nutrition["total_vitamin_c"], 2),
                "ingredient_count": dish.ingredient_count or 0,
                "matched_count": self._calc_match_count(dish, getattr(request, "ingredient_list", None) or getattr(request, "ingredients", []) or []),
                "season": dish.season or "",
                "flavor": dish.flavor or "",
                "cost_price": round(adjusted_cost, 2),
                "age_group": target_age_group,
                "portion_factor": round(portion_factor, 2),
                "original_id": dish_id
            }
            
            formatted_items.append(formatted_item)
        
        return formatted_items
    
    def _calc_match_count(self, dish: MenuItem, ingredient_list: List[str]) -> int:
        """计算食材匹配数量"""
        if not ingredient_list:
            return 0
        
        dish_recipe = dish.dish_recipe or ""
        matched = 0
        
        for ingredient in ingredient_list:
            if ingredient.strip() and ingredient.strip() in dish_recipe:
                matched += 1
        
        return matched
    
    def _generate_evaluation_summary(self, weighted_days: List[Dict]) -> Dict[str, Any]:
        """生成评估摘要"""
        if not weighted_days:
            return {"error": "无评估数据"}
        
        total_plans = 0
        total_score = 0
        best_day_score = 0
        best_day_idx = 0
        
        for day_idx, day_plans in enumerate(weighted_days):
            day_score = 0
            meal_count = 0
            
            for meal, data in day_plans.items():
                if "summary" in data:
                    score = data["summary"].get("weighted_score", 0)
                    day_score += score
                    total_score += score
                    meal_count += 1
                    total_plans += 1
            
            if meal_count > 0:
                day_avg_score = day_score / meal_count
                if day_avg_score > best_day_score:
                    best_day_score = day_avg_score
                    best_day_idx = day_idx
        
        avg_score = total_score / total_plans if total_plans > 0 else 0
        
        return {
            "total_plans_evaluated": total_plans,
            "average_score": round(avg_score, 2),
            "best_day": best_day_idx + 1,
            "best_day_score": round(best_day_score, 2),
            "recommendation_quality": self._get_quality_label(avg_score)
        }
    
    def _get_quality_label(self, score: float) -> str:
        """根据评分获取质量标签"""
        if score >= 85:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 60:
            return "合格"
        else:
            return "需要优化"