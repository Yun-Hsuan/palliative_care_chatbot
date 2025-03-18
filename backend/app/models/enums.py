from enum import Enum, IntEnum

class ConversationType(str, Enum):
    """對話類型"""
    SYMPTOM_COLLECTION = "symptom_collection"  # 症狀收集
    GENERAL = "general"                        # 一般對話

class ConversationStatus(str, Enum):
    """對話狀態"""
    ACTIVE = "active"          # 進行中
    COMPLETED = "completed"    # 已完成
    INTERRUPTED = "interrupted"  # 已中斷

class MessageType(str, Enum):
    """消息類型"""
    USER = "user"        # 用戶消息
    SYSTEM = "system"    # 系統消息
    BOT = "bot"         # 機器人回應

class SymptomStatus(str, Enum):
    """症狀狀態"""
    NULL = "null"      # 未記錄
    YES = "yes"       # 有此症狀
    NO = "no"         # 無此症狀 