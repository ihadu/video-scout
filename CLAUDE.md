# Video Scout 项目配置与规范

## 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **前端**: Vue 3 + Vite
- **视频处理**: FFmpeg (转码、缩略图生成)

## 开发环境

### 端口配置
- 前端开发服务：3000 (或自动选择其他端口)
- 后端 API: 8000

### 启动服务
```bash
# 清理占用端口
lsof -ti:3000 | xargs -r kill -9
lsof -ti:8000 | xargs -r kill -9

# 启动前端
cd frontend && npm run dev

# 启动后端
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 代码规范

### 提交信息格式
- `feat:` 新功能
- `fix:` 修复 bug
- `refactor:` 重构
- `docs:` 文档更新
- `style:` 代码格式调整
- `test:` 测试相关

### 前端开发
- 使用 Vue 3 Composition API
- 分类/标签选择对话框中，已选中的项应排在前面并有明显视觉标识
- 对话框打开时同步当前选中状态

### 后端开发
- SQLAlchemy 关系使用 `uselist=False` 时，直接访问关联对象属性
- 避免双向循环依赖，优先通过关系而非外键 ID 字段查询
- 视频文件不存在时返回 410 Gone 状态码

## 数据库迁移
- 使用 `psql` 执行 SQL 迁移文件
- 批量数据操作必须实现幂等性

## 视频处理
- 扫描卡住时采用分批渐进处理，配置合理的 chunk size
- 优先保护 HDD 性能，避免连续大量 IO 操作
- 转码任务状态通过 `TranscodeTask` 表管理

## Git 配置
- 使用 SSH 方式推送：`git@github.com:ihadu/video-scout.git`
- SSH 密钥位于 `~/.ssh/id_ed25519`

## 常用 API 端点
- `/api/play/<video_id>` - 播放视频（支持 Range 请求）
- `/api/play/info/<video_id>` - 获取视频播放信息
- `/api/videos/<id>/categories` - 视频分类管理
- `/api/videos/<id>/tags` - 视频标签管理
- `/api/discover/recommend` - 发现页视频推荐
