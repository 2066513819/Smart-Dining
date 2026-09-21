"""
供应商价格表通用导入工具
用于提取 Excel 文件中的食材成本数据并导入到数据库
支持灵活的列名映射，适配不同格式的供应商表格
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import re

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.config import settings
except ImportError:
    # 如果无法导入配置，使用默认配置
    settings = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupplierPriceImporter:
    """供应商价格表导入器 - 通用版本"""

    # 列名映射配置（支持多种可能的列名）
    COLUMN_MAPPINGS = {
        'l1_category': [
            '一级分类', '大分类', '主分类', '分类', 'l1', '一级', '大类',
            'category', 'category_l1', '一级类目', '类目', '类型'
        ],
        'l2_category': [
            '二级分类', '小分类', '子分类', 'l2', '二级', '小类',
            'sub_category', 'category_l2', '二级类目', '子类', '明细'
        ],
        'ingredient_name': [
            '食材名称', '品名', '商品名称', '名称', '食材', '商品', '产品名称',
            'name', 'ingredient', 'product', 'item', '物料名称', '物料',
            '食材品名', '货品名称', '货品'
        ],
        'unit': [
            '单位', '计量单位', '规格', 'unit', 'units', '计价单位',
            '包装规格', '计量', '计数单位'
        ],
        'price': [
            '价格', '单价', '金额', 'price', '单价(元)', '金额(元)',
            '价格(元)', '成本', '成本价', '进货价', '采购价', '入库价'
        ],
        'remark': [
            '备注', '说明', '描述', 'remark', 'notes', 'note',
            '规格说明', '品牌', '产地', '供应商'
        ]
    }

    def __init__(self, excel_path: str, db_url: Optional[str] = None):
        """
        初始化导入器

        Args:
            excel_path: Excel 文件路径
            db_url: 数据库连接URL，如果不提供则使用 settings 中的配置
        """
        self.excel_path = Path(excel_path)
        self.df = None
        self.detected_columns = {}  # 检测到的列名映射
        self.l1_categories = {}  # 一级分类缓存 {name: code}
        self.l2_categories = {}  # 二级分类缓存 {(l1_code, name): code}
        self.stats = {
            'total_rows': 0,
            'success': 0,
            'skipped': 0,
            'l1_created': 0,
            'l2_created': 0,
            'errors': []
        }

        # 数据库连接
        if db_url:
            self.engine = create_engine(db_url, echo=False)
        elif settings:
            db_url = (
                f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
            self.engine = create_engine(db_url, echo=False)
        else:
            raise ValueError("请提供数据库连接URL或确保 settings 配置正确")

        self.Session = sessionmaker(bind=self.engine)

    def load_excel(self, sheet_name: Optional[str] = None) -> bool:
        """
        加载 Excel 文件

        Args:
            sheet_name: 指定 sheet 名称，如果不指定则加载第一个 sheet

        Returns:
            bool: 是否成功加载
        """
        try:
            # 获取所有 sheet
            xl = pd.ExcelFile(self.excel_path)
            available_sheets = xl.sheet_names
            logger.info(f"Excel 文件包含 {len(available_sheets)} 个 sheet: {available_sheets}")

            # 如果指定了 sheet_name，使用指定的；否则使用第一个
            if sheet_name and sheet_name in available_sheets:
                target_sheet = sheet_name
            else:
                target_sheet = available_sheets[0]
                if sheet_name:
                    logger.warning(f"指定的 sheet '{sheet_name}' 不存在，使用第一个 sheet '{target_sheet}'")

            self.df = pd.read_excel(self.excel_path, sheet_name=target_sheet)
            self.stats['total_rows'] = len(self.df)

            logger.info(f"成功加载 Excel 文件: {self.excel_path}")
            logger.info(f"工作表: {target_sheet}")
            logger.info(f"总行数: {len(self.df)}")
            logger.info(f"列名: {list(self.df.columns)}")

            # 自动检测列映射
            self._detect_columns()
            return True

        except Exception as e:
            logger.error(f"加载 Excel 文件失败: {e}")
            self.stats['errors'].append(f"加载失败: {e}")
            return False

    def _detect_columns(self) -> None:
        """自动检测列名映射"""
        df_columns_lower = {str(col).lower().strip(): col for col in self.df.columns}

        for field, possible_names in self.COLUMN_MAPPINGS.items():
            detected = None
            for name in possible_names:
                name_lower = name.lower().strip()
                if name_lower in df_columns_lower:
                    detected = df_columns_lower[name_lower]
                    break

            self.detected_columns[field] = detected

        logger.info("列名检测完成:")
        for field, col_name in self.detected_columns.items():
            status = f"✓ {col_name}" if col_name else "✗ 未找到"
            logger.info(f"  {field}: {status}")

    def get_l1_code_by_name(self, name: str, session) -> Optional[int]:
        """
        根据一级分类名称获取 code，如果不存在则自动分配新的 code

        Args:
            name: 一级分类名称
            session: 数据库会话

        Returns:
            int: 一级分类 code，如果名称无效返回 None
        """
        if not name or pd.isna(name):
            return None

        name = str(name).strip()
        if not name:
            return None

        # 先从缓存查找
        if name in self.l1_categories:
            return self.l1_categories[name]

        # 从数据库查询
        result = session.execute(
            text("SELECT code FROM l1_categories WHERE name = :name"),
            {"name": name}
        ).fetchone()

        if result:
            code = result[0]
        else:
            # 不存在，分配新的 code（从数据库获取最大值 + 1）
            max_code = session.execute(
                text("SELECT MAX(code) FROM l1_categories")
            ).fetchone()[0] or 100
            code = max_code + 1

            # 插入新的一级分类
            session.execute(
                text("""
                    INSERT INTO l1_categories (code, name, sort_no, remark)
                    VALUES (:code, :name, 0, '从价格表自动创建')
                """),
                {"code": code, "name": name}
            )
            self.stats['l1_created'] += 1
            logger.info(f"创建新的一级分类: {name} (code: {code})")

        # 缓存结果
        self.l1_categories[name] = code
        return code

    def get_l2_code_by_name(self, l1_code: int, name: str, session) -> Optional[int]:
        """
        根据二级分类名称和一级分类 code 获取二级分类 code，如果不存在则自动分配新的 code

        Args:
            l1_code: 一级分类 code
            name: 二级分类名称
            session: 数据库会话

        Returns:
            int: 二级分类 code，如果名称无效返回 None
        """
        if not name or pd.isna(name) or not l1_code:
            return None

        name = str(name).strip()
        if not name:
            return None

        key = (l1_code, name)

        # 先从缓存查找
        if key in self.l2_categories:
            return self.l2_categories[key]

        # 从数据库查询
        result = session.execute(
            text("""
                SELECT code FROM l2_categories
                WHERE l1_code = :l1_code AND name = :name
            """),
            {"l1_code": l1_code, "name": name}
        ).fetchone()

        if result:
            code = result[0]
        else:
            # 不存在，分配新的 code
            # 二级分类 code 规则：前3位 = l1_code，后2位自增
            max_code = session.execute(
                text("""
                    SELECT MAX(code) FROM l2_categories
                    WHERE l1_code = :l1_code
                """),
                {"l1_code": l1_code}
            ).fetchone()[0]

            if max_code:
                # 从最大值 + 1
                new_suffix = int(str(max_code)[-2:]) + 1
                if new_suffix > 99:
                    logger.warning(f"二级分类数量超过99个，需要调整编码规则")
                    new_suffix = 99
                code = int(f"{l1_code}{new_suffix:02d}")
            else:
                # 第一个二级分类
                code = int(f"{l1_code}01")

            # 插入新的二级分类
            session.execute(
                text("""
                    INSERT INTO l2_categories (code, l1_code, name, sort_no, remark)
                    VALUES (:code, :l1_code, :name, 0, '从价格表自动创建')
                """),
                {"code": code, "l1_code": l1_code, "name": name}
            )
            self.stats['l2_created'] += 1
            logger.info(f"创建新的二级分类: {name} (code: {code}, l1_code: {l1_code})")

        # 缓存结果
        self.l2_categories[key] = code
        return code

    def parse_row(self, row: pd.Series) -> Optional[Dict]:
        """
        解析 Excel 行数据

        Args:
            row: pandas Series 对象

        Returns:
            Dict: 解析后的数据，如果数据无效返回 None
        """
        # 检测必要字段
        l1_col = self.detected_columns.get('l1_category')
        name_col = self.detected_columns.get('ingredient_name')

        if not l1_col or not name_col:
            return None

        # 获取数据
        l1_name = row.get(l1_col)
        ingredient_name = row.get(name_col)

        # 验证必要字段
        if pd.isna(l1_name) or not str(l1_name).strip():
            return None
        if pd.isna(ingredient_name) or not str(ingredient_name).strip():
            return None

        # 获取二级分类（可选）
        l2_col = self.detected_columns.get('l2_category')
        l2_name = row.get(l2_col) if l2_col else None

        # 获取单位
        unit_col = self.detected_columns.get('unit')
        unit = '500g'  # 默认单位
        if unit_col:
            unit_val = row.get(unit_col)
            if not pd.isna(unit_val):
                unit = self._normalize_unit(str(unit_val))

        # 获取价格
        price_col = self.detected_columns.get('price')
        price = 0.0
        if price_col:
            price_val = row.get(price_col)
            if not pd.isna(price_val):
                try:
                    price = float(price_val)
                except (ValueError, TypeError):
                    pass

        # 获取备注
        remark_col = self.detected_columns.get('remark')
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

    def _normalize_unit(self, unit_str: str) -> str:
        """
        标准化单位

        Args:
            unit_str: 原始单位字符串

        Returns:
            str: 标准化后的单位
        """
        if not unit_str:
            return '500g'

        unit_str = str(unit_str).lower().strip()

        # 常见单位映射
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

    def import_to_database(self, batch_size: int = 100) -> Dict:
        """
        导入数据到数据库

        Args:
            batch_size: 每批提交的行数

        Returns:
            Dict: 导入统计信息
        """
        if self.df is None:
            logger.error("请先加载 Excel 文件")
            return self.stats

        session = self.Session()

        try:
            for idx, row in self.df.iterrows():
                try:
                    # 解析行数据
                    data = self.parse_row(row)

                    if not data:
                        self.stats['skipped'] += 1
                        continue

                    # 获取或创建一级分类
                    l1_code = self.get_l1_code_by_name(data['l1_name'], session)
                    if not l1_code:
                        self.stats['skipped'] += 1
                        continue

                    # 获取或创建二级分类
                    l2_code = None
                    if data['l2_name']:
                        l2_code = self.get_l2_code_by_name(l1_code, data['l2_name'], session)

                    # 插入或更新 ingredient_l1_catalog
                    self._upsert_ingredient_l1(session, data, l1_code)

                    # 如果有二级分类，插入或更新 ingredient_l2_catalog
                    if l2_code:
                        self._upsert_ingredient_l2(session, data, l1_code, l2_code)

                    self.stats['success'] += 1

                    # 每 batch_size 行提交一次
                    if (idx + 1) % batch_size == 0:
                        session.commit()
                        logger.info(f"已处理 {idx + 1}/{len(self.df)} 行，成功导入 {self.stats['success']} 条...")

                except Exception as e:
                    self.stats['errors'].append(f"第 {idx + 1} 行处理失败: {e}")
                    logger.error(f"处理第 {idx + 1} 行时出错: {e}")
                    continue

            # 最终提交
            session.commit()
            logger.info("=" * 80)
            logger.info("导入完成!")
            logger.info(f"总计: {self.stats['total_rows']} 行")
            logger.info(f"成功: {self.stats['success']} 条")
            logger.info(f"跳过: {self.stats['skipped']} 条")
            logger.info(f"创建一级分类: {self.stats['l1_created']} 个")
            logger.info(f"创建二级分类: {self.stats['l2_created']} 个")
            if self.stats['errors']:
                logger.warning(f"错误: {len(self.stats['errors'])} 个")
            logger.info("=" * 80)

        except Exception as e:
            session.rollback()
            logger.error(f"导入失败: {e}")
            self.stats['errors'].append(f"导入失败: {e}")
            raise
        finally:
            session.close()

        return self.stats

    def _upsert_ingredient_l1(self, session, data: Dict, l1_code: int):
        """插入或更新 ingredient_l1_catalog"""
        existing = session.execute(
            text("""
                SELECT id FROM ingredient_l1_catalog
                WHERE ingredient_name = :name AND l1_code = :code
            """),
            {"name": data['ingredient_name'], "code": l1_code}
        ).fetchone()

        if existing:
            session.execute(
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
            session.execute(
                text("""
                    INSERT INTO ingredient_l1_catalog
                    (ingredient_name, l1_code, unit, price, remark)
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

    def _upsert_ingredient_l2(self, session, data: Dict, l1_code: int, l2_code: int):
        """插入或更新 ingredient_l2_catalog"""
        existing = session.execute(
            text("""
                SELECT id FROM ingredient_l2_catalog
                WHERE ingredient_name = :name AND l2_code = :code
            """),
            {"name": data['ingredient_name'], "code": l2_code}
        ).fetchone()

        if existing:
            session.execute(
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
            session.execute(
                text("""
                    INSERT INTO ingredient_l2_catalog
                    (ingredient_name, l1_code, l2_code, unit, price, remark)
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

    def preview_data(self, rows: int = 10) -> None:
        """
        预览数据

        Args:
            rows: 预览行数
        """
        if self.df is None:
            logger.error("请先加载 Excel 文件")
            return

        print("\n" + "=" * 100)
        print(f"📊 文件预览: {self.excel_path.name}")
        print("=" * 100)
        print(f"总行数: {len(self.df)}")
        print(f"列名: {list(self.df.columns)}")

        print("\n📋 列名映射检测:")
        for field, col_name in self.detected_columns.items():
            status = f"✓ {col_name}" if col_name else "✗ 未检测到"
            print(f"  {field:20s} -> {status}")

        print(f"\n📄 前 {rows} 行原始数据:")
        print(self.df.head(rows).to_string())

        print(f"\n🔍 解析后数据示例:")
        for idx in range(min(rows, len(self.df))):
            row = self.df.iloc[idx]
            parsed = self.parse_row(row)
            if parsed:
                print(f"  行 {idx + 1}: {parsed}")
            else:
                print(f"  行 {idx + 1}: [跳过 - 数据不完整]")

        print("\n" + "=" * 100)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="供应商价格表导入工具 - 通用版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 预览数据（不导入）
  python import_supplier_price_table.py "26年1月商品入库价格表.xlsx" --preview

  # 导入数据
  python import_supplier_price_table.py "26年1月商品入库价格表.xlsx"

  # 指定工作表
  python import_supplier_price_table.py "价格表.xlsx" --sheet "Sheet2"

  # 自定义数据库连接
  python import_supplier_price_table.py "价格表.xlsx" --db-url "mysql+pymysql://user:pass@localhost/db"
        """
    )

    parser.add_argument("excel_file", help="Excel 文件路径")
    parser.add_argument("--sheet", "-s", help="指定工作表名称（默认第一个）")
    parser.add_argument("--preview", "-p", action="store_true", help="仅预览，不导入")
    parser.add_argument("--db-url", "-d", help="数据库连接URL（默认使用 settings 配置）")
    parser.add_argument("--batch-size", "-b", type=int, default=100, help="每批提交的行数（默认100）")

    args = parser.parse_args()

    # 创建导入器
    try:
        importer = SupplierPriceImporter(args.excel_file, db_url=args.db_url)
    except ValueError as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)

    # 加载 Excel
    if not importer.load_excel(sheet_name=args.sheet):
        sys.exit(1)

    # 预览模式
    if args.preview:
        importer.preview_data()
        return

    # 确认导入
    print("\n" + "=" * 100)
    print("即将导入数据到数据库，请确认:")
    print(f"  文件: {args.excel_file}")
    print(f"  总行数: {importer.stats['total_rows']}")
    print(f"  批次大小: {args.batch_size}")
    print("=" * 100)

    confirm = input("\n是否确认导入? (yes/no): ")
    if confirm.lower() not in ['yes', 'y', '是']:
        print("已取消导入")
        return

    # 执行导入
    stats = importer.import_to_database(batch_size=args.batch_size)

    # 输出结果
    print("\n" + "=" * 100)
    print("📊 导入统计:")
    print(f"  总计处理: {stats['total_rows']} 行")
    print(f"  成功导入: {stats['success']} 条")
    print(f"  跳过: {stats['skipped']} 条")
    print(f"  创建一级分类: {stats['l1_created']} 个")
    print(f"  创建二级分类: {stats['l2_created']} 个")

    if stats['errors']:
        print(f"\n⚠️  错误 ({len(stats['errors'])} 个):")
        for err in stats['errors'][:10]:  # 只显示前10个错误
            print(f"  - {err}")
        if len(stats['errors']) > 10:
            print(f"  ... 还有 {len(stats['errors']) - 10} 个错误")

    print("=" * 100)


if __name__ == "__main__":
    main()
