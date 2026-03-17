"""
收藏 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models import UserFavorite, Video, get_db


router = APIRouter()


class FavoriteResponse(BaseModel):
    """收藏响应模型"""
    id: int
    video_id: int
    created_at: str
    
    class Config:
        from_attributes = True


class FavoriteWithVideo(BaseModel):
    """带视频信息的收藏模型"""
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
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[FavoriteWithVideo])
async def get_favorites(db: Session = Depends(get_db)):
    """
    获取收藏列表
    """
    favorites = db.query(UserFavorite).join(
        Video, UserFavorite.video_id == Video.id
    ).filter(Video.is_valid == True).all()
    
    result = []
    for fav in favorites:
        video = db.query(Video).filter(Video.id == fav.video_id).first()
        if video:
            result.append({
                "id": fav.id,
                "video_id": fav.video_id,
                "file_name": video.file_name,
                "file_path": video.file_path,
                "file_size": video.file_size,
                "duration": video.duration,
                "width": video.width,
                "height": video.height,
                "format": video.format,
                "thumbnail_generated": video.thumbnail_generated,
                "created_at": fav.created_at.isoformat()
            })
    
    return result


@router.post("/{video_id}", response_model=FavoriteResponse)
async def add_favorite(video_id: int, db: Session = Depends(get_db)):
    """
    添加收藏
    
    - **video_id**: 视频 ID
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已收藏
    existing = db.query(UserFavorite).filter(UserFavorite.video_id == video_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="视频已在收藏中")
    
    # 添加收藏
    favorite = UserFavorite(video_id=video_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    
    return {
        "id": favorite.id,
        "video_id": favorite.video_id,
        "created_at": favorite.created_at.isoformat()
    }


@router.delete("/{video_id}")
async def remove_favorite(video_id: int, db: Session = Depends(get_db)):
    """
    取消收藏
    
    - **video_id**: 视频 ID
    """
    favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏不存在")
    
    db.delete(favorite)
    db.commit()
    
    return {"message": "已取消收藏"}


@router.get("/{video_id}/status")
async def check_favorite_status(video_id: int, db: Session = Depends(get_db)):
    """
    检查视频是否已收藏
    
    - **video_id**: 视频 ID
    """
    favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video_id).first()
    
    return {
        "video_id": video_id,
        "is_favorited": favorite is not None
    }


class RatingRequest(BaseModel):
    """评分请求模型"""
    rating: int  # 1-5 星，0 清除评分


class RatingResponse(BaseModel):
    """评分响应模型"""
    video_id: int
    rating: int
    is_favorited: bool


@router.get("/{video_id}/rating", response_model=RatingResponse)
async def get_video_rating(video_id: int, db: Session = Depends(get_db)):
    """
    获取视频评分
    
    - **video_id**: 视频 ID
    """
    favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video_id).first()
    
    return {
        "video_id": video_id,
        "rating": favorite.rating if favorite else 0,
        "is_favorited": favorite is not None
    }


@router.put("/{video_id}/rating", response_model=RatingResponse)
async def update_video_rating(video_id: int, rating: RatingRequest, db: Session = Depends(get_db)):
    """
    更新视频评分
    
    - **video_id**: 视频 ID
    - **rating**: 评分（1-5 星，0 清除评分）
    """
    # 验证评分范围
    if not 0 <= rating.rating <= 5:
        raise HTTPException(status_code=400, detail="评分必须在 0-5 之间")
    
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 获取或创建收藏记录
    favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video_id).first()
    
    if rating.rating > 0:
        # 设置评分
        if not favorite:
            favorite = UserFavorite(video_id=video_id, rating=rating.rating)
            db.add(favorite)
        else:
            favorite.rating = rating.rating
    else:
        # 清除评分
        if favorite:
            if favorite.rating == 0:
                # 如果评分已经是 0，删除收藏记录
                db.delete(favorite)
                favorite = None
            else:
                favorite.rating = 0
    
    db.commit()
    
    return {
        "video_id": video_id,
        "rating": favorite.rating if favorite else 0,
        "is_favorited": favorite is not None
    }
