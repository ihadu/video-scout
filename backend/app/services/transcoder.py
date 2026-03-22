"""
视频转码服务 - 将 AVI 等格式转换为 MP4，支持归档模式
"""

import subprocess
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Literal

from sqlalchemy.orm import Session
from models import TranscodeTask, Video, SessionLocal


# ffmpeg 路径
FFMPEG_PATH = "/Users/ihadu/miniconda3/envs/video-tools/bin/ffmpeg"
FFPROBE_PATH = "/Users/ihadu/miniconda3/envs/video-tools/bin/ffprobe"


class TranscoderService:
    """视频转码服务"""

    def __init__(self):
        pass

    def get_video_duration(self, video_path: str) -> Optional[float]:
        """获取视频总时长（秒）"""
        try:
            cmd = [
                FFPROBE_PATH,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            print(f"获取视频时长失败：{e}")
        return None

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

            # 获取视频总时长
            total_duration = self.get_video_duration(original_path)
            if total_duration:
                print(f"视频总时长：{total_duration:.2f}秒")

            # 使用 ffmpeg 进行转码，添加 -progress 参数输出进度到 stdout
            cmd = [
                FFMPEG_PATH,
                "-i", original_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-y",  # 覆盖输出文件
                "-progress", "pipe:1",  # 输出进度信息到 stdout
                "-v", "error",  # 只输出错误信息到 stderr
                output_path
            ]

            print(f"开始转码：{original_path} -> {output_path}")

            # 执行转码并实时获取进度
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # 行缓冲
            )

            # 解析 progress 输出
            # ffmpeg -progress 输出格式: out_time_us=12345678\nprogress=continue\n...
            current_time_us = 0
            current_progress = 0
            last_reported_progress = -1

            while True:
                line = process.stdout.readline()
                if not line:
                    break

                line = line.strip()

                # 解析 out_time_us (微秒)
                if line.startswith('out_time_us='):
                    try:
                        current_time_us = int(line.split('=')[1])
                    except (ValueError, IndexError):
                        pass

                # 解析 progress 状态行，表示一次进度更新完成
                if line.startswith('progress=') and total_duration:
                    # 将微秒转换为秒
                    current_time = current_time_us / 1000000.0
                    current_progress = min(int((current_time / total_duration) * 100), 99)

                    # 回调更新进度（只在进度变化时更新）
                    if callback and current_progress != last_reported_progress:
                        callback(video_id, current_progress)
                        last_reported_progress = current_progress

            # 等待进程完成
            stdout_data, stderr_data = process.communicate()

            if process.returncode == 0:
                print(f"转码成功：{output_path}")
                if callback:
                    callback(video_id, 100)
                return True
            else:
                print(f"转码失败，返回码：{process.returncode}")
                if stderr_data:
                    print(f"错误信息：{stderr_data[-500:]}")  # 打印最后 500 字符错误信息
                return False

        except Exception as e:
            print(f"转码异常：{e}")
            import traceback
            traceback.print_exc()
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

    def transcode_with_archive(
        self,
        video_id: int,
        original_path: str,
        output_path: str,
        archive_mode: Literal['keep', 'subdir', 'custom', 'delete'] = 'keep',
        archive_path: Optional[str] = None,
        callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        转码并归档原视频

        Args:
            video_id: 视频ID
            original_path: 原文件路径
            output_path: 输出文件路径（MP4）
            archive_mode: 归档模式
                - 'keep': 保留原视频（当前行为）
                - 'subdir': 移动到同目录 .archive/ 子目录
                - 'custom': 移动到指定归档路径
                - 'delete': 删除原视频
            archive_path: 自定义归档路径（archive_mode='custom'时使用）
            callback: 进度回调 (video_id, progress)

        Returns:
            是否成功
        """
        # 1. 执行转码
        success = self.transcode(video_id, original_path, output_path, callback)

        if not success:
            print(f"[归档转码] 视频 {video_id} 转码失败，保留原视频")
            return False

        # 2. 转码成功，处理原视频归档
        try:
            if archive_mode == 'delete':
                # 删除原视频
                os.remove(original_path)
                print(f"[归档转码] 已删除原视频：{original_path}")

            elif archive_mode == 'subdir':
                # 移动到同目录的 .archive/ 子目录
                self._archive_to_subdir(original_path)

            elif archive_mode == 'custom' and archive_path:
                # 移动到指定归档路径
                self._archive_to_custom(original_path, archive_path)

            elif archive_mode == 'keep':
                print(f"[归档转码] 保留原视频：{original_path}")

            return True

        except Exception as e:
            print(f"[归档转码] 归档原视频失败：{e}")
            # 归档失败不影响转码成功状态
            return True

    def _archive_to_subdir(self, original_path: str) -> str:
        """
        将原视频移动到同目录的 .archive/ 子目录

        Args:
            original_path: 原文件路径

        Returns:
            归档后的文件路径
        """
        dir_name = os.path.dirname(original_path)
        file_name = os.path.basename(original_path)
        archive_dir = os.path.join(dir_name, '.archive')

        # 创建归档目录
        os.makedirs(archive_dir, exist_ok=True)

        # 移动文件
        archive_path = os.path.join(archive_dir, file_name)

        # 如果目标文件已存在，添加数字后缀
        counter = 1
        base_name, ext = os.path.splitext(file_name)
        while os.path.exists(archive_path):
            archive_path = os.path.join(archive_dir, f"{base_name}_{counter}{ext}")
            counter += 1

        shutil.move(original_path, archive_path)
        print(f"[归档转码] 原视频已归档到：{archive_path}")
        return archive_path

    def _archive_to_custom(self, original_path: str, custom_archive_path: str) -> str:
        """
        将原视频移动到指定归档路径

        Args:
            original_path: 原文件路径
            custom_archive_path: 自定义归档路径

        Returns:
            归档后的文件路径
        """
        # 获取原视频相对于其父目录的相对路径
        original_dir = os.path.dirname(original_path)
        file_name = os.path.basename(original_path)

        # 在归档路径中保持相同的目录结构
        archive_dir = custom_archive_path

        # 创建归档目录
        os.makedirs(archive_dir, exist_ok=True)

        # 移动文件
        archive_path = os.path.join(archive_dir, file_name)

        # 如果目标文件已存在，添加数字后缀
        counter = 1
        base_name, ext = os.path.splitext(file_name)
        while os.path.exists(archive_path):
            archive_path = os.path.join(archive_dir, f"{base_name}_{counter}{ext}")
            counter += 1

        shutil.move(original_path, archive_path)
        print(f"[归档转码] 原视频已归档到：{archive_path}")
        return archive_path


# 浏览器支持的格式
BROWSER_SUPPORTED_FORMATS = {'.mp4', '.webm', '.m4v'}

# 需要转码的格式
NEEDS_TRANSCODE_FORMATS = {'.avi', '.mov', '.mkv', '.flv', '.wmv', '.ts', '.m2ts'}


def transcode_video_background(
    task_id: int,
    archive_mode: Literal['keep', 'subdir', 'custom', 'delete'] = 'keep',
    archive_path: Optional[str] = None
):
    """
    后台转码任务，完成后自动归档

    Args:
        task_id: 转码任务 ID
        archive_mode: 归档模式
            - 'keep': 保留原视频
            - 'subdir': 移动到同目录 .archive/ 子目录
            - 'custom': 移动到指定归档路径
            - 'delete': 删除原视频
        archive_path: 自定义归档路径（archive_mode='custom'时使用）
    """
    db = SessionLocal()
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

        # 进度回调 - 使用新会话避免长时间事务
        def progress_callback(vid: int, progress: int):
            try:
                # 每10%或每5%更新一次，避免频繁更新
                if progress % 5 == 0:
                    db.query(TranscodeTask).filter(TranscodeTask.id == task_id).update({
                        'progress': progress
                    })
                    db.commit()
                    print(f"[转码] 视频 {vid} 进度更新: {progress}%")
            except Exception as e:
                print(f"[转码] 更新进度失败: {e}")
                db.rollback()

        # 执行转码并归档
        success = transcoder.transcode_with_archive(
            video_id=task.video_id,
            original_path=task.original_path,
            output_path=output_path,
            archive_mode=archive_mode,
            archive_path=archive_path,
            callback=progress_callback
        )

        if success:
            task.status = "completed"
            task.transcoded_path = output_path
            task.progress = 100

            # 更新视频记录，指向新的MP4路径
            video.file_path = output_path
            video.file_name = os.path.basename(output_path)
            video.format = '.mp4'
            video.modified_at = datetime.utcnow()
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
