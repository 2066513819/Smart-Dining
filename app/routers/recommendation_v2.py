"""
餐饮推荐路由 - 重构版本
提供更健壮、更智能的推荐功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import traceback

from app.models.user import User
from app.schemas.dish import (
    RecommendationRequest, 
    DatabaseRecommendationRequest,
    MealSetRecommendationRequest
)
from pydantic import BaseModel, Field
from typing import Optional
from app.services.db_service import get_db
from app.services.recommendation_service import RecommendationService
from app.services.dify_service import DifyService
from app.routers.auth import get_current_user
from app.core.exceptions import RecommendationException

router = APIRouter(prefix="/api/v2/recommendation", tags=["recommendation-v2"])
logger = logging.getLogger(__name__)


# ========== 权重评分推荐相关模型 ==========

class WeightedScoringRequest(BaseModel):
    """权重评分推荐请求"""
    meal_type: str = Field(default="lunch", description="餐次类型: breakfast/lunch/dinner")
    age_group: str = Field(default="junior_high", description="年龄段: primary_low/junior_high/senior")
    cost_budget: float = Field(default=20.0, description="成本预算")
    category_rules: Optional[Dict[str, int]] = Field(
        default=None,
        description="分类规则，如 {'主食类': 1, '荤菜类': 1, '素菜类': 2}"
    )
    flavors: Optional[List[str]] = Field(default=None, description="口味偏好")
    seasons: Optional[List[str]] = Field(default=None, description="时令偏好")
    ingredients: Optional[List[str]] = Field(default=None, description="已有食材")
    max_combinations: int = Field(default=100, ge=10, le=500, description="最大评估组合数")
    top_n: int = Field(default=3, ge=1, le=10, description="返回的最佳计划数")


class WeightedMealPlanRequest(BaseModel):
    """带权重评分的多日餐饮计划请求"""
    days: int = Field(default=1, ge=1, le=7, description="天数")
    age_group: str = Field(default="junior_high", description="年龄段")
    meal_types: List[str] = Field(
        default=["breakfast", "lunch", "dinner"],
        description="餐次类型列表"
    )
    cost_budget_per_meal: Dict[str, float] = Field(
        default={"breakfast": 10.0, "lunch": 20.0, "dinner": 20.0},
        description="每餐成本预算"
    )
    flavors: Optional[List[str]] = Field(default=None, description="口味偏好")
    seasons: Optional[List[str]] = Field(default=None, description="时令偏好")
    ingredients: Optional[List[str]] = Field(default=None, description="已有食材")


@router.post("/smart-recommend")
def smart_recommendation(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    智能推荐端点
    根据用户需求和上下文自动选择最佳推荐策略
    
    支持多种输入方式：
    1. 完整的prompt（优先使用）
    2. 结构化参数（meal_type, cycle, age_group等）
    3. 混合模式（prompt + 结构化参数）
    """
    try:
        logger.info(f"收到智能推荐请求: user={current_user.id}, meal_type={request.meal_type}")
        
        # 解析请求参数
        request_data = {
            "meal_type": request.meal_type or "lunch",
            "count": 5,  # 默认推荐数量
            "categories": [],
            "flavors": [],
            "seasons": [],
            "nutrition_requirements": [],
            "ingredients": request.ingredients or [],
            "exclude_ids": [],
            "max_cost": None
        }
        
        # 如果有完整的prompt，优先使用AI推荐
        if request.prompt:
            logger.info("使用AI推荐（有完整prompt）")
            return _get_ai_recommendation(request.prompt, current_user.id)
        
        # 使用新的推荐服务
        recommendation_service = RecommendationService(db=db, user=current_user)
        result = recommendation_service.recommend_smart(
            request_data=request_data,
            user=current_user
        )
        
        logger.info(f"智能推荐成功: {len(result['recommendations'])} 个菜品")
        return result
        
    except RecommendationException as e:
        logger.warning(f"推荐服务异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"推荐失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"智能推荐失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )


@router.post("/database-recommend")
def database_recommendation_v2(
    request: DatabaseRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    数据库推荐端点（增强版）
    基于数据库菜品进行智能推荐
    
    特点：
    1. 支持多种过滤条件
    2. 智能匹配食材
    3. 营养需求筛选
    4. 成本控制
    """
    try:
        logger.info(f"收到数据库推荐请求: user={current_user.id}, count={request.count}")
        
        recommendation_service = RecommendationService(db=db, user=current_user)
        
        # 执行推荐
        recommendations = recommendation_service.recommend_by_meal_type(
            meal_type=request.meal_type or "lunch",
            count=request.count,
            categories=request.category,
            flavors=request.flavor,
            seasons=request.season,
            nutrition_requirements=request.nutrition_requirements,
            ingredients=request.ingredients,
            exclude_ids=request.exclude_ids,
            max_cost=request.max_cost
        )
        
        # 计算统计信息
        stats = _calculate_recommendation_stats(recommendations)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "metadata": {
                "total_count": len(recommendations),
                "requested_count": request.count,
                "stats": stats,
                "applied_filters": {
                    "has_categories": bool(request.category),
                    "has_flavors": bool(request.flavor),
                    "has_seasons": bool(request.season),
                    "has_ingredients": bool(request.ingredients),
                    "has_nutrition_requirements": bool(request.nutrition_requirements),
                    "has_cost_limit": request.max_cost is not None
                }
            }
        }
        
    except RecommendationException as e:
        logger.warning(f"数据库推荐异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据库推荐失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"数据库推荐失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )


@router.post("/meal-set-recommend")
def meal_set_recommendation_v2(
    request: MealSetRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    套餐推荐端点（增强版）
    生成多日套餐计划
    
    特点：
    1. 支持多日计划
    2. 严格遵循配餐规则
    3. 智能避免重复
    4. 成本控制和营养均衡
    """
    try:
        logger.info(f"收到套餐推荐请求: user={current_user.id}, days={request.days}")
        
        recommendation_service = RecommendationService(db=db, user=current_user)
        
        # 构建成本限制
        max_cost_per_meal = {}
        if request.max_cost_breakfast:
            max_cost_per_meal["breakfast"] = request.max_cost_breakfast
        if request.max_cost_lunch:
            max_cost_per_meal["lunch"] = request.max_cost_lunch
        if request.max_cost_dinner:
            max_cost_per_meal["dinner"] = request.max_cost_dinner
        
        # 执行套餐推荐
        meal_plans = recommendation_service.recommend_meal_set(
            days=request.days,
            meal_types=request.meal_types or ["breakfast", "lunch", "dinner"],
            flavors=request.flavor,
            seasons=request.season,
            ingredients=request.ingredients,
            max_cost_per_meal=max_cost_per_meal
        )
        
        # 计算总体统计
        total_stats = _calculate_meal_set_stats(meal_plans)
        
        return {
            "success": True,
            "meal_plans": meal_plans,
            "metadata": {
                "total_days": request.days,
                "total_meals": len(meal_plans) * len(meal_plans[0]["meals"]) if meal_plans else 0,
                "stats": total_stats,
                "cost_summary": {
                    "total_cost": total_stats["total_cost"],
                    "avg_cost_per_day": total_stats["avg_cost_per_day"],
                    "cost_limits_applied": bool(max_cost_per_meal)
                }
            }
        }
        
    except RecommendationException as e:
        logger.warning(f"套餐推荐异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"套餐推荐失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"套餐推荐失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )


@router.post("/ai-recommend")
async def ai_recommendation(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI推荐端点
    使用Dify服务获取AI生成的推荐
    
    注意：这是降级方案，当数据库推荐不满足需求时使用
    """
    try:
        logger.info(f"收到AI推荐请求: user={current_user.id}")
        
        query = request.get("query", "")
        count = request.get("count", 3)
        category = request.get("category", "")
        
        if not query:
            # 构建默认查询
            category_prompt = f"类别为: {category}" if category else "类别随机"
            query = f"请生成 {count} 个餐饮菜品，{category_prompt}。返回格式必须是 JSON 数组，每个对象包含 name, category, description, nutrition 字段。nutrition 字段应包含卡路里、蛋白质、脂肪、碳水化合物信息。"
        
        dify_service = DifyService()
        result = dify_service.get_recommendation(query, str(current_user.id))
        
        # 尝试解析AI返回的JSON
        answer = result.get("answer", "")
        dishes = _parse_ai_response(answer)
        
        return {
            "success": True,
            "source": "ai",
            "dishes": dishes,
            "metadata": {
                "query_used": query,
                "raw_response_length": len(answer),
                "parsed_dishes_count": len(dishes)
            }
        }
        
    except Exception as e:
        logger.error(f"AI推荐失败: {str(e)}\n{traceback.format_exc()}")
        # 返回友好的错误信息
        return {
            "success": False,
            "source": "ai",
            "dishes": [],
            "error": {
                "message": "AI推荐服务暂时不可用",
                "suggestion": "请尝试使用数据库推荐功能",
                "details": str(e) if logger.getEffectiveLevel() <= logging.DEBUG else None
            }
        }


@router.post("/weighted-scoring")
def weighted_scoring_recommendation(
    request: WeightedScoringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    权重评分推荐端点 - 核心新功能
    
    算法特点：
    1. 系统自动筛选多种组合计划
    2. 按权重计算综合评分:
       - 营养值达标率：40% (肯定满足对应年龄段营养需求)
       - 成本控制：35%
       - 食材种类多样性：25%
    3. 选择评分最高的餐饮计划展示给用户
    
    示例请求:
    ```json
    {
        "meal_type": "lunch",
        "age_group": "junior_high",
        "cost_budget": 25.0,
        "category_rules": {"主食类": 1, "荤菜类": 1, "素菜类": 2, "汤类": 1},
        "max_combinations": 100,
        "top_n": 3
    }
    ```
    
    返回结果包含:
    - best_plan: 评分最高的方案
    - alternative_plans: 备选方案
    - all_scored_plans: 所有评估过的方案（前10个）
    - weights: 使用的权重配置
    - nutrition_targets: 该年龄段的营养目标值
    """
    try:
        logger.info(
            f"收到权重评分推荐请求: user={current_user.id}, "
            f"meal={request.meal_type}, age={request.age_group}, budget={request.cost_budget}"
        )
        
        # 获取分类规则
        category_rules = request.category_rules
        if not category_rules:
            # 使用默认规则
            from app.config.guideline_meal_rules import get_guideline_meal_rules
            meal_rules = get_guideline_meal_rules(request.age_group)
            category_rules = meal_rules.get(request.meal_type, {
                "主食类": 1, "荤菜类": 1, "素菜类": 2, "汤类": 1
            })
        
        # 执行权重评分推荐
        recommendation_service = RecommendationService(db=db, user=current_user)
        result = recommendation_service.recommend_with_weighted_scoring(
            meal_type=request.meal_type,
            age_group=request.age_group,
            category_rules=category_rules,
            cost_budget=request.cost_budget,
            flavors=request.flavors,
            seasons=request.seasons,
            ingredients=request.ingredients,
            max_combinations=request.max_combinations,
            top_n=request.top_n
        )
        
        if result["success"]:
            logger.info(
                f"权重评分推荐成功: 评估了 {result['metadata']['total_combinations_evaluated']} 个组合, "
                f"最佳评分={result['metadata']['best_score']}"
            )
        else:
            logger.warning(f"权重评分推荐未找到合适方案: {result.get('message', '未知原因')}")
        
        return result
        
    except RecommendationException as e:
        error_msg = str(e)
        logger.warning(f"权重评分推荐异常: {error_msg}")
        # 返回包含详细错误信息的JSON响应，而不是抛出异常
        return {
            "success": False,
            "error": {
                "type": "RecommendationException",
                "message": error_msg,
                "suggestion": "请检查输入参数是否正确，或查看日志获取更多信息"
            },
            "request_info": {
                "meal_type": request.meal_type,
                "age_group": request.age_group,
                "cost_budget": request.cost_budget,
                "category_rules": category_rules if 'category_rules' in locals() else None
            }
        }
    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"权重评分推荐失败: {error_msg}\n{error_traceback}")
        # 返回包含详细错误信息的JSON响应
        return {
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": error_msg,
                "traceback": error_traceback if logger.getEffectiveLevel() <= logging.DEBUG else None,
                "suggestion": "服务器内部错误，请联系管理员或稍后重试"
            },
            "request_info": {
                "meal_type": request.meal_type,
                "age_group": request.age_group,
                "cost_budget": request.cost_budget,
                "category_rules": category_rules if 'category_rules' in locals() else None
            }
        }


@router.post("/weighted-meal-plan")
def weighted_meal_plan_recommendation(
    request: WeightedMealPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    带权重评分的多日餐饮计划推荐端点
    
    为每一天、每一餐生成多个候选方案，选择评分最高的组合
    
    示例请求:
    ```json
    {
        "days": 3,
        "age_group": "junior_high",
        "meal_types": ["breakfast", "lunch", "dinner"],
        "cost_budget_per_meal": {
            "breakfast": 10.0,
            "lunch": 25.0,
            "dinner": 20.0
        }
    }
    ```
    """
    try:
        logger.info(
            f"收到带权重评分的餐饮计划请求: user={current_user.id}, "
            f"days={request.days}, age={request.age_group}"
        )
        
        recommendation_service = RecommendationService(db=db, user=current_user)
        result = recommendation_service.recommend_meal_plan_with_scoring(
            days=request.days,
            age_group=request.age_group,
            meal_types=request.meal_types,
            cost_budget_per_meal=request.cost_budget_per_meal,
            flavors=request.flavors,
            seasons=request.seasons,
            ingredients=request.ingredients
        )
        
        logger.info(f"带权重评分的餐饮计划推荐成功: {request.days} 天计划生成完成")
        return result
        
    except RecommendationException as e:
        logger.warning(f"餐饮计划推荐异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"餐饮计划推荐失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"餐饮计划推荐失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )


@router.get("/weights-info")
def get_recommendation_weights_info() -> Dict[str, Any]:
    """
    获取推荐权重配置信息
    
    返回当前使用的权重系数分配:
    - 营养值达标率：40%
    - 成本控制：35%
    - 食材种类多样性：25%
    """
    from app.config.recommendation_weights import DEFAULT_WEIGHTS
    
    return {
        "success": True,
        "weights": {
            "nutrition": {
                "value": DEFAULT_WEIGHTS.WEIGHT_NUTRITION,
                "percentage": f"{DEFAULT_WEIGHTS.WEIGHT_NUTRITION * 100:.0f}%",
                "description": "营养值达标率（热量、蛋白质、脂肪、碳水化合物、钙、铁、维生素C）"
            },
            "cost": {
                "value": DEFAULT_WEIGHTS.WEIGHT_COST,
                "percentage": f"{DEFAULT_WEIGHTS.WEIGHT_COST * 100:.0f}%",
                "description": "成本控制（相对于预算的最优成本比例）"
            },
            "ingredient_variety": {
                "value": DEFAULT_WEIGHTS.WEIGHT_INGREDIENT_VARIETY,
                "percentage": f"{DEFAULT_WEIGHTS.WEIGHT_INGREDIENT_VARIETY * 100:.0f}%",
                "description": "食材种类多样性（食材数量、颜色多样性、分类多样性）"
            }
        },
        "algorithm_description": {
            "steps": [
                "系统自动筛选多种组合计划",
                "按权重给每个方案计算综合评分",
                "营养评分基于各营养素的达标率",
                "成本评分基于与预算的最优比例",
                "多样性评分基于食材数量和颜色",
                "选择评分最高的餐饮计划展示给用户"
            ],
            "scoring_range": "0-100分，越高越好"
        }
    }


@router.get("/health")
def recommendation_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    推荐服务健康检查
    
    检查：
    1. 数据库连接
    2. 推荐服务可用性
    3. AI服务连接（可选）
    """
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "healthy"
        
        # 检查推荐服务
        service = RecommendationService(db=db, user=current_user)
        test_result = service.recommend_by_meal_type(meal_type="lunch", count=1)
        service_status = "healthy" if test_result else "degraded"
        
        # 检查AI服务
        ai_status = "unknown"
        try:
            dify_service = DifyService()
            ai_info = dify_service.validate_config()
            ai_status = "healthy" if ai_info.get("available", False) else "unavailable"
        except Exception:
            ai_status = "unavailable"
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status,
                "recommendation_service": service_status,
                "ai_service": ai_status
            },
            "capabilities": {
                "database_recommendation": True,
                "smart_recommendation": True,
                "meal_set_recommendation": True,
                "weighted_scoring_recommendation": True,
                "weighted_meal_plan_recommendation": True,
                "ai_recommendation": ai_status == "healthy"
            }
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "services": {
                "database": "unhealthy",
                "recommendation_service": "unhealthy",
                "ai_service": "unknown"
            }
        }


# ========== 辅助函数 ==========

def _get_ai_recommendation(prompt: str, user_id: str) -> Dict[str, Any]:
    """获取AI推荐"""
    dify_service = DifyService()
    result = dify_service.get_recommendation(prompt, user_id)
    
    return {
        "success": True,
        "source": "ai",
        "recommendations": [result],  # 包装为列表以保持接口一致性
        "metadata": {
            "note": "AI推荐结果，可能需要进一步处理",
            "raw_response": result
        }
    }


def _calculate_recommendation_stats(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算推荐结果统计信息"""
    if not recommendations:
        return {
            "total_items": 0,
            "avg_calories": 0,
            "avg_protein": 0,
            "total_cost": 0,
            "category_distribution": {}
        }
    
    total_calories = sum(item.get("total_calories", 0) for item in recommendations)
    total_protein = sum(item.get("total_protein", 0) for item in recommendations)
    total_cost = sum(item.get("cost_price", 0) for item in recommendations)
    
    # 分类分布
    category_dist = {}
    for item in recommendations:
        category = item.get("category", "其他") or "其他"
        category_dist[category] = category_dist.get(category, 0) + 1
    
    # 口味分布
    flavor_dist = {}
    for item in recommendations:
        flavor = item.get("flavor", "原味") or "原味"
        flavor_dist[flavor] = flavor_dist.get(flavor, 0) + 1
    
    return {
        "total_items": len(recommendations),
        "avg_calories": round(total_calories / len(recommendations), 1),
        "avg_protein": round(total_protein / len(recommendations), 1),
        "total_cost": round(total_cost, 2),
        "avg_cost": round(total_cost / len(recommendations), 2),
        "category_distribution": category_dist,
        "flavor_distribution": flavor_dist
    }


def _calculate_meal_set_stats(meal_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算套餐计划统计信息"""
    if not meal_plans:
        return {
            "total_days": 0,
            "total_meals": 0,
            "total_cost": 0,
            "avg_cost_per_day": 0
        }
    
    total_cost = 0
    total_calories = 0
    total_protein = 0
    meal_count = 0
    
    for day_plan in meal_plans:
        total_cost += day_plan.get("total_cost", 0)
        
        for meal_type, meal_data in day_plan.get("meals", {}).items():
            meal_count += 1
            for item in meal_data.get("recommendations", []):
                total_calories += item.get("total_calories", 0)
                total_protein += item.get("total_protein", 0)
    
    return {
        "total_days": len(meal_plans),
        "total_meals": meal_count,
        "total_cost": round(total_cost, 2),
        "avg_cost_per_day": round(total_cost / len(meal_plans), 2),
        "avg_calories_per_meal": round(total_calories / meal_count, 1) if meal_count > 0 else 0,
        "avg_protein_per_meal": round(total_protein / meal_count, 1) if meal_count > 0 else 0
    }


def _parse_ai_response(answer: str) -> List[Dict[str, Any]]:
    """解析AI返回的响应，提取菜品信息"""
    import json
    import re
    
    if not answer:
        return []
    
    try:
        # 尝试直接解析JSON
        dishes = json.loads(answer)
        if isinstance(dishes, list):
            return dishes
    except json.JSONDecodeError:
        pass
    
    # 尝试从文本中提取JSON
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, answer, re.DOTALL)
    if match:
        try:
            dishes = json.loads(match.group(1))
            if isinstance(dishes, list):
                return dishes
        except json.JSONDecodeError:
            pass
    
    # 如果都失败，返回空列表
    return []