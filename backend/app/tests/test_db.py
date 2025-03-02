import asyncio
import logging

from sqlalchemy import text

from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    try:
        # Try to connect to the database
        async with engine.connect() as conn:
            # Execute a simple query
            result = await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection()) 