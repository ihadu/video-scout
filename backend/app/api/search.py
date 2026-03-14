"""
搜索 API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from pydantic import BaseModel

from models import Video, get_db


router = APIRouter()


class SearchVideoResponse(BaseModel):
    """搜索结果响应模型"""
    id: int
    file_name: str
    file_path: str
    file_size: int
    duration: float
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """搜索响应模型"""
    total: int
    videos: List[SearchVideoResponse]


@router.get("", response_model=SearchResponse)
async def search_videos(
    q: Optional[str] = Query(None, description="搜索关键词"),
    min_duration: Optional[float] = Query(None, ge=0, description="最小时长（秒）"),
    max_duration: Optional[float] = Query(None, ge=0, description="最大时长（秒）"),
    format: Optional[str] = Query(None, description="视频格式过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    搜索视频
    
    - **q**: 搜索关键词（文件名模糊匹配）
    - **min_duration**: 最小时长（秒）
    - **max_duration**: 最大时长（秒）
    - **format**: 视频格式过滤
    - **page**: 页码
    - **page_size**: 每页数量
    """
    # 构建查询条件
    query = db.query(Video).filter(Video.is_valid == True)
    
    # 关键词搜索
    if q:
        query = query.filter(
            or_(
                Video.file_name.ilike(f"%{q}%"),
                Video.file_path.ilike(f"%{q}%")
            )
        )
    
    # 时长过滤
    if min_duration is not None:
        query = query.filter(Video.duration >= min_duration)
    
    if max_duration is not None:
        query = query.filter(Video.duration <= max_duration)
    
    # 格式过滤
    if format:
        query = query.filter(Video.format == format.lower())
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    videos = query.order_by(Video.modified_at.desc()).offset(offset).limit(page_size).all()
    
    return SearchResponse(
        total=total,
        videos=[SearchVideoResponse.model_validate(v) for v in videos]
    )


@router.get("/duration-ranges")
async def get_duration_ranges(db: Session = Depends(get_db)):
    """
    获取视频时长分布统计
    """
    # 短视频：< 1 分钟
    short = db.query(Video).filter(
        Video.is_valid == True,
        Video.duration < 60
    ).count()
    
    # 中视频：1-10 分钟
    medium = db.query(Video).filter(
        Video.is_valid == True,
        Video.duration >= 60,
        Video.duration <= 600
    ).count()
    
    # 长视频：> 10 分钟
    long = db.query(Video).filter(
        Video.is_valid == True,
        Video.duration > 600
    ).count()
    
    return {
        "short": short,
        "medium": medium,
        "long": long,
        "total": short + medium + long
    }
