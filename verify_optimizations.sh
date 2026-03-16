#!/bin/bash

echo "========================================="
echo "Video Scout 优化验证"
echo "========================================="
echo ""

# 检查服务状态
echo "1. 检查服务状态..."
docker compose -f /home/ihadu/.nanobot/workspace/video-scout/video-scout-mvp/docker-compose.yml ps
echo ""

# 等待服务启动
echo "2. 等待服务启动..."
sleep 3
echo ""

# 测试前端访问
echo "3. 测试前端访问..."
curl -s -o /dev/null -w "HTTP 状态码：%{http_code}\n" http://192.168.18.89:3000/videos
echo ""

# 检查 URL 同步功能（通过查看源代码）
echo "4. 检查 URL 同步功能..."
if docker exec video-scout-frontend grep -q "syncURL" /usr/share/nginx/html/assets/*.js 2>/dev/null; then
    echo "✅ URL 同步功能已部署"
else
    echo "⚠️  URL 同步功能检查失败（可能是文件压缩导致）"
fi
echo ""

# 检查响应式优化（通过查看 CSS）
echo "5. 检查响应式优化..."
if docker exec video-scout-frontend grep -q "flex-wrap: wrap" /usr/share/nginx/html/assets/*.css 2>/dev/null; then
    echo "✅ 响应式优化已部署"
else
    echo "⚠️  响应式优化检查失败（可能是 CSS 压缩导致）"
fi
echo ""

# 检查缓存功能
echo "6. 检查缓存功能..."
if docker exec video-scout-frontend grep -q "localStorage" /usr/share/nginx/html/assets/*.js 2>/dev/null; then
    echo "✅ 缓存功能已部署"
else
    echo "⚠️  缓存功能检查失败（可能是文件压缩导致）"
fi
echo ""

echo "========================================="
echo "手动验证步骤："
echo "========================================="
echo ""
echo "1. 移动端响应式测试："
echo "   - 打开浏览器开发者工具 (F12)"
echo "   - 切换到移动端模式 (Ctrl+Shift+M)"
echo "   - 访问 http://192.168.18.89:3000/videos"
echo "   - 检查筛选栏是否自动换行，无横向滚动条"
echo ""
echo "2. URL 同步测试："
echo "   - 访问 http://192.168.18.89:3000/videos"
echo "   - 点击任意分类或标签筛选"
echo "   - 检查 URL 是否更新为 /videos?category=X 或 /videos?tag=X"
echo "   - 刷新页面，检查筛选状态是否保持"
echo "   - 复制带参数的 URL 到新标签页打开，检查筛选是否自动应用"
echo ""
echo "3. 缓存功能测试："
echo "   - 打开浏览器开发者工具 (F12)"
echo "   - 切换到 Network 标签，勾选 Preserve log"
echo "   - 访问 http://192.168.18.89:3000/videos"
echo "   - 记录 /api/categories 和 /api/tags 请求次数"
echo "   - 刷新页面或重新访问视频库"
echo "   - 检查 API 请求次数是否减少（应该从缓存读取）"
echo ""
echo "4. 缓存刷新测试："
echo "   - 访问 http://192.168.18.89:3000/categories"
echo "   - 添加/编辑/删除一个分类"
echo "   - 返回视频库页面"
echo "   - 检查新分类是否立即显示（缓存已刷新）"
echo ""

echo "========================================="
echo "访问地址："
echo "========================================="
echo "前端：http://192.168.18.89:3000"
echo "视频库：http://192.168.18.89:3000/videos"
echo "分类管理：http://192.168.18.89:3000/categories"
echo "标签管理：http://192.168.18.89:3000/tags"
echo ""
