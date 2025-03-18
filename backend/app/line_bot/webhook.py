"""
Line Webhook 處理模組

此模組處理來自 Line 平台的 webhook 請求。
在本地開發環境中，此模組處於非活動狀態。
"""

from fastapi import APIRouter, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FollowEvent, UnfollowEvent
)
from app.core.config import settings
from app.core.logger import logger
from app.line_bot import is_line_bot_enabled

# 創建路由器但不立即註冊
router = APIRouter(prefix="/line", tags=["line"])

# Line Bot API 客戶端（僅在啟用時初始化）
line_bot_api: LineBotApi | None = None
handler: WebhookHandler | None = None

def initialize_line_bot():
    """
    初始化 Line Bot API 客戶端
    
    此函數應該在應用啟動時調用，且僅在正確配置了 Line Bot 時才會實際初始化。
    """
    global line_bot_api, handler
    
    if is_line_bot_enabled:
        line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
        handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        logger.info("Line Bot API 客戶端已初始化")
    else:
        logger.warning("Line Bot 未配置，webhook 端點將返回 503 錯誤") 