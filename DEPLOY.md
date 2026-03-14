# Video Scout 部署指南

## 📋 前置要求

### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少 10GB 可用磁盘空间
- 推荐 4 核 CPU，8GB 内存

### 检查 Docker 是否安装
```bash
docker --version
docker-compose --version
```

## 🚀 部署步骤

### 1. 准备环境

```bash
# 进入项目目录
cd /home/ihadu/.nanobot/workspace/video-scout/video-scout-mvp

# 检查文件完整性
ls -la
```

### 2. 配置视频目录权限

**重要：** Docker 容器需要访问你的视频目录，需要正确设置权限。

```bash
# 假设你的视频目录在 /mnt/nas/videos
# 将视频目录挂载到容器中

# 方法 1：修改 docker-compose.yml，添加 volume 映射
# 在 backend 服务下添加：
# volumes:
#   - /mnt/nas/videos:/videos:ro  # ro 表示只读

# 方法 2：在应用中添加目录时，使用容器内的路径
# 添加目录时输入：/videos
```

### 3. 启动服务

```bash
# 启动所有服务（PostgreSQL + 后端 + 前端）
docker-compose up -d

# 查看启动日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 4. 访问应用

- **前端界面**: http://你的服务器 IP:3000
- **API 文档**: http://你的服务器 IP:8000/docs
- **数据库**: localhost:5432 (仅本地访问)

### 5. 添加扫描目录

1. 打开前端界面
2. 进入"扫描管理"页面
3. 输入视频目录路径
   - 如果挂载了 volume：`/videos`
   - 如果是本地路径：`/path/to/your/videos`
4. 点击"添加目录"
5. 点击"扫描"按钮开始扫描

## 🔧 配置选项

### 修改端口

编辑 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 改为 8080 端口
  
  backend:
    ports:
      - "8081:8000"  # 改为 8081 端口
```

### 修改数据库密码

编辑 `docker-compose.yml`:

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: your_new_password
  
  backend:
    environment:
      POSTGRES_PASSWORD: your_new_password
```

### 持久化数据

数据已经通过 Docker volumes 持久化：
- `postgres_data` - 数据库文件
- `thumbnail_data` - 缩略图缓存

## 📊 维护命令

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f postgres
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
```

### 更新应用
```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建
docker-compose build

# 启动服务
docker-compose up -d
```

### 清理数据
```bash
# 停止并删除所有容器和卷（⚠️ 会删除所有数据！）
docker-compose down -v

# 只删除容器，保留数据
docker-compose down
```

### 数据库备份
```bash
# 备份数据库
docker-compose exec postgres pg_dump -U videoscout videoscout > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U videoscout videoscout < backup.sql
```

## 🐛 常见问题

### Q: 无法访问前端页面
```bash
# 检查防火墙
ufw allow 3000
ufw allow 8000

# 检查容器状态
docker-compose ps
```

### Q: 扫描目录失败
- 检查目录路径是否正确
- 检查 Docker 容器是否有权限访问该目录
- 查看后端日志：`docker-compose logs backend`

### Q: 缩略图生成失败
- 检查 ffmpeg 是否可用
- 检查视频文件是否损坏
- 查看后端日志

### Q: 数据库连接失败
```bash
# 检查 PostgreSQL 状态
docker-compose ps postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 重启 PostgreSQL
docker-compose restart postgres
```

### Q: 内存不足
```bash
# 限制 PostgreSQL 内存使用
# 编辑 docker-compose.yml，添加：
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
```

## 📈 性能优化

### 1. 调整 PostgreSQL 参数
```bash
# 编辑 docker-compose.yml
services:
  postgres:
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=128MB
```

### 2. 调整缩略图质量
```python
# 编辑 backend/app/services/thumbnail.py
# 修改 -q:v 参数（1-31，越小质量越高）
'-q:v', '5'  # 降低质量，加快生成速度
```

### 3. 使用 SSD 存储缩略图
```bash
# 编辑 docker-compose.yml
volumes:
  thumbnail_data:
    driver: local
    driver_opts:
      type: none
      device: /ssd/thumbnails
      o: bind
```

## 🔒 安全建议

### 1. 修改默认密码
```yaml
# docker-compose.yml
POSTGRES_PASSWORD: 强密码至少 16 位
```

### 2. 限制数据库访问
```yaml
# 不暴露 5432 端口到主机
# 删除这行：
# ports:
#   - "5432:5432"
```

### 3. 使用反向代理
建议使用 Nginx 或 Caddy 作为反向代理，启用 HTTPS。

## 📞 技术支持

遇到问题？查看：
- API 文档：http://your-server:8000/docs
- 项目 README: README.md
- Docker 日志：`docker-compose logs -f`

---

**祝部署顺利！** 🎉
