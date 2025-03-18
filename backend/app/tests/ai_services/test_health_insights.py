"""
測試 Azure Health Insights 服務整合
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.ai_services.health_insights import HealthInsightsService

@pytest.fixture
def mock_health_insights_response():
    """模擬 Health Insights API 響應"""
    return {
        "entities": [
            {
                "text": "咳嗽",
                "category": "Symptom",
                "confidence": 0.95
            },
            {
                "text": "呼吸困難",
                "category": "Symptom",
                "confidence": 0.92
            }
        ],
        "relationships": [
            {
                "source": "咳嗽",
                "target": "呼吸困難",
                "type": "RelatedTo"
            }
        ],
        "assertions": [
            {
                "text": "咳嗽",
                "type": "Present",
                "certainty": "Positive"
            }
        ]
    }

@pytest.mark.asyncio
async def test_analyze_text_success(mock_health_insights_response):
    """測試文本分析功能 - 成功案例"""
    with patch('httpx.AsyncClient') as mock_client:
        # 設置模擬客戶端
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = mock_health_insights_response
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # 初始化服務
        service = HealthInsightsService()
        
        # 執行測試
        result = await service.analyze_text("我最近一直咳嗽，而且感覺呼吸有點困難")
        
        # 驗證結果
        assert isinstance(result, dict)
        assert "entities" in result
        assert "relationships" in result
        assert "assertions" in result
        assert len(result["entities"]) == 2
        assert result["entities"][0]["text"] == "咳嗽"
        
        # 驗證 API 調用
        mock_instance.post.assert_called_once()
        call_args = mock_instance.post.call_args
        assert "analyze" in call_args[0][0]
        assert call_args[1]["headers"]["Content-Type"] == "application/json"

@pytest.mark.asyncio
async def test_analyze_text_api_error():
    """測試文本分析功能 - API 錯誤處理"""
    with patch('httpx.AsyncClient') as mock_client:
        # 設置模擬客戶端拋出異常
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(side_effect=httpx.HTTPError("API Error"))
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # 初始化服務
        service = HealthInsightsService()
        
        # 驗證異常處理
        with pytest.raises(Exception) as exc_info:
            await service.analyze_text("測試文本")
        
        assert "API Error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_standardize_symptoms():
    """測試症狀標準化功能"""
    service = HealthInsightsService()
    symptoms = ["咳嗽", "頭痛"]
    
    # 目前這個方法是待實現的，所以應該返回 None
    result = await service.standardize_symptoms(symptoms)
    assert result is None

@pytest.mark.asyncio
async def test_assess_risk():
    """測試風險評估功能"""
    service = HealthInsightsService()
    symptoms = [
        {"original": "咳嗽", "standard": "Cough", "code": "R05"},
        {"original": "發燒", "standard": "Fever", "code": "R50.9"}
    ]
    
    # 目前這個方法是待實現的，所以應該返回 None
    result = await service.assess_risk(symptoms)
    assert result is None

def test_service_initialization_no_config():
    """測試服務初始化 - 配置缺失"""
    with patch('app.ai_services.health_insights.is_health_insights_enabled', False):
        with pytest.raises(RuntimeError) as exc_info:
            HealthInsightsService()
        
        assert "Health Insights 服務未配置" in str(exc_info.value) 