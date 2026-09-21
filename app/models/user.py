from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.services.db_service import Base
import enum

# 年龄阶段枚举
class AgeGroup(str, enum.Enum):
    PRIMARY = "primary"      # 6-8岁小学
    JUNIOR_LOW = "junior_low"  # 9-11岁初中低龄组
    JUNIOR_HIGH = "junior_high"  # 12-14岁初中高龄组
    SENIOR = "senior"       # 15-17岁高中

class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    # 关系
    users = relationship("User", back_populates="school_rel")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    age_group = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False) # user or admin
    avatar = Column(String, nullable=True)
    
    # 关系
    school_rel = relationship("School", back_populates="users")
    meal_plans = relationship("MealPlan", back_populates="user")
