from typing import Optional, Dict
from pydantic import BaseModel, validator, Field
from datetime import datetime

class VitalSignsUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, pattern="^(男|女|其他)$")
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0)
    blood_pressure: Optional[str] = Field(None, pattern=r"^\d{2,3}/\d{2,3}$")

    @validator('blood_pressure')
    def validate_blood_pressure(cls, v):
        if v is not None:
            systolic, diastolic = map(int, v.split('/'))
            if not (60 <= systolic <= 200 and 40 <= diastolic <= 130):
                raise ValueError("血壓數值超出正常範圍")
        return v

class SymptomUpdate(BaseModel):
    symptom: str = Field(..., min_length=1, max_length=100)
    details: Optional[str] = Field(None, max_length=500)

    @validator('symptom')
    def validate_symptom(cls, v):
        # 這裡可以添加症狀名稱的驗證邏輯
        # 例如檢查是否在預定義的症狀列表中
        return v.strip()

class CollectionResponse(BaseModel):
    id: str
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    vital_signs: VitalSignsUpdate
    symptoms: Dict[str, dict]
    is_complete: bool

    class Config:
        orm_mode = True 