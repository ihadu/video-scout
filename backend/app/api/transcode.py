"""
转码 API
"""

import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from models import TranscodeTask, Video, get_db
from services.transcoder import transcode_video_background


router = APIRouter(prefix="/transcode", tags=["转码"])


@router.post("/start/{video_id}")
async def start_transcode(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    启动视频转码任务

    - **video_id**: 视频 ID
    """
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 检查是否已有转码任务
    existing_task = db.query(TranscodeTask).filter(
        TranscodeTask.video_id == video_id,
        TranscodeTask.status.in_(["pending", "running"])
    ).first()

    if existing_task:
        raise HTTPException(status_code=400, detail="转码任务正在进行中")

    # 创建转码任务
    task = TranscodeTask(
        video_id=video_id,
        status="pending",
        original_path=video.file_path
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 后台执行转码
    background_tasks.add_task(transcode_video_background, task.id)

    return {
        "task_id": task.id,
        "status": task.status,
        "message": "转码任务已启动"
    }


@router.get("/status/{video_id}")
async def get_transcode_status(video_id: int, db: Session = Depends(get_db)):
    """
    获取转码任务状态

    - **video_id**: 视频 ID
    """
    task = db.query(TranscodeTask).filter(
        TranscodeTask.video_id == video_id
    ).order_by(TranscodeTask.created_at.desc()).first()

    if not task:
        return {"status": "not_started"}

    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "transcoded_path": task.transcoded_path,
        "error_message": task.error_message,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }


@router.post("/cancel/{video_id}")
async def cancel_transcode(video_id: int, db: Session = Depends(get_db)):
    """
    取消转码任务

    - **video_id**: 视频 ID
    """
    task = db.query(TranscodeTask).filter(
        TranscodeTask.video_id == video_id,
        TranscodeTask.status.in_(["pending", "running"])
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="没有进行中的转码任务")

    task.status = "cancelled"
    task.completed_at = datetime.utcnow()
    db.commit()

    return {
        "message": "转码任务已取消",
        "task_id": task.id
    }


@router.post("/delete/{video_id}")
async def delete_transcoded_file(video_id: int, db: Session = Depends(get_db)):
    """
    删除转码后的文件

    - **video_id**: 视频 ID
    """
    task = db.query(TranscodeTask).filter(
        TranscodeTask.video_id == video_id,
        TranscodeTask.status == "completed"
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="没有找到转码后的文件")

    # 删除文件
    if task.transcoded_path and os.path.exists(task.transcoded_path):
        try:
            os.remove(task.transcoded_path)
            print(f"删除转码文件：{task.transcoded_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除文件失败：{e}")

    # 更新任务状态
    task.status = "cancelled"
    task.transcoded_path = None
    task.completed_at = datetime.utcnow()
    db.commit()

    return {
        "message": "转码文件已删除",
        "task_id": task.id
    }
