"""
视频转码服务 - 将 AVI 等格式转换为 MP4
"""

import subprocess
import os
from datetime import datetime
from typing import Optional, Callable

from sqlalchemy.orm import Session
from models import TranscodeTask, Video, get_db


# ffmpeg 路径
FFMPEG_PATH = "/Users/ihadu/miniconda3/envs/video-tools/bin/ffmpeg"


class TranscoderService:
    """视频转码服务"""

    def __init__(self):
        pass

    def transcode(
        self,
        video_id: int,
        original_path: str,
        output_path: str,
        callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        将视频转换为 MP4 格式

        Args:
            video_id: 视频 ID
            original_path: 原文件路径
            output_path: 输出文件路径
            callback: 进度回调函数 (video_id, progress)

        Returns:
            是否成功
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 使用 ffmpeg 进行转码，保持原视频质量
            cmd = [
                FFMPEG_PATH,
                "-i", original_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-y",  # 覆盖输出文件
                output_path
            ]

            print(f"开始转码：{original_path} -> {output_path}")

            # 执行转码
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待完成
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"转码成功：{output_path}")
                if callback:
                    callback(video_id, 100)
                return True
            else:
                print(f"转码失败：{stderr}")
                return False

        except Exception as e:
            print(f"转码异常：{e}")
            return False

    def get_output_path(self, original_path: str) -> str:
        """
        生成转码后文件路径

        Args:
            original_path: 原文件路径

        Returns:
            转码后文件路径
        """
        # 在同目录下生成.mp4 文件
        dir_name = os.path.dirname(original_path)
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        output_path = os.path.join(dir_name, f"{base_name}.mp4")

        return output_path


def transcode_video_background(task_id: int):
    """
    后台转码任务

    Args:
        task_id: 转码任务 ID
    """
    db = next(get_db())
    try:
        # 获取转码任务
        task = db.query(TranscodeTask).filter(TranscodeTask.id == task_id).first()
        if not task:
            raise ValueError("转码任务不存在")

        # 获取视频信息
        video = db.query(Video).filter(Video.id == task.video_id).first()
        if not video:
            raise ValueError("视频不存在")

        # 更新任务状态为运行中
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.progress = 0
        db.commit()

        # 生成输出路径
        transcoder = TranscoderService()
        output_path = transcoder.get_output_path(task.original_path)

        # 进度回调
        def progress_callback(vid: int, progress: int):
            db.query(TranscodeTask).filter(TranscodeTask.id == task_id).update({
                'progress': progress
            })
            db.commit()

        # 执行转码
        success = transcoder.transcode(
            video_id=task.video_id,
            original_path=task.original_path,
            output_path=output_path,
            callback=progress_callback
        )

        if success:
            task.status = "completed"
            task.transcoded_path = output_path
            task.progress = 100
        else:
            task.status = "failed"
            task.error_message = "转码失败，请检查日志"

        task.completed_at = datetime.utcnow()
        db.commit()

        print(f"转码任务 {task_id} 完成，状态：{task.status}")

    except Exception as e:
        print(f"转码任务失败：{e}")
        import traceback
        traceback.print_exc()

        try:
            task = db.query(TranscodeTask).filter(TranscodeTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass
    finally:
        db.close()
