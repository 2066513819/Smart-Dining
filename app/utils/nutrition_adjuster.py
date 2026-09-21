from app.config.nutrition_ratios import NUTRITION_RATIOS, GUIDELINE_BASE_GROUP


def normalize_age_group(age_group: str) -> str:
    """统一年龄段标识为配置键（小写，下划线），兼容旧值"""
    if not age_group:
        return GUIDELINE_BASE_GROUP
    val = str(age_group).lower().strip()
    # 兼容复合值 "primary,junior_low"
    if "," in val:
        val = val.split(",")[0].strip()
    mapping = {
        "primary": "primary",
        "小学": "primary",
        "junior_low": "junior_low",
        "junior-low": "junior_low",
        "junior": "junior_high",
        "junior_high": "junior_high",
        "junior-high": "junior_high",
        "初中": "junior_high",
        "senior": "senior",
        "高中": "senior",
    }
    return mapping.get(val, mapping.get(val.replace("-", "_"), GUIDELINE_BASE_GROUP))

class NutritionAdjuster:
    """营养调整器，用于根据不同年龄阶段调整营养含量和配料量"""
    
    @staticmethod
    def adjust_nutrition(age_group: str, nutrition_data: dict) -> dict:
        """
        根据年龄阶段调整营养数据
        
        Args:
            age_group: 目标年龄阶段
            nutrition_data: 原始营养数据（高中生基准）
            
        Returns:
            调整后的营养数据
        """
        target_group = normalize_age_group(age_group)
        # 获取对应年龄阶段的比例
        ratios = NUTRITION_RATIOS.get(target_group, NUTRITION_RATIOS[GUIDELINE_BASE_GROUP])
        
        # 创建调整后的数据副本
        adjusted_data = nutrition_data.copy()
        
        # 调整营养成分
        adjusted_data["total_calories"] = round(float(nutrition_data.get("total_calories", 0)) * ratios["calories"], 2)
        adjusted_data["total_carbohydrates"] = round(float(nutrition_data.get("total_carbohydrates", 0)) * ratios["carbohydrates"], 2)
        adjusted_data["total_fat"] = round(float(nutrition_data.get("total_fat", 0)) * ratios["fat"], 2)
        adjusted_data["total_protein"] = round(float(nutrition_data.get("total_protein", 0)) * ratios["protein"], 2)
        adjusted_data["total_calcium"] = round(float(nutrition_data.get("total_calcium", 0)) * ratios["calcium"], 2)
        adjusted_data["total_iron"] = round(float(nutrition_data.get("total_iron", 0)) * ratios["iron"], 2)
        adjusted_data["total_vitamin_c"] = round(float(nutrition_data.get("total_vitamin_c", 0)) * ratios["vitamin_c"], 2)
        
        return adjusted_data
    
    @staticmethod
    def adjust_ingredients(age_group: str, ingredients: str) -> str:
        """
        根据年龄阶段调整配料量
        注意：这是一个简单实现，直接返回原始配料字符串
        
        Args:
            age_group: 目标年龄阶段
            ingredients: 原始配料字符串
            
        Returns:
            调整后的配料字符串
        """
        if not ingredients:
            return ingredients
        target_group = normalize_age_group(age_group)
        ratio = NUTRITION_RATIOS.get(target_group, NUTRITION_RATIOS[GUIDELINE_BASE_GROUP]).get("ingredient_amount", 1.0)
        # 保持原有文本，不再追加说明
        return ingredients
