"""
Discover 推荐 API - 双模式推荐系统
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
import random

from models import Video, VideoCategory, VideoTag, UserFavorite, get_db


router = APIRouter()


class VideoRecommendation(BaseModel):
    """推荐视频响应模型"""
    id: int
    file_name: str
    file_path: str
    file_size: int
    duration: float
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    rating: int = 0
    watch_count: int = 0
    has_category: bool = False
    has_tag: bool = False
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """推荐响应模型"""
    videos: List[VideoRecommendation]
    mode: str
    metadata: dict


def get_video_metadata(db: Session, video: Video) -> dict:
    """获取视频的完整元数据"""
    # 获取评分
    favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video.id).first()
    rating = favorite.rating if favorite else 0
    
    # 获取观看次数
    watch_count = video.watch_count or 0
    
    # 检查是否有分类
    has_category = db.query(VideoCategory).filter(VideoCategory.video_id == video.id).first() is not None
    
    # 检查是否有标签
    has_tag = db.query(VideoTag).filter(VideoTag.video_id == video.id).first() is not None
    
    return {
        "id": video.id,
        "file_name": video.file_name,
        "file_path": video.file_path,
        "file_size": video.file_size,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "format": video.format,
        "rating": rating,
        "watch_count": watch_count,
        "has_category": has_category,
        "has_tag": has_tag
    }


def get_recommendations_organize(db: Session, limit: int, max_duration: float) -> List[dict]:
    """
    整理模式推荐算法
    标记越不完整，权重越高
    """
    # 获取所有符合条件的视频
    videos = db.query(Video).filter(
        Video.duration <= max_duration,
        Video.is_valid == True
    ).all()
    
    scored_videos = []
    for video in videos:
        score = 0
        
        # 有分类？-10 分
        has_category = db.query(VideoCategory).filter(VideoCategory.video_id == video.id).first() is not None
        if has_category:
            score -= 10
        
        # 有标签？-10 分
        has_tag = db.query(VideoTag).filter(VideoTag.video_id == video.id).first() is not None
        if has_tag:
            score -= 10
        
        # 有评分？-5 分
        favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video.id).first()
        if favorite and favorite.rating > 0:
            score -= 5
        
        scored_videos.append((video, score))
    
    # 按分数降序（未标记优先）
    scored_videos.sort(key=lambda x: x[1], reverse=True)
    
    # 返回前 limit 个视频的元数据
    result = []
    for video, score in scored_videos[:limit]:
        result.append(get_video_metadata(db, video))
    
    return result


def get_recommendations_recommend(db: Session, limit: int, max_duration: float) -> List[dict]:
    """
    推荐模式算法
    评分越高/观看越多，权重越高
    """
    # 获取所有符合条件的视频
    videos = db.query(Video).filter(
        Video.duration <= max_duration,
        Video.is_valid == True
    ).all()
    
    scored_videos = []
    for video in videos:
        score = 0
        
        # 评分权重：5 星=50 分，4 星=40 分...
        favorite = db.query(UserFavorite).filter(UserFavorite.video_id == video.id).first()
        rating = favorite.rating if favorite else 0
        score += rating * 10
        
        # 观看次数权重：每次=2 分
        watch_count = video.watch_count or 0
        score += watch_count * 2
        
        # 分类数量权重：每个=3 分
        category_count = db.query(VideoCategory).filter(VideoCategory.video_id == video.id).count()
        score += category_count * 3
        
        # 标签数量权重：每个=2 分
        tag_count = db.query(VideoTag).filter(VideoTag.video_id == video.id).count()
        score += tag_count * 2
        
        scored_videos.append((video, score))
    
    # 按分数降序（高评分优先）
    scored_videos.sort(key=lambda x: x[1], reverse=True)
    
    # 返回前 limit 个视频的元数据
    result = []
    for video, score in scored_videos[:limit]:
        result.append(get_video_metadata(db, video))
    
    return result


def get_recommendation_metadata(db: Session) -> dict:
    """获取推荐元数据（整理进度等）"""
    # 总视频数
    total_videos = db.query(Video).filter(Video.is_valid == True).count()
    
    # 完全未标记的视频数（无分类 + 无标签 + 无评分）
    unmarked_query = db.query(Video).filter(
        Video.is_valid == True
    )
    
    # 有分类的视频 ID
    video_with_category = db.query(VideoCategory.video_id).distinct().subquery()
    # 有标签的视频 ID
    video_with_tag = db.query(VideoTag.video_id).distinct().subquery()
    # 有评分的视频 ID
    video_with_rating = db.query(UserFavorite.video_id).filter(UserFavorite.rating > 0).distinct().subquery()
    
    # 未标记视频 = 不在以上任何查询中的视频
    unmarked_videos = db.query(Video).filter(
        Video.is_valid == True,
        ~Video.id.in_(video_with_category),
        ~Video.id.in_(video_with_tag),
        ~Video.id.in_(video_with_rating)
    ).count()
    
    # 整理进度
    marking_progress = 0
    if total_videos > 0:
        marking_progress = round((1 - unmarked_videos / total_videos) * 100, 1)
    
    return {
        "total_videos": total_videos,
        "unmarked_videos": unmarked_videos,
        "marked_videos": total_videos - unmarked_videos,
        "marking_progress": marking_progress
    }


@router.get("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = Query(20, ge=1, le=100),
    max_duration: float = Query(600, ge=0),
    mode: str = Query("organize", enum=["organize", "recommend"]),
    db: Session = Depends(get_db)
):
    """
    获取推荐视频
    
    - **limit**: 返回数量（1-100）
    - **max_duration**: 最大时长（秒）
    - **mode**: 推荐模式（organize=整理模式，recommend=推荐模式）
    """
    # 根据模式选择算法
    if mode == "organize":
        videos = get_recommendations_organize(db, limit, max_duration)
    else:
        videos = get_recommendations_recommend(db, limit, max_duration)
    
    # 获取元数据
    metadata = get_recommendation_metadata(db)
    
    return {
        "videos": videos,
        "mode": mode,
        "metadata": metadata
    }
