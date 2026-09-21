from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.services.db_service import Base

class IngredientNutrition(Base):
    __tablename__ = "ingredient_nutrition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True, comment="食材名称")
    dietary_fiber = Column(Numeric(10, 2), default=0.00, comment="总膳食纤维(Dietary fiber) [g]")
    carbohydrates = Column(Numeric(10, 2), default=0.00, comment="碳水化合物(CHO) [g]")
    vitamin_a = Column(Numeric(10, 4), default=0.0000, comment="维生素A(Vitain) [mg]")
    vitamin_c = Column(Numeric(10, 2), default=0.00, comment="维生素C(Vitain C) [mg]")
    energy_kj = Column(Numeric(10, 2), default=0.00, comment="能量(Enery)[KJ]")
    fat = Column(Numeric(10, 2), default=0.00, comment="脂肪(Fat)[g]")
    protein = Column(Numeric(10, 2), default=0.00, comment="蛋白质(Protein)[g]")
    calcium = Column(Numeric(10, 2), default=0.00, comment="钙(Ca)[mg]")
    iron = Column(Numeric(10, 2), default=0.00, comment="铁(Fe)[mg]")
    zinc = Column(Numeric(10, 2), default=0.00, comment="锌(Zn)[mg]")
    fat_energy_ratio = Column(Numeric(5, 2), default=0.00, comment="脂肪供能比（%E)")
    carbohydrate_energy_ratio = Column(Numeric(5, 2), default=0.00, comment="碳水化合物供能比（%E)")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
