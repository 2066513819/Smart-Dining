from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.services.db_service import Base

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_type = Column(String(50), nullable=False, index=True)
    dish_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="", index=True)
    dish_recipe = Column(Text, nullable=True)
    total_calories = Column(Numeric(10, 1), nullable=False, default=0.0)
    total_carbohydrates = Column(Numeric(10, 1), nullable=False, default=0.0)
    total_fat = Column(Numeric(10, 1), nullable=False, default=0.0)
    total_protein = Column(Numeric(10, 1), nullable=False, default=0.0)
    total_calcium = Column(Numeric(10, 1), nullable=False, default=0.0)
    total_iron = Column(Numeric(10, 1), nullable=False, default=0.0)
    total_vitamin_c = Column(Numeric(10, 1), nullable=False, default=0.0)
    ingredient_count = Column(Integer, nullable=False, default=0)
    matched_count = Column(Integer, nullable=False, default=0)
    season = Column(String(100), nullable=False, default="")
    flavor = Column(String(100), nullable=False, default="")
    cost_price = Column(Numeric(10, 2), nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_dish_type', 'dish_type'),
        Index('idx_category', 'category'),
        Index('idx_season', 'season'),
        Index('idx_flavor', 'flavor'),
        Index('idx_calories', 'total_calories'),
        Index('idx_protein', 'total_protein'),
    )
