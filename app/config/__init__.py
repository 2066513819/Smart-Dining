from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str
    
    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Dify API配置 - 只使用原始的配置字段
    DIFY_API_KEY: str
    DIFY_API_URL: str
    DIFY_APP_ID: str = "16ce7bb2-50e2-44da-9771-c5c221b8b913"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
