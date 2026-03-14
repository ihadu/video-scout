"""
观看历史 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel

from models import WatchHistory, Video, get_db


router = APIRouter()


class HistoryResponse(BaseModel):
    """观看历史响应模型"""
    id: int
    video_id: int
    progress: float
    watched_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class HistoryWithVideo(BaseModel):
    """带视频信息的观看历史"""
    id: int
    video_id: int
    file_name: str
    file_path: str
    file_size: int
    duration: float
    width: int = None
    height: int = None
    format: str = None
    thumbnail_generated: bool = False
    progress: float
    watched_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[HistoryWithVideo])
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取观看历史
    
    - **limit**: 返回数量（默认 20）
    """
    histories = db.query(WatchHistory).order_by(desc(WatchHistory.watched_at)).limit(limit).all()
    
    result = []
    for history in histories:
        video = db.query(Video).filter(Video.id == history.video_id).first()
        if video:
            result.append({
                "id": history.id,
                "video_id": history.video_id,
                "file_name": video.file_name,
                "file_path": video.file_path,
                "file_size": video.file_size,
                "duration": video.duration,
                "width": video.width,
                "height": video.height,
                "format": video.format,
                "thumbnail_generated": video.thumbnail_generated,
                "progress": history.progress,
                "watched_at": history.watched_at.isoformat(),
                "updated_at": history.updated_at.isoformat()
            })
    
    return result


@router.post("/{video_id}/progress")
async def update_progress(
    video_id: int,
    progress: float,
    db: Session = Depends(get_db)
):
    """
    更新观看进度
    
    - **video_id**: 视频 ID
    - **progress**: 观看进度（秒）
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 查找是否已有记录
    history = db.query(WatchHistory).filter(WatchHistory.video_id == video_id).first()
    
    if history:
        # 更新现有记录
        history.progress = progress
        history.watched_at = history.updated_at  # 保持原来的观看时间
    else:
        # 创建新记录
        history = WatchHistory(video_id=video_id, progress=progress)
        db.add(history)
    
    db.commit()
    
    return {
        "video_id": video_id,
        "progress": progress,
        "message": "观看进度已保存"
    }


@router.delete("")
async def clear_history(db: Session = Depends(get_db)):
    """
    清空观看历史
    """
    db.query(WatchHistory).delete()
    db.commit()
    
    return {"message": "观看历史已清空"}
