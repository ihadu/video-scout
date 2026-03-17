"""
Video Scout - FastAPI Backend
本地视频资源管理与快速检索工具
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.videos import router as videos_router
from api.scan import router as scan_router
from api.search import router as search_router
from api.player import router as player_router
from api.favorites import router as favorites_router
from api.history import router as history_router
from api.categories import router as categories_router
from api.discover import router as discover_router
from models import init_db

app = FastAPI(
    title="Video Scout API",
    description="本地视频资源管理与快速检索工具",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(videos_router, prefix="/api/videos", tags=["videos"])
app.include_router(scan_router, prefix="/api/scan", tags=["scan"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(player_router, prefix="/api/play", tags=["player"])
app.include_router(favorites_router, prefix="/api/favorites", tags=["favorites"])
app.include_router(history_router, prefix="/api/history", tags=["history"])
app.include_router(categories_router, prefix="/api", tags=["categories"])
app.include_router(discover_router, prefix="/api/discover", tags=["discover"])


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    print("Video Scout API 启动中...")
    init_db()


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "Video Scout API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
