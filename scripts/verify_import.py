"""
验证供应商价格表导入结果
用于检查导入后的数据完整性和准确性
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.config import settings
except ImportError:
    print("无法导入 settings，请确保在项目根目录运行")
    sys.exit(1)


def create_session():
    """创建数据库会话"""
    db_url = (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def verify_import():
    """验证导入结果"""
    session = create_session()

    print("\n" + "=" * 80)
    print("📊 供应商价格表导入验证报告")
    print("=" * 80)

    # 1. 一级分类统计
    print("\n📁 一级分类统计:")
    result = session.execute(text("""
        SELECT l1.code, l1.name, COUNT(DISTINCT i.id) as ingredient_count
        FROM l1_categories l1
        LEFT JOIN ingredient_l1_catalog i ON l1.code = i.l1_code
        GROUP BY l1.code, l1.name
        ORDER BY ingredient_count DESC
    """)).fetchall()

    if result:
        print(f"{'编码':<8} {'名称':<20} {'食材数量':<10}")
        print("-" * 40)
        for row in result:
            print(f"{row[0]:<8} {row[1]:<20} {row[2]:<10}")
    else:
        print("暂无一级分类数据")

    # 2. 二级分类统计
    print("\n📂 二级分类统计:")
    result = session.execute(text("""
        SELECT l1.name as l1_name, l2.name as l2_name, COUNT(DISTINCT i.id) as ingredient_count
        FROM l2_categories l2
        JOIN l1_categories l1 ON l2.l1_code = l1.code
        LEFT JOIN ingredient_l2_catalog i ON l2.code = i.l2_code
        GROUP BY l1.name, l2.name
        ORDER BY ingredient_count DESC
        LIMIT 20
    """)).fetchall()

    if result:
        print(f"{'一级分类':<15} {'二级分类':<15} {'食材数量':<10}")
        print("-" * 45)
        for row in result:
            print(f"{row[0]:<15} {row[1]:<15} {row[2]:<10}")
    else:
        print("暂无二级分类数据")

    # 3. 食材价格统计
    print("\n🥘 食材价格统计（前20条最新）:")
    result = session.execute(text("""
        SELECT 
            i.ingredient_name,
            l1.name as category,
            i.unit,
            i.price,
            i.updated_at
        FROM ingredient_l1_catalog i
        JOIN l1_categories l1 ON i.l1_code = l1.code
        ORDER BY i.updated_at DESC
        LIMIT 20
    """)).fetchall()

    if result:
        print(f"{'食材名称':<20} {'分类':<12} {'单位':<8} {'价格':<10} {'更新时间':<20}")
        print("-" * 75)
        for row in result:
            update_time = row[4].strftime('%Y-%m-%d %H:%M') if row[4] else '-'
            print(f"{row[0]:<20} {row[1]:<12} {row[2]:<8} {row[3]:<10.2f} {update_time:<20}")
    else:
        print("暂无食材价格数据")

    # 4. 总体统计
    print("\n📈 总体统计:")
    stats = {}

    stats['l1_count'] = session.execute(
        text("SELECT COUNT(*) FROM l1_categories")
    ).fetchone()[0]

    stats['l2_count'] = session.execute(
        text("SELECT COUNT(*) FROM l2_categories")
    ).fetchone()[0]

    stats['l1_ingredients'] = session.execute(
        text("SELECT COUNT(*) FROM ingredient_l1_catalog")
    ).fetchone()[0]

    stats['l2_ingredients'] = session.execute(
        text("SELECT COUNT(*) FROM ingredient_l2_catalog")
    ).fetchone()[0]

    stats['avg_price'] = session.execute(
        text("SELECT AVG(price) FROM ingredient_l1_catalog WHERE price > 0")
    ).fetchone()[0] or 0

    print(f"  一级分类总数: {stats['l1_count']}")
    print(f"  二级分类总数: {stats['l2_count']}")
    print(f"  一级分类食材总数: {stats['l1_ingredients']}")
    print(f"  二级分类食材总数: {stats['l2_ingredients']}")
    print(f"  平均价格: {stats['avg_price']:.2f} 元")

    # 5. 检查异常数据
    print("\n⚠️  异常数据检查:")

    # 检查价格为0或空的食材
    result = session.execute(text("""
        SELECT COUNT(*) FROM ingredient_l1_catalog
        WHERE price = 0 OR price IS NULL
    """)).fetchone()[0]
    if result > 0:
        print(f"  警告: {result} 个食材价格为0或未设置")
    else:
        print("  ✓ 所有食材价格已设置")

    # 检查没有单位的食材
    result = session.execute(text("""
        SELECT COUNT(*) FROM ingredient_l1_catalog
        WHERE unit IS NULL OR unit = ''
    """)).fetchone()[0]
    if result > 0:
        print(f"  警告: {result} 个食材单位未设置")
    else:
        print("  ✓ 所有食材单位已设置")

    # 检查重复的食材名称
    result = session.execute(text("""
        SELECT ingredient_name, COUNT(*) as cnt
        FROM ingredient_l1_catalog
        GROUP BY ingredient_name
        HAVING COUNT(*) > 1
        LIMIT 10
    """)).fetchall()
    if result:
        print(f"  警告: 发现 {len(result)} 个重复食材名称（同一食材多个分类）")
        for row in result:
            print(f"    - {row[0]}: {row[1]} 次")
    else:
        print("  ✓ 未发现重复食材名称")

    print("\n" + "=" * 80)
    print("验证完成!")
    print("=" * 80)

    session.close()


if __name__ == "__main__":
    verify_import()
