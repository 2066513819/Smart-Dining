# 《学生餐营养指南》中早餐、午餐、晚餐的食物种类及供给量标准
# 参考指南中的食物种类及供给量表格

# 基准年龄组（初中高年龄组 12-14岁）的食物种类及供给量
# 其他年龄段按比例调整
GUIDELINE_MEAL_RULES = {
    "junior_high": {  # 12-14岁初中高年龄组（基准）
        "breakfast": {
            "主食类": 1,           # 如：包子、馒头、米饭等
            "奶及奶制品类": 1,     # 如：牛奶
            "蛋类或豆制品类": 1,   # 如：鸡蛋、豆浆
            "蔬菜水果类": 1,       # 如：蔬菜、水果
        },
        "lunch": {
            "主食类": 1,           # 如：米饭、面条
            "荤菜类": 1,           # 如：肉类、鱼类
            "素菜类": 1,           # 如：蔬菜
            "汤类": 1,             # 如：汤品
            "水果类": 1,           # 如：水果
        },
        "dinner": {
            "主食类": 1,           # 如：米饭、馒头
            "荤菜类": 1,           # 如：肉类、鱼类
            "素菜类": 1,           # 如：蔬菜
            "汤类": 1,             # 如：汤品
        }
    },
    # 注意：不同年龄段在食物种类上基本相同，主要是供给量（克数）不同
    # 但我们这里用菜品份数来控制，营养值会根据年龄段自动调整
    # 因此其他年龄段可以复用相同的规则结构
    "primary": {  # 6-8岁小学，规则与基准相同，营养值按比例调整
        "breakfast": {
            "主食类": 1,
            "奶及奶制品类": 1,
            "蛋类或豆制品类": 1,
            "蔬菜水果类": 1,
        },
        "lunch": {
            "主食类": 1,
            "荤菜类": 1,
            "素菜类": 1,
            "汤类": 1,
            "水果类": 1,
        },
        "dinner": {
            "主食类": 1,
            "荤菜类": 1,
            "素菜类": 1,
            "汤类": 1,
        }
    },
    "junior_low": {  # 9-11岁初中低年龄组
        "breakfast": {
            "主食类": 1,
            "奶及奶制品类": 1,
            "蛋类或豆制品类": 1,
            "蔬菜水果类": 1,
        },
        "lunch": {
            "主食类": 1,
            "荤菜类": 1,
            "素菜类": 1,
            "汤类": 1,
            "水果类": 1,
        },
        "dinner": {
            "主食类": 1,
            "荤菜类": 1,
            "素菜类": 1,
            "汤类": 1,
        }
    },
    "senior": {  # 15-17岁高中
        "breakfast": {
            "主食类": 1,
            "奶及奶制品类": 1,
            "蛋类或豆制品类": 1,
            "蔬菜水果类": 1,
        },
        "lunch": {
            "主食类": 1,
            "荤菜类": 1,
            "素菜类": 1,
            "汤类": 1,
            "水果类": 1,
        },
        "dinner": {
            "主食类": 1,
            "荤菜类": 1,
            "素菜类": 1,
            "汤类": 1,
        }
    }
}


def get_guideline_meal_rules(age_group: str) -> dict:
    """
    根据年龄段获取符合《学生餐营养指南》标准的配餐规则
    
    Args:
        age_group: 年龄段，如 "primary", "junior_low", "junior_high", "senior"
        
    Returns:
        包含 breakfast, lunch, dinner 的配餐规则字典
    """
    from app.utils.nutrition_adjuster import normalize_age_group
    
    normalized_group = normalize_age_group(age_group)
    rules = GUIDELINE_MEAL_RULES.get(normalized_group, GUIDELINE_MEAL_RULES["junior_high"])
    
    return {
        "breakfast": rules.get("breakfast", {}),
        "lunch": rules.get("lunch", {}),
        "dinner": rules.get("dinner", {}),
    }


def get_default_meal_rules() -> dict:
    """
    获取默认配餐规则（基于初中高年龄组的指南标准）
    """
    return GUIDELINE_MEAL_RULES["junior_high"]
