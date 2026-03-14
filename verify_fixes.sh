#!/bin/bash

# Video Scout 代码验证脚本
# 用于检查代码修复是否正确

echo "🔍 Video Scout 代码验证"
echo "========================"

ERRORS=0

# 检查 1: 验证 player.py 的流式读取
echo -n "✅ 检查 1: 视频流式读取修复... "
if grep -q "stream_video_file" backend/app/api/player.py && \
   grep -q "def stream_video_file" backend/app/api/player.py && \
   grep -q "f.seek(start)" backend/app/api/player.py; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 2: 验证 thumbnail.py 的路径配置
echo -n "✅ 检查 2: 缩略图路径配置... "
if grep -q "THUMBNAIL_DIR" backend/app/services/thumbnail.py && \
   grep -q "/app/data/thumbnails" backend/app/services/thumbnail.py; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 3: 验证数据库索引
echo -n "✅ 检查 3: 数据库索引... "
if grep -q "idx_videos_created_at" backend/app/models/__init__.py && \
   grep -q "idx_videos_modified_at" backend/app/models/__init__.py; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 4: 验证无未使用的导入
echo -n "✅ 检查 4: 清理未使用导入... "
if ! grep -q "import stat" backend/app/services/scanner.py && \
   ! grep -q "LargeBinary" backend/app/models/__init__.py && \
   ! grep -q "StaticPool" backend/app/models/__init__.py && \
   ! grep -q "import threading" backend/app/api/scan.py; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 5: 验证 scan_tasks_status 已移除
echo -n "✅ 检查 5: 移除内存状态存储... "
if ! grep -q "scan_tasks_status" backend/app/api/scan.py; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 6: 验证 docker-compose 环境变量
echo -n "✅ 检查 6: Docker 环境变量... "
if grep -q "THUMBNAIL_DIR=/app/data/thumbnails" docker-compose.yml; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 7: 语法检查
echo -n "✅ 检查 7: Python 语法检查... "
python3 -m py_compile backend/app/main.py 2>/dev/null && \
python3 -m py_compile backend/app/models/__init__.py 2>/dev/null && \
python3 -m py_compile backend/app/api/player.py 2>/dev/null && \
python3 -m py_compile backend/app/api/scan.py 2>/dev/null && \
python3 -m py_compile backend/app/services/scanner.py 2>/dev/null && \
python3 -m py_compile backend/app/services/thumbnail.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 通过"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "========================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ 所有检查通过！代码修复完成。"
    echo ""
    echo "下一步："
    echo "1. docker-compose build --no-cache  # 重新构建镜像"
    echo "2. docker-compose up -d             # 启动服务"
    echo "3. docker-compose logs -f           # 查看日志"
    exit 0
else
    echo "❌ 有 $ERRORS 个检查失败，请检查上述问题。"
    exit 1
fi
