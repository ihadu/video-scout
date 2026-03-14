"""
扫描 API - 支持进度追踪
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from models import ScanDirectory, ScanTask, get_db
from services.scanner import VideoScanner


router = APIRouter()

scanner = VideoScanner()


class ScanDirectoryCreate(BaseModel):
    """创建扫描目录请求"""
    path: str
    name: Optional[str] = None


class ScanDirectoryResponse(BaseModel):
    """扫描目录响应"""
    id: int
    path: str
    name: str
    is_active: bool
    last_scanned: Optional[datetime] = None
    total_files: Optional[int] = None
    scanned_files: Optional[int] = None
    
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
        
        # 进度回调函数 - 更新数据库
        def callback(dir_id, progress, scanned, total):
            # 每 10% 更新一次数据库，减少写入次数
            if progress % 10 == 0:
                db.query(ScanTask).filter(ScanTask.directory_id == dir_id).update({
                    'progress': progress,
                    'scanned_count': scanned
                })
                db.commit()
        
        # 执行扫描
        stats = scanner.scan_directory_incremental(
            db, directory_id, directory.path, callback
        )
        
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
        
        print(f"扫描完成：目录 {directory.name}, 成功 {stats['success']}, 跳过 {stats.get('skipped', 0)}, 失败 {stats['failed']}")
        
    except Exception as e:
        print(f"扫描失败：{e}")
        import traceback
        traceback.print_exc()
        
        # 更新任务状态
        try:
            if 'task' in locals():
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
    
    # 创建扫描目录记录
    name = scan_dir.name or os.path.basename(scan_dir.path)
    directory = ScanDirectory(
        path=scan_dir.path,
        name=name,
        is_active=True
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
    获取扫描状态（已添加的目录列表 + 扫描任务状态）
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
            "scanned_files": d.scanned_files
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
                "error_message": latest_task.error_message
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
        "error_message": latest_task.error_message
    }


@router.delete("/remove/{directory_id}")
async def remove_scan_directory(
    directory_id: int,
    db: Session = Depends(get_db)
):
    """
    移除扫描目录
    
    - **directory_id**: 目录 ID
    """
    directory = db.query(ScanDirectory).filter(
        ScanDirectory.id == directory_id
    ).first()
    
    if not directory:
        raise HTTPException(status_code=404, detail="目录不存在")
    
    db.delete(directory)
    db.commit()
    
    return {"message": "目录已移除"}


@router.post("/toggle/{directory_id}")
async def toggle_directory(
    directory_id: int,
    db: Session = Depends(get_db)
):
    """
    启用/禁用扫描目录
    
    - **directory_id**: 目录 ID
    """
    directory = db.query(ScanDirectory).filter(
        ScanDirectory.id == directory_id
    ).first()
    
    if not directory:
        raise HTTPException(status_code=404, detail="目录不存在")
    
    directory.is_active = not directory.is_active
    db.commit()
    
    return {
        "id": directory.id,
        "is_active": directory.is_active
    }
