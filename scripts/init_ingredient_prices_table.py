
from app.services.db_service import engine, Base
from app.models.ingredient_price import IngredientPrice
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_db():
    try:
        logger.info("Starting table creation...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully (including ingredient_prices if it was missing).")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

if __name__ == "__main__":
    setup_db()
