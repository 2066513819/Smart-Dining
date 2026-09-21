"""
创建食材价格别名表 ingredient_price_aliases。
用于配方中的名称与价格表名称不一致时（如 西红柿/番茄）匹配到同一条价格。
执行: python scripts/create_ingredient_price_aliases_table.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.services.db_service import engine

def main():
    with engine.connect() as conn:
        if "mysql" in str(engine.url):
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ingredient_price_aliases (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ingredient_price_id INT NOT NULL,
                    alias_name VARCHAR(255) NOT NULL,
                    CONSTRAINT fk_alias_price FOREIGN KEY (ingredient_price_id)
                        REFERENCES ingredient_prices(id) ON DELETE CASCADE,
                    INDEX ix_ingredient_price_id (ingredient_price_id)
                )
            """))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ingredient_price_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingredient_price_id INTEGER NOT NULL REFERENCES ingredient_prices(id) ON DELETE CASCADE,
                    alias_name VARCHAR(255) NOT NULL
                )
            """))
        conn.commit()
    print("表 ingredient_price_aliases 已创建或已存在。")

if __name__ == "__main__":
    main()
