"""
AI 服務整合模組

此模組整合了各種 AI 服務，包括：
- Azure OpenAI (AOAI) 服務
- Azure Health Insights 服務 (待實現)
- 自定義的問診邏輯

主要功能：
1. 智能問診
   - 症狀識別和分析
   - 智能追問
   - 風險評估

2. 醫療知識處理
   - 症狀關聯分析
   - 醫療術語標準化
   - 健康建議生成

3. 對話管理
   - 上下文維護
   - 對話流程控制
   - 意圖識別
"""

from app.core.config import settings

# 服務狀態檢查
is_aoai_enabled = bool(
    settings.AZURE_OPENAI_API_KEY and 
    settings.AZURE_OPENAI_ENDPOINT and
    settings.AZURE_OPENAI_DEPLOYMENT_NAME
)

# TODO: 等待 Health Insights 服務實現
# is_health_insights_enabled = bool(
#     settings.AZURE_HEALTH_INSIGHTS_KEY and 
#     settings.AZURE_HEALTH_INSIGHTS_ENDPOINT
# ) 