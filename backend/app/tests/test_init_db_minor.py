import asyncio
import logging
from sqlalchemy import inspect, text
from app.db.session import engine, init_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core tables to test (starting with just one table)
CORE_TABLES = {
    'healthcare_members',  # Base user table
    'patient',            # Patient table (singular form)
    'conversations',       # Conversation table (singular form)
    'symptom_records',     # Symptom record table (singular form)
}

async def verify_tables(conn):
    """Helper function to verify tables using connection"""
    def _do_inspect(connection):
        inspector = inspect(connection)
        return set(inspector.get_table_names())
    
    return await conn.run_sync(_do_inspect)

async def quick_test():
    """Perform a quick test of database connection and core table creation"""
    try:
        logger.info("Starting quick test...")

        # 1. Test database connection
        logger.info("Testing database connection...")
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            assert result.scalar() == 1
            logger.info("✓ Database connection successful")

        # 2. Create tables
        logger.info("Creating tables...")
        await init_db()
        logger.info("✓ Table creation commands executed")

        # 3. Verify core tables
        logger.info("Verifying core tables...")
        async with engine.begin() as conn:
            actual_tables = await verify_tables(conn)
            
            # Check for missing core tables
            missing_tables = CORE_TABLES - actual_tables
            if missing_tables:
                logger.error(f"❌ Missing core tables: {missing_tables}")
                raise Exception("Core tables are missing")
            
            # Display found core tables
            logger.info("Core tables status:")
            for table in sorted(CORE_TABLES):
                if table in actual_tables:
                    logger.info(f"✓ {table}")
            
            # Display additional tables found (optional)
            extra_tables = actual_tables - CORE_TABLES
            if extra_tables:
                logger.info("\nAdditional tables created:")
                for table in sorted(extra_tables):
                    logger.info(f"- {table}")

        logger.info("\n✓ Quick test completed successfully")
        return True

    except Exception as e:
        logger.error(f"\n❌ Error during test: {str(e)}")
        return False
    finally:
        # Clean up database connection
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if not success:
        exit(1)  # Exit with non-zero code if test fails 