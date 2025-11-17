# 碳排放管理系统 - Docker 部署版本

这是一个基于 Django 的碳排放管理系统，使用 Docker + Nginx 进行容器化部署。

## ✨ 功能特性

- 📊 碳排放数据录入与管理
- 📈 数据可视化仪表板
- 🔢 碳排放系数管理
- 👥 多用户权限管理
- 🌐 中英文双语支持
- 📱 响应式设计

## 🏗️ 技术栈

- **后端**: Django 4.2
- **数据库**: SQLite (可升级为 PostgreSQL)
- **Web服务器**: Nginx
- **应用服务器**: Gunicorn
- **容器化**: Docker + Docker Compose
- **前端**: Bootstrap 5

## 📦 项目文件说明

### Docker 相关文件

- `Dockerfile` - Docker 镜像构建文件
- `docker-compose.yml` - Docker Compose 编排配置
- `docker-entrypoint.sh` - 容器启动脚本
- `.dockerignore` - Docker 构建忽略文件

### Nginx 配置

- `nginx/nginx.conf` - Nginx 主配置文件
- `nginx/conf.d/carbon_management.conf` - 应用专用配置

### 部署相关

- `deploy.sh` - 一键部署脚本
- `.env.example` - 环境变量模板
- `DEPLOYMENT.md` - 详细部署文档

## 🚀 快速开始

### 本地开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 运行迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

### Docker 部署（生产环境）

```bash
# 1. 构建并启动容器
chmod +x deploy.sh
./deploy.sh

# 2. 创建管理员账户
docker-compose exec web python manage.py createsuperuser

# 3. 访问应用
# 浏览器打开: http://localhost
```

详细部署说明请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📂 目录结构

```
carbon_management/
├── carbon_management/      # 项目配置
│   ├── settings.py        # Django 设置
│   ├── urls.py            # URL 路由
│   └── wsgi.py            # WSGI 配置
├── coefficients/          # 系数管理应用
├── data_entry/            # 数据录入应用
├── dashboard/             # 仪表板应用
├── templates/             # HTML 模板
├── static/                # 静态文件
├── media/                 # 用户上传文件
├── nginx/                 # Nginx 配置
├── Dockerfile             # Docker 配置
├── docker-compose.yml     # Docker Compose
└── requirements.txt       # Python 依赖
```

## 🔧 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 数据库配置

默认使用 SQLite，生产环境建议使用 PostgreSQL。

### 静态文件

```bash
# 收集静态文件
python manage.py collectstatic --noinput
```

## 🛠️ 维护命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 备份数据库
docker cp carbon_management_web:/app/db.sqlite3 ./backup.sqlite3
```

## 🔒 安全建议

1. 修改默认 SECRET_KEY
2. 设置 DEBUG=False
3. 配置正确的 ALLOWED_HOSTS
4. 使用 HTTPS（配置 SSL 证书）
5. 定期备份数据库
6. 更新依赖包

## 📊 性能优化

- 使用 PostgreSQL 替代 SQLite
- 配置 Redis 缓存
- 启用 Nginx Gzip 压缩
- 调整 Gunicorn workers 数量
- 使用 CDN 加速静态文件

## 🐛 常见问题

### 1. 静态文件无法加载

```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

### 2. 数据库迁移失败

```bash
docker-compose exec web python manage.py migrate --run-syncdb
```

### 3. 权限错误

```bash
sudo chown -R 1000:1000 media/ db.sqlite3
```

## 📝 开发指南

### 添加新应用

```bash
docker-compose exec web python manage.py startapp app_name
```

### 数据库迁移

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 运行测试

```bash
docker-compose exec web python manage.py test
```

## 📄 许可证

本项目仅供学习和研究使用。

## 👥 贡献

欢迎提交 Issue 和 Pull Request。

## 📞 联系方式

如有问题，请查看 [DEPLOYMENT.md](DEPLOYMENT.md) 中的故障排查部分。
