from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.ENVIRONMENT == "local",  # Only enable echo in local environment
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

# Dependency to get async session
async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        # Import base models for testing
        from app.models.healthcare_member import HealthcareMember
        from app.models.patient import Patient
        from app.models.conversation import Conversation
        from app.models.symptom import SymptomRecord
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)

# Cleanup database connections
async def close_db():
    await engine.dispose() 