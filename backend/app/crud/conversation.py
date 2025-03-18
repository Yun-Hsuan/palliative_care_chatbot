from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.conversation import Conversation, ConversationCreate, ConversationUpdate

class CRUDConversation(CRUDBase[Conversation, ConversationCreate, ConversationUpdate]):
    async def get_by_patient(
        self, db: AsyncSession, *, patient_id: UUID
    ) -> list[Conversation]:
        """獲取特定病人的所有對話"""
        result = await db.execute(
            select(Conversation).where(Conversation.patient_id == patient_id)
        )
        return result.scalars().all()

    async def get_active_conversation(
        self, db: AsyncSession, *, patient_id: UUID
    ) -> Optional[Conversation]:
        """獲取病人的活躍對話"""
        from app.models.enums import ConversationStatus
        
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.patient_id == patient_id,
                Conversation.status == ConversationStatus.IN_PROGRESS
            )
            .order_by(Conversation.start_time.desc())
        )
        return result.scalar_one_or_none()

conversation = CRUDConversation(Conversation) 