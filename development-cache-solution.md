# 開發環境緩存問題解決方案

## Vite 配置優化
```typescript
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [react(), TanStackRouterVite()],
  server: {
    hmr: {
      protocol: 'ws',
      host: 'localhost',
    },
    fs: {
      strict: true,
    },
    cors: true,
    host: '0.0.0.0',
    watch: {
      usePolling: true,
      interval: 1000,
    }
  },
})
```

## Docker Compose 配置
```yaml
services:
  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - CHOKIDAR_USEPOLLING=true
      - WATCHPACK_POLLING=true
```

## Package.json 開發腳本
```json
{
  "scripts": {
    "dev:clean": "vite --force",
    "dev:debug": "vite --debug"
  }
}
```

## 環境變數設置
在 `frontend/.env` 中添加：
```
VITE_DEV_MODE=true
VITE_API_BASE_URL=http://localhost:8000
```

## 開發調試命令
```bash
# 查看容器日誌
docker-compose logs -f frontend

# 查看容器狀態
docker-compose ps
```

## 瀏覽器開發工具設置
1. Network 頁籤：勾選 "Disable cache"
2. Application 頁籤：管理 Service Workers

## 最佳實踐建議
1. 使用 volume 掛載本地目錄
2. 確保容器內外的 node_modules 隔離
3. 使用 Docker 的 development 模式
4. 添加適當的日誌記錄
5. 使用 nodemon 監控文件變化

## 預期效果
- 提供更好的開發體驗
- 減少緩存問題
- 提供更多調試信息
- 加快開發-測試循環
- 方便定位問題 