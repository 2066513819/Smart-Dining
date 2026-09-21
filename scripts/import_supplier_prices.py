"""
供应商价格表导入脚本
用于提取 Excel 文件中的食材成本数据并导入到 l1_categories 和 l2_categories 表
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupplierPriceImporter:
    """供应商价格表导入器"""

    def __init__(self, excel_path: str):
        """
        初始化导入器

        Args:
            excel_path: Excel 文件路径
        """
        self.excel_path = Path(excel_path)
        self.df = None
        self.l1_categories = {}  # 一级分类缓存 {name: code}
        self.l2_categories = {}  # 二级分类缓存 {(l1_code, name): code}

        # 数据库连接
        self.engine = create_engine(
            f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            echo=False
        )
        self.Session = sessionmaker(bind=self.engine)

    def load_excel(self) -> bool:
        """
        加载 Excel 文件

        Returns:
            bool: 是否成功加载
        """
        try:
            self.df = pd.read_excel(self.excel_path)
            logger.info(f"成功加载 Excel 文件: {self.excel_path}")
            logger.info(f"总行数: {len(self.df)}")
            logger.info(f"列名: {list(self.df.columns)}")
            return True
        except Exception as e:
            logger.error(f"加载 Excel 文件失败: {e}")
            return False

    def get_l1_code_by_name(self, name: str, session) -> int:
        """
        根据一级分类名称获取 code，如果不存在则自动分配新的 code

        Args:
            name: 一级分类名称
            session: 数据库会话

        Returns:
            int: 一级分类 code
        """
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
            ).fetchone()[0] or 0
            code = max_code + 1

            # 插入新的一级分类
            session.execute(
                text("""
                    INSERT INTO l1_categories (code, name, sort_no, remark)
                    VALUES (:code, :name, 0, '')
                """),
                {"code": code, "name": name}
            )
            logger.info(f"创建新的一级分类: {name} (code: {code})")

        # 缓存结果
        self.l1_categories[name] = code
        return code

    def get_l2_code_by_name(self, l1_code: int, name: str, session) -> int:
        """
        根据二级分类名称和一级分类 code 获取二级分类 code，如果不存在则自动分配新的 code

        Args:
            l1_code: 一级分类 code
            name: 二级分类名称
            session: 数据库会话

        Returns:
            int: 二级分类 code
        """
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
                code = int(f"{l1_code}{new_suffix:02d}")
            else:
                # 第一个二级分类
                code = int(f"{l1_code}01")

            # 插入新的二级分类
            session.execute(
                text("""
                    INSERT INTO l2_categories (code, l1_code, name, sort_no, remark)
                    VALUES (:code, :l1_code, :name, 0, '')
                """),
                {"code": code, "l1_code": l1_code, "name": name}
            )
            logger.info(f"创建新的二级分类: {name} (code: {code}, l1_code: {l1_code})")

        # 缓存结果
        self.l2_categories[key] = code
        return code

    def parse_excel_row(self, row: pd.Series) -> Dict:
        """
        解析 Excel 行数据

        根据实际 Excel 表格结构调整此方法
        当前假设的列结构（需根据实际表格调整）：
        - 一级分类: 对应 l1_categories.name
        - 二级分类: 对应 l2_categories.name
        - 食材名称: 食材名称
        - 单位: 单位（如 500g/斤/kg）
        - 价格: 单价

        Args:
            row: pandas Series 对象

        Returns:
            Dict: 解析后的数据
        """
        # TODO: 根据实际的 Excel 列名进行调整
        # 这里使用通用名称，请根据实际 Excel 文件修改

        data = {
            'l1_name': None,
            'l2_name': None,
            'ingredient_name': None,
            'unit': '500g',  # 默认单位
            'price': 0.0,
            'remark': ''
        }

        # 尝试识别列名（支持多种可能的列名）
        row_lower = {k.lower(): v for k, v in row.items()}

        # 一级分类
        for key in ['一级分类', '大分类', '分类', 'l1_category', 'category_l1']:
            if key in row_lower:
                data['l1_name'] = str(row_lower[key]).strip()
                break

        # 二级分类
        for key in ['二级分类', '小分类', 'sub_category', 'l2_category', 'category_l2']:
            if key in row_lower:
                data['l2_name'] = str(row_lower[key]).strip()
                break

        # 食材名称
        for key in ['食材名称', '品名', '商品名称', '名称', 'name', 'ingredient', 'product']:
            if key in row_lower:
                data['ingredient_name'] = str(row_lower[key]).strip()
                break

        # 单位
        for key in ['单位', 'unit']:
            if key in row_lower:
                data['unit'] = str(row_lower[key]).strip()
                break

        # 价格
        for key in ['价格', '单价', 'price', '金额']:
            if key in row_lower:
                try:
                    data['price'] = float(row_lower[key])
                except (ValueError, TypeError):
                    pass
                break

        # 备注
        for key in ['备注', 'remark', '说明']:
            if key in row_lower:
                data['remark'] = str(row_lower[key]).strip()
                break

        return data

    def import_to_database(self) -> Tuple[int, int]:
        """
        导入数据到数据库

        Returns:
            Tuple[int, int]: (成功导入的 l1 数量, 成功导入的 l2 数量)
        """
        if self.df is None:
            logger.error("请先加载 Excel 文件")
            return 0, 0

        session = self.Session()

        l1_count = 0
        l2_count = 0

        try:
            for idx, row in self.df.iterrows():
                # 跳过空行
                if row.isna().all():
                    continue

                data = self.parse_excel_row(row)

                # 验证必要字段
                if not data['l1_name'] or pd.isna(data['l1_name']):
                    continue

                if not data['ingredient_name'] or pd.isna(data['ingredient_name']):
                    continue

                # 处理一级分类
                l1_code = self.get_l1_code_by_name(data['l1_name'], session)

                # 如果有二级分类，处理二级分类
                l2_code = None
                if data['l2_name'] and not pd.isna(data['l2_name']):
                    l2_code = self.get_l2_code_by_name(l1_code, data['l2_name'], session)
                    l2_count += 1
                else:
                    l2_count += 1

                # 插入或更新 ingredient_l1_catalog
                # 检查是否已存在
                existing = session.execute(
                    text("""
                        SELECT id FROM ingredient_l1_catalog
                        WHERE ingredient_name = :name AND l1_code = :code
                    """),
                    {"name": data['ingredient_name'], "code": l1_code}
                ).fetchone()

                if existing:
                    # 更新
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
                    logger.debug(f"更新 ingredient_l1_catalog: {data['ingredient_name']}")
                else:
                    # 插入
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
                    logger.debug(f"插入 ingredient_l1_catalog: {data['ingredient_name']}")

                # 如果有二级分类，插入或更新 ingredient_l2_catalog
                if l2_code:
                    existing_l2 = session.execute(
                        text("""
                            SELECT id FROM ingredient_l2_catalog
                            WHERE ingredient_name = :name AND l2_code = :code
                        """),
                        {"name": data['ingredient_name'], "code": l2_code}
                    ).fetchone()

                    if existing_l2:
                        # 更新
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
                                "id": existing_l2[0]
                            }
                        )
                    else:
                        # 插入
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

                l1_count += 1

                # 每100行提交一次，避免大事务
                if (idx + 1) % 100 == 0:
                    session.commit()
                    logger.info(f"已处理 {idx + 1} 行...")

            session.commit()
            logger.info(f"导入完成！l1_categories: {l1_count}, l2_categories: {l2_count}")
            return l1_count, l2_count

        except Exception as e:
            session.rollback()
            logger.error(f"导入失败: {e}")
            raise
        finally:
            session.close()

    def preview_excel(self, rows: int = 10):
        """
        预览 Excel 内容

        Args:
            rows: 预览行数
        """
        if self.df is None:
            logger.error("请先加载 Excel 文件")
            return

        print("\n" + "=" * 80)
        print(f"文件名: {self.excel_path.name}")
        print(f"总行数: {len(self.df)}")
        print(f"列名: {list(self.df.columns)}")
        print("=" * 80)

        print("\n前几行数据预览:")
        print(self.df.head(rows).to_string())

        print("\n数据类型:")
        print(self.df.dtypes.to_string())

        print("\n" + "=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="供应商价格表导入工具")
    parser.add_argument("excel_file", help="Excel 文件路径")
    parser.add_argument("--preview", "-p", action="store_true", help="仅预览，不导入")
    parser.add_argument("--dry-run", "-d", action="store_true", help="模拟运行，不实际修改数据库")

    args = parser.parse_args()

    importer = SupplierPriceImporter(args.excel_file)

    # 加载 Excel
    if not importer.load_excel():
        return

    # 预览模式
    if args.preview:
        importer.preview_excel()
        return

    # 导入模式
    if args.dry_run:
        logger.info("模拟运行模式，不会修改数据库")
        importer.preview_excel(rows=5)
    else:
        importer.import_to_database()


if __name__ == "__main__":
    main()
