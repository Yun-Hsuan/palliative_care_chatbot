## Environment Variables Management Best Practices

### Directory Structure
```plaintext
project_root/
├── .env.example              # Template with all possible variables
├── .env                      # Only contains ENVIRONMENT selection
├── env-config/              # Not tracked in Git
│   ├── local/
│   │   └── .env            # Complete config for local development
│   ├── staging/
│   │   └── .env            # Complete config for staging
│   └── production/
│       └── .env            # Complete config for production
```

### Key Principles

1. **Complete Configuration Files**
   - Each environment has its own complete configuration file
   - No reliance on variable override mechanisms
   - All required variables are explicitly set in each environment

2. **Sensitive Information Management**
   - Sensitive data stored in `env-config/` directory
   - Directory excluded from Git tracking
   - Each environment maintains its own secrets

3. **Environment Selection**
   - Root `.env` only contains environment selection
   - No sensitive information in version control
   - Clear separation between environment selection and configuration

### Implementation

1. **Template File** (`.env.example`):
```env
# Project Information
PROJECT_NAME="Project Name"
STACK_NAME=project-stack

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethis
POSTGRES_DB=app

# Security
SECRET_KEY=changethis
```

2. **Root Environment File** (`.env`):
```env
ENVIRONMENT=local
```

3. **Environment-Specific Files** (`env-config/{environment}/.env`):
- Contains all necessary variables for the specific environment
- Includes sensitive information
- Not tracked in version control

### Usage

```bash
# Development with Docker Compose
docker compose --env-file ./env-config/local/.env up

# Development with FastAPI CLI (Local Development Server)
cd backend && set -a && source ../env-config/local/.env && set +a && fastapi dev app/main.py

# Staging
docker compose --env-file ./env-config/staging/.env up

# Production
docker compose --env-file ./env-config/production/.env up
```

### Required Environment Variables for Backend

The following environment variables are required when starting the backend service:

### Benefits

1. **Security**
   - Sensitive information isolated in non-versioned directory
   - Clear separation between public and private configurations
   - Environment-specific secrets management

2. **Maintainability**
   - Each environment is self-contained
   - No complex variable override chains
   - Easy to understand and modify configurations

3. **Reliability**
   - Reduced risk of configuration errors
   - No dependency on variable precedence
   - Clear validation of required variables

4. **Development Workflow**
   - Easy environment switching
   - Clear configuration templates
   - Simplified onboarding process

### Git Configuration

```gitignore
# Ignore environment configurations but keep examples
env-config/
!env-config/**/.env.example

# Keep root environment file template
.env.example
```

### Best Practices

1. Always maintain up-to-date `.env.example` files
2. Document all variables and their purposes
3. Use consistent naming conventions
4. Regular audit of sensitive information
5. Maintain separate secrets management for production

### Local Development Notes

1. **Docker vs FastAPI CLI**
   - Docker Compose for complete development environment (including database services)
     * Use `docker compose --env-file ./env-config/local/.env up` to start full environment
     * Automatically handles service dependencies (database, cache, etc.)
     * Suitable for full feature testing and production simulation
   
   - FastAPI CLI for local rapid development and debugging
     * Use `fastapi dev app/main.py` to start development server
     * Supports hot reload for automatic restart after code changes
     * Ideal for API development and quick debugging
   
   - When using FastAPI CLI, ensure:
     * All required environment variables are properly set
     * Dependent services (like database) are running
     * Python virtual environment is activated

2. **Environment Variable Validation**
   - Backend service validates required environment variables on startup
     * Uses Pydantic for environment variable validation
     * Ensures all required configurations are provided
     * Prevents runtime errors due to missing critical configs
   
   - Missing required environment variables will cause service startup failure
     * Check error messages for missing variables
     * Ensure env file contains all required configurations
     * Verify environment variables are properly loaded
   
   - Environment variable handling with FastAPI CLI
     * Use `set -a && source .env && set +a` to load environment variables
     * Ensure commands are executed in correct directory
     * Use `printenv` command to verify environment variables

3. **Development Workflow**
   - Initial Setup
     * Copy `.env.example` to `env-config/local/.env`
     * Modify configuration values as needed
     * Ensure database configuration is correct
    
   - Daily Development
     * Use FastAPI CLI for rapid development and debugging
     * Switch to Docker Compose when full environment is needed
     * Regularly update environment variable documentation
    
   - Debugging Tips
     * Leverage FastAPI CLI's auto-reload feature
     * Utilize FastAPI's interactive docs (/docs)
     * Switch between different startup methods as needed

This approach ensures:
- Secure handling of sensitive information
- Clear separation of concerns
- Easy environment management
- Reliable configuration across different deployments

## Chatbot Development Plan

### 1. 基礎對話功能實現
1. **對話初始化**
   - [ ] 實現 `/api/v1/conversations/start` 端點
   - [ ] 創建新的對話記錄
   - [ ] 設置初始對話狀態和類型

2. **消息處理**
   - [ ] 實現 `/api/v1/conversations/{conversation_id}/messages` 端點
   - [ ] 處理用戶輸入消息
   - [ ] 生成 AI 響應
   - [ ] 保存對話歷史

### 2. 症狀收集功能
1. **症狀記錄**
   - [ ] 實現症狀識別邏輯
   - [ ] 創建症狀記錄
   - [ ] 關聯症狀特徵收集

2. **智能問診流程**
   - [ ] 實現基於規則的問診邏輯
   - [ ] 處理相關症狀追蹤
   - [ ] 實現症狀嚴重程度評估

3. **數據驗證和存儲**
   - [ ] 實現症狀數據驗證
   - [ ] 保存完整症狀記錄
   - [ ] 更新對話狀態

### 3. AI 模型整合
1. **自然語言處理**
   - [ ] 集成 NLP 模型
   - [ ] 實現意圖識別
   - [ ] 實現實體提取

2. **對話管理**
   - [ ] 實現對話狀態追蹤
   - [ ] 管理多輪對話流程
   - [ ] 處理上下文相關性

### 4. 醫療邏輯實現
1. **症狀關聯規則**
   - [ ] 實現症狀關聯分析
   - [ ] 建立症狀特徵關係
   - [ ] 處理症狀優先級

2. **診斷建議生成**
   - [ ] 實現初步診斷邏輯
   - [ ] 生成診斷報告
   - [ ] 提供治療建議

### 5. 用戶界面整合
1. **API 端點完善**
   - [ ] 實現所有必要的 REST API
   - [ ] 添加 WebSocket 支持
   - [ ] 實現實時通訊

2. **前端整合**
   - [ ] 設計對話界面
   - [ ] 實現即時反饋
   - [ ] 添加錯誤處理

### 6. 安全性和性能
1. **安全措施**
   - [ ] 實現訪問控制
   - [ ] 添加數據驗證
   - [ ] 實現敏感信息保護

2. **性能優化**
   - [ ] 實現緩存機制
   - [ ] 優化數據庫查詢
   - [ ] 添加性能監控

### 當前開發重點

1. **第一階段：基礎對話功能**
   - 實現基本的對話初始化和消息處理
   - 建立對話管理機制
   - 完成基礎 API 端點

2. **技術堆棧確認**
   - FastAPI 後端框架
   - SQLModel 數據模型
   - PostgreSQL 數據庫
   - WebSocket 實時通訊
   - AI 模型集成（待定）

3. **下一步行動項目**
   - [ ] 創建對話控制器（ConversationController）
   - [ ] 實現消息處理服務（MessageService）
   - [ ] 建立 WebSocket 連接處理
   - [ ] 開發基礎 AI 響應邏輯

### API 端點設計

```python
# 對話管理
POST /api/v1/conversations/start
GET /api/v1/conversations/{conversation_id}
POST /api/v1/conversations/{conversation_id}/messages

# 症狀記錄
POST /api/v1/symptoms/record
GET /api/v1/symptoms/{symptom_id}
PUT /api/v1/symptoms/{symptom_id}

# 診斷相關
POST /api/v1/diagnoses/create
GET /api/v1/diagnoses/{diagnosis_id}
PUT /api/v1/diagnoses/{diagnosis_id}/status
```

### 開發注意事項

1. **代碼質量**
   - 遵循 Python 類型提示
   - 添加詳細的文檔字符串
   - 實現單元測試覆蓋

2. **安全考慮**
   - 實現適當的訪問控制
   - 保護敏感醫療信息
   - 記錄重要操作日誌

3. **可擴展性**
   - 使用模塊化設計
   - 實現清晰的接口
   - 準備好擴展新功能

## 系統架構更新

### 1. 整合服務架構

```plaintext
                                    Azure Services
                                    +------------------------+
                                    |                        |
LINE OA        FastAPI Backend      | - Azure OpenAI        |
+--------+     +--------------+     | - Azure Bot Service   |
|        |     |              |     | - Health Insights     |
| Line   +---->+ API Gateway  +---->|                      |
| Bot    |     |              |     |                      |
+--------+     +--------------+     |                      |
                     |             +------------------------+
                     |
                     v
               PostgreSQL DB
               +----------+
               |          |
               | Data     |
               | Storage  |
               +----------+
```

### 2. 核心組件

1. **Line OA 整合**
   - Line Messaging API 配置
   - Webhook 端點設置
   - 消息處理中間件

2. **Azure 服務整合**
   - Azure OpenAI 服務配置
   - Bot Service 設置
   - Health Insights API 整合

3. **後端服務**
   - 消息路由和處理
   - 對話狀態管理
   - 數據持久化

### 3. 環境變量需求

```env
# Line Bot Configuration
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_access_token

# Azure Configuration
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_BOT_SERVICE_KEY=your_bot_service_key
AZURE_HEALTH_INSIGHTS_KEY=your_health_insights_key

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethis
POSTGRES_DB=app
```

### 4. 開發順序調整

1. **Line Bot 基礎設置**
   - [ ] 配置 Line Channel
   - [ ] 實現 Webhook 端點
   - [ ] 基本消息處理

2. **Azure 服務整合**
   - [ ] 配置 Azure OpenAI
   - [ ] 設置 Bot Service
   - [ ] 整合 Health Insights

3. **對話流程實現**
   - [ ] 設計對話流程
   - [ ] 實現狀態管理
   - [ ] 整合醫療邏輯

### 5. API 端點修改

```python
# Line Bot Webhook
POST /api/v1/line/webhook

# Azure 服務整合
POST /api/v1/bot/message
GET /api/v1/health-insights/analyze

# 對話管理
GET /api/v1/conversations/{conversation_id}
PUT /api/v1/conversations/{conversation_id}/status
```

### 6. 實現步驟

1. **Line Bot 設置**
   ```python
   from linebot import (
       LineBotApi, WebhookHandler
   )
   from linebot.models import (
       MessageEvent, TextMessage, TextSendMessage
   )
   
   line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
   handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
   
   @router.post("/webhook")
   async def line_webhook(request: Request):
       signature = request.headers['X-Line-Signature']
       body = await request.body()
       handler.handle(body.decode(), signature)
       return 'OK'
   ```

2. **Azure OpenAI 整合**
   ```python
   from openai import AzureOpenAI
   
   client = AzureOpenAI(
       api_key=settings.AZURE_OPENAI_API_KEY,
       api_version="2024-02-15-preview",
       azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
   )
   ```

3. **Health Insights 整合**
   ```python
   async def analyze_symptoms(text: str):
       headers = {
           "Authorization": f"Bearer {settings.AZURE_HEALTH_INSIGHTS_KEY}",
           "Content-Type": "application/json"
       }
       async with httpx.AsyncClient() as client:
           response = await client.post(
               f"{settings.AZURE_HEALTH_INSIGHTS_ENDPOINT}/analyze",
               json={"text": text},
               headers=headers
           )
           return response.json()
   ```

### 7. 數據模型調整

1. **Line 用戶關聯**
   ```python
   class UserLineProfile(SQLModel, table=True):
       id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       user_id: UUID = Field(foreign_key="user.id")
       line_user_id: str = Field(unique=True, index=True)
       display_name: str
       picture_url: str | None
       status_message: str | None
   ```

2. **對話模型更新**
   ```python
   class Conversation(SQLModel, table=True):
       id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       line_user_id: str = Field(index=True)
       status: ConversationStatus
       last_message_timestamp: datetime
       context: dict = Field(default_factory=dict)
       azure_conversation_id: str | None
   ```

### 8. 開發注意事項

1. **安全性考慮**
   - Line Webhook 驗證
   - Azure 服務認證管理
   - 用戶數據保護

2. **性能優化**
   - 異步處理消息
   - 緩存 Azure 響應
   - 批量處理請求

3. **錯誤處理**
   - Line API 錯誤處理
   - Azure 服務異常處理
   - 網絡超時處理

4. **監控和日誌**
   - 對話狀態追蹤
   - Azure 服務調用監控
   - 錯誤日誌記錄

### 9. 測試策略

1. **單元測試**
   - Line 消息處理
   - Azure 服務調用
   - 數據模型驗證

2. **整合測試**
   - Line Webhook 測試
   - Azure 服務整合測試
   - 數據庫操作測試

3. **端到端測試**
   - 完整對話流程
   - 錯誤恢復機制
   - 性能測試

### 下一步行動項目

1. **環境設置**
   - [ ] 註冊 Line Developer 帳號
   - [ ] 創建 Azure 服務資源
   - [ ] 配置必要的環境變量

2. **基礎架構**
   - [ ] 實現 Line Webhook
   - [ ] 設置 Azure 服務客戶端
   - [ ] 創建數據模型

3. **核心功能**
   - [ ] 實現消息處理
   - [ ] 整合 Azure 服務
   - [ ] 實現對話流程

## Azure OpenAI 服務整合記錄 (2024-03-15)

### 1. 基礎設置與配置

1. **環境變數配置**
   ```env
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_ENDPOINT=https://aoai-dataclean-elifeec.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
   AZURE_OPENAI_VERSION=2024-05-01-preview
   ```

2. **配置管理優化**
   - 在 `env-config/local/.env` 中管理敏感配置
   - 通過 `settings.py` 統一管理配置項
   - 添加配置驗證和服務狀態檢查

### 2. 核心服務實現

1. **OpenAI 服務類**
   ```python
   class OpenAIService:
       def __init__(self):
           self.client = AzureOpenAI(
               azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
               api_key=settings.AZURE_OPENAI_API_KEY,
               api_version=settings.AZURE_OPENAI_VERSION
           )
   ```

2. **系統提示詞設計**
   - 實現結構化的醫療問診對話
   - 定義清晰的回應格式（JSON）
   - 包含症狀識別、嚴重程度評估等關鍵元素

3. **日誌系統建立**
   - 實現統一的日誌記錄
   - 支持錯誤追蹤和上下文記錄
   - 便於問題診斷和監控

### 3. 測試與驗證

1. **互動式測試工具**
   - 實現了簡單但實用的命令行測試界面
   - 支持持續對話測試
   - 格式化輸出提升可讀性

2. **測試功能包括**
   - 服務初始化驗證
   - API 調用測試
   - 響應格式驗證
   - 錯誤處理測試

### 4. 當前功能

1. **症狀分析**
   ```json
   {
       "identified_symptoms": ["症狀1", "症狀2"],
       "follow_up_questions": ["問題1", "問題2"],
       "severity_assessment": "嚴重程度描述",
       "recommendations": ["建議1", "建議2"]
   }
   ```

2. **交互體驗**
   - 自然語言輸入
   - 結構化輸出
   - 清晰的視覺呈現
   - 持續對話支持

### 5. 下一步計劃

1. **功能優化**
   - [ ] 優化系統提示詞
   - [ ] 改進回應的專業性
   - [ ] 添加更多醫療相關驗證

2. **架構擴展**
   - [ ] 實現對話歷史管理
   - [ ] 添加用戶會話狀態
   - [ ] 整合到 FastAPI 路由

3. **監控與維護**
   - [ ] 添加性能監控
   - [ ] 實現錯誤報告
   - [ ] 優化資源使用

### 6. 注意事項

1. **安全性考慮**
   - 敏感配置通過環境變數管理
   - API 密鑰嚴格保護
   - 錯誤信息安全處理

2. **最佳實踐**
   - 使用異步操作提高性能
   - 實現優雅的錯誤處理
   - 保持代碼模塊化