from typing import Optional, Dict, List, Callable, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.exceptions import (
    CollectionNotFoundError,
    CollectionExistsError,
    SymptomLimitExceededError,
    InvalidVitalSignsError,
    SymptomNotFoundError
)
from ..models.conversation import SymptomCollection, SymptomEntry, SymptomStatus, VitalStatus
from ..schemas.symptom_collection import VitalSignsUpdate, SymptomUpdate

class SymptomCollectionService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self._completion_callbacks: List[Callable] = []

    def add_completion_callback(self, callback: Callable[[SymptomCollection], Any]):
        """添加收集完成時的回調函數"""
        self._completion_callbacks.append(callback)

    async def get_collection(self, conversation_id: UUID) -> SymptomCollection:
        """獲取指定對話的症狀收集記錄"""
        query = select(SymptomCollection).where(SymptomCollection.conversation_id == conversation_id)
        result = await self.db_session.execute(query)
        collection = result.scalar_one_or_none()
        
        if not collection:
            raise CollectionNotFoundError(f"找不到對話 {conversation_id} 的症狀收集記錄")
        
        return collection

    async def create_collection(self, conversation_id: UUID) -> SymptomCollection:
        """創建新的症狀收集記錄"""
        # 檢查是否已存在
        try:
            await self.get_collection(conversation_id)
            raise CollectionExistsError(f"對話 {conversation_id} 已有症狀收集記錄")
        except CollectionNotFoundError:
            pass

        collection = SymptomCollection(
            conversation_id=conversation_id,
            vital_status=VitalStatus(),
            symptoms={},
            is_complete=False
        )
        
        self.db_session.add(collection)
        await self.db_session.commit()
        await self.db_session.refresh(collection)
        
        return collection

    async def update_vital_signs(self, conversation_id: UUID, vital_signs: VitalSignsUpdate) -> SymptomCollection:
        """更新生命體徵數據"""
        collection = await self.get_collection(conversation_id)
        
        # 更新非空的字段
        for field, value in vital_signs.dict(exclude_unset=True).items():
            setattr(collection.vital_status, field, value)
        
        collection.updated_at = datetime.utcnow()
        await self._check_completion(collection)
        
        await self.db_session.commit()
        await self.db_session.refresh(collection)
        
        return collection

    async def record_symptom(
        self,
        conversation_id: UUID,
        symptom: str,
        status: SymptomStatus = SymptomStatus.YES,
        details: Optional[str] = None
    ) -> SymptomCollection:
        """記錄症狀"""
        collection = await self.get_collection(conversation_id)
        
        # 檢查症狀數量限制
        if len(collection.symptoms) >= 4 and symptom not in collection.symptoms:
            raise SymptomLimitExceededError("已達到症狀數量上限")
        
        collection.symptoms[symptom] = SymptomEntry(
            symptom=symptom,
            status=status,
            details=details
        )
        
        collection.updated_at = datetime.utcnow()
        await self._check_completion(collection)
        
        await self.db_session.commit()
        await self.db_session.refresh(collection)
        
        return collection

    async def update_symptom_details(
        self,
        conversation_id: UUID,
        symptom: str,
        details: str
    ) -> SymptomCollection:
        """更新症狀細節"""
        collection = await self.get_collection(conversation_id)
        
        if symptom not in collection.symptoms:
            raise SymptomNotFoundError(f"找不到症狀: {symptom}")
        
        collection.symptoms[symptom].details = details
        collection.updated_at = datetime.utcnow()
        await self._check_completion(collection)
        
        await self.db_session.commit()
        await self.db_session.refresh(collection)
        
        return collection

    async def _check_completion(self, collection: SymptomCollection) -> None:
        """檢查是否所有必要資訊都已收集"""
        # 檢查基本體徵是否完整
        vital_complete = all([
            collection.vital_status.age,
            collection.vital_status.gender,
            collection.vital_status.temperature,
            collection.vital_status.blood_pressure
        ])
        
        # 檢查症狀記錄是否完整
        symptoms_complete = all(
            symptom.status != SymptomStatus.NULL
            for symptom in collection.symptoms.values()
        )
        
        # 更新完成狀態
        was_complete = collection.is_complete
        collection.is_complete = vital_complete and symptoms_complete
        
        # 如果狀態從未完成變為完成，觸發回調
        if not was_complete and collection.is_complete:
            for callback in self._completion_callbacks:
                await callback(collection)

    async def get_next_required_info(self, conversation_id: UUID) -> str:
        """獲取下一個需要收集的資訊"""
        collection = await self.get_collection(conversation_id)
        
        # 檢查基本體徵
        vital = collection.vital_status
        if not vital.age:
            return "需要詢問年齡"
        if not vital.gender:
            return "需要詢問性別"
        if not vital.temperature:
            return "需要詢問體溫"
        if not vital.blood_pressure:
            return "需要詢問血壓"
        
        # 檢查症狀
        for symptom in collection.symptoms.values():
            if symptom.status == SymptomStatus.YES and not symptom.details:
                return f"需要詢問症狀 '{symptom.symptom}' 的詳細情況"
        
        # 如果症狀數量少於4個，提示可以繼續收集
        if len(collection.symptoms) < 4:
            return "可以繼續詢問其他症狀"
        
        return "所有必要資訊已收集完成" 