"""
餐饮推荐权重配置

根据用户要求，设计以下权重系数分配：
- 营养值达标率：40% (0.40)
- 成本控制：35% (0.35)
- 食材种类多样性：25% (0.25)

评分机制：
1. 系统自动筛选多种组合计划
2. 按权重计算综合评分
3. 选择评分最高的餐饮计划展示给用户
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class RecommendationWeights:
    """
    推荐权重配置类
    
    属性:
        WEIGHT_NUTRITION: 营养值达标率权重 (40%)
        WEIGHT_COST: 成本控制权重 (35%)
        WEIGHT_INGREDIENT_VARIETY: 食材种类多样性权重 (25%)
    """
    # 主要权重分配
    WEIGHT_NUTRITION: float = 0.40          # 营养值达标率权重
    WEIGHT_COST: float = 0.35               # 成本控制权重
    WEIGHT_INGREDIENT_VARIETY: float = 0.25  # 食材种类多样性权重
    
    # 验证权重总和是否为1.0
    def validate_weights(self) -> bool:
        """验证权重总和是否为1.0"""
        total = self.WEIGHT_NUTRITION + self.WEIGHT_COST + self.WEIGHT_INGREDIENT_VARIETY
        return abs(total - 1.0) < 0.001
    
    # 营养评分子权重（细粒度控制）
    NUTRITION_SUB_WEIGHTS: Dict[str, float] = None
    
    def __post_init__(self):
        """初始化后设置子权重"""
        self.NUTRITION_SUB_WEIGHTS = {
            "calories": 0.25,    # 热量达标重要性
            "protein": 0.30,     # 蛋白质达标重要性
            "fat": 0.15,         # 脂肪达标重要性
            "carbohydrates": 0.15,  # 碳水化合物达标重要性
            "calcium": 0.075,    # 钙达标重要性
            "iron": 0.075,       # 铁达标重要性
            "vitamin_c": 0.075   # 维生素C达标重要性
        }
    
    # 成本评分参数
    COST_PARAMS: Dict[str, Any] = None
    
    def get_cost_params(self) -> Dict[str, Any]:
        """获取成本评分参数"""
        if self.COST_PARAMS is None:
            self.COST_PARAMS = {
                "optimal_cost_ratio": 0.85,   # 最优成本比例（成本/预算）
                "max_acceptable_ratio": 1.0,  # 最大可接受成本比例
                "min_acceptable_ratio": 0.5,  # 最小可接受成本比例（过低可能营养不足）
            }
        return self.COST_PARAMS
    
    # 食材多样性参数
    INGREDIENT_VARIETY_PARAMS: Dict[str, Any] = None
    
    def get_variety_params(self) -> Dict[str, Any]:
        """获取食材多样性评分参数"""
        if self.INGREDIENT_VARIETY_PARAMS is None:
            self.INGREDIENT_VARIETY_PARAMS = {
                "unique_ingredient_weight": 2.0,   # 新食材得分权重
                "color_diversity_weight": 1.5,       # 颜色多样性权重
                "category_diversity_weight": 1.5,    # 分类多样性权重
                "min_target_ingredients": 5,         # 目标最少食材种类数
                "max_target_ingredients": 12       # 目标最多食材种类数
            }
        return self.INGREDIENT_VARIETY_PARAMS
    
    # 组合生成参数
    COMBINATION_PARAMS: Dict[str, Any] = None
    
    def get_combination_params(self) -> Dict[str, Any]:
        """获取组合生成参数"""
        if self.COMBINATION_PARAMS is None:
            self.COMBINATION_PARAMS = {
                "max_combinations_to_evaluate": 100,  # 最大评估组合数
                "candidates_per_category": 5,          # 每个分类候选数
                "min_plan_score": 0.0,                 # 最小可接受评分
                "max_plans_to_return": 3               # 返回的最佳计划数量
            }
        return self.COMBINATION_PARAMS


# 全局权重实例（用于快速访问）
DEFAULT_WEIGHTS = RecommendationWeights()

# 旧版本兼容常量
WEIGHT_NUTRITION = DEFAULT_WEIGHTS.WEIGHT_NUTRITION
WEIGHT_COST = DEFAULT_WEIGHTS.WEIGHT_COST
WEIGHT_INGREDIENT_VARIETY = DEFAULT_WEIGHTS.WEIGHT_INGREDIENT_VARIETY


def get_weights() -> RecommendationWeights:
    """
    获取默认权重配置
    
    Returns:
        RecommendationWeights: 权重配置实例
    """
    return DEFAULT_WEIGHTS


def create_custom_weights(
    nutrition: float = 0.40,
    cost: float = 0.35,
    ingredient_variety: float = 0.25
) -> RecommendationWeights:
    """
    创建自定义权重配置
    
    Args:
        nutrition: 营养值权重
        cost: 成本权重
        ingredient_variety: 食材种类权重
        
    Returns:
        RecommendationWeights: 自定义权重配置
    """
    return RecommendationWeights(
        WEIGHT_NUTRITION=nutrition,
        WEIGHT_COST=cost,
        WEIGHT_INGREDIENT_VARIETY=ingredient_variety
    )
