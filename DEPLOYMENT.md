# 碳排放管理系统 - Docker + Nginx 部署指南

## 📋 前置要求

- Ubuntu Server (18.04+)
- Docker (已安装)
- Docker Compose
- 至少 2GB RAM
- 至少 10GB 磁盘空间

## 🚀 快速部署

### 1. 上传项目到服务器

```bash
# 在本地打包项目
cd /Users/kai/Desktop/practice/2025/10/08_Ruby/Ruby_code
tar -czf carbon_management.tar.gz carbon_management/

# 上传到服务器（替换为你的服务器IP）
scp carbon_management.tar.gz user@your-server-ip:/home/user/

# 在服务器上解压
ssh user@your-server-ip
cd /home/user
tar -xzf carbon_management.tar.gz
cd carbon_management
```

### 2. 安装 Docker Compose（如果未安装）

```bash
# 下载 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 3. 配置环境变量（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env

# 修改以下内容：
# - SECRET_KEY: 生成新的密钥
# - ALLOWED_HOSTS: 添加你的域名或IP
```

### 4. 生成 Django Secret Key

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 5. 部署应用

```bash
# 方式一：使用部署脚本（推荐）
chmod +x deploy.sh
./deploy.sh

# 方式二：手动部署
docker-compose build
docker-compose up -d
```

### 6. 创建管理员账户

```bash
# 进入 web 容器
docker-compose exec web python manage.py createsuperuser

# 按提示输入用户名、邮箱和密码
```

### 7. 访问应用

- 主页: `http://your-server-ip`
- 管理后台: `http://your-server-ip/admin`

## 📁 项目结构

```
carbon_management/
├── Dockerfile                 # Docker 镜像配置
├── docker-compose.yml         # Docker Compose 配置
├── docker-entrypoint.sh       # 容器启动脚本
├── deploy.sh                  # 一键部署脚本
├── nginx/                     # Nginx 配置
│   ├── nginx.conf            # Nginx 主配置
│   └── conf.d/
│       └── carbon_management.conf  # 应用配置
├── .env.example              # 环境变量模板
└── DEPLOYMENT.md             # 本文档
```

## 🔧 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看 web 服务日志
docker-compose logs -f web

# 查看 nginx 日志
docker-compose logs -f nginx
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启 web 服务
docker-compose restart web

# 重启 nginx
docker-compose restart nginx
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

### 更新应用

```bash
# 拉取最新代码
git pull  # 如果使用 Git

# 重新构建并启动
docker-compose down
docker-compose build
docker-compose up -d

# 运行数据库迁移
docker-compose exec web python manage.py migrate

# 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput
```

### 数据库操作

```bash
# 运行迁移
docker-compose exec web python manage.py migrate

# 创建迁移文件
docker-compose exec web python manage.py makemigrations

# 进入 Django shell
docker-compose exec web python manage.py shell

# 导出数据
docker-compose exec web python manage.py dumpdata > backup.json

# 导入数据
docker-compose exec web python manage.py loaddata backup.json
```

### 备份数据库

```bash
# 备份 SQLite 数据库
docker cp carbon_management_web:/app/db.sqlite3 ./backup_$(date +%Y%m%d).sqlite3

# 恢复数据库
docker cp ./backup_20231117.sqlite3 carbon_management_web:/app/db.sqlite3
docker-compose restart web
```

## 🔒 HTTPS 配置（可选）

### 1. 获取 SSL 证书

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
sudo apt-get update
sudo apt-get install certbot

# 获取证书（替换为你的域名）
sudo certbot certonly --standalone -d your-domain.com
```

### 2. 配置证书路径

```bash
# 创建 SSL 目录
mkdir -p nginx/ssl

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### 3. 启用 HTTPS

编辑 `nginx/conf.d/carbon_management.conf`，取消 HTTPS 部分的注释，然后重启：

```bash
docker-compose restart nginx
```

## 🛡️ 安全建议

1. **修改 SECRET_KEY**: 在生产环境中使用强随机密钥
2. **设置 DEBUG=False**: 确保在 settings.py 中关闭调试模式
3. **配置 ALLOWED_HOSTS**: 只允许特定域名访问
4. **使用 HTTPS**: 配置 SSL 证书保护数据传输
5. **定期备份**: 设置自动备份数据库和媒体文件
6. **更新依赖**: 定期更新 Python 包和 Docker 镜像
7. **防火墙配置**: 只开放必要的端口（80, 443）

```bash
# 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📊 性能优化

### 1. 调整 Gunicorn Workers

编辑 `docker-entrypoint.sh`，根据服务器 CPU 核心数调整：

```bash
# workers = (2 × CPU核心数) + 1
--workers 4
```

### 2. 启用 Nginx 缓存

在 `nginx/conf.d/carbon_management.conf` 中添加缓存配置。

### 3. 使用 PostgreSQL（推荐）

对于生产环境，建议使用 PostgreSQL 替代 SQLite：

```yaml
# 在 docker-compose.yml 中添加
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: carbon_management
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🐛 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查容器状态
docker-compose ps
```

### 静态文件无法加载

```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

### 数据库错误

```bash
# 重新运行迁移
docker-compose exec web python manage.py migrate --run-syncdb
```

### 权限问题

```bash
# 修复文件权限
sudo chown -R 1000:1000 media/ db.sqlite3
```

## 📞 技术支持

如有问题，请检查：
1. Docker 和 Docker Compose 版本
2. 服务器资源使用情况（CPU、内存、磁盘）
3. 日志文件中的错误信息
4. 防火墙和网络配置

## 📝 更新日志

- **v1.0.0** (2024-11-17): 初始版本，支持 Docker + Nginx 部署
