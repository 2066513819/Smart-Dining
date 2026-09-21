from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置类，使用pydantic-settings进行环境变量管理"""

    # 数据库配置
    DATABASE_URL: str

    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时，更合理的安全设置

    # Dify API配置 - 主推荐智能体
    DIFY_API_KEY: str
    DIFY_API_URL: str
    DIFY_APP_ID: Optional[str] = None

    # Dify API配置 - 菜品分析智能体
    DIFY_ANALYSIS_API_KEY: Optional[str] = None
    DIFY_ANALYSIS_API_URL: Optional[str] = None
    DIFY_ANALYSIS_APP_ID: Optional[str] = None

    # 应用配置
    APP_NAME: str = "餐饮推荐系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_DIR: str = "uploads"

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略未定义的环境变量
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_config()

    def _validate_config(self):
        """验证必需的配置项"""
        required_fields = ['DATABASE_URL', 'SECRET_KEY', 'DIFY_API_KEY', 'DIFY_API_URL']
        missing_fields = []

        for field in required_fields:
            value = getattr(self, field, None)
            if not value:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"配置验证失败: 缺少必需的环境变量: {', '.join(missing_fields)}\n"
                f"请在.env文件中配置这些变量"
            )

        # 验证JWT密钥强度
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                f"SECRET_KEY长度不足（当前: {len(self.SECRET_KEY)}字符），至少需要32个字符"
            )

        # 验证数据库URL格式
        if not any(prefix in self.DATABASE_URL.lower() for prefix in ['mysql', 'sqlite', 'postgresql']):
            raise ValueError(
                f"不支持的数据库类型: {self.DATABASE_URL.split(':')[0] if ':' in self.DATABASE_URL else 'unknown'}"
            )


settings = Settings()
