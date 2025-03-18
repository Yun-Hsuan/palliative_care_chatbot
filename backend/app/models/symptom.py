from datetime import datetime
import uuid
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON

from .enums import SymptomStatus
from .conversation import Conversation

def create_empty_vital_status() -> Dict[str, Any]:
    """創建空的生命體徵狀態"""
    return {
        "age": None,
        "gender": None,
        "temperature": None,
        "systolic_bp": None,
        "diastolic_bp": None
    }

def create_empty_symptom() -> Dict[str, Any]:
    """創建空的症狀記錄"""
    return {
        "symptom_name": None,           # 症狀名稱
        "symptom_status": "null",       # 症狀狀態 (yes/no/null)
        "severity": None,               # 症狀嚴重程度 (mild/moderate/severe)
        "duration": None,               # 症狀持續時間
        "description": None             # 症狀詳細描述
    }

def create_empty_collection() -> Dict[str, Any]:
    """創建完整的空收集結構"""
    return {
        "vital_status": create_empty_vital_status(),
        "symptom_1": create_empty_symptom(),
        "symptom_2": create_empty_symptom(),
        "symptom_3": create_empty_symptom(),
        "symptom_4": create_empty_symptom()
    }

class VitalStatus(SQLModel):
    """生命體徵模型"""
    age: Optional[int] = None
    gender: Optional[str] = None
    temperature: Optional[float] = None
    systolic_bp: Optional[int] = None  # 收縮壓
    diastolic_bp: Optional[int] = None  # 舒張壓

class SymptomEntry(SQLModel):
    """症狀條目模型"""
    name: str
    status: SymptomStatus = SymptomStatus.NULL
    description: Optional[str] = None

class SymptomCollection(SQLModel, table=True):
    """症狀收集模型"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", unique=True, nullable=False)
    line_user_id: str = Field(index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # 使用 JSON 欄位儲存結構化數據
    collection_data: Dict = Field(
        default_factory=create_empty_collection,
        sa_type=JSON
    )
    is_complete: bool = Field(default=False, nullable=False)

    # 關聯
    conversation: Conversation = Relationship(back_populates="symptom_collection") 