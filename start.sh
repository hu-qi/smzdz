#!/bin/bash

# 什么值得做智能体启动脚本

echo "🎯 启动什么值得做智能体服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    exit 1
fi

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 建议在虚拟环境中运行"
    echo "创建虚拟环境: python3 -m venv venv"
    echo "激活虚拟环境: source venv/bin/activate"
fi

# 进入后端目录
cd "$(dirname "$0")/backend" || exit 1

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 找不到 requirements.txt"
    exit 1
fi

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置必要的环境变量"
fi

# 运行测试（可选）
if [ "$1" == "--test" ]; then
    echo "🧪 运行测试..."
    python -m pytest tests/ -v
    if [ $? -ne 0 ]; then
        echo "❌ 测试失败"
        exit 1
    fi
fi

# 启动服务
echo "🚀 启动推荐服务..."
echo "API文档地址: http://localhost:8080/docs"
echo "健康检查: http://localhost:8080/api/v1/health"
echo "按 Ctrl+C 停止服务"

# 启动FastAPI服务
python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    --log-level info