from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from typing import List, Optional
from app.models.menu_item import MenuItem
from app.schemas.dish import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.meal_plan import MealPlan
from datetime import datetime, timezone, timedelta, date
import calendar

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

CHINA_TZ = timezone(timedelta(hours=8))

def format_datetime_with_timezone(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CHINA_TZ)
    if dt.tzinfo != CHINA_TZ:
        dt = dt.astimezone(CHINA_TZ)
    return dt.isoformat()

def to_response(item: MenuItem) -> MenuItemResponse:
    return MenuItemResponse(
        id=item.id,
        dish_type=item.dish_type,
        dish_name=item.dish_name,
        category=item.category or "",
        dish_recipe=item.dish_recipe or "",
        total_calories=float(item.total_calories or 0.0),
        total_carbohydrates=float(item.total_carbohydrates or 0.0),
        total_fat=float(item.total_fat or 0.0),
        total_protein=float(item.total_protein or 0.0),
        total_calcium=float(item.total_calcium or 0.0),
        total_iron=float(item.total_iron or 0.0),
        total_vitamin_c=float(item.total_vitamin_c or 0.0),
        ingredient_count=int(item.ingredient_count or 0),
        matched_count=int(item.matched_count or 0),
        season=item.season or "",
        flavor=item.flavor or "",
        cost_price=float(item.cost_price or 0.0),
        created_at=format_datetime_with_timezone(item.created_at),
        updated_at=format_datetime_with_timezone(item.updated_at),
    )

def normalize_dish_type(v: Optional[str]) -> Optional[str]:
    if not v:
        return v
    if v in ("早餐", "午餐", "晚餐"):
        return {"早餐": "breakfast", "午餐": "lunch", "晚餐": "dinner"}[v]
    return v

@router.get("/", response_model=List[MenuItemResponse])
def list_menu_items(
    skip: int = 0,
    limit: int = 100,
    dish_type: Optional[str] = None,
    category: Optional[List[str]] = Query(None),
    flavor: Optional[str] = None,
    season: Optional[str] = None,
    keyword: Optional[str] = None,
    min_calories: Optional[float] = None,
    max_calories: Optional[float] = None,
    min_protein: Optional[float] = None,
    max_protein: Optional[float] = None,
    min_carbs: Optional[float] = None,
    max_carbs: Optional[float] = None,
    min_fat: Optional[float] = None,
    max_fat: Optional[float] = None,
    ingredient: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(MenuItem)
    logger.debug(f"DEBUG: list_menu_items called with keyword='{keyword}', dish_type='{dish_type}', category='{category}'")
    dt = normalize_dish_type(dish_type)
    if dt:
        q = q.filter(MenuItem.dish_type == dt)
    if category:
        # 过滤掉空字符串并支持多选
        valid_categories = [c for c in category if c]
        if valid_categories:
            q = q.filter(MenuItem.category.in_(valid_categories))
    if flavor:
        q = q.filter(MenuItem.flavor.ilike(f"%{flavor}%"))
    if season:
        q = q.filter(MenuItem.season.ilike(f"%{season}%"))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(or_(MenuItem.dish_name.ilike(kw), MenuItem.dish_recipe.ilike(kw)))
    
    # Nutrition range filters
    if min_calories is not None:
        q = q.filter(MenuItem.total_calories >= min_calories)
    if max_calories is not None:
        q = q.filter(MenuItem.total_calories <= max_calories)
    if min_protein is not None:
        q = q.filter(MenuItem.total_protein >= min_protein)
    if max_protein is not None:
        q = q.filter(MenuItem.total_protein <= max_protein)
    if min_carbs is not None:
        q = q.filter(MenuItem.total_carbohydrates >= min_carbs)
    if max_carbs is not None:
        q = q.filter(MenuItem.total_carbohydrates <= max_carbs)
    if min_fat is not None:
        q = q.filter(MenuItem.total_fat >= min_fat)
    if max_fat is not None:
        q = q.filter(MenuItem.total_fat <= max_fat)
    
    # Ingredient filter
    if ingredient:
        q = q.filter(MenuItem.dish_recipe.ilike(f"%{ingredient}%"))
        
    items = q.order_by(MenuItem.created_at.desc()).offset(skip).limit(limit).all()
    logger.debug(f"DEBUG: Found {len(items)} items for keyword='{keyword}'")
    return [to_response(i) for i in items]

@router.get("/count")
def count_menu_items(
    dish_type: Optional[str] = None,
    category: Optional[List[str]] = Query(None),
    flavor: Optional[str] = None,
    season: Optional[str] = None,
    keyword: Optional[str] = None,
    min_calories: Optional[float] = None,
    max_calories: Optional[float] = None,
    min_protein: Optional[float] = None,
    max_protein: Optional[float] = None,
    min_carbs: Optional[float] = None,
    max_carbs: Optional[float] = None,
    min_fat: Optional[float] = None,
    max_fat: Optional[float] = None,
    ingredient: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(MenuItem)
    dt = normalize_dish_type(dish_type)
    if dt:
        q = q.filter(MenuItem.dish_type == dt)
    if category:
        valid_categories = [c for c in category if c]
        if valid_categories:
            q = q.filter(MenuItem.category.in_(valid_categories))
    if flavor:
        q = q.filter(MenuItem.flavor.ilike(f"%{flavor}%"))
    if season:
        q = q.filter(MenuItem.season.ilike(f"%{season}%"))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(or_(MenuItem.dish_name.ilike(kw), MenuItem.dish_recipe.ilike(kw)))
        
    # Nutrition range filters
    if min_calories is not None:
        q = q.filter(MenuItem.total_calories >= min_calories)
    if max_calories is not None:
        q = q.filter(MenuItem.total_calories <= max_calories)
    if min_protein is not None:
        q = q.filter(MenuItem.total_protein >= min_protein)
    if max_protein is not None:
        q = q.filter(MenuItem.total_protein <= max_protein)
    if min_carbs is not None:
        q = q.filter(MenuItem.total_carbohydrates >= min_carbs)
    if max_carbs is not None:
        q = q.filter(MenuItem.total_carbohydrates <= max_carbs)
    if min_fat is not None:
        q = q.filter(MenuItem.total_fat >= min_fat)
    if max_fat is not None:
        q = q.filter(MenuItem.total_fat <= max_fat)
    
    # Ingredient filter
    if ingredient:
        q = q.filter(MenuItem.dish_recipe.ilike(f"%{ingredient}%"))
        
    total = q.count()
    return {"total": total}

@router.get("/{item_id}", response_model=MenuItemResponse)
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜品未找到")
    return to_response(db_item)

@router.post("/", response_model=MenuItemResponse)
def create_menu_item(item: MenuItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 检查菜品名是否已存在
    existing_item = db.query(MenuItem).filter(MenuItem.dish_name == item.dish_name).first()
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"菜品 '{item.dish_name}' 在菜品库中已存在"
        )
        
    db_item = MenuItem(
        dish_type=item.dish_type,
        dish_name=item.dish_name,
        category=item.category or "",
        dish_recipe=item.dish_recipe or "",
        total_calories=item.total_calories or 0.0,
        total_carbohydrates=item.total_carbohydrates or 0.0,
        total_fat=item.total_fat or 0.0,
        total_protein=item.total_protein or 0.0,
        total_calcium=item.total_calcium or 0.0,
        total_iron=item.total_iron or 0.0,
        total_vitamin_c=item.total_vitamin_c or 0.0,
        ingredient_count=item.ingredient_count or 0,
        matched_count=item.matched_count or 0,
        season=item.season or "",
        flavor=item.flavor or "",
        cost_price=item.cost_price or 0.0,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return to_response(db_item)

@router.put("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(item_id: int, item: MenuItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜品未找到")
    for field, value in item.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return to_response(db_item)

@router.delete("/{item_id}")
def delete_menu_item(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜品未找到")
    db.delete(db_item)
    db.commit()
    return {"message": "菜品删除成功"}


@router.get("/admin/stats")
def get_admin_stats(
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理员仪表盘统计数据"""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # 生成日期列表
    days_list = []
    active_user_counts = []
    new_dish_counts = []
    
    for i in range(days):
        d = start_date + timedelta(days=i)
        days_list.append(d.isoformat())
        
        # 统计每天的新增菜品数
        next_day = d + timedelta(days=1)
        new_dishes = db.query(func.count(MenuItem.id)).filter(
            MenuItem.created_at >= datetime.combine(d, datetime.min.time()).replace(tzinfo=CHINA_TZ),
            MenuItem.created_at < datetime.combine(next_day, datetime.min.time()).replace(tzinfo=CHINA_TZ)
        ).scalar() or 0
        new_dish_counts.append(new_dishes)
        
        # 统计每天活跃用户数（有发布菜谱计划的用户）
        active_users = db.query(func.count(func.distinct(MealPlan.user_id))).filter(
            MealPlan.published_at >= datetime.combine(d, datetime.min.time()).replace(tzinfo=CHINA_TZ),
            MealPlan.published_at < datetime.combine(next_day, datetime.min.time()).replace(tzinfo=CHINA_TZ),
            MealPlan.is_published == 1
        ).scalar() or 0
        active_user_counts.append(active_users)
    
    # 统计总数
    total_database_dishes = db.query(func.count(MenuItem.id)).scalar() or 0
    total_published_meal_plans = db.query(func.count(MealPlan.id)).filter(
        MealPlan.is_published == 1
    ).scalar() or 0
    
    return {
        "days": days_list,
        "active_user_counts": active_user_counts,
        "new_dish_counts": new_dish_counts,
        "totals": {
            "total_database_dishes": total_database_dishes,
            "total_published_meal_plans": total_published_meal_plans
        }
    }
