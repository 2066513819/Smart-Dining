# 《学生餐营养指南》营养供给量标准
# 基准：初中高年龄组 (12-14岁)
# 能量：2400 kcal/天
# 蛋白质：65 g/天
# 脂肪占总能量比例：25%-30%
# 碳水化合物占总能量比例：50%-65%

from app.config.nutrition_ratios import NUTRITION_RATIOS, GUIDELINE_BASE_GROUP

# 各餐次能量分配比例
MEAL_ENERGY_RATIO = {
    "breakfast": 0.25,
    "lunch": 0.40,
    "dinner": 0.35
}

# 基准组 (junior_high) 的每日营养目标
DAILY_BASE_TARGETS = {
    "calories": 2400.0,
    "protein": 65.0,
    "fat": 80.0,  # 2400 * 0.3 / 9 approx 80g
    "carbohydrates": 330.0,  # 2400 * 0.55 / 4 approx 330g
    "calcium": 1000.0,
    "iron": 15.0,
    "vitamin_c": 100.0
}

def get_nutrition_targets(age_group: str, meal: str) -> dict:
    """
    获取指定年龄段和餐次的营养目标
    """
    from app.utils.nutrition_adjuster import normalize_age_group
    
    target_group = normalize_age_group(age_group)
    ratios = NUTRITION_RATIOS.get(target_group, NUTRITION_RATIOS[GUIDELINE_BASE_GROUP])
    meal_ratio = MEAL_ENERGY_RATIO.get(meal.lower(), 0.4)
    
    targets = {}
    for nutrient, base_val in DAILY_BASE_TARGETS.items():
        # 1. 根据年龄段缩放每日总量
        # 2. 根据餐次比例分配到当前餐次
        daily_target = base_val * ratios.get(nutrient if nutrient in ratios else "calories", 1.0)
        meal_target = daily_target * meal_ratio
        targets[f"target_{nutrient}"] = round(meal_target, 2)
        
    return targets
