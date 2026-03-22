"""
缩略图 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from services.thumbnail import ThumbnailService


router = APIRouter()

thumbnail_service = ThumbnailService()


@router.post("/generate/{video_id}")
async def generate_thumbnail(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    生成视频缩略图

    - **video_id**: 视频 ID
    """
    thumbnail_path = thumbnail_service.generate_on_demand(db, video_id)

    if not thumbnail_path:
        raise HTTPException(status_code=500, detail="缩略图生成失败")

    return {
        "video_id": video_id,
        "thumbnail_path": thumbnail_path
    }


@router.get("/{video_id}")
async def get_thumbnail(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    获取缩略图信息

    - **video_id**: 视频 ID
    """
    from models import Video

    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    thumbnail_path = thumbnail_service.get_thumbnail_path(video_id)
    exists = thumbnail_service.thumbnail_exists(video_id)

    return {
        "video_id": video_id,
        "thumbnail_path": thumbnail_path,
        "exists": exists,
        "generated": video.thumbnail_generated
    }
