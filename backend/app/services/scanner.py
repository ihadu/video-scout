"""
视频扫描服务 - 支持增量扫描、进度追踪和自动转码归档
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Generator
from datetime import datetime

from sqlalchemy.orm import Session
from models import Video, ScanDirectory, ScanTask, TranscodeTask, get_db
from services.transcoder import (
    TranscoderService,
    BROWSER_SUPPORTED_FORMATS,
    NEEDS_TRANSCODE_FORMATS
)

# 进度更新频率：每 10 个文件或每 1%（取较大值）
PROGRESS_UPDATE_INTERVAL = 10


# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v'}

# ffprobe 路径（使用 conda 环境）
FFPROBE_PATH = "/Users/ihadu/miniconda3/envs/video-tools/bin/ffprobe"


class VideoScanner:
    """视频扫描服务"""
    
    def __init__(self):
        pass
    
    def get_video_files(self, directory_path: str) -> Generator[str, None, None]:
        """
        递归获取目录下所有视频文件
        
        Args:
            directory_path: 目录路径
            
        Yields:
            视频文件路径
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            raise ValueError(f"目录不存在：{directory_path}")
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
                yield str(file_path)
    
    def count_files(self, directory_path: str) -> int:
        """
        统计目录下视频文件总数
        
        Args:
            directory_path: 目录路径
            
        Returns:
            文件数量
        """
        return sum(1 for _ in self.get_video_files(directory_path))
    
    def extract_metadata(self, file_path: str) -> Optional[Dict]:
        """
        使用 ffprobe 提取视频元数据
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            元数据字典，失败返回 None
        """
        try:
            cmd = [
                FFPROBE_PATH,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60  # 增加超时时间
            )
            
            if result.returncode != 0:
                print(f"ffprobe 失败 {file_path}: {result.stderr}")
                return None
            
            data = json.loads(result.stdout)
            
            # 提取格式信息
            format_info = data.get('format', {})
            duration = float(format_info.get('duration', 0))
            file_size = int(format_info.get('size', 0))
            
            # 提取视频流信息
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            codec = video_stream.get('codec_name', '')
            
            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': file_size,
                'duration': duration,
                'width': width,
                'height': height,
                'format': os.path.splitext(file_path)[1].lower(),
                'codec': codec
            }
            
        except subprocess.TimeoutExpired:
            print(f"提取元数据超时：{file_path}")
            return None
        except Exception as e:
            print(f"提取元数据失败 {file_path}: {e}")
            return None
    
    def get_file_mtime(self, file_path: str) -> Optional[datetime]:
        """获取文件修改时间"""
        try:
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime)
        except:
            return None
    
    def save_or_update_video(self, db: Session, video_info: Dict, file_mtime: datetime) -> Video:
        """
        保存或更新视频记录

        Args:
            db: 数据库会话
            video_info: 视频元数据
            file_mtime: 文件修改时间

        Returns:
            视频对象
        """
        file_path = video_info['file_path']

        # 检查是否已存在
        existing = db.query(Video).filter(Video.file_path == file_path).first()

        if existing:
            # 检查文件是否变化
            if existing.file_mtime and existing.file_mtime == file_mtime:
                # 文件未变化，跳过更新
                return existing

            # 更新现有记录
            existing.file_name = video_info['file_name']
            existing.file_size = video_info['file_size']
            existing.duration = video_info['duration']
            existing.width = video_info['width']
            existing.height = video_info['height']
            existing.format = video_info['format']
            existing.codec = video_info.get('codec')
            existing.modified_at = datetime.utcnow()
            existing.file_mtime = file_mtime
            existing.is_valid = True
            existing.thumbnail_generated = False  # 文件变化后缩略图失效
            return existing
        else:
            # 创建新记录
            video = Video(
                file_path=file_path,
                file_name=video_info['file_name'],
                file_size=video_info['file_size'],
                duration=video_info['duration'],
                width=video_info['width'],
                height=video_info['height'],
                format=video_info['format'],
                codec=video_info.get('codec'),
                file_mtime=file_mtime,
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow(),
                is_valid=True,
                thumbnail_generated=False
            )
            db.add(video)
            db.flush()  # 获取 ID
            return video
    
    def check_stop_flag(self, directory_id: int, db: Session) -> bool:
        """
        检查停止标志

        Args:
            directory_id: 目录 ID
            db: 数据库会话

        Returns:
            是否应该停止
        """
        task = db.query(ScanTask).filter(
            ScanTask.directory_id == directory_id,
            ScanTask.status == 'running'
        ).order_by(ScanTask.created_at.desc()).first()

        if task and task.stop_flag:
            return True
        return False

    def save_checkpoint(self, idx: int, directory_id: int, db: Session):
        """
        保存断点

        Args:
            idx: 当前索引
            directory_id: 目录 ID
            db: 数据库会话
        """
        task = db.query(ScanTask).filter(
            ScanTask.directory_id == directory_id,
            ScanTask.status == 'running'
        ).order_by(ScanTask.created_at.desc()).first()

        if task:
            task.checkpoint = idx
            db.commit()

    def get_checkpoint(self, directory_id: int, db: Session) -> int:
        """
        获取断点位置

        Args:
            directory_id: 目录 ID
            db: 数据库会话

        Returns:
            断点索引
        """
        task = db.query(ScanTask).filter(
            ScanTask.directory_id == directory_id,
            ScanTask.status.in_(['running', 'cancelled'])
        ).order_by(ScanTask.created_at.desc()).first()

        if task:
            return task.checkpoint
        return 0

    def update_current_file(self, file_path: str, directory_id: int, db: Session):
        """
        更新当前扫描文件路径

        Args:
            file_path: 文件路径
            directory_id: 目录 ID
            db: 数据库会话
        """
        task = db.query(ScanTask).filter(
            ScanTask.directory_id == directory_id,
            ScanTask.status == 'running'
        ).order_by(ScanTask.created_at.desc()).first()

        if task:
            task.current_file_path = file_path
            db.commit()

    def scan_directory_incremental(self, db: Session, directory_id: int,
                                   directory_path: str, callback=None) -> Dict:
        """
        增量扫描目录（支持断点续传和优雅停止）

        Args:
            db: 数据库会话
            directory_id: 目录 ID
            directory_path: 目录路径
            callback: 进度回调函数 (directory_id, progress, scanned, total)

        Returns:
            扫描统计信息
        """
        stats = {
            'total': 0,
            'scanned': 0,
            'skipped': 0,
            'success': 0,
            'failed': 0
        }

        # 获取所有视频文件
        all_files = list(self.get_video_files(directory_path))
        total = len(all_files)
        stats['total'] = total

        # 获取断点位置
        checkpoint = self.get_checkpoint(directory_id, db)

        print(f"开始扫描目录 {directory_path}，共 {total} 个文件，断点：{checkpoint}")

        for idx, file_path in enumerate(all_files):
            try:
                # 从断点恢复
                if idx < checkpoint:
                    continue

                # 检查停止标志
                if self.check_stop_flag(directory_id, db):
                    self.save_checkpoint(idx, directory_id, db)
                    print(f"扫描被取消，保存断点：{idx}/{total}")
                    stats['cancelled_at'] = idx
                    return stats

                # 更新当前扫描文件路径
                self.update_current_file(file_path, directory_id, db)

                # 调用回调函数更新进度（更频繁的更新）
                if callback:
                    progress = int((idx + 1) / total * 100) if total > 0 else 0
                    callback(directory_id, progress, idx + 1, total)

                # 获取文件修改时间
                file_mtime = self.get_file_mtime(file_path)

                if not file_mtime:
                    stats['failed'] += 1
                    stats['scanned'] += 1
                    continue

                # 检查数据库中是否已存在且未变化
                existing = db.query(Video).filter(Video.file_path == file_path).first()

                if existing and existing.file_mtime and existing.file_mtime == file_mtime:
                    # 文件未变化，跳过
                    stats['skipped'] += 1
                    stats['scanned'] += 1

                    # 更频繁的进度更新
                    if stats['scanned'] % PROGRESS_UPDATE_INTERVAL == 0:
                        db.commit()
                    continue

                # 提取元数据
                video_info = self.extract_metadata(file_path)

                if not video_info:
                    # 提取失败，标记为无效
                    if existing:
                        existing.is_valid = False
                        existing.modified_at = datetime.utcnow()
                    stats['failed'] += 1
                else:
                    # 保存或更新
                    video = self.save_or_update_video(db, video_info, file_mtime)
                    video_id = video.id
                    stats['success'] += 1

                stats['scanned'] += 1

                # 更频繁的提交（每 10 个文件）
                if stats['scanned'] % PROGRESS_UPDATE_INTERVAL == 0:
                    db.commit()
                    print(f"已处理 {stats['scanned']}/{total} 个文件")

            except Exception as e:
                print(f"扫描文件失败 {file_path}: {e}")
                stats['failed'] += 1
                continue

        # 提交剩余数据
        db.commit()

        print(f"扫描完成：成功 {stats['success']}, 跳过 {stats['skipped']}, 失败 {stats['failed']}")
        return stats
    
    def mark_missing_files(self, db: Session, directory_path: str):
        """
        标记已不存在的文件为无效
        
        Args:
            db: 数据库会话
            directory_path: 目录路径
        """
        # 获取数据库中该目录下的所有视频
        videos = db.query(Video).filter(
            Video.file_path.startswith(directory_path),
            Video.is_valid == True
        ).all()
        
        marked_count = 0
        for video in videos:
            if not os.path.exists(video.file_path):
                video.is_valid = False
                video.modified_at = datetime.utcnow()
                marked_count += 1
        
        if marked_count > 0:
            db.commit()
            print(f"标记 {marked_count} 个不存在的文件为无效")
        
        return marked_count
    
    def verify_all_directories(self, db: Session) -> Dict:
        """
        验证所有活跃目录的完整性
        
        Args:
            db: 数据库会话
            
        Returns:
            验证统计信息
        """
        stats = {
            'total_directories': 0,
            'total_videos': 0,
            'marked_invalid': 0,
            'details': []
        }
        
        # 获取所有活跃目录
        directories = db.query(ScanDirectory).filter(
            ScanDirectory.is_active == True
        ).all()
        
        stats['total_directories'] = len(directories)
        
        for directory in directories:
            dir_stats = {
                'directory_id': directory.id,
                'directory_name': directory.name,
                'directory_path': directory.path,
                'marked_count': 0
            }
            
            # 检查该目录下的视频文件
            marked_count = self.mark_missing_files(db, directory.path)
            dir_stats['marked_count'] = marked_count
            stats['marked_invalid'] += marked_count
            
            # 统计该目录下的视频总数
            video_count = db.query(Video).filter(
                Video.file_path.startswith(directory.path)
            ).count()
            dir_stats['total_videos'] = video_count
            stats['total_videos'] += video_count
            
            stats['details'].append(dir_stats)
        
        # 提交所有更改
        if stats['marked_invalid'] > 0:
            db.commit()

        return stats

    def needs_transcode(self, video: Video) -> bool:
        """
        检查视频是否需要转码

        Args:
            video: 视频对象

        Returns:
            是否需要转码
        """
        ext = video.format.lower() if video.format else ''
        return ext in NEEDS_TRANSCODE_FORMATS

    def create_transcode_task_for_video(
        self,
        db: Session,
        video: Video,
        archive_mode: str = 'keep',
        archive_path: Optional[str] = None
    ) -> Optional[TranscodeTask]:
        """
        为视频创建转码任务

        Args:
            db: 数据库会话
            video: 视频对象
            archive_mode: 归档模式
            archive_path: 自定义归档路径

        Returns:
            转码任务对象，或 None
        """
        # 检查是否已存在待处理或运行中的任务
        existing = db.query(TranscodeTask).filter(
            TranscodeTask.video_id == video.id,
            TranscodeTask.status.in_(['pending', 'running'])
        ).first()

        if existing:
            print(f"    [跳过] 视频 {video.file_name} 已有待处理任务")
            return None

        # 检查转码后的MP4是否已存在
        dir_name = os.path.dirname(video.file_path)
        base_name = os.path.splitext(os.path.basename(video.file_path))[0]
        mp4_path = os.path.join(dir_name, f"{base_name}.mp4")

        if os.path.exists(mp4_path):
            print(f"    [跳过] 转码后的MP4已存在: {mp4_path}")
            # 更新视频记录指向MP4
            video.file_path = mp4_path
            video.file_name = os.path.basename(mp4_path)
            video.format = '.mp4'
            video.modified_at = datetime.utcnow()
            db.commit()
            return None

        # 创建转码任务
        task = TranscodeTask(
            video_id=video.id,
            status='pending',
            progress=0,
            original_path=video.file_path,
            created_at=datetime.utcnow()
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"    [创建] 转码任务 ID: {task.id}，视频: {video.file_name}")
        return task

    def scan_directory_with_auto_transcode(
        self,
        db: Session,
        directory_id: int,
        directory_path: str,
        auto_transcode: bool = False,
        archive_mode: str = 'keep',
        archive_path: Optional[str] = None,
        callback=None
    ) -> Dict:
        """
        扫描目录，支持自动转码归档

        Args:
            db: 数据库会话
            directory_id: 目录 ID
            directory_path: 目录路径
            auto_transcode: 是否自动转码
            archive_mode: 归档模式 ('keep', 'subdir', 'custom', 'delete')
            archive_path: 自定义归档路径
            callback: 进度回调函数

        Returns:
            扫描统计信息
        """
        # 首先执行常规扫描
        stats = self.scan_directory_incremental(db, directory_id, directory_path, callback)

        if not auto_transcode:
            return stats

        # 自动转码处理
        print(f"\n[自动转码] 开始处理需要转码的视频...")

        transcode_stats = {
            'transcode_total': 0,
            'transcode_created': 0,
            'transcode_skipped': 0
        }

        # 获取该目录下所有需要转码的视频
        videos = db.query(Video).filter(
            Video.file_path.startswith(directory_path),
            Video.is_valid == True
        ).all()

        for video in videos:
            if self.needs_transcode(video):
                transcode_stats['transcode_total'] += 1

                # 确定归档路径
                current_archive_path = archive_path
                if archive_mode == 'subdir':
                    current_archive_path = None  # transcode_with_archive会自动处理

                task = self.create_transcode_task_for_video(
                    db, video, archive_mode, current_archive_path
                )

                if task:
                    transcode_stats['transcode_created'] += 1
                else:
                    transcode_stats['transcode_skipped'] += 1

        print(f"[自动转码] 完成：总计 {transcode_stats['transcode_total']}, "
              f"创建任务 {transcode_stats['transcode_created']}, "
              f"跳过 {transcode_stats['transcode_skipped']}")

        # 合并统计信息
        stats.update(transcode_stats)
        return stats

