from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# 食材价格模型
class IngredientPriceBase(BaseModel):
    name: str
    price: float
    unit: Optional[str] = "g"

class IngredientPriceCreate(IngredientPriceBase):
    pass

class IngredientPriceResponse(IngredientPriceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    aliases: Optional[List[str]] = Field(default_factory=list, description="配方中可匹配的同义名称，如 西红柿、小番茄")

    class Config:
        from_attributes = True

class IngredientPriceBulkCreate(BaseModel):
    prices: List[IngredientPriceCreate]

# 推荐请求模型
class RecommendationRequest(BaseModel):
    # 将这些字段设为可选，以支持前端直接传入完整的 `prompt` 时不触发 Pydantic 验证错误
    meal_type: Optional[str] = None  # 餐次类型，如早中晚餐
    cycle: Optional[str] = None      # 周期，如一天
    age_group: Optional[str] = None  # 年龄阶段
    user_id: Optional[str] = None    # 用户ID
    # 可选的完整 prompt（优先使用），当前端已将规则拼接为完整提示词时使用
    prompt: Optional[str] = None
    ingredients: Optional[list[str]] = []
    ingredient_prices: Optional[dict[str, float]] = {}

# 数据库推荐请求模型
class DatabaseRecommendationRequest(BaseModel):
    dish_type: Optional[list[str]] = []  # 菜品类型，如breakfast, lunch, dinner
    meal_type: Optional[str] = None      # 餐次类型，用于匹配配餐规则
    category: Optional[list[str]] = []  # 菜品分类，如主食类、素菜类等
    flavor: Optional[list[str]] = []  # 口味，如原味、甜、咸、辣、酸、腥
    season: Optional[list[str]] = []  # 时令，可多选，如四季皆宜、春季、夏季、秋季、冬季
    count: int = Field(default=5, ge=1, le=20)  # 推荐数量，默认5，范围1-20
    nutrition_requirements: Optional[list[str]] = []  # 营养需求，如高蛋白、低脂肪等
    ingredients: Optional[list[str]] = []  # 用户已有食材列表，用于优先匹配
    ingredient_prices: Optional[dict[str, float]] = {}  # 食材价格字典 {食材名: 单价}
    exclude_ids: Optional[list[int]] = []  # 排除的菜品ID
    max_cost: Optional[float] = Field(None, description="最大成本价格")

# 团餐餐次特定设置
class MealSetting(BaseModel):
    num_people: Optional[int] = Field(None, ge=1, description="该餐次的就餐人数")
    target_age_group: Optional[str] = Field(None, description="该餐次的目标人群/年龄段")

# 按配餐规则生成早中晚餐套餐推荐（后端读取管理员保存的规则）
class MealSetRecommendationRequest(BaseModel):
    days: int = Field(default=1, ge=1, le=7)
    meal_types: Optional[list[str]] = []  # breakfast/lunch/dinner
    flavor: Optional[list[str]] = []
    season: Optional[list[str]] = []
    nutrition_requirements: Optional[list[str]] = []
    ingredients: Optional[list[str]] = []
    ingredient_prices: Optional[dict[str, float]] = {}  # 食材价格字典 {食材名: 单价}
    # 成本价格规则
    max_cost_breakfast: Optional[float] = Field(None, description="早餐最大成本")
    max_cost_lunch: Optional[float] = Field(None, description="中餐最大成本")
    max_cost_dinner: Optional[float] = Field(None, description="晚餐最大成本")
    total_max_cost: Optional[float] = Field(None, description="单日总最大成本")
    servings: int = Field(default=1, ge=1, description="默认份数/人数")
    num_people: Optional[int] = Field(None, ge=1, description="默认就餐人数，用于团餐平均营养计算")
    target_age_group: Optional[str] = Field(None, description="默认目标人群")
    meal_settings: Optional[Dict[str, MealSetting]] = Field(default={}, description="各餐次的特定设置")

# MenuItem 创建模型
class MenuItemCreate(BaseModel):
    dish_type: str
    dish_name: str
    category: Optional[str] = ""
    dish_recipe: Optional[str] = ""
    total_calories: Optional[float] = 0.0
    total_carbohydrates: Optional[float] = 0.0
    total_fat: Optional[float] = 0.0
    total_protein: Optional[float] = 0.0
    total_calcium: Optional[float] = 0.0
    total_iron: Optional[float] = 0.0
    total_vitamin_c: Optional[float] = 0.0
    ingredient_count: Optional[int] = 0
    matched_count: Optional[int] = 0
    season: Optional[str] = ""
    flavor: Optional[str] = ""
    cost_price: Optional[float] = 0.0
    
    class Config:
        extra = "ignore"

class MenuItemUpdate(BaseModel):
    dish_type: Optional[str] = None
    dish_name: Optional[str] = None
    category: Optional[str] = None
    dish_recipe: Optional[str] = None
    total_calories: Optional[float] = None
    total_carbohydrates: Optional[float] = None
    total_fat: Optional[float] = None
    total_protein: Optional[float] = None
    total_calcium: Optional[float] = None
    total_iron: Optional[float] = None
    total_vitamin_c: Optional[float] = None
    ingredient_count: Optional[int] = None
    matched_count: Optional[int] = None
    season: Optional[str] = None
    flavor: Optional[str] = None
    cost_price: Optional[float] = None
    
    class Config:
        extra = "ignore"

class MenuItemResponse(BaseModel):
    id: int
    dish_type: str
    dish_name: str
    category: str
    dish_recipe: Optional[str] = ""
    total_calories: float
    total_carbohydrates: float
    total_fat: float
    total_protein: float
    total_calcium: float
    total_iron: float
    total_vitamin_c: float
    ingredient_count: int
    matched_count: int
    season: str
    flavor: str
    cost_price: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
