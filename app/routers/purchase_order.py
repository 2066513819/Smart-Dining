from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from io import StringIO
import csv
from datetime import datetime, date

from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.models import User, MealPlan
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.ingredient_price import IngredientPrice
from app.models.ingredient_price_alias import IngredientPriceAlias

router = APIRouter(tags=["purchase_orders"])


def unit_to_grams_factor(unit: str) -> float:
    u = (unit or "").strip().lower()
    # 常见写法兼容：元/千克、每公斤、kg/件 等
    if any(k in u for k in ("kg", "千克", "公斤")):
        return 1000.0
    if any(k in u for k in ("500g", "斤")):
        return 500.0
    if any(k in u for k in ("g", "克")):
        return 1.0
    if any(k in u for k in ("mg", "毫克")):
        return 0.001
    if any(k in u for k in ("ml", "毫升")):
        return 1.0
    if any(k in u for k in ("l", "升")):
        return 1000.0
    if u in ("g", "克"):
        return 1.0
    if u in ("500g", "斤"):
        return 500.0
    if u in ("kg", "千克", "公斤"):
        return 1000.0
    if u in ("两", ):
        return 50.0
    if u in ("mg", "毫克"):
        return 0.001
    if u in ("ml", "毫升"):
        return 1.0
    if u in ("l", "升"):
        return 1000.0
    return 1.0


def get_per_gram_price(db: Session, name: str) -> float:
    nm = (name or "").strip()
    item = db.query(IngredientPrice)\
        .filter(IngredientPrice.name == nm)\
        .order_by(IngredientPrice.updated_at.desc())\
        .first()
    if not item and nm:
        alias = db.query(IngredientPriceAlias)\
            .filter(IngredientPriceAlias.alias_name == nm)\
            .first()
        if alias:
            item = db.query(IngredientPrice)\
                .filter(IngredientPrice.id == alias.ingredient_price_id)\
                .first()
    if not item:
        # 允许名称包含匹配
        item = db.query(IngredientPrice)\
            .filter(IngredientPrice.name.like(f"%{nm}%"))\
            .order_by(IngredientPrice.updated_at.desc())\
            .first()
    if not item:
        return 0.0
    try:
        factor = unit_to_grams_factor(item.unit or "g")
        price_per_gram = float(item.price) / factor if factor > 0 else float(item.price)
        return round(price_per_gram, 6)
    except Exception:
        return 0.0


@router.get("/purchase_orders/by-plan/{plan_id}")
def get_order_by_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    po = db.query(PurchaseOrder).filter(PurchaseOrder.meal_plan_id == plan_id).first()
    if not po:
        return {"exists": False}
    return {"exists": True, "order_id": int(po.id), "order_code": po.order_code}


@router.post("/purchase_orders/generate-from-plan")
def generate_from_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可生成采购单")
    mp: MealPlan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="菜谱计划不存在")

    # 若已生成，直接返回
    existing = db.query(PurchaseOrder).filter(PurchaseOrder.meal_plan_id == plan_id).first()
    if existing:
        return {"order_id": int(existing.id), "order_code": existing.order_code, "detail": "已存在采购单"}

    meals = mp.meals or []
    proc_row = None
    for it in meals:
        if isinstance(it, dict) and str(it.get("meal_type", "")).lower() == "__procurement__":
            proc_row = it
            break
    if not proc_row:
        raise HTTPException(status_code=400, detail="该计划中未找到配方采购表")

    rows: List[Dict[str, Any]] = proc_row.get("procurement_rows") or []
    rows = [r for r in rows if r and str(r.get("ingredient", "")).strip()]
    if not rows:
        raise HTTPException(status_code=400, detail="采购表为空")

    # 生成采购单
    po = PurchaseOrder(
        meal_plan_id=mp.id,
        school_name=None,
        plan_date=mp.date,
        status=0,
        remark=f"由菜谱计划[{mp.name}]自动生成"
    )
    db.add(po)
    db.flush()  # 先拿到ID
    po.order_code = f"PO{datetime.now().strftime('%Y%m%d')}-{po.id}"

    total_grams = 0.0
    total_amount = 0.0

    for r in rows:
        ing = str(r.get("ingredient", "")).strip()
        grams = float(r.get("total_grams", 0) or 0)
        if not ing or grams <= 0:
            continue
        per_gram = get_per_gram_price(db, ing)  # 每克价（公共价格表）
        amount = round(per_gram * grams, 2)
        item = PurchaseOrderItem(
            order_id=po.id,
            ingredient_name=ing,
            unit="g",
            price_per_unit=per_gram,
            total_grams=grams,
            amount=amount
        )
        db.add(item)
        total_grams += grams
        total_amount += amount

    po.total_grams = round(total_grams, 3)
    po.total_amount = round(total_amount, 2)

    db.commit()
    db.refresh(po)
    return {"order_id": int(po.id), "order_code": po.order_code, "total_amount": float(po.total_amount)}


@router.get("/purchase_orders/{order_id}/export-csv")
def export_order_csv(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可导出")
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="采购单不存在")
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.order_id == order_id).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["食材", "总克数(g)", "每克单价(¥)", "金额(¥)"])
    for it in items:
        writer.writerow([
            it.ingredient_name,
            float(it.total_grams),
            f"{float(it.price_per_unit):.4f}",
            f"{float(it.amount):.2f}"
        ])
    writer.writerow([])
    writer.writerow(["合计", float(po.total_grams), "", f"{float(po.total_amount):.2f}"])

    csv_data = output.getvalue().encode("utf-8-sig")
    filename = f"{po.order_code or ('PO-' + str(po.id))}.csv"
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=csv_data, headers=headers)

SETTINGS = {}

