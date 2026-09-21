from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

from app.services.db_service import get_db
from app.config.guideline_nutrition_standards import get_nutrition_targets as fallback_targets

router = APIRouter(tags=["nutrition"])


def _normalize_age_group(code: str) -> str:
    s = (code or "").strip().lower()
    # 兼容写法
    m = {
        "primary": "primary_low",  # 若仅写primary，默认走小学低
        "primary_low": "primary_low",
        "primary-high": "primary_high",
        "primary_high": "primary_high",
        "junior_low": "primary_high",   # 向下兼容旧代码枚举
        "junior": "junior",
        "junior_high": "junior",
        "senior": "senior"
    }
    return m.get(s, s)


def _map_db_row_to_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    # row来源于视图vw_nutrition_meal_targets_simple
    out = {}
    def pick(key: str, alias: str):
        if row.get(key) is not None:
            out[alias] = float(row.get(key))
    pick("target_calories_kcal", "target_calories")
    pick("target_protein_g", "target_protein")
    pick("target_calcium_mg", "target_calcium")
    pick("target_iron_mg", "target_iron")
    pick("target_zinc_mg", "target_zinc")
    pick("target_vitamin_a_ug_rae", "target_vitamin_a")
    pick("target_vitamin_c_mg", "target_vitamin_c")
    pick("target_dietary_fiber_g", "target_dietary_fiber")
    # 三大营养素占比直接透传（按需使用）
    for k in ["fat_pct_min", "fat_pct_max", "sat_fat_pct_max", "carbs_pct_min", "carbs_pct_max"]:
        if row.get(k) is not None:
            out[k] = float(row.get(k))
    return out


@router.get("/nutrition/targets")
def nutrition_targets(age_group: str, meal: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    优先从 nutrition_guidelines_simple + nutrition_meal_ratios 读取该餐次目标值；
    若表/视图不存在或缺数据，则回退到内置 guideline_nutrition_standards.get_nutrition_targets。
    """
    ag = _normalize_age_group(age_group)
    m = (meal or "").strip().lower()
    if m not in ("breakfast", "lunch", "dinner"):
        raise HTTPException(status_code=400, detail="meal 必须为 breakfast/lunch/dinner")

    # 1) 优先查视图（若存在）
    try:
        q = text("""
            SELECT age_group_code, age_group_name, age_range, meal,
                   target_calories_kcal, target_protein_g,
                   fat_pct_min, fat_pct_max, sat_fat_pct_max,
                   carbs_pct_min, carbs_pct_max,
                   target_calcium_mg, target_iron_mg, target_zinc_mg,
                   target_vitamin_a_ug_rae, target_vitamin_c_mg, target_dietary_fiber_g
            FROM vw_nutrition_meal_targets_simple
            WHERE age_group_code = :ag AND meal = :meal
            LIMIT 1
        """)
        row = db.execute(q, {"ag": ag, "meal": m}).mappings().first()
        if row:
            payload = _map_db_row_to_payload(dict(row))
            # 若最关键值仍缺失，继续回退
            if payload.get("target_calories") is not None:
                return payload
    except Exception:
        # 视图不存在或查询失败，进入回退
        pass

    # 2) 回退到内置算法（代码中的基准+比例）
    try:
        res = fallback_targets(age_group, meal)
        # 规范化键名为当前接口风格
        out = {}
        mapping = {
            "target_calories": "target_calories",
            "target_protein": "target_protein",
            "target_fat": "target_fat",
            "target_carbohydrates": "target_carbohydrates",
            "target_calcium": "target_calcium",
            "target_iron": "target_iron",
            "target_vitamin_c": "target_vitamin_c"
        }
        for k, v in mapping.items():
            if res.get(k) is not None:
                out[v] = float(res[k])
        return out
    except Exception:
        raise HTTPException(status_code=500, detail="无法获取营养目标值（表与默认均不可用）")

