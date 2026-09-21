"""食材价格别名：配方中的名称与价格表名称不一致时，通过别名映射到同一条价格记录"""
from sqlalchemy import Column, Integer, String, ForeignKey
from app.services.db_service import Base


class IngredientPriceAlias(Base):
    __tablename__ = "ingredient_price_aliases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_price_id = Column(Integer, ForeignKey("ingredient_prices.id", ondelete="CASCADE"), nullable=False, index=True)
    alias_name = Column(String(255), nullable=False, comment="配方中可能出现的名称，如 西红柿、小番茄")
