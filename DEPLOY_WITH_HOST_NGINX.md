# 使用宿主机 Nginx 部署指南

当服务器上已经有 Nginx 运行时，使用此方案部署。

## 📋 部署架构

```
客户端 → 宿主机 Nginx (80/443) → Docker 容器 (127.0.0.1:8000) → Django 应用
```

## 🚀 部署步骤

### 1. 在服务器上部署 Docker 容器

```bash
cd /root/carbon_management

# 启动 Docker 容器（只运行 Django，不运行 Nginx）
docker-compose up -d

# 检查容器状态
docker-compose ps

# 应该看到 carbon_management_web 容器在运行
```

### 2. 收集静态文件到项目目录

```bash
# 确保静态文件在宿主机可访问
docker-compose exec web python manage.py collectstatic --noinput

# 检查静态文件目录
ls -la /root/carbon_management/staticfiles/
```

### 3. 配置宿主机 Nginx

```bash
# 备份现有配置（如果需要）
cp /etc/nginx/conf.d/yagao.online.conf /etc/nginx/conf.d/yagao.online.conf.backup

# 复制新配置
cp nginx-host.conf /etc/nginx/conf.d/carbon_management.conf

# 或者直接编辑现有配置
nano /etc/nginx/conf.d/yagao.online.conf
```

### 4. 更新 Nginx 配置内容

将 `/etc/nginx/conf.d/yagao.online.conf` 修改为：

```nginx
upstream django_carbon {
    server 127.0.0.1:8000;
}

server {
    server_name yagao.online;
    listen 443 ssl;
    ssl_certificate /etc/ssl/yagao.online/cert.pem;
    ssl_certificate_key /etc/ssl/yagao.online/key.pem;

    charset utf-8;
    client_max_body_size 20M;

    # 访问日志
    access_log /var/log/nginx/carbon_access.log;
    error_log /var/log/nginx/carbon_error.log;

    # 静态文件
    location /static/ {
        alias /root/carbon_management/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias /root/carbon_management/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Django 应用
    location / {
        proxy_pass http://django_carbon;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name yagao.online;
    return 301 https://$server_name$request_uri;
}
```

### 5. 测试并重启 Nginx

```bash
# 测试 Nginx 配置
nginx -t

# 如果测试通过，重启 Nginx
systemctl reload nginx

# 或者
nginx -s reload
```

### 6. 创建管理员账户

```bash
docker-compose exec web python manage.py createsuperuser
```

### 7. 验证部署

访问 `https://yagao.online`，应该能看到应用正常运行。

## 🔧 常用命令

### Docker 容器管理

```bash
# 查看日志
docker-compose logs -f web

# 重启容器
docker-compose restart web

# 停止容器
docker-compose down

# 更新应用
git pull
docker-compose down
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
systemctl reload nginx
```

### Nginx 管理

```bash
# 测试配置
nginx -t

# 重新加载配置
nginx -s reload

# 查看日志
tail -f /var/log/nginx/carbon_access.log
tail -f /var/log/nginx/carbon_error.log
```

## 🐛 故障排查

### 1. 502 Bad Gateway

检查 Docker 容器是否运行：
```bash
docker-compose ps
docker-compose logs web
```

检查端口是否监听：
```bash
netstat -tlnp | grep 8000
# 或
ss -tlnp | grep 8000
```

### 2. 静态文件 404

检查静态文件路径：
```bash
ls -la /root/carbon_management/staticfiles/
```

重新收集静态文件：
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

检查 Nginx 配置中的路径是否正确。

### 3. 权限问题

```bash
# 确保 Nginx 可以读取静态文件
chmod -R 755 /root/carbon_management/staticfiles/
chmod -R 755 /root/carbon_management/media/
```

### 4. 容器无法启动

```bash
# 查看详细日志
docker-compose logs web

# 检查端口占用
netstat -tlnp | grep 8000
```

## 📊 性能优化

### 1. 启用 Nginx 缓存

在 Nginx 配置中添加：

```nginx
# 在 http 块中
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=carbon_cache:10m max_size=100m inactive=60m;

# 在 location / 块中
proxy_cache carbon_cache;
proxy_cache_valid 200 10m;
proxy_cache_bypass $http_cache_control;
add_header X-Cache-Status $upstream_cache_status;
```

### 2. 调整 Gunicorn Workers

编辑 `docker-entrypoint.sh`：

```bash
# workers = (2 × CPU核心数) + 1
--workers 4
```

## 🔒 安全建议

1. **限制静态文件目录权限**
   ```bash
   chmod 755 /root/carbon_management/staticfiles/
   ```

2. **配置防火墙**
   ```bash
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

3. **定期备份数据库**
   ```bash
   docker cp carbon_management_web:/app/db.sqlite3 ./backup_$(date +%Y%m%d).sqlite3
   ```

4. **更新 SECRET_KEY**
   编辑 `.env.docker` 文件，设置新的 SECRET_KEY

## 📝 配置文件对比

### 原配置（有问题）
```nginx
location / {
   proxy_pass http://127.0.0.1;  # ❌ 错误：缺少端口
   ...
}
```

### 新配置（正确）
```nginx
upstream django_carbon {
    server 127.0.0.1:8000;  # ✅ 正确：指定端口
}

location / {
   proxy_pass http://django_carbon;  # ✅ 使用 upstream
   ...
}
```

## ✅ 部署检查清单

- [ ] Docker 容器正常运行 (`docker-compose ps`)
- [ ] 端口 8000 正在监听 (`netstat -tlnp | grep 8000`)
- [ ] 静态文件已收集 (`ls staticfiles/`)
- [ ] Nginx 配置正确 (`nginx -t`)
- [ ] Nginx 已重启 (`systemctl reload nginx`)
- [ ] 管理员账户已创建
- [ ] 网站可以正常访问 (`https://yagao.online`)
- [ ] 静态文件加载正常
- [ ] 管理后台可以访问 (`https://yagao.online/admin`)

## 📞 需要帮助？

如果遇到问题，请提供：
1. `docker-compose logs web` 的输出
2. `/var/log/nginx/carbon_error.log` 的内容
3. `nginx -t` 的结果
4. `netstat -tlnp | grep 8000` 的输出
