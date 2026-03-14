#!/bin/bash

# Video Scout 测试脚本
# 用于验证环境配置是否正确

echo "🎬 Video Scout 环境检测"
echo "======================"

# 检查 Docker
echo -n "✅ Docker: "
if command -v docker &> /dev/null; then
    docker --version
else
    echo "❌ 未安装 Docker"
    exit 1
fi

# 检查 Docker Compose
echo -n "✅ Docker Compose: "
if command -v docker-compose &> /dev/null; then
    docker-compose --version
elif docker compose version &> /dev/null; then
    docker compose version
else
    echo "❌ 未安装 Docker Compose"
    exit 1
fi

# 检查 ffmpeg
echo -n "✅ ffmpeg: "
if docker run --rm jrottenberg/ffmpeg:4.2.2-alpine ffmpeg -version &> /dev/null; then
    echo "✅ 可用（Docker 镜像）"
else
    echo "⚠️  需要 Docker 权限"
fi

# 检查端口占用
echo -n "✅ 端口 3000: "
if lsof -i :3000 &> /dev/null; then
    echo "⚠️  已被占用"
else
    echo "✅ 可用"
fi

echo -n "✅ 端口 8000: "
if lsof -i :8000 &> /dev/null; then
    echo "⚠️  已被占用"
else
    echo "✅ 可用"
fi

echo -n "✅ 端口 5432: "
if lsof -i :5432 &> /dev/null; then
    echo "⚠️  已被占用"
else
    echo "✅ 可用"
fi

# 检查磁盘空间
echo -n "✅ 磁盘空间： "
FREE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "剩余 $FREE_SPACE"

# 检查配置文件
echo "✅ 配置文件:"
for file in docker-compose.yml README.md; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file 不存在"
    fi
done

echo ""
echo "======================"
echo "环境检测完成！"
echo ""
echo "下一步："
echo "1. 运行 docker-compose up -d 启动服务"
echo "2. 访问 http://localhost:3000"
echo "3. 在扫描管理页面添加视频目录"
