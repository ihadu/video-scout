"""
视频列表 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models import Video, get_db


router = APIRouter()


class VideoResponse(BaseModel):
    """视频响应模型"""
    id: int
    file_name: str
    file_path: str
    file_size: int
    duration: float
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """视频列表响应模型"""
    total: int
    page: int
    page_size: int
    videos: List[VideoResponse]


@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("modified_at", alias="sort"),
    sort_order: str = Query("desc", alias="order"),
    min_duration: Optional[float] = Query(None, ge=0, description="最小时长（秒）"),
    max_duration: Optional[float] = Query(None, ge=0, description="最大时长（秒）"),
    format: Optional[str] = Query(None, description="视频格式过滤"),
    db: Session = Depends(get_db)
):
    """
    获取视频列表
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **sort**: 排序字段 (file_name, duration, file_size, modified_at, created_at)
    - **order**: 排序方向 (asc, desc)
    - **min_duration**: 最小时长（秒）
    - **max_duration**: 最大时长（秒）
    - **format**: 视频格式过滤
    """
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 查询视频列表
    query = db.query(Video).filter(Video.is_valid == True)
    
    # 时长过滤
    if min_duration is not None:
        query = query.filter(Video.duration >= min_duration)
    
    if max_duration is not None:
        query = query.filter(Video.duration <= max_duration)
    
    # 格式过滤
    if format:
        query = query.filter(Video.format == format.lower())
    
    # 查询总数（应用过滤后）
    total = query.count()
    
    # 排序
    sort_columns = ['file_name', 'duration', 'file_size', 'modified_at', 'created_at']
    if sort_by not in sort_columns:
        sort_by = 'modified_at'
    
    if sort_order == 'desc':
        query = query.order_by(getattr(Video, sort_by).desc())
    else:
        query = query.order_by(getattr(Video, sort_by).asc())
    
    videos = query.offset(offset).limit(page_size).all()
    
    return VideoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        videos=[VideoResponse.model_validate(v) for v in videos]
    )


# 清理无效视频记录（必须在 /{video_id} 之前定义，避免路由冲突）
@router.delete("/invalid")
async def delete_invalid_videos(db: Session = Depends(get_db)):
    """
    清理所有无效视频记录（物理删除）
    
    删除所有 is_valid=False 的视频记录，释放数据库空间
    """
    # 统计无效记录数量
    invalid_count = db.query(Video).filter(Video.is_valid == False).count()
    
    if invalid_count == 0:
        return {
            "message": "没有需要清理的无效记录",
            "deleted_count": 0
        }
    
    # 物理删除无效记录
    deleted_count = db.query(Video).filter(Video.is_valid == False).delete()
    db.commit()
    
    print(f"清理完成：删除 {deleted_count} 条无效视频记录")
    
    return {
        "message": "清理完成",
        "deleted_count": deleted_count
    }


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """
    获取视频详情
    
    - **video_id**: 视频 ID
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    return VideoResponse.model_validate(video)


@router.delete("/{video_id}")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """
    删除视频索引（不删除文件）
    
    - **video_id**: 视频 ID
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 软删除
    video.is_valid = False
    db.commit()
    
    return {"message": "视频索引已删除"}
