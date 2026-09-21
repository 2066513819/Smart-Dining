from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.ingredient_price import IngredientPrice
from app.models.ingredient_price_alias import IngredientPriceAlias
from app.schemas.dish import IngredientPriceBulkCreate, IngredientPriceResponse, IngredientPriceCreate
from sqlalchemy import func, text
from pydantic import BaseModel

router = APIRouter()


def _unit_to_grams_factor(unit: str) -> float:
    """1 个该单位约等于多少克，用于换算每克价"""
    u = (unit or "").strip().lower()
    # 常见价格单位写法兼容：如 "元/千克"、"每公斤"、"kg/件"
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
    if u in ("两",):
        return 50.0
    if u in ("mg", "毫克"):
        return 0.001
    if u in ("个", "只", "枚"):
        return 50.0
    if u in ("颗",):
        return 30.0
    if u in ("瓶",):
        return 500.0
    if u in ("盒",):
        return 250.0
    if u in ("袋", "包"):
        return 100.0
    if u in ("根",):
        return 50.0
    if u in ("片",):
        return 10.0
    if u in ("块",):
        return 30.0
    if u in ("勺",):
        return 10.0
    if u in ("瓣",):
        return 5.0
    if u in ("ml", "毫升"):
        return 1.0
    if u in ("l", "升"):
        return 1000.0
    if u in ("箱",):
        return 10000.0
    return 1.0


def _aliases_for_price_ids(db: Session, price_ids: List[int]) -> dict:
    """批量查询 price_id -> [alias_name]"""
    if not price_ids:
        return {}
    rows = db.query(IngredientPriceAlias).filter(
        IngredientPriceAlias.ingredient_price_id.in_(price_ids)
    ).all()
    out = {}
    for pid in price_ids:
        out[pid] = []
    for r in rows:
        out.setdefault(r.ingredient_price_id, []).append(r.alias_name.strip())
    return out


def _price_to_response(db: Session, item: IngredientPrice) -> IngredientPriceResponse:
    aliases = _aliases_for_price_ids(db, [item.id]).get(item.id, [])
    return IngredientPriceResponse(
        id=item.id,
        name=item.name,
        price=float(item.price),
        unit=item.unit or "g",
        created_at=item.created_at,
        updated_at=item.updated_at,
        aliases=aliases,
    )

@router.post("/bulk-save", response_model=List[IngredientPriceResponse])
def bulk_save_prices(
    data: IngredientPriceBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量保存或更新食材价格（公共数据，所有用户共享）
    """
    results = []
    unique_prices = {}
    for item in data.prices:
        clean_name = item.name.strip()
        unique_prices[clean_name] = item

    for name, item in unique_prices.items():
        # 按名称匹配，不按用户过滤（食材成本为公共数据）
        existing = db.query(IngredientPrice).filter(
            func.trim(IngredientPrice.name) == name
        ).first()

        if existing:
            existing.name = name
            existing.price = item.price
            existing.unit = item.unit
            db_item = existing
        else:
            db_item = IngredientPrice(
                name=name,
                price=item.price,
                unit=item.unit
            )
            db.add(db_item)
        
        results.append(db_item)
    
    try:
        db.commit()
        for item in results:
            db.refresh(item)
        return [_price_to_response(db, item) for item in results]
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存食材价格失败: {str(e)}"
        )

@router.get("/count")
def count_my_prices(
    name: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取食材价格总数（公共数据，所有用户看到相同列表）
    """
    query = db.query(IngredientPrice)
    if name:
        query = query.filter(IngredientPrice.name.like(f"%{name}%"))
    return {"total": query.count()}

@router.get("/my-prices", response_model=List[IngredientPriceResponse])
def get_my_prices(
    name: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取食材价格列表，支持分页和搜索（公共数据）。每条含 aliases，配方中写别名也会匹配到该价格。
    """
    query = db.query(IngredientPrice)
    if name:
        query = query.filter(IngredientPrice.name.like(f"%{name}%"))
    items = query.offset(skip).limit(limit).all()
    return [_price_to_response(db, item) for item in items]


@router.get("/effective-price-map")
def get_effective_price_map(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取“有效价格”映射（每克）：
    - 优先使用供应商价格（ingredient_l2_catalog + ingredient_l1_catalog）
    - 供应商缺失时，回退到参考价格（ingredient_prices）
    """
    # 1) 供应商价格（优先）
    l2_rows = db.execute(text("""
        SELECT ingredient_name, price, unit
        FROM ingredient_l2_catalog
        WHERE price IS NOT NULL AND price > 0
    """)).fetchall()
    l1_rows = db.execute(text("""
        SELECT i.ingredient_name, i.price, i.unit
        FROM ingredient_l1_catalog i
        WHERE i.price IS NOT NULL AND i.price > 0
          AND NOT EXISTS (
            SELECT 1 FROM ingredient_l2_catalog i2
            WHERE i2.ingredient_name = i.ingredient_name
          )
    """)).fetchall()

    supplier_map: Dict[str, float] = {}
    for row in list(l2_rows) + list(l1_rows):
        name = (row[0] or "").strip()
        if not name:
            continue
        price = float(row[1] or 0)
        factor = _unit_to_grams_factor(row[2] or "g")
        per_gram = price / factor if factor > 0 else price
        supplier_map[name] = per_gram

    # 2) 参考价格（兜底），含别名（配方里名称与价格表不一致时可命中）
    ref_items = db.query(IngredientPrice).all()
    ref_map: Dict[str, float] = {}
    id_to_per_gram: Dict[int, float] = {}
    for item in ref_items:
        name = (item.name or "").strip()
        if not name:
            continue
        price = float(item.price or 0)
        if price <= 0:
            continue
        factor = _unit_to_grams_factor(item.unit or "g")
        per_gram = price / factor if factor > 0 else price
        ref_map[name] = per_gram
        id_to_per_gram[item.id] = per_gram

    if id_to_per_gram:
        alias_rows = db.query(IngredientPriceAlias).filter(
            IngredientPriceAlias.ingredient_price_id.in_(list(id_to_per_gram.keys()))
        ).all()
        for a in alias_rows:
            an = (a.alias_name or "").strip()
            if an and a.ingredient_price_id in id_to_per_gram:
                ref_map[an] = id_to_per_gram[a.ingredient_price_id]

    # 3) 合并：供应商优先，参考兜底
    effective = dict(ref_map)
    effective.update(supplier_map)

    return {
        "count": len(effective),
        "supplier_count": len(supplier_map),
        "reference_count": len(ref_map),
        "prices": effective
    }

@router.post("/", response_model=IngredientPriceResponse)
def create_price(
    data: IngredientPriceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建单个食材价格（公共数据，所有用户共享）
    """
    existing = db.query(IngredientPrice).filter(IngredientPrice.name == data.name.strip()).first()

    if existing:
        existing.price = data.price
        existing.unit = data.unit
        db_item = existing
    else:
        db_item = IngredientPrice(
            name=data.name.strip(),
            price=data.price,
            unit=data.unit
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_item)
    return _price_to_response(db, db_item)

@router.put("/{price_id}", response_model=IngredientPriceResponse)
def update_price(
    price_id: int,
    data: IngredientPriceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新食材价格（公共数据，任意登录用户可修改）
    """
    db_item = db.query(IngredientPrice).filter(IngredientPrice.id == price_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="价格记录未找到")

    db_item.name = data.name.strip()
    db_item.price = data.price
    db_item.unit = data.unit
    
    db.commit()
    db.refresh(db_item)
    return _price_to_response(db, db_item)

@router.delete("/{price_id}")
def delete_price(
    price_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除食材价格（公共数据，任意登录用户可删除）
    """
    db_item = db.query(IngredientPrice).filter(IngredientPrice.id == price_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="价格记录未找到")

    db.delete(db_item)
    db.commit()
    return {"message": "删除成功"}


class AliasCreate(BaseModel):
    alias_name: str


@router.post("/{price_id}/aliases", status_code=status.HTTP_201_CREATED)
def add_alias(
    price_id: int,
    data: AliasCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为某条食材价格添加别名，配方中出现该别名时按本条价格计算成本"""
    price_row = db.query(IngredientPrice).filter(IngredientPrice.id == price_id).first()
    if not price_row:
        raise HTTPException(status_code=404, detail="价格记录未找到")
    alias_name = (data.alias_name or "").strip()
    if not alias_name:
        raise HTTPException(status_code=400, detail="别名不能为空")
    existing = db.query(IngredientPriceAlias).filter(
        IngredientPriceAlias.ingredient_price_id == price_id,
        IngredientPriceAlias.alias_name == alias_name
    ).first()
    if existing:
        return {"message": "该别名已存在", "id": existing.id}
    alias_row = IngredientPriceAlias(ingredient_price_id=price_id, alias_name=alias_name)
    db.add(alias_row)
    db.commit()
    db.refresh(alias_row)
    return {"message": "别名已添加", "id": alias_row.id}


@router.delete("/{price_id}/aliases/{alias_name:path}")
def delete_alias(
    price_id: int,
    alias_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除某条食材价格的别名"""
    alias_row = db.query(IngredientPriceAlias).filter(
        IngredientPriceAlias.ingredient_price_id == price_id,
        IngredientPriceAlias.alias_name == alias_name
    ).first()
    if not alias_row:
        raise HTTPException(status_code=404, detail="别名未找到")
    db.delete(alias_row)
    db.commit()
    return {"message": "已删除"}
