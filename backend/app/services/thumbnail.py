"""
缩略图服务 - 按需生成
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from models import Video


class ThumbnailService:
    """缩略图生成服务"""
    
    def __init__(self):
        # 使用环境变量或默认绝对路径
        self.output_dir = Path(os.getenv('THUMBNAIL_DIR', '/app/data/thumbnails'))
        # 确保缩略图目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_thumbnail(self, video_path: str, video_id: int) -> Optional[str]:
        """
        生成视频缩略图
        
        策略：
        - 优先取视频时长的 10% 位置
        - 如果视频 < 30 秒，取中间帧
        - 如果视频 < 5 秒，取第 2 秒
        
        Args:
            video_path: 视频文件路径
            video_id: 视频 ID
            
        Returns:
            缩略图路径，失败返回 None
        """
        try:
            # 先获取视频时长
            duration = self.get_video_duration(video_path)
            
            if not duration or duration <= 0:
                print(f"无法获取视频时长：{video_path}")
                return None
            
            # 计算截取时间点
            if duration < 5:
                # 超短视频，取第 2 秒
                seek_time = min(2, duration - 0.1)
            elif duration < 30:
                # 短视频，取中间帧
                seek_time = duration / 2
            else:
                # 正常视频，取 10% 位置
                seek_time = duration * 0.1
            
            # 计算缩略图文件名
            thumbnail_filename = f"thumb_{video_id}.jpg"
            thumbnail_path = self.output_dir / thumbnail_filename
            
            # ffmpeg 命令：截取指定时间点的帧
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(seek_time),      # seek 到指定时间
                '-vframes', '1',             # 只提取 1 帧
                '-vf', 'scale=-2:240',      # 高度 240px，宽度自动计算
                '-q:v', '3',                 # 质量 (1-31，越小质量越高)
                '-y',                        # 覆盖已存在文件
                '-loglevel', 'error',        # 减少输出
                str(thumbnail_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            if result.returncode == 0 and thumbnail_path.exists():
                return str(thumbnail_path)
            else:
                print(f"生成缩略图失败：{result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"生成缩略图超时：{video_path}")
            return None
        except Exception as e:
            print(f"生成缩略图异常 {video_path}: {e}")
            return None
    
    def get_video_duration(self, video_path: str) -> Optional[float]:
        """
        获取视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            时长（秒），失败返回 None
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                video_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            
            return duration if duration > 0 else None
            
        except Exception as e:
            print(f"获取视频时长失败 {video_path}: {e}")
            return None
    
    def get_thumbnail_path(self, video_id: int) -> str:
        """
        获取缩略图路径
        
        Args:
            video_id: 视频 ID
            
        Returns:
            缩略图路径
        """
        return str(self.output_dir / f"thumb_{video_id}.jpg")
    
    def thumbnail_exists(self, video_id: int) -> bool:
        """
        检查缩略图是否存在
        
        Args:
            video_id: 视频 ID
            
        Returns:
            是否存在
        """
        return self.get_thumbnail_path(video_id).exists()
    
    def generate_on_demand(self, db: Session, video_id: int) -> Optional[str]:
        """
        按需生成缩略图
        
        Args:
            db: 数据库会话
            video_id: 视频 ID
            
        Returns:
            缩略图路径，失败返回 None
        """
        # 获取视频信息
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            print(f"视频不存在：{video_id}")
            return None
        
        if not video.is_valid:
            print(f"视频无效：{video_id}")
            return None
        
        # 检查缩略图是否已存在
        if self.thumbnail_exists(video_id):
            # 检查数据库中是否标记为已生成
            if not video.thumbnail_generated:
                video.thumbnail_generated = True
                db.commit()
            return self.get_thumbnail_path(video_id)
        
        # 生成缩略图
        thumbnail_path = self.generate_thumbnail(video.file_path, video_id)
        
        if thumbnail_path:
            # 更新数据库标记
            video.thumbnail_generated = True
            db.commit()
        
        return thumbnail_path
