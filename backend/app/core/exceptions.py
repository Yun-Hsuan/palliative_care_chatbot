class BaseError(Exception):
    """基礎錯誤類"""
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)

class SymptomCollectionError(BaseError):
    """症狀收集相關錯誤的基礎類"""
    pass

class CollectionNotFoundError(SymptomCollectionError):
    """找不到症狀收集記錄"""
    pass

class CollectionExistsError(SymptomCollectionError):
    """症狀收集記錄已存在"""
    pass

class SymptomLimitExceededError(SymptomCollectionError):
    """症狀數量超過限制"""
    pass

class InvalidVitalSignsError(SymptomCollectionError):
    """無效的生命體徵數據"""
    pass

class SymptomNotFoundError(SymptomCollectionError):
    """找不到指定的症狀"""
    pass 