"""
视频扫描服务 - 支持增量扫描和进度追踪
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Generator
from datetime import datetime

from sqlalchemy.orm import Session
from models import Video, ScanDirectory, ScanTask, get_db


# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v'}


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
                'ffprobe',
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
    
    def save_or_update_video(self, db: Session, video_info: Dict, file_mtime: datetime) -> int:
        """
        保存或更新视频记录
        
        Args:
            db: 数据库会话
            video_info: 视频元数据
            file_mtime: 文件修改时间
            
        Returns:
            视频 ID
        """
        file_path = video_info['file_path']
        
        # 检查是否已存在
        existing = db.query(Video).filter(Video.file_path == file_path).first()
        
        if existing:
            # 检查文件是否变化
            if existing.file_mtime and existing.file_mtime == file_mtime:
                # 文件未变化，跳过更新
                return existing.id
            
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
            return video.id
        
        return existing.id
    
    def scan_directory_incremental(self, db: Session, directory_id: int, 
                                   directory_path: str, callback=None) -> Dict:
        """
        增量扫描目录（只扫描新增或修改的文件）
        
        Args:
            db: 数据库会话
            directory_id: 目录 ID
            directory_path: 目录路径
            callback: 进度回调函数 (current, total, status)
            
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
        
        print(f"开始扫描目录 {directory_path}，共 {total} 个文件")
        
        for idx, file_path in enumerate(all_files):
            try:
                # 调用回调函数更新进度
                if callback:
                    progress = int((idx + 1) / total * 100)
                    callback(directory_id, progress, idx + 1, total)
                
                # 获取文件修改时间
                file_mtime = self.get_file_mtime(file_path)
                
                if not file_mtime:
                    stats['failed'] += 1
                    continue
                
                # 检查数据库中是否已存在且未变化
                existing = db.query(Video).filter(Video.file_path == file_path).first()
                
                if existing and existing.file_mtime and existing.file_mtime == file_mtime:
                    # 文件未变化，跳过
                    stats['skipped'] += 1
                    stats['scanned'] += 1
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
                    video_id = self.save_or_update_video(db, video_info, file_mtime)
                    stats['success'] += 1
                
                stats['scanned'] += 1
                
                # 每处理 100 个文件提交一次，避免事务过大
                if stats['scanned'] % 100 == 0:
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
