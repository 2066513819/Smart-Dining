from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.ingredient_nutrition import IngredientNutrition
from app.schemas.ingredient_nutrition import (
    IngredientNutritionCreate, 
    IngredientNutritionUpdate, 
    IngredientNutritionResponse, 
    IngredientNutritionBulkCreate
)
from sqlalchemy import and_, or_, func

router = APIRouter()

@router.get("/count")
def count_ingredient_nutritions(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取食材营养信息总数
    """
    query = db.query(IngredientNutrition)
    if name:
        query = query.filter(IngredientNutrition.name.like(f"%{name}%"))
    
    return {"total": query.count()}

@router.get("/", response_model=List[IngredientNutritionResponse])
def get_ingredient_nutritions(
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取食材营养信息列表，支持按名称搜索和分页
    """
    query = db.query(IngredientNutrition)
    
    if name:
        query = query.filter(IngredientNutrition.name.like(f"%{name}%"))
        
    # 分页
    items = query.offset(skip).limit(limit).all()
    
    # 彻底解决 ResponseValidationError：手动构建字典并确保没有 None 值
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "name": item.name,
            "dietary_fiber": float(item.dietary_fiber or 0.0),
            "carbohydrates": float(item.carbohydrates or 0.0),
            "vitamin_a": float(item.vitamin_a or 0.0),
            "vitamin_c": float(item.vitamin_c or 0.0),
            "energy_kj": float(item.energy_kj or 0.0),
            "fat": float(item.fat or 0.0),
            "protein": float(item.protein or 0.0),
            "calcium": float(item.calcium or 0.0),
            "iron": float(item.iron or 0.0),
            "zinc": float(item.zinc or 0.0),
            "fat_energy_ratio": float(item.fat_energy_ratio or 0.0),
            "carbohydrate_energy_ratio": float(item.carbohydrate_energy_ratio or 0.0),
            "created_at": item.created_at,
            "updated_at": item.updated_at
        })
                
    return result

@router.post("/", response_model=IngredientNutritionResponse)
def create_ingredient_nutrition(
    data: IngredientNutritionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建单个食材营养信息
    """
    existing = db.query(IngredientNutrition).filter(IngredientNutrition.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"食材 '{data.name}' 已存在"
        )
    
    # 处理 None 值
    item_dict = data.dict()
    for key, value in item_dict.items():
        if value is None and key != 'name':
            item_dict[key] = 0.0
            
    db_item = IngredientNutrition(
        **item_dict
    )
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
        
        # 确保返回的对象中数值不为 None
        for attr in [
            'dietary_fiber', 'carbohydrates', 'vitamin_a', 'vitamin_c', 
            'energy_kj', 'fat', 'protein', 'calcium', 'iron', 'zinc', 
            'fat_energy_ratio', 'carbohydrate_energy_ratio'
        ]:
            if getattr(db_item, attr) is None:
                setattr(db_item, attr, 0.0)
                
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )

@router.put("/{item_id}", response_model=IngredientNutritionResponse)
def update_ingredient_nutrition(
    item_id: int,
    data: IngredientNutritionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新食材营养信息
    """
    db_item = db.query(IngredientNutrition).filter(IngredientNutrition.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="未找到该食材记录")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is None and key != 'name':
            setattr(db_item, key, 0.0)
        else:
            setattr(db_item, key, value)
    
    try:
        db.commit()
        db.refresh(db_item)
        
        # 同样确保返回的对象中数值不为 None
        for attr in [
            'dietary_fiber', 'carbohydrates', 'vitamin_a', 'vitamin_c', 
            'energy_kj', 'fat', 'protein', 'calcium', 'iron', 'zinc', 
            'fat_energy_ratio', 'carbohydrate_energy_ratio'
        ]:
            if getattr(db_item, attr) is None:
                setattr(db_item, attr, 0.0)
        
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{item_id}")
def delete_ingredient_nutrition(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除食材营养信息
    """
    db_item = db.query(IngredientNutrition).filter(IngredientNutrition.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="未找到该食材记录")
    
    try:
        db.delete(db_item)
        db.commit()
        return {"message": "删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/bulk-save")
def bulk_save_ingredient_nutrition(
    data: IngredientNutritionBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量保存食材营养信息（存在则更新，不存在则创建）
    """
    results = []
    # 使用字典处理批次内的重复项
    unique_items = {}
    for item in data.items:
        # 在去重阶段就进行 strip 处理
        clean_name = item.name.strip()
        unique_items[clean_name] = item

    for name, item in unique_items.items():
        # 这里 name 已经是经过 strip 处理的 clean_name
        # 使用 func.trim 确保能匹配到数据库中带空格的记录
        db_item = db.query(IngredientNutrition).filter(
            func.trim(IngredientNutrition.name) == name
        ).first()
        
        # 将 Pydantic 模型转换为字典，并处理 None 值
        item_dict = item.dict()
        for key, value in item_dict.items():
            if value is None:
                item_dict[key] = 0.0
        
        if db_item:
            # 更新现有记录，同时修正名称
            for key, value in item_dict.items():
                setattr(db_item, key, value)
            db_item.name = name
        else:
            # 创建新记录
            db_item = IngredientNutrition(
                **item_dict
            )
            db.add(db_item)
        results.append(db_item)
    
    try:
        db.commit()
        return {"message": f"成功处理 {len(results)} 条记录"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量保存失败: {str(e)}")
