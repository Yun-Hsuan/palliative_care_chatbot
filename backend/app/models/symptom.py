import uuid
from datetime import datetime
from typing import Optional, List, Dict

from sqlmodel import Field, SQLModel, Relationship

from .enums import SymptomSeverity
from .user import User
from .patient import Patient
from .conversation import Conversation

# Symptom Record Model
class SymptomRecord(SQLModel, table=True):
    """Model for recording symptom collection sessions."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id")
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id")
    recorded_by_id: uuid.UUID = Field(foreign_key="user.id")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    assessment_datetime: datetime
    note: Optional[str] = None
    collection_order: int  # 1-4 for tracking order in conversation
    collection_complete: bool = Field(default=False)

    # Relationships
    patient: Patient = Relationship(back_populates="symptom_records")
    recorded_by: User = Relationship()
    conversation: Conversation = Relationship(back_populates="symptom_records")
    details: List["SymptomDetail"] = Relationship(back_populates="symptom_record")

# Symptom Detail Model
class SymptomDetail(SQLModel, table=True):
    """Model for storing detailed symptom information."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    symptom_record_id: uuid.UUID = Field(foreign_key="symptomrecord.id")
    category: str = Field(max_length=50)  # e.g., "respiratory", "digestive", "pain"
    primary_symptom: str = Field(max_length=100)  # e.g., "cough", "nausea", "headache"
    severity: SymptomSeverity
    duration: str = Field(max_length=50)  # e.g., "3 days", "1 week"
    frequency: str = Field(max_length=50)  # e.g., "continuous", "intermittent"
    characteristics: Dict = Field(default={})  # Detailed characteristics in JSON format
    related_symptoms: List[str] = Field(default=[])
    impact_on_daily_life: int = Field(ge=1, le=5)  # 1-5 scale

    # Relationships
    symptom_record: SymptomRecord = Relationship(back_populates="details")

# Symptom Characteristic Model
class SymptomCharacteristic(SQLModel, table=True):
    """Model for defining characteristics that can be collected for symptoms."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    symptom_category: str = Field(max_length=50)  # Symptom category
    characteristic_key: str = Field(max_length=50)  # Characteristic key (e.g., color, consistency, location)
    name: str = Field(max_length=100)  # Display name of the characteristic
    type: str = Field(max_length=20)  # Data type (text, number, select, multiple)
    options: Optional[List[str]] = None  # Options for select and multiple types
    required: bool = Field(default=False)  # Whether this characteristic is required
    follow_up_questions: Optional[List[str]] = None  # Follow-up questions to ask

# Related Symptom Rule Model
class RelatedSymptomRule(SQLModel, table=True):
    """Model for defining rules to identify related symptoms."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    primary_symptom: str = Field(max_length=100)  # Primary symptom that triggers the rule
    related_symptoms: List[str] = Field(default=[])  # List of potentially related symptoms
    condition: Dict = Field(default={})  # Trigger conditions in JSON format
    priority: int = Field(ge=1, le=5)  # Priority for asking follow-up questions

# API Models
class SymptomRecordCreate(SQLModel):
    """Model for creating a new symptom record."""
    patient_id: uuid.UUID
    conversation_id: uuid.UUID
    assessment_datetime: datetime
    note: Optional[str] = None
    collection_order: int

class SymptomDetailCreate(SQLModel):
    """Model for creating a new symptom detail."""
    symptom_record_id: uuid.UUID
    category: str
    primary_symptom: str
    severity: SymptomSeverity
    duration: str
    frequency: str
    characteristics: Dict = Field(default={})
    related_symptoms: List[str] = Field(default=[])
    impact_on_daily_life: int

class SymptomCharacteristicCreate(SQLModel):
    """Model for creating a new symptom characteristic."""
    symptom_category: str
    characteristic_key: str
    name: str
    type: str
    options: Optional[List[str]] = None
    required: bool = False
    follow_up_questions: Optional[List[str]] = None

class RelatedSymptomRuleCreate(SQLModel):
    """Model for creating a new related symptom rule."""
    primary_symptom: str
    related_symptoms: List[str]
    condition: Dict
    priority: int 