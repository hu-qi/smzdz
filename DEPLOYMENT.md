# 部署说明

## 本地开发部署

### 1. 环境准备
```bash
# 克隆项目
git clone <repository_url>
cd what-to-do-agent

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 2. 配置环境
```bash
# 复制环境配置
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 启动服务
```bash
# 使用启动脚本
chmod +x ../start.sh
../start.sh

# 或直接启动
uvicorn app.main:app --reload --port 8080
```

### 4. 验证服务
- 健康检查: http://localhost:8080/api/v1/health
- API文档: http://localhost:8080/docs
- 推荐接口: http://localhost:8080/api/v1/recommend/top3

## Docker部署

### 1. 构建镜像
```bash
# 构建推荐服务镜像
docker build -t what-to-do-agent:latest .

# 使用docker-compose启动全套服务
docker-compose up -d
```

### 2. 验证部署
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs recommendation-api

# 健康检查
curl http://localhost:8080/api/v1/health
```

## 生产环境部署

### 1. 服务器要求
- CPU: 2核以上
- 内存: 4GB以上
- 存储: 20GB以上
- 操作系统: Ubuntu 20.04+

### 2. 环境配置
```bash
# 生产环境配置
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING

# Redis配置
REDIS_HOST=your-redis-host
REDIS_PASSWORD=your-redis-password

# API配置
ZISHU_API_BASE=https://zishu.co/api
```

### 3. 反向代理配置（Nginx）
```nginx
# /etc/nginx/sites-available/what-to-do-agent
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 系统服务配置（systemd）
```ini
# /etc/systemd/system/what-to-do-agent.service
[Unit]
Description=What To Do Agent Service
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/what-to-do-agent/backend
Environment=PATH=/opt/what-to-do-agent/venv/bin
ExecStart=/opt/what-to-do-agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl enable what-to-do-agent
sudo systemctl start what-to-do-agent
sudo systemctl status what-to-do-agent
```

## 监控和维护

### 1. 日志监控
```bash
# 查看应用日志
tail -f /var/log/what-to-do-agent/app.log

# 使用journalctl查看systemd日志
journalctl -u what-to-do-agent -f
```

### 2. 性能监控
- 监控API响应时间
- 监控缓存命中率
- 监控内存和CPU使用率
- 监控Redis连接状态

### 3. 备份策略
- 定期备份Redis数据
- 备份应用配置文件
- 监控磁盘空间

## 集成到自塾官网

### 1. 前端集成
```vue
<!-- 在 zishu/frontend/src/views/Home.vue 中添加 -->
<template>
  <Layout>
    <Header2 />
    <Main />
    
    <!-- 添加推荐卡片 -->
    <RecommendationCard 
      v-if="userStore.isLoggedIn" 
      :api-base="recommendationApiBase"
    />
    
    <Footer />
  </Layout>
</template>

<script setup>
import RecommendationCard from '@/components/RecommendationCard.vue'

const recommendationApiBase = 'http://localhost:8080/api/v1'
</script>
```

### 2. API代理配置
```javascript
// vite.config.ts 或 nginx 配置
proxy: {
  '/recommendation-api': {
    target: 'http://localhost:8080',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/recommendation-api/, '/api/v1')
  }
}
```

## 故障排除

### 常见问题
1. **Redis连接失败**: 检查Redis服务状态和连接配置
2. **API调用超时**: 检查自塾API的网络连接
3. **认证失败**: 确认token格式和有效性
4. **推荐结果为空**: 检查用户数据是否正常获取

### 调试方法
```bash
# 检查服务状态
curl http://localhost:8080/api/v1/health

# 检查性能统计
curl http://localhost:8080/api/v1/admin/performance

# 查看详细日志
docker-compose logs -f recommendation-api
```