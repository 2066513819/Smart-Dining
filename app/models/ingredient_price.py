from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.services.db_service import Base

class IngredientPrice(Base):
    __tablename__ = "ingredient_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="食材或配方名称")
    price = Column(Numeric(10, 4), nullable=False, default=0.0000, comment="单价")
    unit = Column(String(50), default="g", comment="单位（默认g）")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
