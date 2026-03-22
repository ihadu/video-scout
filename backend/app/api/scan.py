"""
扫描 API - 支持进度追踪
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from models import ScanDirectory, ScanTask, Video, get_db
from services.scanner import VideoScanner


router = APIRouter()

scanner = VideoScanner()


class ScanDirectoryCreate(BaseModel):
    """创建扫描目录请求"""
    path: str
    name: Optional[str] = None
    auto_transcode: bool = False
    archive_mode: str = 'keep'
    archive_path: Optional[str] = None


class ScanDirectoryUpdate(BaseModel):
    """更新扫描目录请求"""
    name: Optional[str] = None
    auto_transcode: Optional[bool] = None
    archive_mode: Optional[str] = None
    archive_path: Optional[str] = None


class ScanDirectoryResponse(BaseModel):
    """扫描目录响应"""
    id: int
    path: str
    name: str
    is_active: bool
    last_scanned: Optional[datetime] = None
    total_files: Optional[int] = None
    scanned_files: Optional[int] = None
    auto_transcode: bool = False
    archive_mode: str = 'keep'
    archive_path: Optional[str] = None

    class Config:
        from_attributes = True


class ScanStatusResponse(BaseModel):
    """扫描状态响应"""
    id: int
    status: str  # pending, running, completed, failed, cancelled
    progress: int  # 0-100
    scanned_count: int
    success_count: int
    failed_count: int
    error_message: Optional[str] = None


def scan_directory_background(directory_id: int):
    """
    后台扫描目录
    """
    db = next(get_db())
    task = None
    try:
        # 获取目录信息
        directory = db.query(ScanDirectory).filter(ScanDirectory.id == directory_id).first()

        if not directory:
            raise ValueError('目录不存在')

        # 创建扫描任务记录
        task = ScanTask(
            directory_id=directory_id,
            status='running',
            progress=0,
            started_at=datetime.utcnow()
        )
        db.add(task)
        db.commit()

        # 进度回调函数 - 更频繁更新数据库
        def callback(dir_id, progress, scanned, total):
            # 每 1% 或每 10 个文件更新一次
            db.query(ScanTask).filter(ScanTask.directory_id == dir_id).update({
                'progress': progress,
                'scanned_count': scanned
            })
            db.commit()

        # 执行扫描（支持自动转码）
        stats = scanner.scan_directory_with_auto_transcode(
            db=db,
            directory_id=directory_id,
            directory_path=directory.path,
            auto_transcode=directory.auto_transcode,
            archive_mode=directory.archive_mode or 'keep',
            archive_path=directory.archive_path,
            callback=callback
        )

        # 检查是否被取消
        if stats.get('cancelled_at') is not None:
            # 更新任务状态为已取消
            task.status = 'cancelled'
            task.completed_at = datetime.utcnow()
            db.commit()
            print(f"扫描已取消：目录 {directory.name}, 已扫描 {stats['scanned']}/{stats['total']}")
            return

        # 标记不存在的文件
        scanner.mark_missing_files(db, directory.path)

        # 更新任务状态
        task.status = 'completed'
        task.progress = 100
        task.scanned_count = stats['scanned']
        task.success_count = stats['success']
        task.failed_count = stats['failed']
        task.completed_at = datetime.utcnow()

        # 更新目录信息
        directory.last_scanned = datetime.utcnow()
        directory.scan_progress = 100
        directory.total_files = stats['total']
        directory.scanned_files = stats['scanned']

        db.commit()

        print(f"扫描完成：目录 {directory.name}, 成功 {stats['success']}, "
              f"跳过 {stats.get('skipped', 0)}, 失败 {stats['failed']}")

        # 如果有自动转码，输出转码统计
        if directory.auto_transcode:
            print(f"自动转码：总计 {stats.get('transcode_total', 0)}, "
                  f"创建任务 {stats.get('transcode_created', 0)}, "
                  f"跳过 {stats.get('transcode_skipped', 0)}")

    except Exception as e:
        print(f"扫描失败：{e}")
        import traceback
        traceback.print_exc()

        # 更新任务状态
        try:
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                db.commit()
        except:
            pass
    finally:
        db.close()


@router.post("/add", response_model=ScanDirectoryResponse)
async def add_scan_directory(
    scan_dir: ScanDirectoryCreate,
    db: Session = Depends(get_db)
):
    """
    添加扫描目录

    - **path**: 目录路径
    - **name**: 目录名称（可选，默认使用路径名）
    - **auto_transcode**: 是否自动转码（可选，默认 False）
    - **archive_mode**: 归档模式（可选，默认 'keep'）
        - 'keep': 保留原视频
        - 'subdir': 归档到 .archive/ 子目录
        - 'custom': 使用自定义归档路径
        - 'delete': 删除原视频
    - **archive_path**: 自定义归档路径（archive_mode='custom'时使用）
    """
    # 检查路径是否存在
    if not os.path.exists(scan_dir.path):
        raise HTTPException(status_code=400, detail="目录不存在")

    # 检查是否已存在
    existing = db.query(ScanDirectory).filter(
        ScanDirectory.path == scan_dir.path
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="目录已添加")

    # 验证归档模式
    if scan_dir.archive_mode not in ['keep', 'subdir', 'custom', 'delete']:
        raise HTTPException(status_code=400, detail="无效的归档模式")

    # 验证自定义归档路径
    if scan_dir.archive_mode == 'custom' and scan_dir.archive_path:
        if not os.path.exists(scan_dir.archive_path):
            raise HTTPException(status_code=400, detail="归档目录不存在")

    # 创建扫描目录记录
    name = scan_dir.name or os.path.basename(scan_dir.path)
    directory = ScanDirectory(
        path=scan_dir.path,
        name=name,
        is_active=True,
        auto_transcode=scan_dir.auto_transcode,
        archive_mode=scan_dir.archive_mode,
        archive_path=scan_dir.archive_path
    )

    db.add(directory)
    db.commit()
    db.refresh(directory)

    return ScanDirectoryResponse.model_validate(directory)


@router.post("/start")
async def start_scan(
    background_tasks: BackgroundTasks,
    directory_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    启动扫描任务（后台执行）
    
    - **directory_id**: 指定目录 ID，不指定则扫描所有活跃目录
    """
    if directory_id:
        # 扫描单个目录
        background_tasks.add_task(scan_directory_background, directory_id)
        return {
            "message": "扫描任务已启动",
            "directory_id": directory_id
        }
    else:
        # 扫描所有活跃目录
        directories = db.query(ScanDirectory).filter(
            ScanDirectory.is_active == True
        ).all()
        
        if not directories:
            raise HTTPException(status_code=400, detail="没有活跃的扫描目录")
        
        for directory in directories:
            background_tasks.add_task(scan_directory_background, directory.id)
        
        return {
            "message": f"已启动 {len(directories)} 个扫描任务"
        }


@router.get("/status")
async def get_scan_status(db: Session = Depends(get_db)):
    """
    获取扫描状态（已添加的目录列表 + 扫描任务状态 + 自动转码配置）
    """
    directories = db.query(ScanDirectory).all()

    result = []
    for d in directories:
        dir_info = {
            "id": d.id,
            "path": d.path,
            "name": d.name,
            "is_active": d.is_active,
            "last_scanned": d.last_scanned.isoformat() if d.last_scanned else None,
            "total_files": d.total_files,
            "scanned_files": d.scanned_files,
            "auto_transcode": d.auto_transcode,
            "archive_mode": d.archive_mode or 'keep',
            "archive_path": d.archive_path
        }

        # 从数据库获取最新的扫描任务状态
        latest_task = db.query(ScanTask).filter(
            ScanTask.directory_id == d.id
        ).order_by(ScanTask.created_at.desc()).first()

        if latest_task:
            dir_info["scan_task"] = {
                "task_id": latest_task.id,
                "status": latest_task.status,
                "progress": latest_task.progress,
                "scanned_count": latest_task.scanned_count,
                "success_count": latest_task.success_count,
                "failed_count": latest_task.failed_count,
                "error_message": latest_task.error_message,
                "current_file_path": latest_task.current_file_path,
                "checkpoint": latest_task.checkpoint
            }

        result.append(dir_info)

    return {"directories": result}


@router.get("/task/{directory_id}")
async def get_task_status(directory_id: int, db: Session = Depends(get_db)):
    """
    获取指定目录的扫描任务状态
    """
    latest_task = db.query(ScanTask).filter(
        ScanTask.directory_id == directory_id
    ).order_by(ScanTask.created_at.desc()).first()
    
    if not latest_task:
        raise HTTPException(status_code=404, detail="没有扫描任务记录")
    
    return {
        "task_id": latest_task.id,
        "status": latest_task.status,
        "progress": latest_task.progress,
        "scanned_count": latest_task.scanned_count,
        "success_count": latest_task.success_count,
        "failed_count": latest_task.failed_count,
        "error_message": latest_task.error_message,
        "current_file_path": latest_task.current_file_path,
        "checkpoint": latest_task.checkpoint
    }


@router.post("/cancel/{directory_id}")
async def cancel_scan(directory_id: int, db: Session = Depends(get_db)):
    """
    取消扫描任务（优雅停止）

    - **directory_id**: 目录 ID
    """
    # 查找进行中的任务
    running_task = db.query(ScanTask).filter(
        ScanTask.directory_id == directory_id,
        ScanTask.status == 'running'
    ).first()

    if not running_task:
        raise HTTPException(status_code=404, detail="没有进行中的扫描任务")

    # 设置停止标志，让扫描线程优雅退出
    running_task.stop_flag = True
    db.commit()

    return {
        "message": "扫描任务正在停止",
        "task_id": running_task.id
    }


@router.delete("/remove/{directory_id}")
async def remove_scan_directory(
    directory_id: int,
    delete_videos: bool = True,  # 默认删除视频
    db: Session = Depends(get_db)
):
    """
    移除扫描目录
    
    - **directory_id**: 目录 ID
    - **delete_videos**: 是否同时删除该目录下的视频记录（默认 True）
    """
    directory = db.query(ScanDirectory).filter(
        ScanDirectory.id == directory_id
    ).first()
    
    if not directory:
        raise HTTPException(status_code=404, detail="目录不存在")
    
    deleted_video_count = 0
    
    # 如果选择删除视频，先删除该目录下的所有视频记录
    if delete_videos:
        deleted_video_count = db.query(Video).filter(
            Video.file_path.startswith(directory.path)
        ).delete()
        print(f"删除目录 {directory.name} 关联的 {deleted_video_count} 个视频记录")
    
    # 删除目录配置
    db.delete(directory)
    db.commit()
    
    return {
        "message": "目录已移除",
        "deleted_videos": deleted_video_count if delete_videos else 0
    }


@router.post("/toggle/{directory_id}")
async def toggle_directory(
    directory_id: int,
    db: Session = Depends(get_db)
):
    """
    启用/禁用扫描目录
    
    - **directory_id**: 目录 ID
    - 禁用时会将该目录下所有视频标记为无效（不显示）
    - 启用时会恢复视频显示
    """
    directory = db.query(ScanDirectory).filter(
        ScanDirectory.id == directory_id
    ).first()
    
    if not directory:
        raise HTTPException(status_code=404, detail="目录不存在")
    
    # 切换启用/禁用状态
    new_status = not directory.is_active
    directory.is_active = new_status
    
    # 如果禁用目录，将该目录下所有视频标记为无效
    if not new_status:
        db.query(Video).filter(
            Video.file_path.startswith(directory.path),
            Video.is_valid == True
        ).update({'is_valid': False})
        print(f"禁用目录 {directory.name}，已隐藏该目录下所有视频")
    
    # 如果启用目录，将该目录下所有视频恢复为有效
    if new_status:
        db.query(Video).filter(
            Video.file_path.startswith(directory.path)
        ).update({'is_valid': True})
        print(f"启用目录 {directory.name}，已恢复该目录下所有视频")
    
    db.commit()
    
    return {
        "id": directory.id,
        "is_active": directory.is_active,
        "message": "目录已启用" if directory.is_active else "目录已禁用"
    }


@router.post("/verify")
async def verify_all_directories(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    手动触发完整性检查
    
    扫描所有活跃目录，标记不存在的文件为无效
    """
    # 立即返回，后台执行
    background_tasks.add_task(_verify_background, db)
    
    return {
        "message": "完整性检查任务已启动"
    }


def _verify_background(db: Session):
    """后台执行完整性检查"""
    try:
        scanner = VideoScanner()
        stats = scanner.verify_all_directories(db)
        
        print(f"完整性检查完成：标记 {stats['marked_invalid']} 个文件为无效")
        
    except Exception as e:
        print(f"完整性检查失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


@router.get("/verify/stats")
async def get_verify_stats(db: Session = Depends(get_db)):
    """
    获取无效视频统计信息
    """
    invalid_count = db.query(Video).filter(Video.is_valid == False).count()
    total_count = db.query(Video).count()
    valid_count = total_count - invalid_count

    return {
        "total_videos": total_count,
        "valid_videos": valid_count,
        "invalid_videos": invalid_count
    }


@router.put("/config/{directory_id}", response_model=ScanDirectoryResponse)
async def update_scan_directory_config(
    directory_id: int,
    config: ScanDirectoryUpdate,
    db: Session = Depends(get_db)
):
    """
    更新扫描目录配置

    - **directory_id**: 目录 ID
    - **name**: 目录名称（可选）
    - **auto_transcode**: 是否自动转码（可选）
    - **archive_mode**: 归档模式（可选）
        - 'keep': 保留原视频
        - 'subdir': 归档到 .archive/ 子目录
        - 'custom': 使用自定义归档路径
        - 'delete': 删除原视频
    - **archive_path**: 自定义归档路径（可选）
    """
    directory = db.query(ScanDirectory).filter(
        ScanDirectory.id == directory_id
    ).first()

    if not directory:
        raise HTTPException(status_code=404, detail="目录不存在")

    # 更新名称
    if config.name is not None:
        directory.name = config.name

    # 更新自动转码配置
    if config.auto_transcode is not None:
        directory.auto_transcode = config.auto_transcode

    # 更新归档模式
    if config.archive_mode is not None:
        if config.archive_mode not in ['keep', 'subdir', 'custom', 'delete']:
            raise HTTPException(status_code=400, detail="无效的归档模式")
        directory.archive_mode = config.archive_mode

    # 更新归档路径
    if config.archive_path is not None:
        if config.archive_path and not os.path.exists(config.archive_path):
            raise HTTPException(status_code=400, detail="归档目录不存在")
        directory.archive_path = config.archive_path

    db.commit()
    db.refresh(directory)

    return ScanDirectoryResponse.model_validate(directory)


@router.get("/config/{directory_id}", response_model=ScanDirectoryResponse)
async def get_scan_directory_config(
    directory_id: int,
    db: Session = Depends(get_db)
):
    """
    获取扫描目录配置

    - **directory_id**: 目录 ID
    """
    directory = db.query(ScanDirectory).filter(
        ScanDirectory.id == directory_id
    ).first()

    if not directory:
        raise HTTPException(status_code=404, detail="目录不存在")

    return ScanDirectoryResponse.model_validate(directory)
