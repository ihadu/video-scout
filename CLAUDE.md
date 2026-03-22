# Video Scout 项目配置与规范

## 项目概述

Video Scout 是一个本地视频资源管理与快速检索系统，支持 Web 前端、Android 客户端和后端 API 服务。

## 技术栈

### 后端
- **框架**: FastAPI + SQLAlchemy
- **数据库**: PostgreSQL (psycopg3)
- **视频处理**: FFmpeg (转码、缩略图生成)
- **Python 版本**: 3.9+

### Web 前端
- **框架**: Vue 3 + Vite
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios

### Android 客户端
- **框架**: Jetpack Compose
- **架构**: MVVM + Hilt 依赖注入
- **网络**: Retrofit + OkHttp
- **播放器**: Media3 (ExoPlayer)
- **本地存储**: Room + DataStore
- **图片加载**: Coil
- **最低 SDK**: 26 (Android 8.0)
- **目标 SDK**: 34 (Android 14)
- **Kotlin**: 2.0.21

## 项目结构

```
video-scout/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由模块
│   │   │   ├── videos.py
│   │   │   ├── scan.py
│   │   │   ├── player.py
│   │   │   ├── transcode.py
│   │   │   ├── favorites.py
│   │   │   ├── history.py
│   │   │   ├── categories.py
│   │   │   ├── discover.py
│   │   │   ├── search.py
│   │   │   └── thumbnail.py
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── services/     # 业务逻辑服务
│   │   │   ├── scanner.py
│   │   │   ├── transcoder.py
│   │   │   └── thumbnail.py
│   │   └── main.py       # 应用入口
│   ├── batch_transcode.py    # 批量转码脚本
│   └── requirements.txt
├── frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 调用模块
│   │   ├── components/   # 公共组件
│   │   ├── views/        # 页面组件
│   │   │   ├── VideoLibrary.vue
│   │   │   ├── VideoPlayer.vue
│   │   │   ├── Discover.vue
│   │   │   ├── ScanManagement.vue
│   │   │   ├── CategoryManagement.vue
│   │   │   ├── TagManagement.vue
│   │   │   ├── Favorites.vue
│   │   │   ├── History.vue
│   │   │   └── Statistics.vue
│   │   ├── router/       # 路由配置
│   │   └── App.vue
│   └── package.json
└── android-app/          # Android 客户端
    ├── app/src/main/java/com/videoscout/app/
    │   ├── di/           # 依赖注入模块
    │   │   ├── AppModule.kt
    │   │   ├── NetworkModule.kt
    │   │   ├── DatabaseModule.kt
    │   │   ├── PlayerModule.kt
    │   │   ├── RepositoryModule.kt
    │   │   ├── BaseUrlProvider.kt      # 动态服务器地址
    │   │   └── DynamicBaseUrlInterceptor.kt
    │   ├── ui/           # 界面组件
    │   │   ├── library/      # 资料库
    │   │   ├── discover/     # 发现
    │   │   ├── favorites/    # 收藏
    │   │   ├── history/      # 历史
    │   │   ├── player/       # 播放器
    │   │   ├── settings/     # 设置
    │   │   ├── common/       # 公共组件
    │   │   ├── navigation/   # 导航图
    │   │   └── theme/        # 主题
    │   ├── data/         # 数据层
    │   └── utils/        # 工具类
    │       ├── UrlBuilder.kt
    │       └── NetworkUtils.kt
    └── gradle/libs.versions.toml
```

## 开发环境

### 端口配置
- Web 前端开发服务: 3000
- 后端 API: 8000
- Android 调试: 默认端口

### 启动服务

```bash
# 启动 Web 前端
cd frontend && npm run dev

# 启动后端 API
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Android 应用
# 使用 Android Studio 或 ./gradlew installDebug
```

### 后端环境变量
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ihadu
POSTGRES_PASSWORD=
POSTGRES_DB=videoscout
```

## 代码规范

### 提交信息格式
- `feat:` 新功能
- `fix:` 修复 bug
- `refactor:` 重构
- `docs:` 文档更新
- `style:` 代码格式调整
- `test:` 测试相关
- `chore:` 构建/工具变更

### 后端开发规范

#### SQLAlchemy 关系使用
- 使用 `uselist=False` 的一对一关系时，直接访问关联对象属性
- 避免双向循环依赖，优先通过关系而非外键 ID 字段查询

#### API 设计
- 视频文件不存在时返回 410 Gone 状态码
- 支持 Range 请求的视频播放端点: `/api/play/<video_id>`

#### 数据库
- 使用 `psql` 执行 SQL 迁移文件
- 批量数据操作必须实现幂等性

### Web 前端开发规范

- 使用 Vue 3 Composition API
- 分类/标签选择对话框中，已选中的项应排在前面并有明显视觉标识
- 对话框打开时同步当前选中状态

### Android 开发规范

#### 架构分层
- **UI Layer**: Compose 组件 + ViewModel
- **Domain Layer**: Repository 接口
- **Data Layer**: Repository 实现 + Room/Retrofit

#### 依赖注入
- 使用 Hilt 进行依赖注入
- NetworkModule 提供 Retrofit 实例
- DatabaseModule 提供 Room 数据库
- PlayerModule 提供 ExoPlayer 实例

#### 动态服务器地址
- 使用 DataStore 存储用户配置的服务器地址
- BaseUrlProvider 提供动态 Base URL
- DynamicBaseUrlInterceptor 在运行时更新请求地址

## 数据库模型

### 核心表
- `videos` - 视频元数据
- `scan_directories` - 扫描目录配置
- `scan_tasks` - 扫描任务状态
- `transcode_tasks` - 视频转码任务
- `user_favorites` - 用户收藏
- `watch_history` - 观看历史
- `categories` - 分类（支持树形结构）
- `tags` - 标签
- `video_categories` - 视频分类关联
- `video_tags` - 视频标签关联

## API 端点

### 视频管理
- `GET /api/videos` - 视频列表
- `GET /api/videos/{id}` - 视频详情
- `POST /api/videos/{id}/categories` - 设置分类
- `POST /api/videos/{id}/tags` - 设置标签

### 播放
- `GET /api/play/{video_id}` - 播放视频（支持 Range）
- `GET /api/play/info/{video_id}` - 获取播放信息
- `POST /api/play/{video_id}/progress` - 更新观看进度

### 扫描
- `POST /api/scan/start` - 启动扫描
- `POST /api/scan/stop` - 停止扫描
- `GET /api/scan/status` - 扫描状态
- `GET /api/scan/directories` - 扫描目录列表

### 转码
- `POST /api/transcode/start/{video_id}` - 启动转码
- `GET /api/transcode/status/{video_id}` - 转码状态
- `POST /api/transcode/cancel/{video_id}` - 取消转码
- `POST /api/transcode/delete/{video_id}` - 删除转码文件

### 发现与搜索
- `GET /api/discover/recommend` - 推荐视频
- `GET /api/search?q={query}` - 搜索视频

### 用户数据
- `GET/POST /api/favorites` - 收藏管理
- `GET/POST /api/history` - 观看历史

### 元数据
- `GET/POST /api/categories` - 分类管理
- `GET/POST /api/tags` - 标签管理
- `GET /api/thumbnail/{video_id}` - 缩略图

## 视频处理

### 扫描配置
- 扫描卡住时采用分批渐进处理，配置合理的 chunk size
- 优先保护 HDD 性能，避免连续大量 IO 操作
- 支持断点续传，通过 `checkpoint` 字段记录进度

### 转码流程
1. 创建 `TranscodeTask` 记录
2. FFmpeg 转码为 MP4 (H.264 + AAC)
3. 根据归档模式处理原文件:
   - `keep` - 保留原视频
   - `subdir` - 移动到 `.archive/` 子目录
   - `custom` - 移动到指定路径
   - `delete` - 删除原视频

### 批量转码脚本
```bash
# 预览模式
python batch_transcode.py --scan-dir /path/to/videos --dry-run

# 转码并归档到子目录
python batch_transcode.py --scan-dir /path/to/videos --archive-mode subdir

# 处理所有配置的扫描目录
python batch_transcode.py --all-dirs --archive-mode subdir
```

## Git 配置

- 使用 SSH 方式推送: `git@github.com:ihadu/video-scout.git`
- SSH 密钥位于 `~/.ssh/id_ed25519`

## Android 版本配置

### 默认服务器地址
- 编译配置在 `build.gradle.kts`: `DEFAULT_SERVER_URL = "http://192.168.0.104:8000"`
- 运行时可修改：设置页 -> 服务器地址

### 导航结构
- Library (资料库) - 视频列表
- Discover (发现) - 推荐/随机播放
- Favorites (收藏) - 收藏视频
- History (历史) - 观看历史
- Settings (设置) - 服务器配置

## Docker 部署

```bash
# 使用 docker-compose 启动
docker-compose up -d
```

包含服务:
- PostgreSQL 数据库
- 后端 API 服务
- Web 前端 (Nginx)
