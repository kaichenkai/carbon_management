#!/bin/bash

echo "=========================================="
echo "碳排放管理系统 - 初始化脚本"
echo "Carbon Emission Management System - Setup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "创建虚拟环境 (Creating virtual environment)..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
    echo ""
fi

# Activate virtual environment
echo "激活虚拟环境 (Activating virtual environment)..."
source venv/bin/activate
echo "✓ 虚拟环境已激活"
echo ""

# Install dependencies
echo "安装依赖包 (Installing dependencies)..."
pip install -r requirements.txt
echo "✓ 依赖包安装完成"
echo ""

# Create necessary directories
echo "创建必要目录 (Creating directories)..."
mkdir -p media
mkdir -p locale
mkdir -p static
echo "✓ 目录创建完成"
echo ""

# Run migrations
echo "执行数据库迁移 (Running migrations)..."
python manage.py makemigrations
python manage.py migrate
echo "✓ 数据库迁移完成"
echo ""

# Create superuser prompt
echo "=========================================="
echo "现在需要创建超级管理员账号"
echo "Now creating superuser account"
echo "=========================================="
python manage.py createsuperuser

echo ""
echo "=========================================="
echo "✓ 初始化完成！"
echo "✓ Setup completed!"
echo "=========================================="
echo ""
echo "下一步 (Next steps):"
echo "1. 运行开发服务器: python manage.py runserver"
echo "   Run development server: python manage.py runserver"
echo ""
echo "2. 访问系统: http://127.0.0.1:8000/"
echo "   Access system: http://127.0.0.1:8000/"
echo ""
echo "3. 访问管理后台: http://127.0.0.1:8000/admin/"
echo "   Access admin: http://127.0.0.1:8000/admin/"
echo ""
echo "4. 在管理后台创建酒店和用户"
echo "   Create hotels and users in admin panel"
echo ""
