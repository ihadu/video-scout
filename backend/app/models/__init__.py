"""
数据库模型定义 - PostgreSQL 版本
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from typing import Generator

# PostgreSQL 连接配置
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'videoscout')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'videoscout123')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'videoscout')

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

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
    
    # 创建复合索引以提升查询性能
    __table_args__ = (
        Index('idx_videos_search', 'file_name', 'file_path'),
        Index('idx_videos_duration', 'duration', 'is_valid'),
        Index('idx_videos_format', 'format', 'is_valid'),
        Index('idx_videos_created_at', 'created_at', 'is_valid'),
        Index('idx_videos_modified_at', 'modified_at', 'is_valid'),
    )


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
