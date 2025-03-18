from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.ENVIRONMENT == "local",  # Only enable echo in local environment
    pool_pre_ping=True,  # Add connection pool pre-ping
    pool_size=5,         # Set connection pool size
    max_overflow=10      # Maximum overflow connection count
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False      # Disable auto-flush for better performance
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
        # Import required models
        from app.models.conversation import Conversation, Message
        from app.models.symptom import SymptomCollection
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)

# Cleanup database connections
async def close_db():
    await engine.dispose() 