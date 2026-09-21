"""
用户服务层
封装用户相关的业务逻辑
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user import User, School
from app.schemas.user import UserCreate
from app.core.exceptions import (
    BusinessException,
    ResourceNotFoundException,
    ValidationException
)

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundException(f"用户 (ID: {user_id})")
        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate, creator_role: str = "user") -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing_user = UserService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise BusinessException("用户名已存在", "USERNAME_EXISTS")

        # 获取或创建学校
        school = db.query(School).filter(School.name == user_data.school).first()
        if not school:
            school = School(name=user_data.school)
            db.add(school)
            db.flush()  # 获取ID但不提交

        # 创建用户
        from app.routers.auth import get_password_hash
        hashed_password = get_password_hash(user_data.password)

        user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            school_id=school.id,
            age_group=user_data.age_group,
            role=user_data.role if creator_role == "admin" else "user"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"用户创建成功: {user.username}")
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, update_data: dict, operator_role: str) -> User:
        """更新用户信息"""
        user = UserService.get_user_by_id(db, user_id)

        # 只允许管理员更新其他用户
        if operator_role != "admin":
            raise AuthorizationException("无权限修改其他用户信息")

        # 更新用户名
        if "username" in update_data:
            existing = UserService.get_user_by_username(db, update_data["username"])
            if existing and existing.id != user_id:
                raise BusinessException("用户名已存在", "USERNAME_EXISTS")
            user.username = update_data["username"]

        # 更新密码
        if "password" in update_data and update_data["password"]:
            from app.routers.auth import get_password_hash
            user.hashed_password = get_password_hash(update_data["password"])

        # 更新角色
        if "role" in update_data:
            if update_data["role"] not in ("admin", "user"):
                raise ValidationException("角色不合法")
            user.role = update_data["role"]

        # 更新学校
        if "school" in update_data:
            school = db.query(School).filter(School.name == update_data["school"]).first()
            if not school:
                school = School(name=update_data["school"])
                db.add(school)
                db.flush()
            user.school_id = school.id

        # 更新年龄段
        if "age_group" in update_data:
            user.age_group = update_data["age_group"]

        db.commit()
        db.refresh(user)

        logger.info(f"用户更新成功: {user.username}")
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int, operator_role: str) -> None:
        """删除用户"""
        # 只允许管理员删除用户
        if operator_role != "admin":
            raise AuthorizationException("无权限删除用户")

        user = UserService.get_user_by_id(db, user_id)

        db.delete(user)
        db.commit()

        logger.info(f"用户删除成功: {user.username}")

    @staticmethod
    def list_users(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """
        获取用户列表

        Returns:
            (用户列表, 总数)
        """
        query = db.query(User)

        # 关键词搜索
        if keyword:
            query = query.filter(User.username.ilike(f"%{keyword}%"))

        # 使用eager loading避免N+1查询
        query = query.options(db.joinedload(User.school_rel))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        # 格式化返回结果
        results = []
        for u in items:
            results.append({
                "id": u.id,
                "username": u.username,
                "user_id": u.id,
                "school": u.school_rel.name if u.school_rel else "",
                "age_group": u.age_group,
                "role": u.role or "user",
                "avatar": u.avatar or ""
            })

        return results, total


# 导入AuthorizationException
from app.core.exceptions import AuthorizationException
