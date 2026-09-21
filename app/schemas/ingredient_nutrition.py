from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class IngredientNutritionBase(BaseModel):
    name: str = Field(..., description="食材名称")
    dietary_fiber: Optional[float] = Field(default=0.0, description="总膳食纤维(Dietary fiber) [g]")
    carbohydrates: Optional[float] = Field(default=0.0, description="碳水化合物(CHO) [g]")
    vitamin_a: Optional[float] = Field(default=0.0, description="维生素A(Vitain) [mg]")
    vitamin_c: Optional[float] = Field(default=0.0, description="维生素C(Vitain C) [mg]")
    energy_kj: Optional[float] = Field(default=0.0, description="能量(Enery)[KJ]")
    fat: Optional[float] = Field(default=0.0, description="脂肪(Fat)[g]")
    protein: Optional[float] = Field(default=0.0, description="蛋白质(Protein)[g]")
    calcium: Optional[float] = Field(default=0.0, description="钙(Ca)[mg]")
    iron: Optional[float] = Field(default=0.0, description="铁(Fe)[mg]")
    zinc: Optional[float] = Field(default=0.0, description="锌(Zn)[mg]")
    fat_energy_ratio: Optional[float] = Field(default=0.0, description="脂肪供能比（%E)")
    carbohydrate_energy_ratio: Optional[float] = Field(default=0.0, description="碳水化合物供能比（%E)")

class IngredientNutritionCreate(IngredientNutritionBase):
    pass

class IngredientNutritionUpdate(BaseModel):
    name: Optional[str] = None
    dietary_fiber: Optional[float] = None
    carbohydrates: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_c: Optional[float] = None
    energy_kj: Optional[float] = None
    fat: Optional[float] = None
    protein: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None
    zinc: Optional[float] = None
    fat_energy_ratio: Optional[float] = None
    carbohydrate_energy_ratio: Optional[float] = None

class IngredientNutritionResponse(IngredientNutritionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IngredientNutritionBulkCreate(BaseModel):
    items: List[IngredientNutritionCreate]
