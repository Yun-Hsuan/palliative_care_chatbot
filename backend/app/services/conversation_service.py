from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, orm
import uuid
import logging

from app.models.conversation import Conversation, Message, ConversationType, ConversationStatus, MessageType
from app.models.symptom import (
    SymptomCollection,
    SymptomStatus,
    create_empty_collection
)

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self,
        line_user_id: str,
        conversation_type: ConversationType = ConversationType.GENERAL
    ) -> Conversation:
        """Get user's active conversation, create new one if not exists"""
        try:
            # Find user's active conversation
            query = select(Conversation).where(
                Conversation.line_user_id == line_user_id,
                Conversation.is_active == True
            )
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()

            if conversation:
                # 檢查是否已有症狀收集記錄
                if conversation_type == ConversationType.SYMPTOM_COLLECTION:
                    symptom_collection = await self.get_active_symptom_collection(conversation.id)
                    if not symptom_collection:
                        # 如果沒有，創建一個新的
                        symptom_collection = SymptomCollection(
                            conversation_id=conversation.id,
                            line_user_id=line_user_id,
                            collection_data=create_empty_collection()
                        )
                        self.db.add(symptom_collection)
                        await self.db.commit()
                return conversation

            # Create new conversation
            conversation = Conversation(
                line_user_id=line_user_id,
                conversation_type=conversation_type,
                status=ConversationStatus.ACTIVE,
                is_active=True
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

            # Create associated symptom collection record if it's a symptom collection conversation
            if conversation_type == ConversationType.SYMPTOM_COLLECTION:
                symptom_collection = SymptomCollection(
                    conversation_id=conversation.id,
                    line_user_id=line_user_id,
                    collection_data=create_empty_collection()
                )
                self.db.add(symptom_collection)
                await self.db.commit()

            return conversation
        except Exception as e:
            await self.db.rollback()
            logger.error(f"創建對話時發生錯誤: {str(e)}")
            raise

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        message_type: MessageType
    ) -> Message:
        """Add new message to conversation"""
        try:
            message = Message(
                conversation_id=conversation_id,
                content=content,
                message_type=message_type
            )
            self.db.add(message)
            await self.db.commit()
            await self.db.refresh(message)
            return message
        except Exception as e:
            await self.db.rollback()
            raise

    async def get_conversation_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = 10
    ) -> List[Message]:
        """Get conversation history"""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).limit(limit)
        
        result = await self.db.execute(query)
        messages = result.scalars().all()
        return list(reversed(messages))  # Return messages in chronological order

    async def end_conversation(
        self,
        conversation_id: uuid.UUID,
        status: ConversationStatus = ConversationStatus.COMPLETED
    ) -> None:
        """End conversation"""
        try:
            conversation = await self.db.get(Conversation, conversation_id)
            if conversation:
                # 結束對話
                conversation.is_active = False
                conversation.status = status
                conversation.end_time = datetime.utcnow()
                
                # 將症狀收集標記為完成
                symptom_collection = await self.get_active_symptom_collection(conversation_id)
                if symptom_collection:
                    symptom_collection.is_complete = True
                    symptom_collection.updated_at = datetime.utcnow()
                    # 強制將更改標記為"髒"數據
                    orm.attributes.flag_modified(symptom_collection, "collection_data")
                
                # 創建新的對話
                new_conversation = Conversation(
                    line_user_id=conversation.line_user_id,
                    conversation_type=conversation.conversation_type,
                    status=ConversationStatus.ACTIVE,
                    is_active=True
                )
                self.db.add(new_conversation)
                await self.db.commit()
                await self.db.refresh(new_conversation)
                
                # 如果是症狀收集對話，創建新的症狀收集記錄
                if conversation.conversation_type == ConversationType.SYMPTOM_COLLECTION:
                    new_symptom_collection = SymptomCollection(
                        conversation_id=new_conversation.id,
                        line_user_id=conversation.line_user_id,
                        collection_data=create_empty_collection()
                    )
                    self.db.add(new_symptom_collection)
                    await self.db.commit()
                
                await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise

    async def get_active_symptom_collection(
        self,
        conversation_id: uuid.UUID
    ) -> Optional[SymptomCollection]:
        """Get active symptom collection record"""
        query = select(SymptomCollection).where(
            SymptomCollection.conversation_id == conversation_id,
            SymptomCollection.is_complete == False
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_vital_status(
        self,
        conversation_id: uuid.UUID,
        vital_data: Dict
    ) -> None:
        """Update vital signs data"""
        try:
            symptom_collection = await self.get_active_symptom_collection(conversation_id)
            if symptom_collection:
                symptom_collection.vital_status.update(vital_data)
                symptom_collection.updated_at = datetime.utcnow()
                await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise

    async def update_symptom(
        self,
        conversation_id: uuid.UUID,
        symptom_name: str,
        status: SymptomStatus,
        description: Optional[str] = None
    ) -> None:
        """Update symptom information"""
        try:
            symptom_collection = await self.get_active_symptom_collection(conversation_id)
            if symptom_collection:
                symptom_collection.symptoms[symptom_name] = {
                    "status": status.value,
                    "description": description,
                    "updated_at": datetime.utcnow().isoformat()
                }
                symptom_collection.updated_at = datetime.utcnow()
                await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise

    async def update_collection_data(
        self,
        conversation_id: uuid.UUID,
        collection_data: Dict
    ) -> None:
        """更新收集數據"""
        try:
            symptom_collection = await self.get_active_symptom_collection(conversation_id)
            if symptom_collection:
                # 深度更新 collection_data
                if "vital_status" in collection_data:
                    if "vital_status" not in symptom_collection.collection_data:
                        symptom_collection.collection_data["vital_status"] = {}
                    # 只更新非空值
                    for key, value in collection_data["vital_status"].items():
                        if value is not None and value != "null":
                            symptom_collection.collection_data["vital_status"][key] = value
                
                # 更新症狀相關字段
                for key, value in collection_data.items():
                    if key.startswith("symptom_"):
                        # 檢查症狀記錄是否有效
                        if (value.get("symptom_name") is None or 
                            value.get("symptom_name") == "null" or
                            value.get("symptom_status") == "null"):
                            continue
                            
                        # 檢查是否已存在相同的症狀
                        existing_symptom_key = None
                        for existing_key, existing_value in symptom_collection.collection_data.items():
                            if (existing_key.startswith("symptom_") and 
                                existing_value.get("symptom_name") == value.get("symptom_name")):
                                existing_symptom_key = existing_key
                                break
                        
                        if existing_symptom_key:
                            # 更新現有症狀的資訊
                            current_symptom = symptom_collection.collection_data[existing_symptom_key]
                            # 只更新非空值
                            for field, new_value in value.items():
                                if new_value is not None and new_value != "null":
                                    current_symptom[field] = new_value
                        else:
                            # 如果是新症狀，找到下一個可用的編號
                            symptom_numbers = [
                                int(k.replace("symptom_", ""))
                                for k in symptom_collection.collection_data.keys()
                                if k.startswith("symptom_")
                            ]
                            next_number = max(symptom_numbers, default=0) + 1
                            new_key = f"symptom_{next_number}"
                            symptom_collection.collection_data[new_key] = value
                
                # 確保更新被標記
                symptom_collection.updated_at = datetime.utcnow()
                
                # 強制將更改標記為"髒"數據，確保 SQLAlchemy 會更新它
                orm.attributes.flag_modified(symptom_collection, "collection_data")
                
                await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise