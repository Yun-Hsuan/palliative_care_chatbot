"""
測試 Azure OpenAI 服務整合

此模組測試與 Azure OpenAI 服務的整合，包括：
- 服務初始化
- API 調用
- 錯誤處理
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.ai_services.openai_service import OpenAIService
from app.core.config import Settings

@pytest.fixture
def mock_openai_response():
    """模擬 OpenAI API 響應"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""
                {
                    "identified_symptoms": ["咳嗽", "呼吸困難"],
                    "follow_up_questions": ["咳嗽持續多久了？", "是否有痰？"],
                    "severity_assessment": "中度",
                    "recommendations": ["建議及時就醫", "保持臥床休息"]
                }
                """
            )
        )
    ]
    return mock_response

# 模擬成功的 API 響應
MOCK_SUCCESSFUL_RESPONSE = MagicMock(
    choices=[
        MagicMock(
            message=MagicMock(
                content='''
                {
                    "identified_symptoms": ["發燒", "咳嗽"],
                    "follow_up_questions": ["症狀持續多久了？", "有服用任何藥物嗎？"],
                    "severity_assessment": "輕度症狀",
                    "recommendations": ["多休息", "多喝水"]
                }
                '''
            )
        )
    ]
)

def test_service_initialization_with_valid_config():
    """測試服務使用有效配置時的初始化"""
    with patch("app.ai_services.openai_service.settings", Settings(
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com",
        AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
        AZURE_OPENAI_VERSION="2024-05-01-preview"
    )):
        service = OpenAIService()
        assert service.client is not None
        assert isinstance(service.system_prompt, dict)
        assert service.system_prompt["role"] == "system"

def test_service_initialization_without_config():
    """測試服務在缺少配置時的初始化"""
    with patch("app.ai_services.openai_service.settings", Settings(
        AZURE_OPENAI_API_KEY=None,
        AZURE_OPENAI_ENDPOINT=None,
        AZURE_OPENAI_DEPLOYMENT_NAME=None
    )), pytest.raises(RuntimeError) as exc_info:
        OpenAIService()
    assert "Azure OpenAI 服務未配置" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_symptoms_success():
    """測試症狀分析功能 - 成功案例"""
    with patch("app.ai_services.openai_service.settings", Settings(
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com",
        AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
        AZURE_OPENAI_VERSION="2024-05-01-preview"
    )):
        service = OpenAIService()
        
        # 模擬 OpenAI 客戶端響應
        service.client.chat.completions.create = MagicMock(return_value=MOCK_SUCCESSFUL_RESPONSE)
        
        result = service.analyze_symptoms("我最近感覺喉嚨痛，有點發燒")
        
        # 驗證 API 調用參數
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args[1]
        assert call_args["model"] == "test-deployment"
        assert call_args["temperature"] == 0.7
        assert call_args["max_tokens"] == 800
        assert call_args["response_format"] == {"type": "json_object"}
        
        # 驗證返回結果
        assert "identified_symptoms" in result
        assert "follow_up_questions" in result
        assert "severity_assessment" in result
        assert "recommendations" in result

@pytest.mark.asyncio
async def test_analyze_symptoms_with_history():
    """測試帶有對話歷史的症狀分析"""
    with patch("app.ai_services.openai_service.settings", Settings(
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com",
        AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
        AZURE_OPENAI_VERSION="2024-05-01-preview"
    )):
        service = OpenAIService()
        service.client.chat.completions.create = MagicMock(return_value=MOCK_SUCCESSFUL_RESPONSE)
        
        conversation_history = [
            {"role": "user", "content": [{"type": "text", "text": "我感覺不太舒服"}]},
            {"role": "assistant", "content": "請描述一下具體症狀"}
        ]
        
        result = service.analyze_symptoms(
            "我最近感覺喉嚨痛，有點發燒",
            conversation_history=conversation_history
        )
        
        # 驗證歷史消息是否被正確包含
        call_args = service.client.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        assert len(messages) == 4  # system prompt + 2 history messages + current message
        assert messages[1:3] == conversation_history

@pytest.mark.asyncio
async def test_analyze_symptoms_api_error():
    """測試 API 調用失敗的情況"""
    with patch("app.ai_services.openai_service.settings", Settings(
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com",
        AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
        AZURE_OPENAI_VERSION="2024-05-01-preview"
    )):
        service = OpenAIService()
        
        # 模擬 API 錯誤
        service.client.chat.completions.create = MagicMock(
            side_effect=Exception("API 調用失敗")
        )
        
        with pytest.raises(Exception) as exc_info:
            service.analyze_symptoms("我最近感覺喉嚨痛，有點發燒")
        
        assert "API 調用失敗" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_symptoms_no_history():
    """測試症狀分析功能 - 無對話歷史"""
    with patch('openai.AzureOpenAI', autospec=True) as mock_client:
        # 設置模擬客戶端
        instance = mock_client.return_value
        instance.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="{}"))]
        ))
        
        # 初始化服務
        service = OpenAIService()
        
        # 執行測試
        result = await service.analyze_symptoms("我頭痛", None)
        
        # 驗證 API 調用
        instance.chat.completions.create.assert_called_once()
        call_args = instance.chat.completions.create.call_args[1]
        assert len(call_args["messages"]) == 2  # system + current only

@pytest.mark.asyncio
async def test_analyze_symptoms_api_error():
    """測試症狀分析功能 - API 錯誤處理"""
    with patch('openai.AzureOpenAI', autospec=True) as mock_client:
        # 設置模擬客戶端拋出異常
        instance = mock_client.return_value
        instance.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        # 初始化服務
        service = OpenAIService()
        
        # 驗證異常處理
        with pytest.raises(Exception) as exc_info:
            await service.analyze_symptoms("測試消息", None)
        
        assert str(exc_info.value) == "API Error" 