from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import logging

from app.core.config import settings
from app.db.session import engine
from app.models import SQLModel
from app.api import deps

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

@router.post("/create-tables", response_model=Dict[str, str])
async def create_tables(
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, str]:
    """
    Create all database tables.
    Only available in development environment.
    """
    if settings.ENVIRONMENT != "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is only allowed in development environment"
        )
    
    try:
        async with engine.begin() as conn:
            # Ensure all models are imported
            from app.models.conversation import Conversation, Message
            from app.models.symptom import SymptomCollection
            
            await conn.run_sync(SQLModel.metadata.create_all)
        
        logger.info("Successfully created all database tables")
        return {"message": "Successfully created all database tables", "status": "success"}
    
    except Exception as e:
        logger.error(f"Error occurred while creating database tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred while creating database tables: {str(e)}"
        )

@router.post("/drop-tables", response_model=Dict[str, str])
async def drop_tables(
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, str]:
    """
    Drop all database tables.
    Only available in development environment and requires additional confirmation.
    """
    if settings.ENVIRONMENT != "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is only allowed in development environment"
        )
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        
        logger.info("Successfully dropped all database tables")
        return {
            "message": "Successfully dropped all database tables",
            "status": "success",
            "warning": "All data has been permanently deleted"
        }
    
    except Exception as e:
        logger.error(f"Error occurred while dropping database tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred while dropping database tables: {str(e)}"
        )