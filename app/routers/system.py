from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.system_setting import SystemSetting
from app.config.guideline_meal_rules import get_default_meal_rules, get_guideline_meal_rules

router = APIRouter()

ALLOWED_CATEGORIES = [
    "荤菜类",
    "主食类",
    "素菜类",
    "豆制品类",
    "奶及奶制品类",
    "水果类",
    "饮料类",
    "调味品",
    "蛋类或豆制品类",  # 早餐常用
    "蔬菜水果类",      # 早餐常用
    "汤类",            # 午晚餐常用
]

# 使用《学生餐营养指南》标准的默认配餐规则
DEFAULT_MEAL_RULES: Dict[str, Dict[str, int]] = get_default_meal_rules()


class MealRulesPayload(BaseModel):
    breakfast: Dict[str, int] = {}
    lunch: Dict[str, int] = {}
    dinner: Dict[str, int] = {}
    costs: Dict[str, float] = {"breakfast": 0.0, "lunch": 0.0, "dinner": 0.0}
    num_people: Dict[str, int] = {"breakfast": 1, "lunch": 1, "dinner": 1}
    dining_style: str = "盘餐"  # "团餐" 或 "盘餐"


def _validate_rules(rules: Dict[str, Any]):
    # 验证配餐数量规则
    for meal_key in ("breakfast", "lunch", "dinner"):
        raw = rules.get(meal_key) or {}
        if not isinstance(raw, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{meal_key} 必须是对象")
        for cat, cnt in raw.items():
            if cat not in ALLOWED_CATEGORIES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的类别: {cat}")
            if not isinstance(cnt, int):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{meal_key}.{cat} 必须是整数")
            if cnt < 0 or cnt > 20:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{meal_key}.{cat} 数字范围 0-20")
    
    # 验证配餐成本规则
    costs = rules.get("costs") or {}
    if not isinstance(costs, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="costs 必须是对象")
    for meal_key in ("breakfast", "lunch", "dinner"):
        cost = costs.get(meal_key, 0.0)
        if not isinstance(cost, (int, float)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"costs.{meal_key} 必须是数字")
        if cost < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"costs.{meal_key} 不能为负数")

    # 验证就餐人数规则
    num_people = rules.get("num_people") or {}
    if not isinstance(num_people, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="num_people 必须是对象")
    for meal_key in ("breakfast", "lunch", "dinner"):
        cnt = num_people.get(meal_key, 1)
        if not isinstance(cnt, int):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"num_people.{meal_key} 必须是整数")
        if cnt < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"num_people.{meal_key} 至少为 1")
    
    # 验证餐饮形式
    dining_style = rules.get("dining_style")
    if dining_style not in ("团餐", "盘餐"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的餐饮形式")


@router.get("/meal-rules")
def get_meal_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(SystemSetting).filter(SystemSetting.key == "meal_rules").first()
    
    # 默认成本与人数
    default_costs = {"breakfast": 10.0, "lunch": 20.0, "dinner": 20.0}
    default_num_people = {"breakfast": 1, "lunch": 1, "dinner": 1}
    
    if not item or not item.value:
        res = DEFAULT_MEAL_RULES.copy()
        res["costs"] = default_costs
        res["num_people"] = default_num_people
        return res
        
    try:
        data = json.loads(item.value)
    except Exception:
        res = DEFAULT_MEAL_RULES.copy()
        res["costs"] = default_costs
        res["num_people"] = default_num_people
        return res
        
    merged = {
        "breakfast": data.get("breakfast") if isinstance(data, dict) else {},
        "lunch": data.get("lunch") if isinstance(data, dict) else {},
        "dinner": data.get("dinner") if isinstance(data, dict) else {},
        "costs": data.get("costs") if isinstance(data, dict) and "costs" in data else default_costs,
        "num_people": data.get("num_people") if isinstance(data, dict) and "num_people" in data else default_num_people,
        "dining_style": data.get("dining_style") if isinstance(data, dict) and "dining_style" in data else "盘餐"
    }
    return merged


@router.put("/meal-rules")
def save_meal_rules(
    payload: MealRulesPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 普通用户与管理员均可配置早中晚餐饮设置（用于菜谱制定时的配餐规则）
    rules = payload.model_dump()
    _validate_rules(rules)
    raw = json.dumps(rules, ensure_ascii=False)
    item = db.query(SystemSetting).filter(SystemSetting.key == "meal_rules").first()
    if not item:
        item = SystemSetting(key="meal_rules", value=raw)
        db.add(item)
    else:
        item.value = raw
    db.commit()
    return {"detail": "保存成功"}


@router.get("/roles")
def list_roles(page: int = 1, page_size: int = 10, keyword: Optional[str] = None):
    # 返回空的分页结构，前端能正常渲染空表格
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/roles/{role_id}")
def get_role(role_id: int):
    raise HTTPException(status_code=404, detail="角色不存在")


@router.post("/roles")
def create_role(payload: dict):
    # 简单占位实现，返回模拟的角色数据（ID 可替换为真实实现）
    return {"id": 1, "name": payload.get("name"), "description": payload.get("description"), "permissions": payload.get("permissions", "")}


@router.put("/roles/{role_id}")
def update_role(role_id: int, payload: dict):
    return {"id": role_id, "name": payload.get("name"), "description": payload.get("description"), "permissions": payload.get("permissions", "")}


@router.delete("/roles/{role_id}")
def delete_role(role_id: int):
    return {"detail": "删除成功"}


@router.get("/permissions/tree")
def permissions_tree(role_id: Optional[int] = None):
    # 返回空权限树，前端会显示无权限项
    return {"permissions": []}


@router.post("/roles/{role_id}/permissions")
def save_role_permissions(role_id: int, permissions: dict):
    return {"detail": "权限保存成功"}
