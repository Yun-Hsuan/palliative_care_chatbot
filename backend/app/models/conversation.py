from datetime import datetime
import uuid
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

from .enums import ConversationType, ConversationStatus, MessageType

class Message(SQLModel, table=True):
    """聊天消息模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", nullable=False)
    content: str = Field(nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    message_type: MessageType = Field(nullable=False)

    # 關聯
    conversation: "Conversation" = Relationship(back_populates="messages")

class Conversation(SQLModel, table=True):
    """對話模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    line_user_id: str = Field(index=True, nullable=False)  # LINE 用戶 ID
    start_time: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    end_time: Optional[datetime] = None
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, nullable=False)
    conversation_type: ConversationType = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)

    # 關聯
    messages: List[Message] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    symptom_collection: Optional["SymptomCollection"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    ) 