"""
加权推荐路由
提供真正的多计划权重评分筛选功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import traceback

from app.models.user import User
from app.schemas.dish import MealSetRecommendationRequest
from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.utils.weighted_recommendation import WeightedRecommendation
from app.core.exceptions import RecommendationException

router = APIRouter(prefix="/api/recommendation", tags=["weighted-recommendation"])


@router.post("/weighted-meal-set-recommendation")
def weighted_meal_set_recommendation(
    request: MealSetRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    加权套餐推荐
    生成多个候选计划，按权重评分筛选最优方案
    
    权重配置：
    - 营养值达标率: 40%
    - 成本控制: 35%
    - 食材种类多样性: 25%
    
    算法流程：
    1. 为每个餐次分类获取候选菜品
    2. 生成多种菜品组合方案
    3. 对每个方案计算三个维度的评分
    4. 按权重计算综合评分
    5. 选择评分最高的方案推荐
    
    返回结果包含：
    - 加权评分详情
    - 多个候选计划的评估结果
    - 最佳选择的理由说明
    """
    try:
        print(f"\n=== 开始加权套餐推荐 ===")
        print(f"用户: {current_user.username}")
        print(f"请求: {request}")
        
        # 创建加权推荐实例
        weighted_rec = WeightedRecommendation(db)
        
        # 解析用户年龄段
        from app.utils.nutrition_adjuster import normalize_age_group
        raw_age_group = request.target_age_group or getattr(current_user, "age_group", "") or ""
        target_age_group = normalize_age_group(raw_age_group)
        
        # 加载配餐规则
        from app.config.guideline_meal_rules import get_guideline_meal_rules, get_default_meal_rules
        from app.models.system_setting import SystemSetting
        
        # 优先使用管理员配置的规则
        setting = db.query(SystemSetting).filter(SystemSetting.key == "meal_rules").first()
        if setting and setting.value:
            try:
                meal_rules = json.loads(setting.value)
                print("DEBUG: 使用管理员配置的配餐规则")
            except:
                meal_rules = get_default_meal_rules(target_age_group)
                print("DEBUG: 管理员配置解析失败，使用指南规则")
        else:
            meal_rules = get_default_meal_rules(target_age_group)
            print("DEBUG: 使用学生餐营养指南标准规则")
        
        # 检查规则是否包含per_meal
        if "per_meal" not in meal_rules:
            raise RecommendationException("配餐规则不完整，缺少per_meal配置")
        
        # 严格模式判断
        is_strict = False  # 默认不使用严格模式
        
        # 获取食材价格
        ingredient_prices = getattr(request, "ingredient_prices", {})
        
        # 生成加权推荐
        result = weighted_rec.generate_weighted_meal_set(
            request=request,
            meal_rules=meal_rules,
            target_age_group=target_age_group,
            ingredient_prices=ingredient_prices,
            strict_mode=is_strict
        )
        
        print(f"\n=== 加权推荐完成 ===")
        print(f"总评估计划数: {result.get('evaluation_summary', {}).get('total_plans_evaluated', 0)}")
        print(f"平均评分: {result.get('evaluation_summary', {}).get('average_score', 0):.2f}")
        print(f"推荐质量: {result.get('evaluation_summary', {}).get('recommendation_quality', '未知')}")
        
        return result
        
    except RecommendationException as e:
        print(f"推荐异常: {e}")
        raise e
    except Exception as e:
        print(f"加权套餐推荐失败，详细错误信息:")
        print(traceback.format_exc())
        
        # 提供友好的错误信息
        error_detail = {
            "message": "加权套餐推荐失败",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "suggestion": "请检查配餐规则配置和菜品数据库是否完整",
            "fallback_suggestion": "可以尝试使用普通套餐推荐模式"
        }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/weights-info")
def get_recommendation_weights_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取推荐权重配置信息
    
    返回当前系统中使用的权重配置详情
    """
    try:
        from app.config.recommendation_weights import (
            WEIGHT_NUTRITION, WEIGHT_COST, WEIGHT_INGREDIENT_VARIETY,
            default_weights
        )
        
        # 基本权重
        basic_weights = {
            "nutrition": {
                "value": WEIGHT_NUTRITION,
                "percentage": f"{WEIGHT_NUTRITION * 100:.1f}%",
                "description": "营养值达标率权重"
            },
            "cost": {
                "value": WEIGHT_COST,
                "percentage": f"{WEIGHT_COST * 100:.1f}%",
                "description": "成本控制权重"
            },
            "ingredient_variety": {
                "value": WEIGHT_INGREDIENT_VARIETY,
                "percentage": f"{WEIGHT_INGREDIENT_VARIETY * 100:.1f}%",
                "description": "食材种类多样性权重"
            }
        }
        
        # 验证权重总和是否为1.0
        total = WEIGHT_NUTRITION + WEIGHT_COST + WEIGHT_INGREDIENT_VARIETY
        is_valid = abs(total - 1.0) < 1e-6
        
        # 营养评分子权重
        nutrition_sub_weights = getattr(default_weights, 'NUTRITION_SUB_WEIGHTS', None)
        if not nutrition_sub_weights:
            nutrition_sub_weights = {
                "calories": 0.25, "protein": 0.30, "fat": 0.15,
                "carbohydrates": 0.15, "calcium": 0.05, "iron": 0.05, "vitamin_c": 0.05
            }
        
        result = {
            "basic_weights": basic_weights,
            "weight_sum": {
                "value": total,
                "is_valid": is_valid,
                "message": "权重总和应为1.0" if is_valid else f"权重总和应为1.0，实际为{total:.2f}"
            },
            "nutrition_sub_weights": {
                k: {"value": v, "percentage": f"{v*100:.1f}%"}
                for k, v in nutrition_sub_weights.items()
            },
            "scoring_algorithm": {
                "total_score": "营养分 × 40% + 成本分 × 35% + 多样性分 × 25%",
                "nutrition_score": "各营养素达标率加权平均",
                "cost_score": "成本与预算的偏离程度评分",
                "variety_score": "食材种类和颜色的多样性评分"
            },
            "usage": {
                "current_api": "/api/recommendation/weighted-meal-set-recommendation",
                "fallback_api": "/api/recommendation/meal-set-recommendation",
                "parameters": "设置weighted=True参数使用加权模式"
            }
        }
        
        return result
        
    except Exception as e:
        print(f"获取权重信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权重信息失败: {str(e)}"
        )


@router.post("/test-weighted-scoring")
def test_weighted_scoring(
    test_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    测试加权评分功能
    
    用于验证权重评分算法是否正确工作
    需要提供测试数据，包含菜品列表、营养目标、成本预算等
    """
    try:
        print(f"测试加权评分: {test_data}")
        
        # 提取测试数据
        dishes = test_data.get("dishes", [])
        nutrition_targets = test_data.get("nutrition_targets", {})
        cost_budget = test_data.get("cost_budget", 0)
        age_group = test_data.get("age_group", "junior_high")
        meal_type = test_data.get("meal_type", "lunch")
        
        if not dishes:
            return {
                "error": "需要提供测试菜品数据",
                "example": {
                    "dishes": [
                        {
                            "dish_name": "番茄炒蛋",
                            "total_calories": 200,
                            "total_protein": 15,
                            "total_fat": 10,
                            "total_carbohydrates": 20,
                            "cost_price": 8.5
                        }
                    ],
                    "nutrition_targets": {
                        "target_calories": 500,
                        "target_protein": 30,
                        "target_fat": 20,
                        "target_carbohydrates": 60
                    },
                    "cost_budget": 30,
                    "age_group": "junior_high",
                    "meal_type": "lunch"
                }
            }
        
        # 创建评分器
        from app.utils.plan_scorer import PlanScorer
        scorer = PlanScorer()
        
        # 计算评分
        scored_plan = scorer.score_plan(
            dishes=dishes,
            nutrition_targets=nutrition_targets,
            cost_budget=cost_budget,
            age_group=age_group,
            meal_type=meal_type
        )
        
        # 计算权重贡献
        weights_info = {
            "weight_nutrition": 0.40,
            "weight_cost": 0.35,
            "weight_variety": 0.25
        }
        
        contribution = {
            "nutrition": scored_plan.nutrition_score * weights_info["weight_nutrition"],
            "cost": scored_plan.cost_score * weights_info["weight_cost"],
            "variety": scored_plan.variety_score * weights_info["weight_variety"]
        }
        
        return {
            "test_success": True,
            "scored_plan": scored_plan.to_dict(),
            "weights_contribution": contribution,
            "weights_info": weights_info,
            "interpretation": {
                "total_score": f"综合评分: {scored_plan.total_score:.2f}/100",
                "nutrition_score": f"营养评分: {scored_plan.nutrition_score:.2f}/100",
                "cost_score": f"成本评分: {scored_plan.cost_score:.2f}/100",
                "variety_score": f"多样性评分: {scored_plan.variety_score:.2f}/100",
                "calculation": f"计算方式: {scored_plan.nutrition_score:.2f}×0.4 + {scored_plan.cost_score:.2f}×0.35 + {scored_plan.variety_score:.2f}×0.25 = {scored_plan.total_score:.2f}"
            }
        }
        
    except Exception as e:
        print(f"测试加权评分失败: {e}")
        print(traceback.format_exc())
        return {
            "test_success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }