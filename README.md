# 【什么值得做】智能体

为自塾平台开发的独立推荐智能体，帮助塾员快速找到当前最值得做的3件事。

## 项目特点

- 🔥 **独立服务**：不修改zishu源码，作为独立服务运行
- 🎯 **智能推荐**：基于用户数据智能推荐最值得做的事情
- ⚡ **高性能**：多级缓存策略，响应时间 < 200ms
- 🔧 **可配置**：支持算法参数在线调优
- 📊 **可解释**：推荐结果可解释，提升用户信任度

## 系统架构

```
前端推荐卡片 → FastAPI服务 → 推荐引擎 → 数据聚合 → 自塾API
                  ↓
             Redis缓存 → 算法优化
```

## 项目结构

```
what-to-do-agent/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── core/        # 核心模块
│   │   ├── api/         # API路由
│   │   ├── services/    # 业务服务
│   │   └── models/      # 数据模型
│   ├── tests/           # 测试
│   └── requirements.txt
├── frontend/            # 前端组件
│   ├── components/      # Vue组件
│   └── assets/         # 静态资源
├── config/             # 配置文件
└── docs/              # 文档
```

## 快速开始

1. 启动后端服务：
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

2. 安装前端依赖：
```bash
cd frontend
npm install
npm run dev
```

3. 访问推荐服务：
- API文档：http://localhost:8080/docs
- 推荐接口：GET /api/v1/recommend/top3

## 核心功能

### 推荐类型
- 📚 **学习推荐**：即将DDL的课程、热门课程
- 🚀 **项目推荐**：适合的创新项目、任务认领
- 🎯 **目标推荐**：目标面谈、学时申报
- 💡 **能力提升**：技能认证、资料完善

### 算法特色
- **时间紧迫度**：DDL越近优先级越高
- **个人匹配度**：基于技能和兴趣匹配
- **重要程度**：系统级重要任务优先
- **成长价值**：长期发展价值评估

## API接口

### 获取Top3推荐
```http
GET /api/v1/recommend/top3
Authorization: Bearer {token}
```

### 响应格式
```json
{
  "code": 200,
  "data": {
    "recommendations": [
      {
        "id": "rec_001",
        "type": "COURSE_URGENT",
        "title": "完成《自塾Python》第5课",
        "description": "学习Python循环与条件语句",
        "action_text": "立即学习",
        "url": "/course/python-101#lesson-5",
        "score": 92,
        "estimated_time": "45分钟",
        "reasons": ["距离DDL还有2天", "入塾必修课程"]
      }
    ]
  }
}
```

## 开发计划

- [x] 项目架构设计
- [ ] 数据源对接
- [ ] 推荐算法实现
- [ ] 前端组件开发
- [ ] 缓存和优化
- [ ] 测试和部署

## 贡献指南

欢迎提交Issue和PR，共同完善这个智能推荐系统！