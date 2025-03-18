"""
Line Bot 整合模組

此模組包含所有與 Line Bot 相關的功能，包括：
- Webhook 處理
- 消息處理
- 事件處理
- Line Bot API 調用

注意：此模組在本地開發環境中預設為禁用狀態。
只有在部署環境中，且正確配置了 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 後才會啟用。
"""

from app.core.config import settings

# 檢查是否啟用 Line Bot 功能
is_line_bot_enabled = settings.line_bot_enabled 