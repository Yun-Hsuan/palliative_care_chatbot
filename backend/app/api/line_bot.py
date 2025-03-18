from fastapi import APIRouter, Request, HTTPException, Depends
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from typing import Dict, Any
import json
from app.core.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.chat_handler import ChatHandler
from app.services.conversation_service import ConversationService
from app.ai_services.openai_service import OpenAIService
from app.db.session import get_session

router = APIRouter()

# 檢查 LINE Bot 配置
print("=== LINE Bot Configuration Check ===")
print(f"LINE_CHANNEL_ACCESS_TOKEN: {settings.LINE_CHANNEL_ACCESS_TOKEN[:10]}..." if settings.LINE_CHANNEL_ACCESS_TOKEN else "LINE_CHANNEL_ACCESS_TOKEN: Not set")
print(f"LINE_CHANNEL_SECRET: {settings.LINE_CHANNEL_SECRET[:10]}..." if settings.LINE_CHANNEL_SECRET else "LINE_CHANNEL_SECRET: Not set")
print(f"LINE Bot enabled: {settings.line_bot_enabled}")
print("==================================")

if not settings.line_bot_enabled:
    logger.warning("LINE Bot is not properly configured. Some features may not work.")

# 初始化 LINE Bot API 和 WebhookHandler
try:
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
    logger.info("LINE Bot API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LINE Bot API: {str(e)}")
    raise

# 存儲用戶的 ChatHandler 實例
user_chat_handlers: Dict[str, ChatHandler] = {}

# 依賴注入
async def get_chat_handler(session: AsyncSession = Depends(get_session)):
    conversation_service = ConversationService(session)
    openai_service = OpenAIService()
    return ChatHandler(conversation_service, openai_service)

@router.post("/webhook")
async def callback(request: Request, chat_handler: ChatHandler = Depends(get_chat_handler)):
    # 獲取 X-Line-Signature header 值
    signature = request.headers.get('X-Line-Signature', '')

    # 獲取請求體作為文本
    body = await request.body()
    body_text = body.decode('utf-8')
    
    # 解析請求體以獲取事件資訊
    try:
        body_json = json.loads(body_text)
        events = body_json.get("events", [])
        
        # 記錄接收到的事件
        logger.info(f"Received LINE webhook events: {json.dumps(events, indent=2)}")
        
        for event in events:
            # 獲取事件來源類型
            source_type = event.get("source", {}).get("type")
            
            # 只處理來自用戶的消息
            if source_type != "user":
                logger.info(f"Ignoring event from source type: {source_type}")
                continue
                
            # 獲取用戶 ID
            user_id = event.get("source", {}).get("userId")
            if not user_id:
                logger.warning("Received event without user ID")
                continue
                
            logger.info(f"Processing event for user: {user_id}")
            
            # 如果是文字消息事件
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                message_text = event.get("message", {}).get("text", "")
                reply_token = event.get("replyToken")
                
                try:
                    # 檢查是否為 EXIT 命令
                    if message_text.upper() == "EXIT":
                        if user_id in user_chat_handlers:
                            # 結束當前對話
                            await user_chat_handlers[user_id].end_chat()
                            # 移除 ChatHandler
                            del user_chat_handlers[user_id]
                            logger.info(f"Ended chat session for user: {user_id}")
                            response = "對話已結束。如果您想開始新的對話，請直接發送消息。"
                        else:
                            response = "目前沒有進行中的對話。"
                    else:
                        # 檢查用戶是否已有 ChatHandler
                        if user_id not in user_chat_handlers:
                            logger.info(f"Creating new chat handler for user: {user_id}")
                            user_chat_handlers[user_id] = chat_handler
                            # 開始新的對話
                            response = await chat_handler.start_chat(user_id)
                        else:
                            # 使用現有的 ChatHandler
                            response = await user_chat_handlers[user_id].handle_message(
                                message=message_text,
                                user_id=user_id
                            )
                    
                    # 回覆消息
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=response)
                    )
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="抱歉，系統處理您的消息時發生錯誤，請稍後再試。")
                    )
        
        # 處理 webhook body
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error in webhook callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": "OK"} 