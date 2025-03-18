"""
Azure OpenAI 服務整合

此模組處理與 Azure OpenAI 的所有互動，包括：
- 模型調用
- 提示詞管理
- 對話上下文處理

參考文檔：
https://learn.microsoft.com/zh-tw/azure/ai-services/openai/how-to/switching-endpoints
"""

from typing import Any, Dict, List, Optional
import os
import json
from openai import AsyncAzureOpenAI
from app.core.config import settings
from app.core.logger import logger
from . import is_aoai_enabled

class OpenAIService:
    def __init__(self):
        """初始化 Azure OpenAI 服務"""
        if not is_aoai_enabled:
            raise RuntimeError("Azure OpenAI 服務未配置")
        
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_VERSION
        )
        
        # 一般對話的系統提示詞
        self.system_prompt = """你是一個專業的安寧緩和醫療諮詢助手。
你的主要任務是：
1. 收集病人的症狀信息
2. 評估症狀的嚴重程度
3. 提供初步建議
4. 詢問相關的跟進問題

請以同理心和專業的態度與病人交流。回應需要考慮以下幾點：
1. 使用溫和、關懷的語氣
2. 避免使用過於專業的醫療術語
3. 適時表達理解和支持
4. 循序漸進地收集信息"""

        # 資料收集的提示詞
        self.collection_prompt = """你是一個專業的醫療諮詢助手，正在收集病人的基本信息。
你需要幫助填寫以下表單的空缺項目（null 值）：

{form_structure}

請注意：
1. 使用溫和、關懷的語氣與病人交流
2. 根據對話上下文，選擇最適合詢問的空缺項目
3. 如果用戶提供的信息不完整或不清楚，要進一步詢問
4. 如果用戶順便提供了其他項目的信息，也要記錄下來
5. 確保所有數值都在合理範圍內：
   - 年齡：0-120歲
   - 體溫：35-42度
   - 收縮壓：60-200 mmHg
   - 舒張壓：40-120 mmHg

你的回應必須包含以下 JSON 格式的信息：
{
    "updates": {
        // 本次對話中獲取到的所有更新信息
        // 例如：
        // "vital_status.age": 25,
        // "vital_status.gender": "male",
        // "symptom_1.symptom_name": "頭痛",
        // "symptom_1.symptom_status": "yes",
        // "symptom_1.symptom_details": "持續性鈍痛"
    },
    "next_question": "下一個要詢問的問題",
    "reasoning": "為什麼選擇問這個問題的簡短解釋"
}"""

    def _get_vital_collection_prompt(self, current_vital_status: Dict[str, Any]) -> str:
        """
        根據當前收集狀態生成動態提示詞
        """
        # 定義每個字段的中文名稱和預期值範圍
        field_info = {
            "age": {
                "name": "年齡",
                "unit": "歲",
                "range": "0-120"
            },
            "gender": {
                "name": "性別",
                "valid_values": ["male (男性)", "female (女性)", "other (其他)"]
            },
            "temperature": {
                "name": "體溫",
                "unit": "攝氏度",
                "range": "35-42"
            },
            "systolic_bp": {
                "name": "收縮壓",
                "unit": "mmHg",
                "range": "60-200"
            },
            "diastolic_bp": {
                "name": "舒張壓",
                "unit": "mmHg",
                "range": "40-120"
            }
        }

        # 找出所有缺失的字段
        missing_fields = [
            field for field in field_info.keys()
            if current_vital_status.get(field) is None
        ]

        # 生成提示詞
        prompt = """你是一個專業的醫療諮詢助手，正在收集病人的基本生命體徵信息。請注意：
1. 使用溫和、關懷的語氣與病人交流
2. 一次只詢問一個信息
3. 如果用戶提供的信息不完整或不清楚，要進一步詢問
4. 如果用戶順便提供了其他信息，也要記錄下來
5. 確保所有數值都在合理範圍內

當前已收集的信息：
"""
        # 添加當前狀態
        for field, value in current_vital_status.items():
            if value is not None:
                field_data = field_info[field]
                if field == "gender":
                    if value == "male":
                        value_str = "男性"
                    elif value == "female":
                        value_str = "女性"
                    else:
                        value_str = "其他"
                    prompt += f"- {field_data['name']}: {value_str}\n"
                else:
                    unit = field_data.get('unit', '')
                    prompt += f"- {field_data['name']}: {value} {unit}\n"

        prompt += "\n還需要收集的信息：\n"
        for field in missing_fields:
            field_data = field_info[field]
            if field == "gender":
                prompt += f"- {field_data['name']}: 可接受的值為 {', '.join(field_data['valid_values'])}\n"
            else:
                prompt += f"- {field_data['name']}: 預期範圍 {field_data['range']} {field_data.get('unit', '')}\n"

        prompt += """
你的任務是：
1. 分析用戶的回答
2. 提取相關的生命體徵信息
3. 決定下一個要詢問的信息
4. 生成友善的回應

你的回應必須包含以下 JSON 格式的信息：
{
    "vital_status": {
        "age": null | number,
        "gender": null | "male" | "female" | "other",
        "temperature": null | number,
        "systolic_bp": null | number,
        "diastolic_bp": null | number
    },
    "next_question": "下一個要詢問的問題",
    "is_complete": false | true,
    "current_focus": "當前正在詢問的字段名稱"
}"""

        return prompt

    async def analyze_symptoms(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] | None = None
    ) -> Dict[str, Any]:
        """
        分析用戶描述的症狀
        
        Args:
            user_message: 用戶輸入的症狀描述
            conversation_history: 之前的對話歷史
            
        Returns:
            Dict 包含：
            - identified_symptoms: 識別出的症狀列表
            - follow_up_questions: 需要追問的問題
            - severity_assessment: 嚴重程度評估
            - recommendations: 建議措施
        """
        try:
            # 構建消息列表
            messages = [{
                "role": "system",
                "content": self.system_prompt
            }]
            
            # 添加對話歷史（如果有）
            if conversation_history:
                messages.extend(conversation_history)
            
            # 添加當前用戶消息
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # 調用 Azure OpenAI
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"}
            )
            
            # 記錄原始回應
            logger.info(f"AOAI 原始回應: {response.choices[0].message.content}")
            
            # 解析回應
            result = response.choices[0].message.content
            return result
            
        except Exception as e:
            logger.error(f"Azure OpenAI 服務調用失敗: {str(e)}")
            raise

    async def chat_completion(
        self,
        messages: List[Dict[str, str]]
    ) -> str:
        """
        調用 Azure OpenAI API 進行對話
        """
        # 確保第一條消息是系統提示詞
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {
                "role": "system",
                "content": self.system_prompt
            })

        try:
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "text"}
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Azure OpenAI 服務調用失敗: {str(e)}")
            return f"抱歉，我現在無法正確回應。錯誤信息：{str(e)}"

    async def collect_vital_status(
        self,
        user_message: str,
        current_vital_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        從用戶消息中提取生命體徵信息
        
        Args:
            user_message: 用戶輸入的消息
            current_vital_status: 當前已收集的生命體徵信息（用於合併）
            
        Returns:
            Dict 包含更新後的 vital_status
        """
        try:
            # 構建消息列表
            messages = [
                {
                    "role": "system",
                    "content": self.collection_prompt.format(
                        form_structure=json.dumps(current_vital_status, ensure_ascii=False, indent=2)
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
            
            # 調用 Azure OpenAI
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # 記錄原始回應
            logger.info(f"AOAI 原始回應: {response.choices[0].message.content}")
            
            # 解析回應
            result = json.loads(response.choices[0].message.content)
            
            # 驗證更新值的合理性
            updates = result.get("updates", {})
            for key, value in updates.items():
                if key.startswith("vital_status."):
                    field = key.split(".")[-1]
                    if field == "age" and (value < 0 or value > 120):
                        updates[key] = None
                    elif field == "temperature" and (value < 35 or value > 42):
                        updates[key] = None
                    elif field == "systolic_bp" and (value < 60 or value > 200):
                        updates[key] = None
                    elif field == "diastolic_bp" and (value < 40 or value > 120):
                        updates[key] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Azure OpenAI 服務調用失敗: {str(e)}")
            raise

    async def process_collection(
        self,
        user_message: str,
        current_collection: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        處理生命體徵資料收集對話
        """
        try:
            vital_prompt = """你是一個專業的醫療諮詢助手，正在收集病人的基本生命體徵信息。

當前收集狀態：
{current_state}

請注意：
1. 使用溫和、關懷的語氣與病人交流
2. 一次只詢問一個信息
3. 如果用戶提供的信息不完整或不清楚，要進一步詢問
4. 如果用戶順便提供了其他信息，也要記錄下來
5. 確保所有數值都在合理範圍內

你的回應必須是完全符合以下格式的 JSON：
{{
    "updates": {{
        "vital_status": {{
            "age": null,        // 年齡 (0-120)
            "gender": null,     // 性別 (male/female/other)
            "temperature": null,  // 體溫 (35-42)
            "systolic_bp": null,  // 收縮壓 (60-200)
            "diastolic_bp": null  // 舒張壓 (40-120)
        }}
    }},
    "next_question": "下一個要詢問的問題",
    "is_complete": false,
    "reasoning": "解釋為什麼選擇這個問題，以及對當前狀況的分析"
}}

注意：
1. 數值必須是數字，不要加引號
2. 未獲得的信息保持 null
3. 性別必須是 "male"、"female" 或 "other" 其中之一
4. 所有字段名都必須完全匹配上述格式"""

            # 確保 vital_status 存在
            if "vital_status" not in current_collection:
                current_collection["vital_status"] = {}

            # 添加當前狀態到提示詞
            prompt = vital_prompt.format(
                current_state=json.dumps(current_collection["vital_status"], ensure_ascii=False, indent=2)
            )
            
            # 構建消息列表
            messages = [
                {
                    "role": "system",
                    "content": prompt
                }
            ]
            
            # 添加對話歷史
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # 添加當前用戶消息
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # 記錄發送給 AOAI 的消息
            logger.info("準備發送給 AOAI 的消息列表:")
            for msg in messages:
                logger.info(f"Role: {msg['role']}, Content: {msg['content'][:100]}...")
            
            try:
                # 記錄開始調用 API
                logger.info("開始調用 AOAI API...")
                
                # 調用 Azure OpenAI
                response = await self.client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800,
                    response_format={"type": "json_object"}
                )
                
                # 記錄 API 調用成功
                logger.info("AOAI API 調用成功")
                
                # 記錄原始回應
                logger.info(f"AOAI 原始回應: {response.choices[0].message.content}")
                
                try:
                    # 嘗試解析 JSON
                    result = json.loads(response.choices[0].message.content)
                    
                    # 記錄解析後的數據
                    logger.info(f"JSON 解析結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    # 驗證基本結構
                    if not isinstance(result, dict):
                        raise ValueError("回應必須是一個 JSON 對象")
                    
                    # 驗證必要字段
                    required_fields = ["updates", "next_question", "is_complete"]
                    missing_fields = [field for field in required_fields if field not in result]
                    if missing_fields:
                        raise ValueError(f"缺少必要字段: {', '.join(missing_fields)}")
                    
                    # 驗證 vital_status 結構
                    if "vital_status" not in result.get("updates", {}):
                        result["updates"]["vital_status"] = {}
                    
                    vital_status = result["updates"]["vital_status"]
                    
                    # 確保所有必要的字段都存在
                    required_vital_fields = ["age", "gender", "temperature", "systolic_bp", "diastolic_bp"]
                    for field in required_vital_fields:
                        if field not in vital_status:
                            vital_status[field] = None
                    
                    # 驗證並轉換數值
                    if vital_status.get("age") is not None:
                        try:
                            age = int(float(str(vital_status["age"]).strip()))
                            if 0 <= age <= 120:
                                vital_status["age"] = age
                            else:
                                vital_status["age"] = None
                        except (ValueError, TypeError):
                            vital_status["age"] = None
                    
                    if vital_status.get("gender") is not None:
                        if vital_status["gender"] not in ["male", "female", "other", None]:
                            vital_status["gender"] = None
                    
                    if vital_status.get("temperature") is not None:
                        try:
                            temp = float(str(vital_status["temperature"]).strip())
                            if 35 <= temp <= 42:
                                vital_status["temperature"] = temp
                            else:
                                vital_status["temperature"] = None
                        except (ValueError, TypeError):
                            vital_status["temperature"] = None
                    
                    # 檢查是否同時包含收縮壓和舒張壓的信息
                    systolic_bp = vital_status.get("systolic_bp")
                    diastolic_bp = vital_status.get("diastolic_bp")
                    
                    # 如果有收縮壓或舒張壓的更新
                    if systolic_bp is not None or diastolic_bp is not None:
                        try:
                            # 檢查是否為完整血壓格式（如 "150/90"）
                            if isinstance(systolic_bp, str) and "/" in systolic_bp:
                                bp_parts = systolic_bp.split("/")
                                if len(bp_parts) == 2:
                                    try:
                                        sys_bp = int(float(bp_parts[0].strip()))
                                        dia_bp = int(float(bp_parts[1].strip()))
                                        if 60 <= sys_bp <= 200 and 40 <= dia_bp <= 120:
                                            vital_status["systolic_bp"] = sys_bp
                                            vital_status["diastolic_bp"] = dia_bp
                                    except (ValueError, TypeError):
                                        pass
                            else:
                                # 單獨處理收縮壓
                                if systolic_bp is not None:
                                    try:
                                        sys_bp = int(float(str(systolic_bp).strip()))
                                        if 60 <= sys_bp <= 200:
                                            vital_status["systolic_bp"] = sys_bp
                                        else:
                                            vital_status["systolic_bp"] = None
                                    except (ValueError, TypeError):
                                        vital_status["systolic_bp"] = None
                                    
                                    # 單獨處理舒張壓
                                    if diastolic_bp is not None:
                                        try:
                                            dia_bp = int(float(str(diastolic_bp).strip()))
                                            if 40 <= dia_bp <= 120:
                                                vital_status["diastolic_bp"] = dia_bp
                                            else:
                                                vital_status["diastolic_bp"] = None
                                        except (ValueError, TypeError):
                                            vital_status["diastolic_bp"] = None
                        except Exception as e:
                            logger.error(f"處理血壓數據時發生錯誤: {str(e)}")
                    
                    # 檢查是否所有生命體徵都已收集
                    result["is_complete"] = all(
                        vital_status.get(field) is not None
                        for field in ["age", "gender", "temperature", "systolic_bp", "diastolic_bp"]
                    )
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析錯誤: {str(e)}")
                    logger.error(f"問題數據: {response.choices[0].message.content}")
                    return {
                        "updates": {"vital_status": {}},
                        "next_question": "抱歉，我無法正確理解您的回答。請再次告訴我病患的年齡。",
                        "is_complete": False,
                        "reasoning": "JSON 解析錯誤，重新收集年齡信息"
                    }
            
            except Exception as e:
                logger.error(f"AOAI API 調用失敗: {str(e)}")
                return {
                    "updates": {"vital_status": {}},
                    "next_question": "抱歉，系統暫時無法處理您的請求。請稍後再試。",
                    "is_complete": False,
                    "reasoning": f"API 調用錯誤: {str(e)}"
                }
        
        except Exception as e:
            logger.error(f"處理收集過程時發生錯誤: {str(e)}")
            return {
                "updates": {"vital_status": {}},
                "next_question": "抱歉，系統處理時發生錯誤。請重新告訴我病患的基本信息。",
                "is_complete": False,
                "reasoning": "系統錯誤，重新開始收集信息"
            }

    async def analyze_symptoms_and_generate_next_question(
        self,
        collection_data: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        分析當前收集到的所有資訊，生成下一個問題
        """
        try:
            analysis_prompt = """你是一個專業的醫療諮詢助手，正在分析病人的所有資訊並決定下一步該詢問什麼。

當前收集到的資訊：
{collection_data}

最近的對話歷史：
{conversation_history}

請按照以下步驟分析並決定下一個問題：

1. 首先，檢查所有現有症狀的完整性：
   - 檢查每個症狀的 null 值
   - 優先處理症狀狀態為 "yes" 但其他字段為 null 的症狀
   - 按照以下順序補充症狀信息：
     a. 症狀狀態（如果為 null）
     b. 嚴重程度（如果為 null）
     c. 持續時間（如果為 null）
     d. 具體描述（如果為 null）

2. 如果所有現有症狀的信息都完整，再考慮是否需要詢問新的症狀：
   - 分析現有症狀的關聯性
   - 考慮可能的伴隨症狀
   - 根據症狀的嚴重程度和緊急程度決定優先順序

3. 生成問題時需要考慮：
   - 問題的具體性和可回答性
   - 使用溫和、關懷的語氣
   - 避免重複詢問已經得到明確答案的問題
   - 根據用戶之前的回答方式調整提問方式

你的回應必須是完全符合以下格式的 JSON：
{{
    "updates": {{
        "symptom_x": {{  // 如果發現新的可能症狀，使用下一個可用的編號
            "symptom_name": string,    // 推測的症狀名稱
            "symptom_status": "null",  // 新推測的症狀狀態一律設為 null
            "severity": null,
            "duration": null,
            "description": null
        }}
    }},
    "next_question": string,  // 下一個要詢問的問題，必須具體且針對性強
    "reasoning": string,      // 為什麼選擇問這個問題的解釋，包含目前的收集進度和對話脈絡考慮
    "is_complete": boolean,   // 是否已經收集到足夠的資訊
    "current_symptom": string,  // 當前正在詢問的症狀名稱
    "question_count": number    // 當前症狀已問的問題數量
}}

注意事項：
1. 優先處理現有症狀的 null 值
2. 確保問題具體且容易回答
3. 使用溫和、關懷的語氣
4. 在 reasoning 中說明當前的收集進度和選擇原因
5. 根據用戶的回答方式調整提問的具體程度"""

            # 構建消息列表
            messages = [
                {
                    "role": "system",
                    "content": analysis_prompt.format(
                        collection_data=json.dumps(collection_data, ensure_ascii=False, indent=2),
                        conversation_history=self._format_conversation_history(conversation_history)
                    )
                }
            ]
            
            # 如果有對話歷史，添加到消息列表中
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # 調用 Azure OpenAI
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.7,  # 提高溫度以增加回答的多樣性
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # 解析回應
            result = json.loads(response.choices[0].message.content)
            
            # 驗證必要字段
            required_fields = ["updates", "next_question", "reasoning", "is_complete", "current_symptom", "question_count"]
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise ValueError(f"缺少必要字段: {', '.join(missing_fields)}")
            
            return result
            
        except Exception as e:
            logger.error(f"分析症狀並生成問題時發生錯誤: {str(e)}")
            return {
                "updates": {},
                "next_question": "請告訴我更多關於您的症狀。",
                "reasoning": "發生錯誤，返回通用問題",
                "is_complete": False,
                "current_symptom": "",
                "question_count": 0
            }

    def _format_conversation_history(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """格式化對話歷史記錄，用於提示詞中"""
        if not conversation_history:
            return "無對話歷史"
        
        formatted_history = []
        for msg in conversation_history[-5:]:  # 只取最近的5條對話
            role = "助手" if msg["role"] == "assistant" else "用戶"
            formatted_history.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted_history)

    async def process_symptom_collection(
        self,
        user_message: str,
        current_collection: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        處理症狀收集對話
        """
        try:
            symptom_prompt = """你是一個專業的醫療諮詢助手，正在收集病人的症狀信息。

當前收集到的症狀：
{current_symptoms}

請分析用戶的回答，更新或添加症狀信息。每個症狀需要收集：
- 症狀名稱
- 症狀狀態（yes/no）
- 嚴重程度（輕度/中度/重度）
- 持續時間
- 具體描述

特別注意：
1. 如果用戶明確表示"沒有"某個症狀，應該：
   - 將該症狀的 symptom_status 設為 "no"
   - 立即轉向詢問其他症狀
   - 不要重複詢問已經被否定的症狀
2. 如果發現症狀記錄中有 null 值，應該優先追問這些信息
3. 如果發現重複的症狀記錄，應該合併它們的信息
4. 如果症狀描述為 null，應該詢問具體的症狀表現

你的回應必須是完全符合以下格式的 JSON：
{{
    "updates": {{
        "symptom_x": {{  // x是阿拉伯數字編號，如果是新症狀，使用下一個可用的編號
            "symptom_name": string,
            "symptom_status": "yes" | "no",  // 如果用戶說"沒有"，必須設為 "no"
            "severity": "mild" | "moderate" | "severe",
            "duration": string,
            "description": string
        }}
    }},
    "current_phase": "symptoms",
    "next_question": "下一個要詢問的問題，優先詢問 null 值的症狀信息",
    "reasoning": "解釋為什麼選擇這個問題，以及對當前狀況的分析"
}}"""

            # 構建消息列表
            messages = [
                {
                    "role": "system",
                    "content": symptom_prompt.format(
                        current_symptoms=json.dumps(
                            {k: v for k, v in current_collection.items() if k.startswith("symptom_")},
                            ensure_ascii=False,
                            indent=2
                        )
                    )
                }
            ]
            
            # 添加對話歷史
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # 添加當前用戶消息
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # 調用 Azure OpenAI 處理用戶回答
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # 解析回應
            result = json.loads(response.choices[0].message.content)
            
            # 更新 collection_data
            if "updates" in result:
                current_collection.update(result["updates"])
            
            # 分析當前狀態並生成下一個問題
            analysis_result = await self.analyze_symptoms_and_generate_next_question(current_collection, conversation_history)
            
            # 合併結果
            result.update({
                "updates": {**result.get("updates", {}), **analysis_result.get("updates", {})},
                "next_question": analysis_result["next_question"],
                "is_complete": analysis_result["is_complete"],
                "current_phase": "symptoms"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"處理症狀收集過程時發生錯誤: {str(e)}")
            return {
                "updates": {},
                "next_question": "抱歉，系統處理時發生錯誤。請重新告訴我您的症狀。",
                "is_complete": False,
                "current_phase": "symptoms"
            }

    async def check_user_consent(
        self,
        user_message: str
    ) -> Dict[str, Any]:
        """
        判斷用戶是否同意進行問診對話
        
        Args:
            user_message: 用戶的回應文字
            
        Returns:
            Dict 包含：
            - consent: bool, 是否同意
            - confidence: float, 判斷的確信度 (0-1)
            - response_type: str, 回應類型 ("explicit_agree"/"explicit_disagree"/"unclear")
            - next_action: str, 建議的下一步動作
        """
        try:
            consent_prompt = """你是一個負責判斷用戶是否同意進行醫療諮詢的助手。

用戶已經收到以下說明：
"這是一個協助安寧照護團隊理解您或所照顧患者的AI Chatbot。接下來我會詢問一些基本訊息還有病症，如果您準備好了，請跟我說 OK 或是準備好了。如果你不同意的話，請說不同意，我們便會終止。"

請分析用戶的回應，判斷其是否同意進行諮詢。

你的回應必須是有效的 JSON 格式，包含以下字段：
{
    "consent": true/false,          # 用戶是否同意
    "confidence": 0.0-1.0,         # 判斷的確信度
    "response_type": string,        # "explicit_agree" 明確同意 / "explicit_disagree" 明確不同意 / "unclear" 不明確
    "next_action": string,          # 建議的下一步動作
    "reasoning": string             # 簡短說明做出此判斷的原因
}"""

            messages = [
                {
                    "role": "system",
                    "content": consent_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.3,  # 使用較低的溫度以獲得更確定的判斷
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 驗證結果格式
            required_fields = ["consent", "confidence", "response_type", "next_action"]
            if not all(field in result for field in required_fields):
                raise ValueError("AI 回應缺少必要字段")
            
            return result
            
        except Exception as e:
            logger.error(f"判斷用戶同意時發生錯誤: {str(e)}")
            # 如果發生錯誤，返回保守的判斷結果
            return {
                "consent": False,
                "confidence": 0.0,
                "response_type": "unclear",
                "next_action": "請重新詢問用戶是否同意進行諮詢",
                "reasoning": "處理過程中發生錯誤，建議重新確認"
            }

    async def check_identity(
        self,
        user_message: str
    ) -> Dict[str, Any]:
        """
        確認用戶身份（本人/家屬/機構照護者）
        
        Args:
            user_message: 用戶的回應文字
            
        Returns:
            Dict 包含：
            - identity: str, 確認的身份 ("self"/"family"/"caregiver")
            - confidence: float, 判斷的確信度 (0-1)
            - is_valid: bool, 是否為有效回應
            - next_question: str, 下一個問題
        """
        try:
            identity_prompt = """你是一個負責確認用戶身份的助手。用戶應該會選擇以下三種身份之一：
1. 本人
2. 家屬
3. 機構照護者

請分析用戶的回應，判斷其身份。如果用戶的回答不明確或不在這三個選項中，應該要求重新選擇。

你的回應必須是有效的 JSON 格式，包含以下字段：
{
    "identity": string,        # "self" 本人 / "family" 家屬 / "caregiver" 機構照護者 / "unknown" 無法判斷
    "confidence": 0.0-1.0,    # 判斷的確信度
    "is_valid": boolean,      # 是否為有效回應
    "next_question": string,  # 下一個問題（根據身份調整稱謂）
    "reasoning": string       # 簡短說明做出此判斷的原因
}"""

            messages = [
                {
                    "role": "system",
                    "content": identity_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 驗證結果格式
            required_fields = ["identity", "confidence", "is_valid", "next_question"]
            if not all(field in result for field in required_fields):
                raise ValueError("AI 回應缺少必要字段")
            
            # 如果是有效回應，根據身份設置下一個問題
            if result["is_valid"]:
                if result["identity"] == "self":
                    result["next_question"] = "好的，請問您的年齡是？"
                elif result["identity"] == "family":
                    result["next_question"] = "好的，請問病患的年齡是？"
                elif result["identity"] == "caregiver":
                    result["next_question"] = "好的，請問被照護者的年齡是？"
            else:
                result["next_question"] = "抱歉，我需要您明確選擇身份類型：\n(1) 本人\n(2) 家屬\n(3) 機構照護者"
            
            return result
            
        except Exception as e:
            logger.error(f"確認身份時發生錯誤: {str(e)}")
            return {
                "identity": "unknown",
                "confidence": 0.0,
                "is_valid": False,
                "next_question": "抱歉，我需要您明確選擇身份類型：\n(1) 本人\n(2) 家屬\n(3) 機構照護者",
                "reasoning": "處理過程中發生錯誤，請重新選擇"
            }

    async def check_vital_status_confirmation(
        self,
        user_message: str
    ) -> Dict[str, Any]:
        """
        檢查用戶是否確認生命體徵信息正確
        
        Args:
            user_message: 用戶的回應文字
            
        Returns:
            Dict 包含：
            - is_confirmed: bool, 是否確認正確
            - next_question: str, 如果需要修改，下一個要問的問題
        """
        try:
            confirmation_prompt = """你是一個負責確認用戶回應的助手。
請判斷用戶是否確認信息正確，或是指出需要修改的項目。

用戶可能的回應類型：
1. 確認正確：例如"正確"、"沒問題"、"對"等
2. 需要修改：例如"年齡不對"、"血壓要改"等
3. 不明確：需要再次確認

你的回應必須是有效的 JSON 格式，包含以下字段：
{
    "is_confirmed": boolean,       # 是否確認正確
    "field_to_modify": string,    # 需要修改的字段（age/gender/temperature/blood_pressure）
    "next_question": string,      # 下一個要問的問題
    "reasoning": string           # 簡短說明做出此判斷的原因
}"""

            messages = [
                {
                    "role": "system",
                    "content": confirmation_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 如果需要修改，生成相應的問題
            if not result.get("is_confirmed", False):
                field = result.get("field_to_modify")
                if field == "age":
                    result["next_question"] = "請重新告訴我病患的年齡："
                elif field == "gender":
                    result["next_question"] = "請重新選擇病患的性別（男性/女性/其他）："
                elif field == "temperature":
                    result["next_question"] = "請重新告訴我病患的體溫（35-42°C）："
                elif field == "blood_pressure":
                    result["next_question"] = "請重新告訴我病患的血壓（收縮壓/舒張壓，例如：120/80）："
                else:
                    result["next_question"] = "請告訴我哪項信息需要修改？"
            
            return result
            
        except Exception as e:
            logger.error(f"確認生命體徵信息時發生錯誤: {str(e)}")
            return {
                "is_confirmed": False,
                "next_question": "抱歉，我沒有聽清楚。請告訴我信息是否正確，或是哪項需要修改？",
                "reasoning": "處理過程中發生錯誤，需要重新確認"
            }

    async def analyze_vital_signs(
        self,
        vital_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析生命體徵數據並生成適當的症狀詢問提示
        
        Args:
            vital_status: 包含生命體徵數據的字典
            
        Returns:
            Dict 包含：
            - updates: 根據生命體徵發現的症狀
            - next_question: 下一個要詢問的問題
            - is_complete: 是否完成分析
            - current_phase: 當前階段
        """
        try:
            analysis_prompt = """你是一個專業的醫療諮詢助手，正在分析病人的生命體徵數據。

當前的生命體徵數據：
{vital_signs}

請分析這些數據，找出任何異常情況，並根據發現的異常轉換為相應的症狀記錄。

請特別注意：
1. 體溫異常：
   - 發燒 (≥ 38°C)
   - 低溫 (≤ 35.5°C)
2. 血壓異常：
   - 高血壓 (收縮壓 ≥ 140 或舒張壓 ≥ 90)
   - 低血壓 (收縮壓 ≤ 90 或舒張壓 ≤ 60)
3. 年齡相關風險

你的回應必須是完全符合以下格式的 JSON：
{{
    "updates": {{
        "symptom_1": {{  // 從 symptom_1 開始編號
            "symptom_name": string,     // 發現的症狀名稱（例如：發燒、低血壓等）
            "symptom_status": "yes"     // 必須是 "yes"，因為這是從生命體徵分析得出的確定症狀
        }},
        "symptom_2": {{
            // 如果發現第二個症狀，使用相同格式
        }}
        // 依此類推...
    }},
    "next_question": string,  // 根據發現的異常，詢問這些症狀的嚴重程度、持續時間等詳細信息
    "is_complete": false,     // 永遠是 false，因為還需要進一步收集症狀詳情
    "current_phase": "symptoms"
}}"""

            # 構建消息列表
            messages = [
                {
                    "role": "system",
                    "content": analysis_prompt.format(
                        vital_signs=json.dumps(vital_status, ensure_ascii=False, indent=2)
                    )
                }
            ]
            
            # 調用 Azure OpenAI
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # 解析回應
            result = json.loads(response.choices[0].message.content)
            
            # 驗證必要字段
            required_fields = ["updates", "next_question", "is_complete", "current_phase"]
            if not all(field in result for field in required_fields):
                raise ValueError("AI 回應缺少必要字段")
            
            # 驗證症狀格式
            if "updates" in result:
                for symptom_key, symptom_data in result["updates"].items():
                    if not symptom_key.startswith("symptom_"):
                        continue
                    
                    # 只保留確定的字段
                    required_symptom_fields = ["symptom_name", "symptom_status"]
                    for field in required_symptom_fields:
                        if field not in symptom_data:
                            symptom_data[field] = None
                    
                    # 確保 symptom_status 是 "yes"
                    symptom_data["symptom_status"] = "yes"
                    
                    # 移除其他字段
                    keys_to_remove = [k for k in symptom_data.keys() if k not in required_symptom_fields]
                    for k in keys_to_remove:
                        del symptom_data[k]
            
            return result
            
        except Exception as e:
            logger.error(f"分析生命體徵時發生錯誤: {str(e)}")
            return {
                "updates": {},
                "next_question": "請告訴我您最近是否有任何不適或症狀？",
                "is_complete": False,
                "current_phase": "symptoms"
            }