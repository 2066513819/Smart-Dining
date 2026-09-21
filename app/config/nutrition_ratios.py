# 参照《学生餐营养指南》（送审稿）表1能量与蛋白质供给量。
# 以初中高年龄组（12-14岁）平均需求作为基准1.0：
# - 能量：约2400 kcal/天（男女平均）
# - 蛋白质：约65 g/天（男女平均）
# 其他营养素按能量倍率近似缩放，保证整体占比一致。
GUIDELINE_BASE_GROUP = "junior_high"

NUTRITION_RATIOS = {
    "primary": {  # 6-8岁
        "calories": 0.69,          # 1650 / 2400
        "carbohydrates": 0.69,
        "fat": 0.69,
        "protein": 0.62,           # 40 / 65
        "calcium": 0.69,
        "iron": 0.69,
        "vitamin_c": 0.69,
        "ingredient_amount": 0.69
    },
    "junior_low": {  # 9-11岁
        "calories": 0.83,          # 2000 / 2400
        "carbohydrates": 0.83,
        "fat": 0.83,
        "protein": 0.77,           # 50 / 65
        "calcium": 0.83,
        "iron": 0.83,
        "vitamin_c": 0.83,
        "ingredient_amount": 0.83
    },
    "junior_high": {  # 12-14岁，基准
        "calories": 1.0,
        "carbohydrates": 1.0,
        "fat": 1.0,
        "protein": 1.0,
        "calcium": 1.0,
        "iron": 1.0,
        "vitamin_c": 1.0,
        "ingredient_amount": 1.0
    },
    "senior": {  # 15-17岁
        "calories": 1.10,          # 2650 / 2400
        "carbohydrates": 1.10,
        "fat": 1.10,
        "protein": 1.04,           # 67.5 / 65
        "calcium": 1.10,
        "iron": 1.10,
        "vitamin_c": 1.10,
        "ingredient_amount": 1.10
    }
}