# Video Scout - 本地视频资源管理工具

一个强大的本地视频资源管理与快速检索工具，专为拥有大量视频文件的用户设计。

## 🎯 功能特性

### 核心功能 (MVP)
- ✅ **目录扫描** - 支持多目录配置，增量扫描
- ✅ **视频浏览** - 网格视图，响应式设计
- ✅ **智能搜索** - 关键词搜索，时长过滤
- ✅ **视频播放** - HTML5 内嵌播放，Range 请求支持
- ✅ **缩略图** - 按需生成，节省资源

### 技术亮点
- **PostgreSQL** - 支持 20 万 + 视频文件
- **增量扫描** - 只扫描新增/修改的文件
- **按需缩略图** - 点击时才生成，节省 CPU 和存储
- **Docker 部署** - 一键启动，开箱即用

## 📋 系统要求

### 最低配置
- CPU: 2 核
- 内存：4GB
- 存储：10GB（缩略图缓存）
- 网络：100Mbps

### 推荐配置
- CPU: 4 核 +
- 内存：8GB+
- 存储：50GB+
- 网络：1Gbps

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd video-scout-mvp

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

启动后访问：
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs

### 方式二：本地开发

#### 后端
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端
```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

## 📖 使用说明

### 1. 添加扫描目录
- 进入"扫描管理"页面
- 输入视频目录路径（如 `/mnt/nas/videos`）
- 点击"添加目录"

### 2. 启动扫描
- 在目录列表中点击"扫描"按钮
- 扫描会在后台执行，可在页面查看进度
- **注意**：首次扫描 20 万文件可能需要数小时

### 3. 浏览视频
- 进入"视频库"页面
- 视频以网格形式展示
- 支持按名称、时间、时长、大小排序

### 4. 搜索视频
- 在搜索框输入关键词
- 支持时长过滤（短/中/长视频）

### 5. 播放视频
- 点击视频卡片进入播放页面
- 支持的格式：MP4, WebM, M4V
- 不支持的格式会提示下载

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| POSTGRES_HOST | PostgreSQL 主机 | postgres |
| POSTGRES_PORT | PostgreSQL 端口 | 5432 |
| POSTGRES_USER | PostgreSQL 用户名 | videoscout |
| POSTGRES_PASSWORD | PostgreSQL 密码 | videoscout123 |
| POSTGRES_DB | 数据库名 | videoscout |

### 目录结构

```
video-scout-mvp/
├── backend/              # 后端代码
│   ├── app/
│   │   ├── main.py      # 入口文件
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据模型
│   │   └── services/    # 业务逻辑
│   └── requirements.txt
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── api/        # API 调用
│   │   └── router/     # 路由配置
│   └── package.json
├── docker/              # Docker 配置
├── docker-compose.yml   # 编排配置
└── README.md
```

## 📊 API 文档

启动服务后访问 http://localhost:8000/docs 查看完整的 API 文档。

### 核心接口

#### 视频管理
- `GET /api/videos` - 获取视频列表
- `GET /api/videos/{id}` - 获取视频详情

#### 搜索
- `GET /api/search` - 搜索视频

#### 扫描
- `POST /api/scan/add` - 添加扫描目录
- `POST /api/scan/start` - 启动扫描
- `GET /api/scan/status` - 获取扫描状态

#### 播放
- `GET /api/play/{id}` - 播放视频
- `GET /api/play/thumbnail/{id}` - 获取缩略图

## ⚠️ 注意事项

### 首次扫描
- 20 万文件首次扫描可能需要 **2-4 小时**
- 建议先扫描小目录测试
- 扫描过程中可以正常使用其他功能

### 缩略图生成
- 采用按需生成策略
- 首次点击视频时可能需要等待几秒
- 生成的缩略图会缓存，下次立即加载

### 浏览器兼容性
- 推荐浏览器：Chrome, Firefox, Edge 最新版
- MP4/WebM格式可直接播放
- MKV/AVI等格式会提示下载

## 🐛 常见问题

### Q: 扫描很慢怎么办？
A: 这是正常的，20 万文件需要时间。建议使用增量扫描，只扫描新增/修改的文件。

### Q: 缩略图不显示？
A: 检查 ffmpeg 是否正确安装，或者等待缩略图生成完成。

### Q: 视频无法播放？
A: 检查视频格式是否被浏览器支持，不支持的格式会提供下载链接。

### Q: 如何清理缩略图？
A: 删除 `thumbnail_data` 卷，缩略图会在需要时重新生成。

## 📝 更新日志

### v1.0.0 (2026-03-14)
- 初始版本发布
- 支持 PostgreSQL 数据库
- 增量扫描功能
- 按需缩略图生成
- 基础搜索和过滤

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发中...** 更多功能即将推出！
