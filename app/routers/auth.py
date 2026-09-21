from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import shutil
import os
import logging
from app.models.user import User, School
from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.services.db_service import get_db
from app.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 初始化模板引擎
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# 密码加密上下文 - 改用pbkdf2_sha256算法，避免bcrypt版本兼容性问题
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=30000  # 设置默认迭代次数
)

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# 验证密码
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 获取密码哈希值
def get_password_hash(password):
    return pwd_context.hash(password)

# 根据用户名获取用户
def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# 获取当前用户
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.info("===== 认证开始 =====")
        logger.info(f"收到的令牌: {token[:20]}..." if len(token) > 20 else f"收到的令牌: {token}")
        logger.debug(f"使用的密钥: {settings.SECRET_KEY[:20]}...")
        logger.debug(f"使用的算法: {settings.ALGORITHM}")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.debug(f"解码后的payload: {payload}")
        
        username: str = payload.get("sub")
        logger.info(f"提取的用户名: {username}")
        
        if username is None:
            logger.warning("用户名不存在，认证失败")
            raise credentials_exception
        
        token_data = TokenData(username=username)
        logger.debug(f"TokenData: {token_data}")
        
        user = get_user(db, username=token_data.username)
        logger.info(f"查询到的用户: {user}")
        
        if user is None:
            logger.warning("用户不存在，认证失败")
            raise credentials_exception
        
        logger.info("===== 认证成功 =====")
        return user
    except JWTError as e:
        logger.warning(f"JWT验证失败: {type(e).__name__}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"认证过程异常: {type(e).__name__}: {str(e)}")
        raise credentials_exception

# 用户注册 (仅管理员可操作)
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可添加账户")
    
    # 检查用户名是否已存在
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 处理学校逻辑
    school_name = user.school
    db_school = db.query(School).filter(School.name == school_name).first()
    if not db_school:
        # 如果学校不存在，创建新学校
        db_school = School(name=school_name)
        db.add(db_school)
        db.commit()
        db.refresh(db_school)
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        school_id=db_school.id, # 关联学校ID
        age_group=user.age_group,
        role=user.role or "user" # 使用传入的角色，默认为普通用户
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 构造响应对象，手动填充school名称
    # 注意：UserResponse模型中school字段是str，而User模型中school_rel才是关系对象
    # SQLAlchemy会自动加载school_rel，但为了确保UserResponse正确序列化，我们需要确保user对象有school属性或正确映射
    # Pydantic的from_attributes=True会尝试从对象属性读取
    # 由于User模型没有school字段了，只有school_rel关系和school_id
    # 我们需要确保UserResponse能获取到学校名称。
    # 最简单的方法是返回前给db_user动态添加一个school属性
    if db_user.school_rel:
        db_user.school = db_user.school_rel.name
    else:
        db_user.school = ""
        
    return db_user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    # 同样处理school字段
    if current_user.school_rel:
        current_user.school = current_user.school_rel.name
    else:
        current_user.school = ""
    return current_user
 
 
# 列表接口（供前端管理页面使用）
@router.get("/users")
def list_users(page: int = 1, page_size: int = 10, keyword: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 仅管理员可访问管理接口
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    query = db.query(User)
    if keyword:
        query = query.filter(User.username.ilike(f"%{keyword}%"))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for u in items:
        school_name = u.school_rel.name if getattr(u, "school_rel", None) else ""
        results.append({
            "id": u.id,
            "username": u.username,
            # 前端模板期望的字段名为 user_id，我们使用数据库主键作为展示值
            "user_id": u.id,
            "school": school_name,
            "age_group": u.age_group,
            "role": (u.role or "user")
        })

    return {"items": results, "total": total, "page": page, "page_size": page_size}


# 管理员：更新用户资料（包括密码）
@router.put("/users/{user_id}")
def admin_update_user(user_id: int, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    
    if "username" in payload:
        target.username = payload["username"]
    
    if "password" in payload and payload["password"]:
        target.hashed_password = get_password_hash(payload["password"])
        
    if "role" in payload:
        if payload["role"] not in ("admin", "user"):
            raise HTTPException(status_code=400, detail="角色不合法")
        target.role = payload["role"]
        
    if "school" in payload:
        school_name = payload["school"]
        db_school = db.query(School).filter(School.name == school_name).first()
        if not db_school:
            db_school = School(name=school_name)
            db.add(db_school)
            db.commit()
            db.refresh(db_school)
        target.school_id = db_school.id
        
    if "age_group" in payload:
        target.age_group = payload["age_group"]
        
    db.commit()
    db.refresh(target)
    
    school_name = target.school_rel.name if getattr(target, "school_rel", None) else ""
    return {
        "id": target.id,
        "username": target.username,
        "school": school_name,
        "age_group": target.age_group,
        "role": target.role or "user",
        "avatar": target.avatar or ""
    }


# 获取单个用户详情（供编辑模态框使用）
@router.get("/users/{user_id}")
def get_user_detail(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    school_name = target.school_rel.name if getattr(target, "school_rel", None) else ""
    return {
        "id": target.id,
        "username": target.username,
        "user_id": target.id,
        "school": school_name,
        "age_group": target.age_group,
        "role": (target.role or "user")
    }


# 删除用户（管理员）
@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    db.delete(target)
    db.commit()
    return {"detail": "删除成功"}

# 登录页面 - GET请求
@router.get("/login")
def login_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse(
        "auth/login.html", 
        {"request": request, "error": error}
    )

# 登录处理 - POST请求
@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db)
):
    user = get_user(db, username=username)
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html", 
            {"request": request, "error": "用户名或密码错误"}
        )
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 这里可以添加设置cookie的逻辑
    response = templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "餐饮推荐系统", "current_user": user}
    )
    
    # 设置JWT令牌到cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return response

# 用户登录（使用OAuth2密码流）
@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 确保上传目录存在
UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 上传头像
@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只允许上传图片文件"
        )
    
    # 验证文件大小（最大5MB）
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片大小不能超过5MB"
        )
    
    # 生成文件名
    filename = f"{current_user.username}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 更新用户头像URL
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar = avatar_url
    db.commit()
    db.refresh(current_user)
    
    return current_user

# 更新个人信息
@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if "username" in profile_data:
        current_user.username = profile_data["username"]
    
    if "school" in profile_data:
        school_name = profile_data["school"]
        db_school = db.query(School).filter(School.name == school_name).first()
        if not db_school:
            db_school = School(name=school_name)
            db.add(db_school)
            db.commit()
            db.refresh(db_school)
        current_user.school_id = db_school.id
    
    if "age_group" in profile_data:
        current_user.age_group = profile_data["age_group"]
    
    if "password" in profile_data and profile_data["password"]:
        current_user.hashed_password = get_password_hash(profile_data["password"])
    
    db.commit()
    db.refresh(current_user)
    
    if current_user.school_rel:
        current_user.school = current_user.school_rel.name
    else:
        current_user.school = ""
    return current_user

# 获取当前用户信息
@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    if current_user.school_rel:
        current_user.school = current_user.school_rel.name
    else:
        current_user.school = ""
    return current_user

# 退出登录
@router.get("/logout")
def logout(request: Request):
    response = templates.TemplateResponse(
        "auth/login.html", 
        {"request": request, "message": "已成功退出登录"}
    )
    
    # 清除cookie
    response.delete_cookie("access_token")
    
    return response
