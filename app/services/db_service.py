from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建SQLAlchemy引擎
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False
elif "mysql" in settings.DATABASE_URL:
    # MySQL 8.0 连接参数优化
    connect_args.update({
        "charset": "utf8mb4",
        "use_unicode": True,
        "connect_timeout": 10
    })

# MySQL 8.0 连接池配置
enigne_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": False  # 生产环境建议关闭
}

engine = create_engine(
    settings.DATABASE_URL, 
    **enigne_kwargs
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()