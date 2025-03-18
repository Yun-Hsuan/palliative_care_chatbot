"""
日誌配置模組

此模組提供統一的日誌記錄功能，包括：
- 控制台輸出
- 文件記錄
- 錯誤追蹤
"""

import logging
import sys
from typing import Any

# 創建 logger
logger = logging.getLogger("palliative_care_chatbot")

# 設置日誌級別
logger.setLevel(logging.INFO)

# 創建控制台處理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 設置日誌格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

# 添加處理器到 logger
logger.addHandler(console_handler)

# 提供一個更簡潔的接口
def log_error(e: Exception, context: dict[str, Any] | None = None) -> None:
    """記錄錯誤信息
    
    Args:
        e: 異常對象
        context: 額外的上下文信息
    """
    error_message = f"錯誤: {str(e)}"
    if context:
        error_message += f"\n上下文: {context}"
    logger.error(error_message, exc_info=True) 