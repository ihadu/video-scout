"""
数据库模型定义 - PostgreSQL 版本
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os
from typing import Generator

# PostgreSQL 连接配置
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'ihadu')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'videoscout')

# 构建数据库连接 URL
if POSTGRES_PASSWORD:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动检测失效连接
    pool_size=10,        # 连接池大小
    max_overflow=20      # 最大额外连接数
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Video(Base):
    """视频元数据模型"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(2048), nullable=False, index=True)
    file_name = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # 字节
    duration = Column(Float, nullable=False, index=True)  # 秒
    width = Column(Integer, nullable=True)  # 视频宽度
    height = Column(Integer, nullable=True)  # 视频高度
    format = Column(String(32), nullable=True, index=True)  # 视频格式
    codec = Column(String(64), nullable=True)  # 编解码器
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    thumbnail_generated = Column(Boolean, default=False)  # 缩略图是否已生成
    file_mtime = Column(DateTime, nullable=True)  # 文件修改时间（用于增量扫描）
    is_valid = Column(Boolean, default=True, nullable=False, index=True)  # 文件是否有效
    watch_count = Column(Integer, default=0, nullable=False)  # 观看次数
    last_watched_at = Column(DateTime, nullable=True)  # 最后观看时间

    # 创建复合索引以提升查询性能
    __table_args__ = (
        Index('idx_videos_search', 'file_name', 'file_path'),
        Index('idx_videos_duration', 'duration', 'is_valid'),
        Index('idx_videos_format', 'format', 'is_valid'),
        Index('idx_videos_created_at', 'created_at', 'is_valid'),
        Index('idx_videos_modified_at', 'modified_at', 'is_valid'),
    )

    # 一对多关系：一个视频可以有多个转码任务
    transcode_tasks = relationship("TranscodeTask", back_populates="video", uselist=False)


class ScanDirectory(Base):
    """扫描目录配置模型"""
    __tablename__ = "scan_directories"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(1024), unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_scanned = Column(DateTime, nullable=True)
    scan_progress = Column(Integer, default=0)  # 扫描进度（百分比）
    total_files = Column(Integer, default=0)  # 目录总文件数
    scanned_files = Column(Integer, default=0)  # 已扫描文件数
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ScanTask(Base):
    """扫描任务模型（支持中断恢复）"""
    __tablename__ = "scan_tasks"

    id = Column(Integer, primary_key=True, index=True)
    directory_id = Column(Integer, nullable=False, index=True)
    status = Column(String(32), default='pending', nullable=False)  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 进度（百分比）
    scanned_count = Column(Integer, default=0)  # 已扫描数量
    success_count = Column(Integer, default=0)  # 成功数量
    failed_count = Column(Integer, default=0)  # 失败数量
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 新增字段：支持断点续传
    current_file_path = Column(String(4096), nullable=True)  # 当前扫描的文件路径
    stop_flag = Column(Boolean, default=False)  # 停止标志
    checkpoint = Column(Integer, default=0)  # 断点位置（已扫描文件索引）


class TranscodeTask(Base):
    """视频转码任务模型"""
    __tablename__ = "transcode_tasks"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    status = Column(String(32), default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 进度（百分比）
    original_path = Column(String(4096), nullable=True)  # 原文件路径
    transcoded_path = Column(String(4096), nullable=True)  # 转码后文件路径
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    video = relationship("Video", back_populates="transcode_tasks")

    # 一对多关系：一个转码任务可能有多个视频（如果设计需要）
    # 这里使用单向关系，避免循环依赖


class UserFavorite(Base):
    """用户收藏模型"""
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, unique=True, nullable=False, index=True)  # 视频 ID（唯一，避免重复收藏）
    rating = Column(Integer, default=0, nullable=True)  # 评分：0-5 星，0 表示未评分
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WatchHistory(Base):
    """观看历史模型"""
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=False, index=True)
    progress = Column(Float, default=0)  # 观看进度（秒）
    watched_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_watch_history_video', 'video_id', 'watched_at'),
    )


class Category(Base):
    """分类模型（支持树形结构）"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=True, index=True)  # 父分类 ID，支持多级分类
    sort_order = Column(Integer, default=0)  # 排序顺序
    icon = Column(String(50), nullable=True)  # 分类图标（emoji）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Tag(Base):
    """标签模型"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default='#e94560')  # 标签颜色
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class VideoCategory(Base):
    """视频 - 分类关联表"""
    __tablename__ = "video_categories"

    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class VideoTag(Base):
    """视频 - 标签关联表"""
    __tablename__ = "video_tags"

    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化数据库
def init_db():
    """初始化数据库表"""
    print("初始化数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表初始化完成！")
