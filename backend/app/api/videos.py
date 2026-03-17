"""
视频列表 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

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
    category_id: Optional[int] = Query(None, description="分类 ID 筛选"),
    tag_ids: Optional[str] = Query(None, description="标签 ID 筛选（多选，逗号分隔）"),
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
    - **category_id**: 分类 ID 筛选（包含子分类）
    - **tag_ids**: 标签 ID 筛选（多选，逗号分隔，OR 关系）
    """
    from models import VideoCategory, VideoTag, Category
    
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
    
    # 分类筛选（包含子分类）
    if category_id is not None:
        # 获取该分类及其所有子分类的 ID
        def get_all_subcategory_ids(cat_id: int, all_ids: list = None) -> list:
            if all_ids is None:
                all_ids = []
            all_ids.append(cat_id)
            # 查询子分类
            subcategories = db.query(Category).filter(Category.parent_id == cat_id).all()
            for subcat in subcategories:
                get_all_subcategory_ids(subcat.id, all_ids)
            return all_ids
        
        category_ids = get_all_subcategory_ids(category_id)
        
        # 使用 IN 查询
        query = query.join(VideoCategory, VideoCategory.video_id == Video.id)\
                   .filter(VideoCategory.category_id.in_(category_ids))
    
    # 标签筛选（支持多选）
    if tag_ids:
        tag_id_list = [int(tid) for tid in tag_ids.split(',') if tid.strip()]
        if tag_id_list:
            # 使用 IN 查询，支持多个标签（OR 关系）
            query = query.join(VideoTag, VideoTag.video_id == Video.id)\
                       .filter(VideoTag.tag_id.in_(tag_id_list))
    
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


def format_file_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    获取视频统计信息
    """
    from models import Category, VideoCategory, Tag, VideoTag
    
    # 基本统计
    total_videos = db.query(Video).filter(Video.is_valid == True).count()
    total_duration = db.query(func.sum(Video.duration)).filter(Video.is_valid == True).scalar() or 0
    total_size = db.query(func.sum(Video.file_size)).filter(Video.is_valid == True).scalar() or 0
    
    # 分类分布
    category_stats = db.query(
        Category.name,
        func.count(VideoCategory.video_id).label('count')
    ).join(VideoCategory, Category.id == VideoCategory.category_id).group_by(Category.id).all()
    
    # 标签分布
    tag_stats = db.query(
        Tag.name,
        func.count(VideoTag.video_id).label('count')
    ).join(VideoTag, Tag.id == VideoTag.tag_id).group_by(Tag.id).order_by(func.count(VideoTag.video_id).desc()).limit(20).all()
    
    # 格式分布
    format_stats = db.query(
        Video.format,
        func.count(Video.id).label('count')
    ).filter(Video.is_valid == True).group_by(Video.format).all()
    
    return {
        'total_videos': total_videos,
        'total_duration': total_duration,
        'total_duration_formatted': f"{total_duration // 3600}小时 {(total_duration % 3600) // 60}分钟",
        'total_size': total_size,
        'total_size_formatted': format_file_size(total_size),
        'category_distribution': [{'name': c.name, 'count': c.count} for c in category_stats],
        'tag_cloud': [{'name': t.name, 'count': t.count} for t in tag_stats],
        'format_distribution': [{'format': f.format, 'count': f.count} for f in format_stats]
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


@router.put("/{video_id}/rename")
async def rename_video(video_id: int, data: dict, db: Session = Depends(get_db)):
    """
    重命名视频
    
    - **video_id**: 视频 ID
    - **data**: {"new_name": "新文件名"}
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    new_name = data.get('new_name')
    if not new_name:
        raise HTTPException(status_code=400, detail="新文件名不能为空")
    
    # 检查是否已存在同名文件
    existing = db.query(Video).filter(
        Video.file_name == new_name,
        Video.id != video_id,
        Video.is_valid == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="文件名已存在")
    
    # 更新文件名
    video.file_name = new_name
    video.modified_at = datetime.utcnow()
    db.commit()
    db.refresh(video)
    
    return {
        "message": "重命名成功",
        "video": VideoResponse.model_validate(video)
    }
