import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from .enums import ConversationStatus, ConversationType, MessageType, DiagnosisStatus


class Conversation(SQLModel, table=True):
    """Conversation model for tracking dialogue sessions with patients"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id", nullable=False)
    initiator_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    start_time: datetime = Field(nullable=False)
    end_time: datetime | None = Field(default=None)
    status: ConversationStatus = Field(nullable=False)
    conversation_type: ConversationType = Field(nullable=False)
    symptoms_collected_count: int = Field(default=0, nullable=False)
    target_symptoms_count: int = Field(default=4, nullable=False)
    current_symptom_focus: str | None = Field(default=None)
    collection_complete: bool = Field(default=False, nullable=False)

    # Relationships
    patient: "Patient" = Relationship(back_populates="conversations")
    initiator: "User" = Relationship(back_populates="initiated_conversations")
    messages: list["Message"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    symptom_records: list["SymptomRecord"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class Message(SQLModel, table=True):
    """Message model for storing individual messages in conversations"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", nullable=False)
    sender_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    content: str = Field(nullable=False)
    timestamp: datetime = Field(nullable=False)
    message_type: MessageType = Field(nullable=False)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    sender: "User" = Relationship(back_populates="messages")


class Diagnosis(SQLModel, table=True):
    """Diagnosis model for recording patient diagnostic information"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id", nullable=False)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(nullable=False)
    symptoms_summary: str = Field(nullable=False)
    ai_suggestion: str = Field(nullable=False)
    medical_team_notes: str | None = Field(default=None)
    priority_level: int = Field(ge=1, le=5, nullable=False)  # 1-5 scale
    status: DiagnosisStatus = Field(nullable=False)

    # Relationships
    patient: "Patient" = Relationship(back_populates="diagnoses")
    created_by: "User" = Relationship(back_populates="created_diagnoses")


# API Models for creation and updates
class ConversationCreate(SQLModel):
    """API model for creating new conversations"""
    patient_id: uuid.UUID
    conversation_type: ConversationType
    target_symptoms_count: int = Field(default=4, ge=1)


class MessageCreate(SQLModel):
    """API model for creating new messages"""
    conversation_id: uuid.UUID
    content: str = Field(min_length=1)
    message_type: MessageType


class DiagnosisCreate(SQLModel):
    """API model for creating new diagnoses"""
    patient_id: uuid.UUID
    symptoms_summary: str = Field(min_length=1)
    ai_suggestion: str = Field(min_length=1)
    medical_team_notes: str | None = None
    priority_level: int = Field(ge=1, le=5) 