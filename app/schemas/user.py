from pydantic import BaseModel, Field
from typing import Optional

# 用户注册模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    school: str = Field(..., min_length=1) # 前端传过来的还是学校名称
    # 支持一个学校对应多个年龄段，这里使用逗号分隔的字符串保存多个值
    # 如: "primary,junior_low"
    age_group: str
    role: Optional[str] = "user"
    # user_id removed

# 用户登录模型
class UserLogin(BaseModel):
    username: str
    password: str

# 用户响应模型
class UserResponse(BaseModel):
    id: int
    username: str
    school: str # 返回时可能需要返回学校名称
    # 返回时同样使用字符串形式（兼容旧数据）
    age_group: str
    role: str
    avatar: Optional[str] = None
    
    class Config:
        from_attributes = True

# Token模型
class Token(BaseModel):
    access_token: str
    token_type: str

# Token数据模型
class TokenData(BaseModel):
    username: Optional[str] = None