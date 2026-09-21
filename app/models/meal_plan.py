from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.services.db_service import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment='计划名称')
    date = Column(Date, nullable=False, comment='计划日期')
    age_group = Column(String(50), nullable=False, comment='年龄段')
    is_published = Column(Integer, nullable=False, default=0, comment='是否发布：0草稿1已发布')
    delivery_status = Column(Integer, nullable=False, default=0, comment='配送状态：0未配送1已配送')
    meals = Column(JSON, nullable=False, comment='餐食安排，JSON 格式')
    total_cost = Column(Float, nullable=False, default=0.0, comment='总成本')
    breakfast_avg_cost = Column(Float, nullable=False, default=0.0, comment='早餐平均成本')
    lunch_avg_cost = Column(Float, nullable=False, default=0.0, comment='中餐平均成本')
    dinner_avg_cost = Column(Float, nullable=False, default=0.0, comment='晚餐平均成本')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    published_at = Column(DateTime, nullable=True, comment='发布时间')
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment='创建用户ID')

    # 关系
    user = relationship("User", back_populates="meal_plans")
