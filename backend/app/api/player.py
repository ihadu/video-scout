"""
播放器 API - 支持按需生成缩略图
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse, Response
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
from datetime import datetime
import os

from models import Video, TranscodeTask, get_db
from services.thumbnail import ThumbnailService
from services.transcoder import transcode_video_background


router = APIRouter()

thumbnail_service = ThumbnailService()


@router.get("/{video_id}")
async def play_video(
    video_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    播放视频（支持 Range 请求，优先返回转码后的 MP4）
    对于不支持的格式，会自动触发转码

    - **video_id**: 视频 ID
    """
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 增加观看次数
    video.watch_count = (video.watch_count or 0) + 1
    video.last_watched_at = datetime.utcnow()
    db.commit()

    # 优先使用转码后的 MP4 文件
    file_path = Path(video.file_path)

    # 查询已完成的转码任务
    transcode_task = db.query(TranscodeTask).filter(
        TranscodeTask.video_id == video_id,
        TranscodeTask.status == "completed"
    ).first()

    if transcode_task and transcode_task.transcoded_path:
        transcoded_path = Path(transcode_task.transcoded_path)
        if transcoded_path.exists():
            file_path = transcoded_path
    else:
        # 检查是否需要自动转码（格式不支持且没有进行中的转码任务）
        if not is_browser_supported(video.format):
            # 检查是否已有进行中的转码任务
            existing_task = db.query(TranscodeTask).filter(
                TranscodeTask.video_id == video_id,
                TranscodeTask.status.in_(["pending", "running"])
            ).first()

            if not existing_task:
                # 自动创建转码任务
                new_task = TranscodeTask(
                    video_id=video_id,
                    status="pending",
                    original_path=video.file_path
                )
                db.add(new_task)
                db.commit()
                db.refresh(new_task)

                # 后台启动转码
                background_tasks.add_task(transcode_video_background, new_task.id)

                # 返回转码中状态
                raise HTTPException(
                    status_code=503,  # Service Unavailable
                    detail={
                        "error": "transcoding_required",
                        "message": "此视频格式需要转码后才能播放",
                        "hint": "转码任务已自动启动，请稍后重试",
                        "task_id": new_task.id
                    }
                )
            else:
                # 已有转码任务进行中
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "transcoding_in_progress",
                        "message": "视频正在转码中",
                        "hint": f"转码进度: {existing_task.progress}%",
                        "progress": existing_task.progress,
                        "task_id": existing_task.id
                    }
                )

    if not file_path.exists():
        raise HTTPException(
            status_code=410,  # Gone - 资源已不存在
            detail={
                "error": "video_file_not_found",
                "message": f"视频文件不存在：{video.file_path}",
                "hint": "请检查外接硬盘是否已挂载"
            }
        )
    
    file_size = file_path.stat().st_size

    # 根据实际使用的文件路径确定 MIME 类型
    if transcode_task and transcode_task.transcoded_path and Path(transcode_task.transcoded_path).exists():
        # 使用转码后文件的格式（.mp4）
        mime_type = "video/mp4"
    else:
        # 使用原始视频格式
        mime_type = get_video_mime_type(video.format)

    # 获取 Range 头
    range_header = request.headers.get("range")
    
    if range_header:
        # 处理 Range 请求
        # request.headers.get("range") 只返回值部分，如 "bytes=0-1023"
        range_value = range_header.strip()
        if range_value.startswith("bytes="):
            bytes_range = range_value[6:]
            
            # 解析字节范围
            if "-" in bytes_range:
                start_str, end_str = bytes_range.split("-", 1)
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
            else:
                start = 0
                end = file_size - 1
            
            # 限制范围
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            
            content_length = end - start + 1
            
            # 返回 206 Partial Content - 使用正确的流式读取
            return StreamingResponse(
                stream_video_file(file_path, start, content_length),
                media_type=mime_type,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                },
                status_code=206
            )
    
    # 无 Range 请求，返回完整文件
    return StreamingResponse(
        stream_video_file(file_path, 0, file_size),
        media_type=mime_type,
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        }
    )


def stream_video_file(file_path: Path, start: int, length: int):
    """
    流式读取视频文件（正确的实现）
    
    Args:
        file_path: 文件路径
        start: 起始位置
        length: 读取长度
        
    Yields:
        8KB 数据块
    """
    chunk_size = 8192
    bytes_read = 0
    
    with open(file_path, "rb") as f:
        # 移动到起始位置
        f.seek(start)
        
        # 分块读取
        while bytes_read < length:
            chunk = f.read(min(chunk_size, length - bytes_read))
            if not chunk:
                break
            yield chunk
            bytes_read += len(chunk)


def get_video_mime_type(format: Optional[str]) -> str:
    """
    根据视频格式获取 MIME 类型
    """
    mime_types = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".flv": "video/x-flv",
        ".m4v": "video/x-m4v"
    }
    
    if format:
        return mime_types.get(format.lower(), "video/mp4")
    return "video/mp4"


def is_browser_supported(format: Optional[str], is_transcoded: bool = False) -> bool:
    """
    检查视频格式是否被浏览器原生支持

    Args:
        format: 视频格式
        is_transcoded: 是否是转码后的文件（转码后总是 MP4，所以总是支持）
    """
    if is_transcoded:
        return True
    supported_formats = {'.mp4', '.webm', '.m4v'}
    if format:
        return format.lower() in supported_formats
    return False


@router.get("/thumbnail/{video_id}")
async def get_thumbnail(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    获取视频缩略图（按需生成）
    
    - **video_id**: 视频 ID
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 尝试按需生成缩略图
    thumbnail_path = thumbnail_service.generate_on_demand(db, video_id)
    
    if not thumbnail_path:
        # 如果生成失败，返回一个默认 SVG 占位图
        placeholder_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180">
  <rect width="320" height="180" fill="#16213e"/>
  <circle cx="160" cy="90" r="40" fill="#0f3460"/>
  <polygon points="145,75 145,105 175,90" fill="#e94560"/>
  <text x="160" y="150" font-family="Arial, sans-serif" font-size="14" fill="#888" text-anchor="middle">缩略图生成中...</text>
</svg>'''
        return Response(
            content=placeholder_svg,
            media_type="image/svg+xml",
            headers={"X-Thumbnail-Status": "not-available"}
        )
    
    thumbnail_file = Path(thumbnail_path)
    
    if not thumbnail_file.exists():
        raise HTTPException(status_code=404, detail="缩略图不存在")
    
    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg"
    )


@router.get("/info/{video_id}")
async def get_video_play_info(video_id: int, db: Session = Depends(get_db)):
    """
    获取视频播放信息（包括是否支持浏览器播放）

    - **video_id**: 视频 ID
    """
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 检查文件是否存在
    file_path = Path(video.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=410,
            detail={
                "error": "video_file_not_found",
                "message": f"视频文件不存在：{video.file_path}",
                "hint": "请检查外接硬盘是否已挂载"
            }
        )

    # 检查是否有已完成的转码任务
    transcode_task = db.query(TranscodeTask).filter(
        TranscodeTask.video_id == video_id,
        TranscodeTask.status == "completed"
    ).first()
    is_transcoded = transcode_task is not None and transcode_task.transcoded_path and Path(transcode_task.transcoded_path).exists()

    # 如果有转码文件，总是视为支持
    supported = is_browser_supported(video.format, is_transcoded=is_transcoded)

    return {
        "id": video.id,
        "file_name": video.file_name,
        "file_path": video.file_path,
        "file_size": video.file_size,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "format": video.format,
        "codec": video.codec,
        "browser_supported": supported,
        "has_transcoded": is_transcoded,
        "transcoded_path": transcode_task.transcoded_path if is_transcoded else None,
        "thumbnail_path": f"/api/play/thumbnail/{video_id}",
        "created_at": video.created_at.isoformat() if video.created_at else None
    }


@router.delete("/file/{video_id}")
async def delete_video_file(video_id: int, db: Session = Depends(get_db)):
    """
    物理删除视频文件（⚠️ 危险操作）
    
    - **video_id**: 视频 ID
    - 此操作会永久删除视频文件，无法恢复！
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    file_path = Path(video.file_path)
    
    # 检查文件是否存在
    if not file_path.exists():
        # 文件已不存在，只删除数据库记录
        db.delete(video)
        db.commit()
        return {
            "message": "视频文件已不存在，已删除数据库记录",
            "file_deleted": False
        }
    
    try:
        # 删除文件
        file_path.unlink()
        file_deleted = True
        print(f"已删除视频文件：{file_path}")
    except PermissionError:
        raise HTTPException(status_code=403, detail="没有权限删除该文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败：{str(e)}")
    
    # 删除数据库记录
    db.delete(video)
    db.commit()
    
    return {
        "message": "视频文件和数据库记录已删除",
        "file_deleted": file_deleted,
        "file_path": str(file_path)
    }
