"""
分类和标签 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models import Category, Tag, VideoCategory, VideoTag, Video, get_db


router = APIRouter()


# ============== 分类相关 ==============

class CategoryCreate(BaseModel):
    """创建分类请求"""
    name: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = 0


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    """分类响应"""
    id: int
    name: str
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    sort_order: int
    icon: Optional[str] = None
    video_count: int = 0
    children: List['CategoryResponse'] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """
    获取所有分类（树形结构）
    """
    # 获取所有分类
    all_categories = db.query(Category).all()
    
    # 过滤所有一级分类（parent_id 为 None）
    root_categories = [c for c in all_categories if c.parent_id is None]
    root_categories.sort(key=lambda x: x.sort_order)
    
    def build_tree(category):
        """递归构建树形结构"""
        result = CategoryResponse.model_validate(category)
        
        # 获取子分类
        children = [c for c in all_categories if c.parent_id == category.id]
        children.sort(key=lambda x: x.sort_order)
        result.children = [build_tree(child) for child in children]
        
        # 统计视频数量（包括子分类）
        def get_all_sub_category_ids(cat_id):
            """获取分类及其所有子分类的 ID"""
            ids = [cat_id]
            sub_cats = [c for c in all_categories if c.parent_id == cat_id]
            for sub_cat in sub_cats:
                ids.extend(get_all_sub_category_ids(sub_cat.id))
            return ids
        
        # 统计该分类及子分类下的视频总数
        sub_cat_ids = get_all_sub_category_ids(category.id)
        result.video_count = db.query(VideoCategory).filter(
            VideoCategory.category_id.in_(sub_cat_ids)
        ).count()
        
        # 获取父分类名称
        if category.parent_id:
            parent = next((c for c in all_categories if c.id == category.parent_id), None)
            if parent:
                result.parent_name = parent.name
        
        return result
    
    return [build_tree(cat) for cat in root_categories]


@router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """
    创建新分类
    """
    # 检查父分类是否存在
    if category.parent_id is not None:
        parent = db.query(Category).filter(Category.id == category.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="父分类不存在")
    
    db_category = Category(
        name=category.name,
        parent_id=category.parent_id,
        icon=category.icon,
        sort_order=category.sort_order or 0
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return CategoryResponse.model_validate(db_category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    """
    更新分类
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if category.name is not None:
        db_category.name = category.name
    if category.parent_id is not None:
        db_category.parent_id = category.parent_id
    if category.icon is not None:
        db_category.icon = category.icon
    if category.sort_order is not None:
        db_category.sort_order = category.sort_order
    
    db.commit()
    db.refresh(db_category)
    
    return CategoryResponse.model_validate(db_category)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    删除分类（级联删除子分类）
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 检查是否有子分类
    children = db.query(Category).filter(Category.parent_id == category_id).all()
    if children:
        raise HTTPException(status_code=400, detail="请先删除子分类")
    
    db.delete(category)
    db.commit()
    
    return {"message": "分类已删除"}


# ============== 标签相关 ==============

class TagCreate(BaseModel):
    """创建标签请求"""
    name: str
    color: Optional[str] = "#e94560"


class TagUpdate(BaseModel):
    """更新标签请求"""
    name: Optional[str] = None
    color: Optional[str] = None


class TagResponse(BaseModel):
    """标签响应"""
    id: int
    name: str
    color: str
    video_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/tags", response_model=List[TagResponse])
async def list_tags(db: Session = Depends(get_db)):
    """
    获取所有标签
    """
    tags = db.query(Tag).order_by(Tag.name).all()
    
    result = []
    for tag in tags:
        response = TagResponse.model_validate(tag)
        response.video_count = db.query(VideoTag).filter(VideoTag.tag_id == tag.id).count()
        result.append(response)
    
    return result


@router.post("/tags", response_model=TagResponse)
async def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """
    创建新标签
    """
    # 检查是否已存在
    existing = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")
    
    db_tag = Tag(
        name=tag.name,
        color=tag.color or "#e94560"
    )
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return TagResponse.model_validate(db_tag)


@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: int, tag: TagUpdate, db: Session = Depends(get_db)):
    """
    更新标签
    """
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    if tag.name is not None:
        # 检查新名称是否已存在
        if tag.name != db_tag.name:
            existing = db.query(Tag).filter(Tag.name == tag.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="标签名已存在")
        db_tag.name = tag.name
    
    if tag.color is not None:
        db_tag.color = tag.color
    
    db.commit()
    db.refresh(db_tag)
    
    return TagResponse.model_validate(db_tag)


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    删除标签
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    db.delete(tag)
    db.commit()
    
    return {"message": "标签已删除"}


# ============== 视频 - 分类/标签关联 ==============

class VideoTagRequest(BaseModel):
    """视频标签请求"""
    tag_ids: List[int]


@router.post("/videos/{video_id}/categories")
async def add_video_categories(video_id: int, request: VideoTagRequest, db: Session = Depends(get_db)):
    """
    为视频添加分类
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查分类是否存在
    categories = db.query(Category).filter(Category.id.in_(request.tag_ids)).all()
    if len(categories) != len(request.tag_ids):
        raise HTTPException(status_code=400, detail="部分分类不存在")
    
    # 添加关联
    for category_id in request.tag_ids:
        existing = db.query(VideoCategory).filter(
            VideoCategory.video_id == video_id,
            VideoCategory.category_id == category_id
        ).first()
        
        if not existing:
            db.add(VideoCategory(video_id=video_id, category_id=category_id))
    
    db.commit()
    
    return {"message": "分类已添加"}


@router.delete("/videos/{video_id}/categories/{category_id}")
async def remove_video_category(video_id: int, category_id: int, db: Session = Depends(get_db)):
    """
    移除视频分类
    """
    result = db.query(VideoCategory).filter(
        VideoCategory.video_id == video_id,
        VideoCategory.category_id == category_id
    ).delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="关联不存在")
    
    db.commit()
    
    return {"message": "分类已移除"}


@router.post("/videos/{video_id}/tags")
async def add_video_tags(video_id: int, request: VideoTagRequest, db: Session = Depends(get_db)):
    """
    为视频添加标签
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查标签是否存在
    tags = db.query(Tag).filter(Tag.id.in_(request.tag_ids)).all()
    if len(tags) != len(request.tag_ids):
        raise HTTPException(status_code=400, detail="部分标签不存在")
    
    # 添加关联
    for tag_id in request.tag_ids:
        existing = db.query(VideoTag).filter(
            VideoTag.video_id == video_id,
            VideoTag.tag_id == tag_id
        ).first()
        
        if not existing:
            db.add(VideoTag(video_id=video_id, tag_id=tag_id))
    
    db.commit()
    
    return {"message": "标签已添加"}


@router.delete("/videos/{video_id}/tags/{tag_id}")
async def remove_video_tag(video_id: int, tag_id: int, db: Session = Depends(get_db)):
    """
    移除视频标签
    """
    result = db.query(VideoTag).filter(
        VideoTag.video_id == video_id,
        VideoTag.tag_id == tag_id
    ).delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="关联不存在")
    
    db.commit()
    
    return {"message": "标签已移除"}


@router.get("/videos/{video_id}/categories", response_model=List[CategoryResponse])
async def get_video_categories(video_id: int, db: Session = Depends(get_db)):
    """
    获取视频的所有分类
    """
    video_cats = db.query(VideoCategory).filter(VideoCategory.video_id == video_id).all()
    
    categories = []
    for vc in video_cats:
        cat = db.query(Category).filter(Category.id == vc.category_id).first()
        if cat:
            categories.append(CategoryResponse.model_validate(cat))
    
    return categories


@router.get("/videos/{video_id}/tags", response_model=List[TagResponse])
async def get_video_tags(video_id: int, db: Session = Depends(get_db)):
    """
    获取视频的所有标签
    """
    video_tags = db.query(VideoTag).filter(VideoTag.video_id == video_id).all()
    
    tags = []
    for vt in video_tags:
        tag = db.query(Tag).filter(Tag.id == vt.tag_id).first()
        if tag:
            tags.append(TagResponse.model_validate(tag))
    
    return tags


@router.get("/categories/{category_id}/videos")
async def get_category_videos(
    category_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取分类下的视频
    """
    # 检查分类是否存在
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 获取分类 ID（包括子分类）
    def get_all_category_ids(cat_id):
        ids = [cat_id]
        children = db.query(Category).filter(Category.parent_id == cat_id).all()
        for child in children:
            ids.extend(get_all_category_ids(child.id))
        return ids
    
    category_ids = get_all_category_ids(category_id)
    
    # 查询视频
    video_ids = db.query(VideoCategory.video_id).filter(
        VideoCategory.category_id.in_(category_ids)
    ).distinct()
    
    videos = db.query(Video).filter(
        Video.id.in_(video_ids),
        Video.is_valid == True
    ).order_by(Video.modified_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    total = db.query(Video).filter(
        Video.id.in_(video_ids),
        Video.is_valid == True
    ).count()
    
    return {
        "videos": videos,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/tags/{tag_id}/videos")
async def get_tag_videos(
    tag_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取标签下的视频
    """
    # 检查标签是否存在
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 查询视频
    video_ids = db.query(VideoTag.video_id).filter(VideoTag.tag_id == tag_id).distinct()
    
    videos = db.query(Video).filter(
        Video.id.in_(video_ids),
        Video.is_valid == True
    ).order_by(Video.modified_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    total = db.query(Video).filter(
        Video.id.in_(video_ids),
        Video.is_valid == True
    ).count()
    
    return {
        "videos": videos,
        "total": total,
        "page": page,
        "page_size": page_size
    }
