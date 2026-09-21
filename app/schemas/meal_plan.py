from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime

class MealItem(BaseModel):
    id: Optional[int] = None
    dish_id: Optional[int] = None
    day: Optional[int] = None
    apply_date: Optional[date] = None
    name: str
    meal_type: Optional[str] = None
    dish_type: Optional[str] = None
    category: Optional[str] = None
    servings: Optional[int] = None
    nutrition: Optional[Any] = None
    dish_recipe: Optional[str] = None
    ingredients: Optional[str] = None
    flavor: Optional[str] = None
    season: Optional[str] = None
    cost_price: Optional[float] = 0.0
    procurement_rows: Optional[List[Any]] = None

class MealPlanCreate(BaseModel):
    name: str
    date: date
    age_group: str
    meals: List[MealItem]
    total_cost: Optional[float] = 0.0
    breakfast_avg_cost: Optional[float] = 0.0
    lunch_avg_cost: Optional[float] = 0.0
    dinner_avg_cost: Optional[float] = 0.0

class MealPlanOut(BaseModel):
    id: int
    name: str
    date: date
    age_group: str
    is_published: int
    delivery_status: int
    meals: List[Any]
    total_cost: Optional[float] = 0.0
    breakfast_avg_cost: Optional[float] = 0.0
    lunch_avg_cost: Optional[float] = 0.0
    dinner_avg_cost: Optional[float] = 0.0
    published_at: Optional[datetime]
    user_id: int

    class Config:
        orm_mode = True
        from_attributes = True

class DeliveryStatusUpdate(BaseModel):
    status: int
