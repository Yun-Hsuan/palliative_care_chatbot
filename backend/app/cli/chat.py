import asyncio
import sys
from typing import Optional
import aioconsole

from app.db.session import async_session
from app.services.conversation_service import ConversationService
from app.ai_services.openai_service import OpenAIService
from app.services.chat_handler import ChatHandler

async def chat_session():
    """開始一個聊天會話"""
    # 創建數據庫會話
    async with async_session() as db:
        # 初始化服務
        conversation_service = ConversationService(db)
        openai_service = OpenAIService()
        chat_handler = ChatHandler(conversation_service, openai_service)

        try:
            # 開始對話
            welcome_message = await chat_handler.start_chat()
            print("\n" + welcome_message)

            while True:
                # 獲取用戶輸入
                user_input = await aioconsole.ainput("\n您: ")
                
                if not user_input.strip():
                    continue

                # 處理用戶消息
                response = await chat_handler.handle_message(user_input)
                print("\n助手: " + response)

                # 檢查是否結束對話
                if user_input.lower() == 'exit':
                    break

        except KeyboardInterrupt:
            print("\n檢測到中斷信號，正在結束對話...")
            await chat_handler.end_chat()
        except Exception as e:
            print(f"\n發生錯誤: {str(e)}")
            await chat_handler.end_chat()

def main():
    """主入口函數"""
    try:
        asyncio.run(chat_session())
    except KeyboardInterrupt:
        print("\n程序已終止")
        sys.exit(0)

if __name__ == "__main__":
    main() 