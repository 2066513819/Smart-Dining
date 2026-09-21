from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.services import db_service
from app.schemas.meal_plan import MealPlanCreate, MealPlanOut, DeliveryStatusUpdate
from app.models.meal_plan import MealPlan
from app.models.purchase_order import PurchaseOrder
from app.routers.auth import get_current_user
from datetime import datetime, date, timezone, timedelta
from fastapi import Depends
from app.services.db_service import get_db
import logging

logger = logging.getLogger(__name__)

# 中国时区（UTC+8）
CHINA_TZ = timezone(timedelta(hours=8))

router = APIRouter(tags=["meal_plans"])

def _json_safe(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _json_safe(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_json_safe(i) for i in v]
    return v


@router.post("/publish", response_model=MealPlanOut)
def publish_meal_plan(
    payload: MealPlanCreate,
    db: Session = Depends(db_service.get_db),
    current_user=Depends(get_current_user),
):
    try:
        meals_payload = [_json_safe(m.dict()) for m in payload.meals]
        
        # 计算总成本
        total_cost = 0.0
        if payload.total_cost is not None and payload.total_cost > 0:
            total_cost = payload.total_cost
        else:
            for m in payload.meals:
                # 累加每个菜品的成本
                # 注意：m.cost_price 是单份成本，需要乘以份数 m.servings
                price = getattr(m, 'cost_price', 0.0) or 0.0
                servings = getattr(m, 'servings', 1) or 1
                total_cost += float(price) * int(servings)
        
        # 处理餐食平均成本
        breakfast_avg_cost = getattr(payload, 'breakfast_avg_cost', 0.0) or 0.0
        lunch_avg_cost = getattr(payload, 'lunch_avg_cost', 0.0) or 0.0
        dinner_avg_cost = getattr(payload, 'dinner_avg_cost', 0.0) or 0.0
        
        mp = MealPlan(
            name=payload.name,
            date=payload.date,
            age_group=payload.age_group,
            meals=meals_payload,
            total_cost=total_cost,
            breakfast_avg_cost=breakfast_avg_cost,
            lunch_avg_cost=lunch_avg_cost,
            dinner_avg_cost=dinner_avg_cost,
            is_published=1,
            published_at=datetime.now(CHINA_TZ),
            user_id=current_user.id,
        )
        db.add(mp)
        db.commit()
        db.refresh(mp)
        
        # 处理发布时间的时区用于响应
        pub_at = mp.published_at
        if pub_at and pub_at.tzinfo is None:
            pub_at = pub_at.replace(tzinfo=CHINA_TZ)
            
        return {
            "id": mp.id,
            "name": mp.name,
            "date": mp.date,
            "age_group": mp.age_group,
            "is_published": mp.is_published,
            "delivery_status": mp.delivery_status or 0,
            # 直接返回 payload 计算结果，避免 JSON 列在某些方言下被当成字符串导致响应校验失败
            "meals": meals_payload,
            "total_cost": mp.total_cost,
            "breakfast_avg_cost": mp.breakfast_avg_cost,
            "lunch_avg_cost": mp.lunch_avg_cost,
            "dinner_avg_cost": mp.dinner_avg_cost,
            # response_model 期望 datetime；FastAPI 会序列化为 ISO 字符串
            "published_at": pub_at.replace(microsecond=0) if pub_at else None,
            "user_id": mp.user_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/published")
def list_published_meal_plans(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    name: Optional[str] = None,
    age_group: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回已发布的菜谱计划列表，支持筛选（普通用户仅限自己，管理员可见全部）"""
    try:
        query = db.query(MealPlan).filter(
            MealPlan.is_published == 1
        )
        
        # 非管理员只能看自己的
        if current_user.role != "admin":
            query = query.filter(MealPlan.user_id == current_user.id)
        
        if start_date:
            query = query.filter(MealPlan.date >= start_date)
        if end_date:
            query = query.filter(MealPlan.date <= end_date)
        if name:
            query = query.filter(MealPlan.name.ilike(f"%{name}%"))
        if age_group:
            query = query.filter(MealPlan.age_group == age_group)
            
        items = query.order_by(MealPlan.date.desc(), MealPlan.published_at.desc()).limit(200).all()
        
        out = []
        for p in items:
            # 处理发布时间的时区
            pub_at = p.published_at
            if pub_at and pub_at.tzinfo is None:
                pub_at = pub_at.replace(tzinfo=CHINA_TZ)
            
            out.append({
                "id": p.id,
                "name": p.name,
                "date": str(p.date) if p.date else None,
                "age_group": p.age_group,
                "total_cost": p.total_cost,
                "breakfast_avg_cost": p.breakfast_avg_cost,
                "lunch_avg_cost": p.lunch_avg_cost,
                "dinner_avg_cost": p.dinner_avg_cost,
                "delivery_status": p.delivery_status or 0,
                "published_at": pub_at.replace(microsecond=0).isoformat() if pub_at else None,
                "user_id": p.user_id,
                "school_name": p.user.school_rel.name if p.user and p.user.school_rel else "未知学校",
                "meals": p.meals
            })
        return out
    except Exception as e:
        logger.exception("读取已发布菜谱失败: %s", e)
        raise HTTPException(status_code=500, detail="无法读取已发布菜谱")


@router.put("/{plan_id}/delivery-status")
def update_delivery_status(
    plan_id: int,
    payload: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新配送状态（仅限管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可更新配送状态")
    
    mp = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="菜谱计划不存在")
    
    status_val = payload.status
    if status_val not in (0, 1):
        raise HTTPException(status_code=400, detail="非法状态值")
    
    mp.delivery_status = status_val
    db.commit()
    return {"detail": "更新成功", "delivery_status": mp.delivery_status}


@router.delete("/{plan_id}")
def delete_meal_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除历史菜谱计划（仅管理员）。"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可删除")

    mp = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="菜谱计划不存在")

    # 如有关联采购单，先清理，避免数据残留
    db.query(PurchaseOrder).filter(PurchaseOrder.meal_plan_id == plan_id).delete(synchronize_session=False)
    db.delete(mp)
    db.commit()
    return {"detail": "删除成功", "id": plan_id}
