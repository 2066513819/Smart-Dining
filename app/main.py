from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from app.routers import auth, recommendation, system, menu_item, ingredient_price
from app.routers.ingredient_nutrition import router as ingredient_nutrition_router
from app.routers import purchase_order as purchase_order_router
from app.routers import nutrition as nutrition_router
from app.routers.supplier_price_import import router as supplier_price_import_router
from app.routers import meal_plan
from app.services.db_service import engine, Base, SessionLocal, get_db
from app.models import User, AgeGroup, School, MealPlan
from app.routers.auth import get_password_hash, get_user
from app.config import settings
import os
import logging
import sys

# 配置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # 输出到控制台
        logging.FileHandler("app.log")  # 输出到文件
    ]
)
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 自动检查并添加缺失的列 (如 delivery_status)
def auto_migrate():
    from sqlalchemy import inspect
    db = SessionLocal()
    try:
        # 检查 meal_plans 表是否有 delivery_status 列
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('meal_plans')]
        if 'delivery_status' not in columns:
            logger.info("正在为 meal_plans 表添加 delivery_status 列...")
            db.execute(text("ALTER TABLE meal_plans ADD COLUMN delivery_status INTEGER DEFAULT 0"))
            db.commit()
            logger.info("delivery_status 列添加成功")

        # 兼容旧库：补齐 total_cost / breakfast_avg_cost / lunch_avg_cost / dinner_avg_cost
        if 'total_cost' not in columns:
            logger.info("正在为 meal_plans 表添加 total_cost 列...")
            db.execute(text("ALTER TABLE meal_plans ADD COLUMN total_cost FLOAT NOT NULL DEFAULT 0.0"))
            db.commit()
            logger.info("total_cost 列添加成功")

        for col in ('breakfast_avg_cost', 'lunch_avg_cost', 'dinner_avg_cost'):
            if col not in columns:
                logger.info(f"正在为 meal_plans 表添加 {col} 列...")
                db.execute(text(f"ALTER TABLE meal_plans ADD COLUMN {col} FLOAT NOT NULL DEFAULT 0.0"))
                db.commit()
                logger.info(f"{col} 列添加成功")
    except Exception as e:
        logger.error(f"自动迁移失败: {e}")
    finally:
        db.close()

auto_migrate()

# 创建默认管理员账号
def create_default_admin():
    logger.debug("开始检查默认管理员账号...")
    db = SessionLocal()
    try:
        # 检查是否已存在默认管理员账号
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("未找到默认管理员账号，开始创建...")
            # 确保存在默认学校
            school = db.query(School).filter(School.name == "测试学校").first()
            if not school:
                school = School(name="测试学校")
                db.add(school)
                db.commit()
                db.refresh(school)
            # 创建默认管理员账号（新结构）
            default_admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                school_id=school.id,
                age_group="senior",
                role="admin"
            )
            db.add(default_admin)
            db.commit()
            logger.info("默认管理员账号已创建：")
            logger.info("用户名：admin")
            logger.info("密码：admin123")
            logger.info("学校：测试学校")
            logger.info("年龄阶段：高中")
            logger.info("角色：管理员")
        else:
            logger.debug("默认管理员账号已存在")
    except Exception as e:
        logger.error(f"创建默认管理员账号失败：{e}")
        db.rollback()
    finally:
        db.close()
        logger.debug("数据库连接已关闭")

# 调用函数创建默认管理员账号
create_default_admin()

# 中国时区（UTC+8）
CHINA_TZ = timezone(timedelta(hours=8))

app = FastAPI(title="餐饮推荐系统API", version="1.0.0")

# 配置模板引擎
templates = Jinja2Templates(directory="app/templates")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# 从请求中获取当前用户
async def get_current_user_from_request(request: Request, db: Session = Depends(get_db)):
    # 尝试从cookie中获取token
    token = request.cookies.get("access_token")
    if token:
        # 移除Bearer前缀
        if token.startswith("Bearer "):
            token = token[7:]
        
        try:
            # 解码JWT令牌
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            
            # 获取用户
            user = get_user(db, username=username)
            return user
        except JWTError:
            return None
    return None

# 配置CORS，确保在所有响应中都包含CORS头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 允许本地前端开发地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # 允许暴露所有头
    max_age=3600,  # 设置CORS预检请求的缓存时间
)



# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(recommendation.router, prefix="/recommendation", tags=["推荐"])
app.include_router(system.router, prefix="/system", tags=["系统"])
app.include_router(menu_item.router, prefix="/menu_items", tags=["菜单项"])
app.include_router(meal_plan.router, prefix="/meal_plans", tags=["发布计划"])
app.include_router(ingredient_price.router, prefix="/ingredient_prices", tags=["食材价格"])
app.include_router(ingredient_nutrition_router, prefix="/ingredient_nutritions", tags=["食材营养"])
app.include_router(supplier_price_import_router, prefix="/supplier-price-import", tags=["供应商价格导入"])
app.include_router(purchase_order_router.router, prefix="", tags=["采购单"])
app.include_router(nutrition_router.router, prefix="", tags=["营养指南"])

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    # 查询已发布的菜谱计划（最近10条，仅限当前用户）
    try:
        if current_user:
            published = db.query(MealPlan).filter(
                MealPlan.is_published == 1,
                MealPlan.user_id == current_user.id
            ).order_by(MealPlan.published_at.desc()).limit(10).all()
        else:
            published = []
    except Exception as e:
        logger.exception("查询已发布菜谱失败：%s", e)
        published = []
    # 序列化为简单字典，便于模板渲染
    published_list = []
    for p in published:
        meals_val = p.meals
        try:
            if isinstance(meals_val, str):
                meals_val = json.loads(meals_val)
        except Exception:
            pass
        # 处理时区
        pub_at = p.published_at
        if pub_at and pub_at.tzinfo is None:
            pub_at = pub_at.replace(tzinfo=CHINA_TZ)
            
        published_list.append({
            "id": p.id,
            "name": p.name,
            "date": str(p.date) if p.date else None,
            "user_id": p.user_id,
            "published_at": pub_at.strftime('%Y-%m-%d %H:%M') if pub_at else (str(p.date) if p.date else None),
            "meals": meals_val
        })
    return templates.TemplateResponse("home.html", {"request": request, "title": "餐饮推荐系统", "current_user": current_user, "published_plans": published_list})

@app.get("/index")
async def index(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    try:
        if current_user:
            published = db.query(MealPlan).filter(
                MealPlan.is_published == 1,
                MealPlan.user_id == current_user.id
            ).order_by(MealPlan.published_at.desc()).limit(10).all()
        else:
            published = []
    except Exception as e:
        logger.exception("查询已发布菜谱失败：%s", e)
        published = []
    published_list = []
    for p in published:
        # 处理时区
        pub_at = p.published_at
        if pub_at and pub_at.tzinfo is None:
            pub_at = pub_at.replace(tzinfo=CHINA_TZ)
            
        published_list.append({
            "id": p.id,
            "name": p.name,
            "date": str(p.date) if p.date else None,
            "user_id": p.user_id,
            "published_at": pub_at.strftime('%Y-%m-%d %H:%M') if pub_at else (str(p.date) if p.date else None),
            "meals": p.meals
        })
    return templates.TemplateResponse("home.html", {"request": request, "title": "餐饮推荐系统", "current_user": current_user, "published_plans": published_list})

# 推荐查询页面
@app.get("/recommendation")
async def recommendation_index(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("recommendation/index.html", {"request": request, "title": "推荐查询", "current_user": current_user})

# 菜品管理页面
@app.get("/dish/list")
async def dish_list(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("system/dish_list.html", {"request": request, "title": "菜品管理", "current_user": current_user})

# 用户管理页面
@app.get("/system/user")
async def user_list(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("system/user_list.html", {"request": request, "title": "用户管理", "current_user": current_user})

# 角色管理页面
@app.get("/system/role")
async def role_list(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("system/role_list.html", {"request": request, "title": "角色管理", "current_user": current_user})

# 个人中心页面
@app.get("/profile")
async def profile(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("auth/profile.html", {"request": request, "title": "个人中心", "current_user": current_user})

# 修改密码页面
@app.get("/change_password")
async def change_password(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("auth/change_password.html", {"request": request, "title": "修改密码", "current_user": current_user})
