from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

from app.models.conversation import ConversationType, ConversationStatus, MessageType
from app.models.symptom import SymptomStatus, create_empty_collection
from app.services.conversation_service import ConversationService
from app.ai_services.openai_service import OpenAIService
from app.core.logger import logger

class ChatHandler:
    def __init__(
        self,
        conversation_service: ConversationService,
        openai_service: OpenAIService
    ):
        self.conversation_service = conversation_service
        self.openai_service = openai_service
        self._current_conversation_id: Optional[uuid.UUID] = None
        self._consent_confirmed: bool = False
        self._identity_confirmed: bool = False
        self._current_identity: Optional[str] = None
        self._current_phase: str = "vital_status"  # 新增階段追踪變數

    async def start_chat(self, user_id: str = "terminal_user") -> str:
        """開始新的對話"""
        conversation = await self.conversation_service.get_or_create_conversation(
            line_user_id=user_id,
            conversation_type=ConversationType.SYMPTOM_COLLECTION
        )
        self._current_conversation_id = conversation.id
        
        # 發送歡迎消息和同意請求
        welcome_message = (
            "您好！這是一個協助安寧照護團隊理解您或所照顧患者的AI Chatbot。\n"
            "接下來我會詢問一些基本訊息還有病症，如果您準備好了，請跟我說 OK 或是準備好了。\n"
            "如果您不同意的話，請說不同意，我們便會終止。"
        )
        await self.conversation_service.add_message(
            conversation_id=conversation.id,
            content=welcome_message,
            message_type=MessageType.SYSTEM
        )
        
        return welcome_message

    async def handle_message(self, message: str, user_id: str = "terminal_user") -> str:
        """處理用戶消息"""
        if not self._current_conversation_id:
            return await self.start_chat(user_id)

        # 檢查是否要結束對話
        if message.lower() == 'exit':
            await self.end_chat()
            return "感謝您的使用，對話已結束。祝您健康愉快！"

        # 記錄用戶消息
        await self.conversation_service.add_message(
            conversation_id=self._current_conversation_id,
            content=message,
            message_type=MessageType.USER
        )

        try:
            # 如果還沒有確認同意，先進行同意確認
            if not self._consent_confirmed:
                consent_result = await self.openai_service.check_user_consent(message)
                
                if consent_result["response_type"] == "unclear":
                    response = "抱歉，我不太確定您的意思。請明確告訴我您是否同意進行諮詢，您可以說「同意」或「不同意」。"
                    await self.conversation_service.add_message(
                        conversation_id=self._current_conversation_id,
                        content=response,
                        message_type=MessageType.BOT
                    )
                    return response
                
                elif consent_result["response_type"] == "explicit_disagree":
                    await self.end_chat()
                    self._current_conversation_id = None
                    self._consent_confirmed = False
                    return "感謝您的回覆。如果您之後改變主意，隨時都可以再來諮詢。祝您健康愉快！"
                
                elif consent_result["response_type"] == "explicit_agree":
                    self._consent_confirmed = True
                    response = "謝謝您的同意。首先，請問您是以什麼身份進行諮詢？\n(1) 本人\n(2) 家屬\n(3) 機構照護者"
                    await self.conversation_service.add_message(
                        conversation_id=self._current_conversation_id,
                        content=response,
                        message_type=MessageType.BOT
                    )
                    return response

            # 如果已確認同意但還沒確認身份，進行身份確認
            if not self._identity_confirmed:
                identity_result = await self.openai_service.check_identity(message)
                
                if not identity_result["is_valid"]:
                    response = identity_result["next_question"]
                    await self.conversation_service.add_message(
                        conversation_id=self._current_conversation_id,
                        content=response,
                        message_type=MessageType.BOT
                    )
                    return response
                
                self._identity_confirmed = True
                self._current_identity = identity_result["identity"]
                
                # 更新 collection_data 中的身份信息
                symptom_collection = await self.conversation_service.get_active_symptom_collection(
                    self._current_conversation_id
                )
                if symptom_collection:
                    symptom_collection.collection_data["identity"] = identity_result["identity"]
                    await self.conversation_service.update_collection_data(
                        self._current_conversation_id,
                        symptom_collection.collection_data
                    )
                
                response = identity_result["next_question"]
                await self.conversation_service.add_message(
                    conversation_id=self._current_conversation_id,
                    content=response,
                    message_type=MessageType.BOT
                )
                return response

            # 如果已經確認身份，進行正常的對話流程
            symptom_collection = await self.conversation_service.get_active_symptom_collection(
                self._current_conversation_id
            )

            if not symptom_collection:
                raise ValueError("找不到活躍的症狀收集記錄")

            # 添加日誌來查看當前的 collection_data
            logger.info(f"當前的 collection_data: {json.dumps(symptom_collection.collection_data, ensure_ascii=False, indent=2)}")

            # 獲取對話歷史
            conversation_history = await self.conversation_service.get_conversation_history(
                self._current_conversation_id
            )
            history = [
                {"role": "user" if msg.message_type == MessageType.USER else "assistant", "content": msg.content}
                for msg in conversation_history[-5:]
            ]

            # 根據當前階段處理用戶消息
            if self._current_phase == "vital_status" and self._identity_confirmed:
                result = await self.openai_service.process_collection(
                    message,
                    symptom_collection.collection_data,
                    history
                )
                
                # 如果生命體徵收集完成，進入確認階段
                if result.get("is_complete", False):
                    self._current_phase = "vital_status_confirmation"
                    gender_display = {
                        "male": "男性",
                        "female": "女性",
                        "other": "其他"
                    }.get(symptom_collection.collection_data["vital_status"]["gender"], "未知")
                    
                    # 使用更新後的數據生成摘要
                    vital_status = result["updates"]["vital_status"]
                    summary = f"""我已經收集到所有的生命體徵信息，請確認以下信息是否正確：

年齡：{vital_status["age"]} 歲
性別：{vital_status["gender"]}
體溫：{vital_status["temperature"]} °C
血壓：{vital_status["systolic_bp"]}/{vital_status["diastolic_bp"]} mmHg

如果信息正確，請回答"正確"或"沒問題"；
如果有需要修改的地方，請告訴我哪項需要修改。"""
                    
                    result["next_question"] = summary

            elif self._current_phase == "vital_status_confirmation" and self._identity_confirmed:
                # 檢查用戶是否確認信息正確
                confirmation_result = await self.openai_service.check_vital_status_confirmation(message)
                logger.info(f"確認結果: {json.dumps(confirmation_result, ensure_ascii=False, indent=2)}")
                
                if confirmation_result.get("is_confirmed", False):
                    # 分析生命體徵
                    vital_analysis = await self.openai_service.analyze_vital_signs(
                        symptom_collection.collection_data["vital_status"]
                    )
                    
                    # 將分析結果添加到 collection_data
                    if "vital_analysis" not in symptom_collection.collection_data:
                        symptom_collection.collection_data["vital_analysis"] = {}
                    symptom_collection.collection_data["vital_analysis"].update(vital_analysis)
                    
                    # 保存更新後的數據
                    await self.conversation_service.update_collection_data(
                        self._current_conversation_id,
                        symptom_collection.collection_data
                    )
                    
                    # 進入症狀收集階段
                    self._current_phase = "symptoms"
                    
                    # 獲取最新的對話歷史
                    conversation_history = await self.conversation_service.get_conversation_history(
                        self._current_conversation_id
                    )
                    history = [
                        {"role": "user" if msg.message_type == MessageType.USER else "assistant", "content": msg.content}
                        for msg in conversation_history[-5:]
                    ]
                    
                    result = await self.openai_service.process_symptom_collection(
                        message,
                        symptom_collection.collection_data,
                        history
                    )
                    
                    # 如果 process_symptom_collection 沒有返回下一個問題，使用分析結果中的初始提示
                    if not result.get("next_question"):
                        result["next_question"] = vital_analysis.get("next_question", "請告訴我您最近是否有任何不適或症狀？")
                else:
                    # 如果需要修改，返回生命體徵收集階段
                    self._current_phase = "vital_status"
                    
                    # 根據確認結果清除需要修改的字段
                    if "field_to_modify" in confirmation_result:
                        field_mapping = {
                            "age": "age",
                            "gender": "gender",
                            "temperature": "temperature",
                            "blood_pressure": ["systolic_bp", "diastolic_bp"],
                            "systolic_bp": "systolic_bp",
                            "diastolic_bp": "diastolic_bp"
                        }
                        
                        field = confirmation_result["field_to_modify"]
                        if field in field_mapping:
                            if isinstance(field_mapping[field], list):
                                # 如果是血壓，需要同時清除收縮壓和舒張壓
                                for subfield in field_mapping[field]:
                                    symptom_collection.collection_data["vital_status"][subfield] = None
                            else:
                                symptom_collection.collection_data["vital_status"][field_mapping[field]] = None
                            
                            # 保存更新後的數據
                            await self.conversation_service.update_collection_data(
                                self._current_conversation_id,
                                symptom_collection.collection_data
                            )
                    
                    # 使用更新後的數據重新調用 process_collection
                    result = await self.openai_service.process_collection(
                        message,
                        symptom_collection.collection_data,
                        history
                    )
                    
                    if not result.get("next_question"):
                        result["next_question"] = "請告訴我正確的數值。"

            elif self._current_phase == "symptoms" and self._identity_confirmed:
                # 獲取最新的對話歷史
                conversation_history = await self.conversation_service.get_conversation_history(
                    self._current_conversation_id
                )
                history = [
                    {"role": "user" if msg.message_type == MessageType.USER else "assistant", "content": msg.content}
                    for msg in conversation_history[-5:]
                ]
                
                # 處理症狀收集階段
                result = await self.openai_service.process_symptom_collection(
                    message,
                    symptom_collection.collection_data,
                    history
                )

            # 添加日誌來查看當前階段和結果
            logger.info(f"當前階段: {self._current_phase}")
            logger.info(f"處理結果: {json.dumps(result, ensure_ascii=False, indent=2)}")

            # 更新收集到的數據
            if result.get("updates"):
                # 添加日誌來查看更新前後的數據
                logger.info(f"更新前的 collection_data: {json.dumps(symptom_collection.collection_data, ensure_ascii=False, indent=2)}")
                
                # 更新 vital_status 內的字段
                if "vital_status" in result["updates"]:
                    if "vital_status" not in symptom_collection.collection_data:
                        symptom_collection.collection_data["vital_status"] = {}
                    symptom_collection.collection_data["vital_status"].update(result["updates"]["vital_status"])
                
                # 更新症狀相關字段
                for key, value in result["updates"].items():
                    if key.startswith("symptom_"):
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
                
                logger.info(f"更新後的 collection_data: {json.dumps(symptom_collection.collection_data, ensure_ascii=False, indent=2)}")
                
                # 保存更新後的數據
                await self.conversation_service.update_collection_data(
                    self._current_conversation_id,
                    symptom_collection.collection_data
                )

            # 檢查是否完成所有收集
            if self._current_phase == "symptoms":
                # 檢查是否已收集到 symptom_9 的 description
                has_symptom_6_description = (
                    "symptom_6" in symptom_collection.collection_data and
                    symptom_collection.collection_data["symptom_6"].get("description") is not None
                )
                
                if has_symptom_6_description:
                    # 檢查是否需要補充
                    needs_more_info = False
                    for key, value in symptom_collection.collection_data.items():
                        if key.startswith("symptom_") and value.get("description") is None:
                            needs_more_info = True
                            break
                    
                    if needs_more_info:
                        # 如果還有症狀需要補充描述，繼續收集到 symptom_10
                        if "symptom_7" in symptom_collection.collection_data:
                            symptom_collection.is_complete = True
                            await self.conversation_service.update_collection_data(
                                self._current_conversation_id,
                                symptom_collection.collection_data
                            )
                            await self.end_chat()
                            return "感謝您的配合。我們已經收集到足夠的資訊，照護團隊會盡快與您聯繫。祝您健康愉快！"
                    else:
                        # 如果所有症狀都有描述，直接結束
                        symptom_collection.is_complete = True
                        await self.conversation_service.update_collection_data(
                            self._current_conversation_id,
                            symptom_collection.collection_data
                        )
                        await self.end_chat()
                        return "感謝您的配合。您提供的症狀資訊已經完整，我們會盡快安排安寧照護團隊的人與您聯繫。祝您健康愉快！"

            # 獲取下一個問題
            response = result.get("next_question", "請告訴我更多信息。")
            
            # 記錄 AI 回應
            await self.conversation_service.add_message(
                conversation_id=self._current_conversation_id,
                content=response,
                message_type=MessageType.BOT
            )

            return response

        except Exception as e:
            logger.error(f"處理消息時發生錯誤: {str(e)}")
            error_message = "抱歉，處理您的消息時發生了錯誤。請重試。"
            await self.conversation_service.add_message(
                conversation_id=self._current_conversation_id,
                content=error_message,
                message_type=MessageType.SYSTEM
            )
            return error_message

    async def end_chat(self) -> None:
        """結束當前對話"""
        if self._current_conversation_id:
            await self.conversation_service.end_conversation(
                conversation_id=self._current_conversation_id,
                status=ConversationStatus.COMPLETED
            )
            self._current_conversation_id = None 