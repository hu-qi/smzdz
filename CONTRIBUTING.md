# 贡献指南

感谢您对【什么值得做】智能体项目的兴趣！我们欢迎所有形式的贡献，包括但不限于：

- 🐛 报告 Bug
- 💡 提出新功能建议  
- 📝 改进文档
- 🔧 提交代码修复或新功能
- 🧪 编写测试用例
- 📊 性能优化

## 📋 开始之前

在开始贡献之前，请：

1. **阅读项目文档**：确保了解项目的目标和架构
2. **查看现有 Issues**：避免重复工作
3. **遵循开发规范**：保持代码风格的一致性

## 🚀 如何贡献

### 报告 Bug

1. 在 [Issues](../../issues) 中搜索是否已有相同问题
2. 如果没有，请使用 Bug 报告模板创建新 Issue
3. 提供详细的重现步骤和环境信息
4. 如果可能，请提供错误日志和截图

### 提出功能请求

1. 查看现有的功能请求，避免重复
2. 使用功能请求模板描述您的想法
3. 解释为什么这个功能对用户有价值
4. 如果可能，提供使用场景和技术建议

### 提交代码

#### 1. 设置开发环境

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/YOUR_USERNAME/what-to-do-agent.git
cd what-to-do-agent

# 2. 创建开发分支
git checkout -b feature/your-feature-name

# 3. 安装依赖
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

#### 2. 开发规范

**代码风格**
- Python: 遵循 PEP 8 规范
- JavaScript/TypeScript: 使用 ESLint 和 Prettier
- 提交信息: 使用清晰的提交信息

**项目结构**
- 遵循无侵入式设计规范，不修改 zishu 源码
- 后端使用 FastAPI 框架
- 前端使用 Vue 3 框架
- 通过 `.env` 配置文件管理环境变量

**测试要求**
- 新功能必须包含测试用例
- 确保所有测试通过
- 保持测试覆盖率

#### 3. 提交流程

```bash
# 1. 确保代码符合规范
# 运行测试
cd backend
python -m pytest tests/

# 检查代码风格
flake8 app/
black app/ --check

# 2. 提交更改
git add .
git commit -m "feat: 添加新的推荐类型"

# 3. 推送到您的分支
git push origin feature/your-feature-name

# 4. 创建 Pull Request
```

## 📝 Pull Request 指南

### PR 标题格式
使用以下前缀之一：
- `feat:` 新功能
- `fix:` Bug 修复  
- `docs:` 文档更新
- `style:` 代码格式修改
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或工具变动

### PR 描述模板

```markdown
## 📝 变更说明
简要描述此 PR 的内容

## 🔧 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 性能优化
- [ ] 重构
- [ ] 测试

## 🧪 测试
- [ ] 已添加测试用例
- [ ] 所有测试通过
- [ ] 手动测试完成

## 📋 检查列表
- [ ] 代码遵循项目规范
- [ ] 已更新相关文档
- [ ] 已测试核心功能
- [ ] 无破坏性变更（或已说明）

## 🔗 相关 Issue
Closes #[issue number]
```

## 🔧 开发环境设置

### 后端开发
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发服务器
uvicorn app.main:app --reload --port 8080
```

### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 测试
```bash
# 后端测试
cd backend
python -m pytest tests/ -v

# 前端测试
cd frontend
npm run test
```

## 🎯 开发重点领域

我们特别欢迎在以下领域的贡献：

### 推荐算法优化
- 改进推荐准确性
- 优化算法性能
- 增加新的推荐类型

### 用户体验改进
- 前端界面优化
- 响应速度提升
- 移动端适配

### 系统稳定性
- 错误处理完善
- 日志系统优化
- 监控和报警

### 文档和测试
- API 文档完善
- 用户指南编写
- 测试覆盖率提升

## 📞 联系我们

如果您有任何问题或需要帮助：

1. 创建 [Issue](../../issues) 进行讨论
2. 查看项目 [Wiki](../../wiki)
3. 参与 [Discussions](../../discussions)

## 🏆 贡献者

感谢所有为项目做出贡献的开发者！

## 📜 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下许可。