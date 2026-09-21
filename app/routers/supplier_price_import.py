"""
供应商价格表导入 API
用于从前端上传 Excel 文件并导入到数据库
"""

from io import BytesIO
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
import re
import json
import math

from app.services.db_service import get_db
from app.routers.auth import get_current_user
from app.models.user import User

# 尝试导入 pandas，如果失败则提供备用方案
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# 尝试导入 openpyxl
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter(tags=["供应商价格导入"])


def json_safe_float(value: Any, default: float = 0.0) -> float:
    """
    将值转换为 JSON 安全的浮点数
    处理 NaN, inf, -inf 等非 JSON 兼容值
    """
    if value is None:
        return default
    try:
        f = float(value)
        # 检查是否为 NaN, inf, -inf
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def clean_for_json(obj: Any) -> Any:
    """
    递归清理对象中的非 JSON 兼容值
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, float):
        return json_safe_float(obj)
    else:
        return obj


# 列名映射配置（支持多种可能的列名）
COLUMN_MAPPINGS = {
    'l1_category': [
        '一级分类', '大分类', '主分类', '分类', 'l1', '一级', '大类',
        'category', 'category_l1', '一级类目', '类目', '类型', '品类',
        '商品分类', '产品分类', '货物分类'
    ],
    'l2_category': [
        '二级分类', '小分类', '子分类', 'l2', '二级', '小类',
        'sub_category', 'category_l2', '二级类目', '子类', '明细',
        '子品类', '细分分类'
    ],
    'ingredient_name': [
        '食材名称', '品名', '商品名称', '名称', '食材', '商品', '产品名称',
        'name', 'ingredient', 'product', 'item', '物料名称', '物料',
        '食材品名', '货品名称', '货品', '商品名', '产品名', '物料品名',
        '货物名称', '货名', '物资名称'
    ],
    'unit': [
        '基本单位', '单位', '计量单位', '规格', 'unit', 'units', '计价单位',
        '包装规格', '计量', '计数单位', '计量方式', '包装单位'
    ],
    'price': [
        '入库单价', '价格', '单价', '金额', 'price', '单价(元)', '金额(元)',
        '价格(元)', '成本', '成本价', '进货价', '采购价', '入库价',
        '元', '参考价', '市场价', '批发价', '供应价'
    ],
    'remark': [
        '商品备注', '备注', '说明', '描述', 'remark', 'notes', 'note',
        '规格说明', '品牌', '产地', '供应商', '规格', '型号'
    ]
}


def read_excel_all_sheets(contents: bytes, filename: str):
    """
    读取 Excel 文件的所有 sheet 并合并为一个 DataFrame
    支持蛋、调料、豆制品、饮料等多 sheet 表格
    返回 (df, sheet_names)
    """
    if filename.endswith('.csv'):
        raise ValueError("read_excel_all_sheets 仅支持 .xlsx/.xls 格式")
    if filename.endswith('.xlsx'):
        all_sheets = pd.read_excel(BytesIO(contents), sheet_name=None, engine='openpyxl')
    else:
        all_sheets = pd.read_excel(BytesIO(contents), sheet_name=None)
    dfs = []
    sheet_names_used = []
    for sheet_name, df in all_sheets.items():
        if df is None or df.empty:
            continue
        if len(df.columns) < 2:  # 跳过几乎空的 sheet
            continue
        df = df.copy()
        df['_source_sheet'] = str(sheet_name)
        dfs.append(df)
        sheet_names_used.append(str(sheet_name))
    if not dfs:
        return pd.DataFrame(), []
    return pd.concat(dfs, ignore_index=True), sheet_names_used


def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """自动检测列名映射"""
    df_columns_lower = {str(col).lower().strip(): col for col in df.columns}
    detected = {}

    for field, possible_names in COLUMN_MAPPINGS.items():
        detected[field] = None
        for name in possible_names:
            name_lower = name.lower().strip()
            if name_lower in df_columns_lower:
                detected[field] = df_columns_lower[name_lower]
                break

    return detected


def normalize_unit(unit_str: str) -> str:
    """标准化单位"""
    if not unit_str:
        return '500g'

    unit_str = str(unit_str).lower().strip()

    unit_map = {
        '斤': '500g',
        '500克': '500g',
        '500g': '500g',
        'kg': '1000g',
        '千克': '1000g',
        '公斤': '1000g',
        '克': 'g',
        'g': 'g',
        '个': '个',
        '只': '只',
        '根': '根',
        '把': '把',
        '袋': '袋',
        '包': '包',
        '瓶': '瓶',
        '盒': '盒',
        '箱': '箱',
        '升': 'L',
        'l': 'L',
        'ml': 'ml',
        '毫升': 'ml',
    }

    for key, value in unit_map.items():
        if key in unit_str:
            return value

    # 如果包含数字，尝试提取
    match = re.search(r'(\d+)\s*(g|克|kg|千克|斤|个|只)', unit_str)
    if match:
        num = match.group(1)
        unit = match.group(2)
        if unit in ['g', '克']:
            return f'{num}g'
        elif unit in ['kg', '千克']:
            return '1000g'
        elif unit == '斤':
            return '500g'

    return unit_str


def parse_excel_row(row: pd.Series, columns: Dict[str, Optional[str]]) -> Optional[Dict]:
    """解析 Excel 行数据"""
    l1_col = columns.get('l1_category')
    name_col = columns.get('ingredient_name')

    if not l1_col or not name_col:
        return None

    l1_name = row.get(l1_col)
    ingredient_name = row.get(name_col)

    if pd.isna(l1_name) or not str(l1_name).strip():
        return None
    if pd.isna(ingredient_name) or not str(ingredient_name).strip():
        return None

    l2_col = columns.get('l2_category')
    l2_name = row.get(l2_col) if l2_col else None

    unit_col = columns.get('unit')
    unit = '500g'
    if unit_col:
        unit_val = row.get(unit_col)
        if not pd.isna(unit_val):
            unit = normalize_unit(str(unit_val))

    price_col = columns.get('price')
    price = 0.0
    if price_col:
        price_val = row.get(price_col)
        if not pd.isna(price_val):
            try:
                price = float(price_val)
            except (ValueError, TypeError):
                pass

    remark_col = columns.get('remark')
    remark = ''
    if remark_col:
        remark_val = row.get(remark_col)
        if not pd.isna(remark_val):
            remark = str(remark_val).strip()

    return {
        'l1_name': str(l1_name).strip(),
        'l2_name': str(l2_name).strip() if l2_name and not pd.isna(l2_name) else None,
        'ingredient_name': str(ingredient_name).strip(),
        'unit': unit,
        'price': price,
        'remark': remark
    }


def get_or_create_l1(name: str, db: Session) -> int:
    """获取或创建一级分类"""
    if not name:
        raise ValueError("一级分类名称不能为空")

    # 查询现有
    result = db.execute(
        text("SELECT code FROM l1_categories WHERE name = :name"),
        {"name": name}
    ).fetchone()

    if result:
        return result[0]

    # 创建新的
    max_code = db.execute(text("SELECT MAX(code) FROM l1_categories")).fetchone()[0] or 100
    code = max_code + 1

    db.execute(
        text("""
            INSERT INTO l1_categories (code, name, sort_no, remark)
            VALUES (:code, :name, 0, '从价格表导入')
        """),
        {"code": code, "name": name}
    )
    logger.info(f"创建一级分类: {name} (code: {code})")
    return code


def get_or_create_l2(l1_code: int, name: str, db: Session) -> int:
    """获取或创建二级分类"""
    if not name or not l1_code:
        raise ValueError("二级分类名称和一级分类编码不能为空")

    # 查询现有
    result = db.execute(
        text("SELECT code FROM l2_categories WHERE l1_code = :l1_code AND name = :name"),
        {"l1_code": l1_code, "name": name}
    ).fetchone()

    if result:
        return result[0]

    # 创建新的
    max_code = db.execute(
        text("SELECT MAX(code) FROM l2_categories WHERE l1_code = :l1_code"),
        {"l1_code": l1_code}
    ).fetchone()[0]

    if max_code:
        new_suffix = int(str(max_code)[-2:]) + 1
        if new_suffix > 99:
            new_suffix = 99
        code = int(f"{l1_code}{new_suffix:02d}")
    else:
        code = int(f"{l1_code}01")

    db.execute(
        text("""
            INSERT INTO l2_categories (code, l1_code, name, sort_no, remark)
            VALUES (:code, :l1_code, :name, 0, '从价格表导入')
        """),
        {"code": code, "l1_code": l1_code, "name": name}
    )
    logger.info(f"创建二级分类: {name} (code: {code}, l1: {l1_code})")
    return code


def upsert_ingredient_l1(data: Dict, l1_code: int, db: Session):
    """插入或更新 ingredient_l1_catalog"""
    existing = db.execute(
        text("SELECT id FROM ingredient_l1_catalog WHERE ingredient_name = :name AND l1_code = :code"),
        {"name": data['ingredient_name'], "code": l1_code}
    ).fetchone()

    if existing:
        db.execute(
            text("""
                UPDATE ingredient_l1_catalog
                SET unit = :unit, price = :price, remark = :remark, updated_at = NOW()
                WHERE id = :id
            """),
            {
                "unit": data['unit'],
                "price": data['price'],
                "remark": data['remark'],
                "id": existing[0]
            }
        )
    else:
        db.execute(
            text("""
                INSERT INTO ingredient_l1_catalog (ingredient_name, l1_code, unit, price, remark)
                VALUES (:name, :l1_code, :unit, :price, :remark)
            """),
            {
                "name": data['ingredient_name'],
                "l1_code": l1_code,
                "unit": data['unit'],
                "price": data['price'],
                "remark": data['remark']
            }
        )


def upsert_ingredient_l2(data: Dict, l1_code: int, l2_code: int, db: Session):
    """插入或更新 ingredient_l2_catalog"""
    existing = db.execute(
        text("SELECT id FROM ingredient_l2_catalog WHERE ingredient_name = :name AND l2_code = :code"),
        {"name": data['ingredient_name'], "code": l2_code}
    ).fetchone()

    if existing:
        db.execute(
            text("""
                UPDATE ingredient_l2_catalog
                SET unit = :unit, price = :price, remark = :remark, updated_at = NOW()
                WHERE id = :id
            """),
            {
                "unit": data['unit'],
                "price": data['price'],
                "remark": data['remark'],
                "id": existing[0]
            }
        )
    else:
        db.execute(
            text("""
                INSERT INTO ingredient_l2_catalog (ingredient_name, l1_code, l2_code, unit, price, remark)
                VALUES (:name, :l1_code, :l2_code, :unit, :price, :remark)
            """),
            {
                "name": data['ingredient_name'],
                "l1_code": l1_code,
                "l2_code": l2_code,
                "unit": data['unit'],
                "price": data['price'],
                "remark": data['remark']
            }
        )


@router.post("/import-supplier-prices")
async def import_supplier_prices(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导入供应商价格表
    接收 Excel 文件，提取食材成本数据并导入到数据库
    """
    # 检查 pandas 是否可用
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器缺少 pandas 库，请联系管理员安装: pip install pandas openpyxl"
        )

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 .xlsx, .xls, .csv 格式的文件"
        )

    stats = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'l1_created': 0,
        'l2_created': 0,
        'errors': []
    }

    try:
        # 读取文件内容
        contents = await file.read()

        # 根据文件类型读取
        if file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(BytesIO(contents), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(contents), encoding='gbk')
        else:
            # 检查 openpyxl 是否可用
            if not OPENPYXL_AVAILABLE and file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器缺少 openpyxl 库，请联系管理员安装: pip install openpyxl"
                )
            df, _ = read_excel_all_sheets(contents, file.filename)
            if df.empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Excel 文件中没有可读取的数据（所有 sheet 均为空）"
                )

        stats['total'] = len(df)

        # 检测列映射
        columns = detect_columns(df)

        # 记录实际检测到的列名，用于调试
        actual_columns = list(df.columns)
        logger.info(f"Excel实际列名: {actual_columns}")
        logger.info(f"列名映射结果: {columns}")

        # 验证必要列
        if not columns['l1_category']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到'一级分类'列。Excel中的列名: {actual_columns}。请确保包含以下任一名称：{', '.join(COLUMN_MAPPINGS['l1_category'][:5])}等"
            )
        if not columns['ingredient_name']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到'食材名称'列。Excel中的列名: {actual_columns}。请确保包含以下任一名称：{', '.join(COLUMN_MAPPINGS['ingredient_name'][:5])}等"
            )

        # 处理每一行
        processed_l1 = set()  # 用于跟踪已处理的一级分类
        processed_l2 = set()  # 用于跟踪已处理的二级分类

        for idx, row in df.iterrows():
            try:
                data = parse_excel_row(row, columns)
                if not data:
                    stats['skipped'] += 1
                    continue

                # 获取或创建一级分类
                l1_code = get_or_create_l1(data['l1_name'], db)
                # 只计数新创建的分类
                if l1_code not in processed_l1:
                    # 检查是否为新创建的（通过查询确认）
                    existing = db.execute(
                        text("SELECT 1 FROM l1_categories WHERE name = :name AND remark = '从价格表导入'"),
                        {"name": data['l1_name']}
                    ).fetchone()
                    if existing:
                        stats['l1_created'] += 1
                        processed_l1.add(l1_code)

                # 获取或创建二级分类
                l2_code = None
                if data['l2_name']:
                    try:
                        l2_code = get_or_create_l2(l1_code, data['l2_name'], db)
                        l2_key = (l1_code, data['l2_name'])
                        if l2_key not in processed_l2:
                            existing = db.execute(
                                text("SELECT 1 FROM l2_categories WHERE l1_code = :l1_code AND name = :name AND remark = '从价格表导入'"),
                                {"l1_code": l1_code, "name": data['l2_name']}
                            ).fetchone()
                            if existing:
                                stats['l2_created'] += 1
                                processed_l2.add(l2_key)
                    except Exception as e:
                        logger.warning(f"创建二级分类失败: {e}")

                # 插入或更新数据
                upsert_ingredient_l1(data, l1_code, db)
                if l2_code:
                    upsert_ingredient_l2(data, l1_code, l2_code, db)

                stats['success'] += 1

            except Exception as e:
                error_msg = f"第 {idx + 1} 行处理失败: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
                continue

        # 提交事务
        db.commit()

        # 清理返回数据中的非 JSON 兼容值
        response_data = {
            "success": True,
            "message": f"导入完成：成功 {stats['success']} 条，跳过 {stats['skipped']} 条",
            "stats": clean_for_json(stats),
            "columns_detected": {k: v for k, v in columns.items() if v}
        }

        return response_data

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"导入失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post("/preview-supplier-prices")
async def preview_supplier_prices(
    file: UploadFile = File(...),
    rows: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    预览供应商价格表
    返回 Excel 文件的前几行数据和列名映射检测结果
    """
    # 检查 pandas 是否可用
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器缺少 pandas 库，请联系管理员安装: pip install pandas openpyxl"
        )

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 .xlsx, .xls, .csv 格式的文件"
        )

    try:
        contents = await file.read()
        sheet_names: List[str] = []

        if file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(BytesIO(contents), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(contents), encoding='gbk')
        else:
            # 检查 openpyxl 是否可用
            if not OPENPYXL_AVAILABLE and file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器缺少 openpyxl 库，请联系管理员安装: pip install openpyxl"
                )
            df, sheet_names = read_excel_all_sheets(contents, file.filename)
            if df.empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Excel 文件中没有可读取的数据（所有 sheet 均为空）"
                )

        # 检测列映射
        columns = detect_columns(df)

        # 返回预览数据（含已加载的 sheet 列表）
        preview_data = []
        for idx in range(min(rows, len(df))):
            row = df.iloc[idx]
            parsed = parse_excel_row(row, columns)
            # 清理 raw 数据中的 NaN/inf
            raw_dict = row.to_dict()
            cleaned_raw = {}
            for k, v in raw_dict.items():
                if pd.isna(v):
                    cleaned_raw[k] = None
                elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    cleaned_raw[k] = None
                else:
                    cleaned_raw[k] = v

            preview_data.append({
                'row': idx + 1,
                'raw': cleaned_raw,
                'parsed': parsed
            })

        # 清理返回数据
        cols = [c for c in df.columns if c != '_source_sheet']
        response = {
            "filename": file.filename,
            "total_rows": int(len(df)),
            "sheets_loaded": sheet_names,
            "columns": cols,
            "columns_detected": columns,
            "preview": clean_for_json(preview_data),
            "required_columns_found": {
                'l1_category': columns['l1_category'] is not None,
                'ingredient_name': columns['ingredient_name'] is not None
            }
        }

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览失败: {str(e)}"
        )
