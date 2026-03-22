# 视频播放修复任务进度

## 任务目标
修复视频播放页面无法正常播放的问题，根本原因是缺少 `ffprobe` 导致视频元数据提取失败。

## 已完成步骤
- [x] 诊断问题：确认 `ffprobe` 缺失导致元数据错误
- [x] 确认系统架构：x86_64
- [x] 确认后端 Python 版本：Python 3.13.3 (Homebrew)

## 当前进度
- [ ] **步骤 1: 安装 Miniconda** - 进行中，安装失败，需要清理后重试
  - 之前尝试安装 Miniconda x86_64 版本失败（目录已存在且损坏）
  - 已删除损坏的 `~/miniconda3` 目录
  - 需要重新执行安装命令

## 待执行命令

### 1. 安装 Miniconda（如果尚未安装）
```bash
curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -o /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p ~/miniconda3
rm /tmp/miniconda.sh
```

### 2. 初始化 conda
```bash
~/miniconda3/bin/conda init zsh
exec zsh  # 或重启终端
```

### 3. 创建环境并安装 ffmpeg
```bash
~/miniconda3/bin/conda create -n video-tools python=3.13 -y
~/miniconda3/bin/conda activate video-tools
~/miniconda3/bin/conda install -c conda-forge ffmpeg -y
```

### 4. 验证安装
```bash
~/miniconda3/bin/conda run -n video-tools ffprobe -version
```

### 5. 修改 scanner.py
需要修改 `backend/app/services/scanner.py` 中的 `extract_metadata()` 方法，使用 conda 环境的 ffprobe 路径：
```python
# 将 subprocess 调用中的 "ffprobe" 替换为完整路径
FFPROBE_PATH = "/Users/ihadu/miniconda3/envs/video-tools/bin/ffprobe"
```

### 6. 重新扫描视频
```bash
curl -X POST "http://localhost:8000/api/scan/start?directory_id=4"
```

### 7. 验证修复
```bash
# 检查元数据
psql -h localhost -U ihadu -d videoscout -c "SELECT id, duration, width, height, codec FROM videos WHERE id = 114;"

# 测试 API
curl http://localhost:8000/api/play/info/114
```

## 如何继续

明天继续执行时，按以下步骤操作：

1. **检查 Miniconda 是否已安装**
   ```bash
   ~/miniconda3/bin/conda --version
   ```

2. **如果已安装，检查 video-tools 环境**
   ```bash
   ~/miniconda3/bin/conda env list
   ```

3. **如果环境存在，验证 ffprobe**
   ```bash
   ~/miniconda3/bin/conda run -n video-tools ffprobe -version
   ```

4. **如果 ffprobe 可用，直接修改 scanner.py 并重新扫描**
   - 读取 `backend/app/services/scanner.py`
   - 修改 `extract_metadata()` 方法使用 conda 的 ffprobe 路径
   - 重启后端服务
   - 重新扫描视频目录

5. **如果任何步骤失败，从该步骤重新开始**

## 关键文件
- `backend/app/services/scanner.py` - 需要修改的文件
- `TASK_PROGRESS.md` - 本进度文件
