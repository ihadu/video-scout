# Video Scout Android Client

抖音式垂直滑动视频浏览器，为 Video Scout 后端服务提供原生 Android 体验。

## 技术栈

- **语言**: Kotlin 1.9.22
- **UI**: Jetpack Compose (BOM 2024.02.00)
- **架构**: MVVM + Repository 模式
- **依赖注入**: Hilt 2.50
- **本地数据库**: Room 2.6.1
- **网络**: Retrofit 2.9.0 + OkHttp 4.12.0
- **视频播放**: Media3 (ExoPlayer) 1.2.1
- **图片加载**: Coil 2.5.0

## 项目结构

```
app/src/main/java/com/videoscout/app/
├── MainActivity.kt              # 应用入口
├── VideoScoutApplication.kt     # Application 类
├── di/                          # Hilt DI 模块
│   ├── AppModule.kt
│   ├── DatabaseModule.kt
│   ├── NetworkModule.kt
│   ├── PlayerModule.kt
│   └── RepositoryModule.kt
├── data/
│   ├── local/                   # Room 数据库
│   ├── remote/                  # Retrofit API
│   ├── repository/              # Repository 实现
│   └── model/                   # 领域模型
├── player/                      # 播放器核心
│   ├── VideoPlayerManager.kt
│   ├── PreloadManager.kt
│   └── PlayerUtils.kt
├── ui/                          # UI 层
│   ├── common/                  # 公共组件
│   ├── discover/                # 发现页
│   ├── library/                 # 视频库
│   ├── favorites/               # 收藏页
│   ├── history/                 # 历史页
│   ├── settings/                # 设置页
│   ├── player/                  # 垂直播放器
│   ├── navigation/              # 导航
│   └── theme/                   # 主题
└── utils/                       # 工具类
```

## 构建说明

### 1. 环境要求

- Android Studio Hedgehog (2023.1.1) 或更高版本
- JDK 17
- Android SDK 34
- Gradle 8.2

### 2. 配置服务器地址

修改 `app/build.gradle.kts` 中的默认服务器地址:

```kotlin
buildConfigField("String", "DEFAULT_SERVER_URL", """"http://你的服务器IP:8000"""""
```

或在应用内的设置页面配置。

### 3. 构建项目

```bash
# 使用 Gradle Wrapper
./gradlew assembleDebug

# 或直接安装到设备
./gradlew installDebug
```

### 4. Android Studio 构建

1. 打开 Android Studio
2. 选择 `File -> Open`，选择 `android-app` 目录
3. 等待 Gradle 同步完成
4. 点击 `Run` 按钮或按 `Shift + F10`

## 核心功能

### 抖音式垂直滑动浏览

- 使用 `VerticalPager` 实现垂直滑动
- 预加载前后各 1 个视频
- 页面切换自动播放/暂停
- 单击显示/隐藏控制层

### 视频预加载策略

- 独立 ExoPlayer 实例仅做缓冲
- 静音、不播放、prepare 后即加入缓存池
- 最大预加载 2 个视频

### 离线缓存

- **内存缓存**: LruCache 存储缩略图
- **磁盘缓存**: Room 存储视频元数据、分类、标签
- **视频流缓存**: ExoPlayer SimpleCache (2GB 上限)

### 服务器发现

- 自动发现局域网内后端服务
- 扫描 1-254 网段
- 测试连接可用性

## 后端 API 对接

| 功能 | 端点 |
|------|------|
| 推荐视频 | `GET /api/discover/recommend` |
| 视频流播放 | `GET /api/play/{id}` |
| 缩略图 | `GET /api/play/thumbnail/{id}` |
| 视频信息 | `GET /api/play/info/{id}` |
| 视频列表 | `GET /api/videos` |
| 收藏列表 | `GET /api/favorites` |
| 历史记录 | `GET /api/history` |
| 分类/标签 | `GET /api/categories`, `/api/tags` |
| 健康检查 | `GET /health` |

## 常见问题

### 编译错误：Unresolved reference

确保所有依赖正确同步：
```bash
./gradlew clean build --refresh-dependencies
```

### 运行时崩溃：Hilt 相关

确保所有使用 Hilt 的类都有正确的注解：
- `@HiltAndroidApp` - Application 类
- `@AndroidEntryPoint` - Activity/Fragment
- `@HiltViewModel` - ViewModel

### 视频无法播放

1. 检查服务器地址配置是否正确
2. 确保后端服务运行正常
3. 检查网络权限是否已授权

## 性能指标

- 冷启动时间 < 2s
- 内存占用 < 300MB（正常使用时）
- 滑动帧率 > 55fps
- 视频启动时间 < 500ms

## License

MIT
