#!/bin/bash

# Ubuntu 服务器初始化和部署脚本
# 适用于 Ubuntu 18.04+

set -e

echo "========================================="
echo "碳排放管理系统 - 服务器环境配置"
echo "========================================="

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 更新系统
echo "更新系统包..."
apt-get update
apt-get upgrade -y

# 安装必要工具
echo "安装必要工具..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release

# 检查 Docker 是否已安装
if ! command -v docker &> /dev/null; then
    echo "Docker 未安装，开始安装..."
    
    # 添加 Docker 官方 GPG 密钥
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # 设置 Docker 仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装 Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # 启动 Docker
    systemctl start docker
    systemctl enable docker
    
    echo "Docker 安装完成"
else
    echo "Docker 已安装，版本: $(docker --version)"
fi

# 检查 Docker Compose 是否已安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose 安装完成"
else
    echo "Docker Compose 已安装"
fi

# 配置防火墙
echo "配置防火墙..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw status

# 创建部署目录
echo "创建部署目录..."
DEPLOY_DIR="/opt/carbon_management"
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

echo ""
echo "========================================="
echo "环境配置完成！"
echo "========================================="
echo ""
echo "下一步操作："
echo "1. 上传项目文件到: $DEPLOY_DIR"
echo "2. 进入项目目录: cd $DEPLOY_DIR"
echo "3. 运行部署脚本: ./deploy.sh"
echo ""
echo "或者使用以下命令上传项目："
echo "scp -r carbon_management/ user@server-ip:$DEPLOY_DIR/"
echo "========================================="
