# 餐饮推荐系统 - 权重评分推荐功能

## 概述

已实现基于权重系数的餐饮推荐系统，核心特点：

1. **自动筛选多种组合**：系统生成多个候选餐饮组合方案
2. **按权重评分**：根据三个维度计算综合评分
3. **选择最优方案**：返回评分最高的餐饮计划

## 权重系数分配

| 维度 | 权重 | 说明 |
|------|------|------|
| 营养值达标率 | 40% | 确保满足对应年龄段的营养需求 |
| 成本控制 | 35% | 优化成本与预算的比例关系 |
| 食材种类多样性 | 25% | 保证食材数量和颜色多样性 |

## 文件结构

### 1. 权重配置
**文件**: `app/config/recommendation_weights.py`

```python
class RecommendationWeights:
    WEIGHT_NUTRITION = 0.40          # 营养值达标率: 40%
    WEIGHT_COST = 0.35               # 成本控制: 35%
    WEIGHT_INGREDIENT_VARIETY = 0.25 # 食材种类多样性: 25%
```

### 2. 评分工具
**文件**: `app/utils/plan_scorer.py`

核心类：
- `PlanScorer`: 餐饮计划评分器
- `ScoredPlan`: 带评分的计划数据类
- `CombinationGenerator`: 菜品组合生成器

评分算法：

#### 营养评分 (0-100分)
- 达标率 90%-110%：满分100分
- 达标率 70%-90%：70-100分线性递减
- 达标率 110%-130%：100-70分线性递减
- 达标率 <70% 或 >130%：严重扣分

#### 成本评分 (0-100分)
- 成本在预算的50%-85%：满分100分
- 成本在预算的85%-100%：线性递减到80分
- 成本超过预算：快速递减
- 成本低于50%：线性递减（可能营养不足）

#### 多样性评分 (0-100分)
- 食材数量 (40%权重): 目标5-12种食材
- 颜色多样性 (30%权重): 绿色、红色、黄色、白色、棕色、紫色
- 分类多样性 (30%权重): 主食、荤菜、素菜、汤类等

### 3. 推荐服务
**文件**: `app/services/recommendation_service.py`

新增方法：

#### `recommend_with_weighted_scoring()`
单餐权重评分推荐

参数：
- `meal_type`: 餐次类型 (breakfast/lunch/dinner)
- `age_group`: 年龄段
- `category_rules`: 分类规则
- `cost_budget`: 成本预算
- `max_combinations`: 最大评估组合数 (默认100)
- `top_n`: 返回的最佳计划数 (默认3)

返回：
- 最佳计划 (best_plan)
- 备选计划 (alternative_plans)
- 所有评分详情
- 权重配置信息

#### `recommend_meal_plan_with_scoring()`
多日餐饮计划推荐

### 4. API端点
**文件**: `app/routers/recommendation_v2.py`

#### POST `/api/v2/recommendation/weighted-scoring`
权重评分推荐

请求示例：
```json
{
    "meal_type": "lunch",
    "age_group": "junior_high",
    "cost_budget": 25.0,
    "category_rules": {
        "主食类": 1,
        "荤菜类": 1,
        "素菜类": 2,
        "汤类": 1
    },
    "max_combinations": 100,
    "top_n": 3
}
```

响应示例：
```json
{
    "success": true,
    "strategy": "weighted_scoring",
    "weights": {
        "nutrition": 0.40,
        "cost": 0.35,
        "ingredient_variety": 0.25
    },
    "best_plan": {
        "dishes": [...],
        "total_score": 87.5,
        "nutrition_score": 92.0,
        "cost_score": 85.0,
        "variety_score": 84.0,
        "total_cost": 23.5,
        "unique_ingredients_count": 8,
        "ingredient_colors": ["红色", "绿色", "黄色", "白色"]
    },
    "alternative_plans": [...],
    "all_scored_plans": [...],
    "nutrition_targets": {
        "target_calories": 960.0,
        "target_protein": 26.0,
        ...
    },
    "metadata": {
        "total_combinations_evaluated": 45,
        "best_score": 87.5
    }
}
```

#### POST `/api/v2/recommendation/weighted-meal-plan`
带权重评分的多日餐饮计划

#### GET `/api/v2/recommendation/weights-info`
获取权重配置信息

响应示例：
```json
{
    "success": true,
    "weights": {
        "nutrition": {
            "value": 0.40,
            "percentage": "40%",
            "description": "营养值达标率"
        },
        "cost": {
            "value": 0.35,
            "percentage": "35%",
            "description": "成本控制"
        },
        "ingredient_variety": {
            "value": 0.25,
            "percentage": "25%",
            "description": "食材种类多样性"
        }
    }
}
```

## 算法流程

1. **获取候选菜品**
   - 根据餐次类型和分类规则从数据库获取候选菜品
   - 每个分类获取5-10个候选

2. **生成组合方案**
   - 按分类规则生成多种菜品组合
   - 默认最多生成100个组合
   - 确保组合多样性

3. **计算综合评分**
   ```
   综合评分 = 营养评分 × 0.40 + 成本评分 × 0.35 + 多样性评分 × 0.25
   ```

4. **选择最优方案**
   - 按综合评分排序
   - 返回评分最高的前N个方案（默认3个）

5. **展示结果**
   - 包含详细评分信息
   - 营养目标对比
   - 成本分析
   - 食材多样性统计

## 使用示例

### 场景：为初中生推荐午餐

```python
# 调用推荐服务
result = recommendation_service.recommend_with_weighted_scoring(
    meal_type="lunch",
    age_group="junior_high",
    category_rules={
        "主食类": 1,    # 1份主食
        "荤菜类": 1,    # 1份荤菜
        "素菜类": 2,    # 2份素菜
        "汤类": 1       # 1份汤
    },
    cost_budget=25.0,    # 预算25元
    max_combinations=100,
    top_n=3
)

# 结果
best_plan = result["best_plan"]
print(f"推荐方案评分: {best_plan['total_score']}")
print(f"营养评分: {best_plan['nutrition_score']}")
print(f"成本评分: {best_plan['cost_score']}")
print(f"多样性评分: {best_plan['variety_score']}")
print(f"总成本: {best_plan['total_cost']}元")
```

## 优势

1. **科学性强**：基于《学生餐营养指南》的营养目标
2. **成本可控**：严格控制在预算范围内
3. **多样性保证**：确保食材种类丰富
4. **透明度高**：提供详细评分依据
5. **可扩展**：权重可动态调整

## 扩展建议

1. **个性化权重**：根据用户偏好动态调整权重
2. **历史学习**：基于用户反馈优化评分算法
3. **季节因素**：增加时令食材权重
4. **健康状态**：根据用户健康状态调整营养目标
