#!/bin/bash

# 碳排放管理系统部署脚本

set -e

echo "碳排放管理系统 - Docker 部署脚本"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 停止并删除旧容器
echo "停止旧容器..."
docker-compose down || true

# 构建镜像
echo "构建 Docker 镜像..."
docker-compose build

# 启动容器
echo "启动容器..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查容器状态
echo "检查容器状态..."
docker-compose ps

echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="
echo "访问地址: http://localhost"
echo "管理后台: http://localhost/admin"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
echo "========================================="
