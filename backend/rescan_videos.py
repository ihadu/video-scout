#!/usr/bin/env python3
"""
重新扫描所有视频并修复元数据
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

from app.models import Video, ScanDirectory, SessionLocal

# ffprobe 路径
FFPROBE_PATH = "/Users/ihadu/miniconda3/envs/video-tools/bin/ffprobe"


def extract_metadata(file_path: str) -> dict:
    """使用 ffprobe 提取视频元数据"""
    try:
        cmd = [
            FFPROBE_PATH,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f"  ffprobe 失败：{result.stderr[:100]}")
            return None

        data = json.loads(result.stdout)

        # 提取格式信息
        format_info = data.get('format', {})
        duration = float(format_info.get('duration', 0))
        file_size = int(format_info.get('size', 0))

        # 提取视频流信息（第一个视频流）
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            print(f"  警告：没有找到视频流")
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
        print(f"  提取元数据超时")
        return None
    except Exception as e:
        print(f"  提取元数据失败：{e}")
        return None


def rescan_all_videos():
    """重新扫描所有视频"""
    db = SessionLocal()

    # 获取所有视频
    videos = db.query(Video).all()
    total = len(videos)

    print(f"开始重新扫描 {total} 个视频...\n")

    updated = 0
    skipped = 0
    failed = 0
    file_not_found = 0

    for idx, video in enumerate(videos, 1):
        print(f"[{idx}/{total}] {video.file_name[:50]}...")

        # 检查文件是否存在
        if not os.path.exists(video.file_path):
            print(f"  文件不存在，标记为无效")
            video.is_valid = False
            file_not_found += 1
            db.commit()
            continue

        # 获取文件修改时间
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(video.file_path))
        except:
            file_mtime = None

        # 提取元数据
        metadata = extract_metadata(video.file_path)

        if not metadata:
            print(f"  提取失败，标记为无效")
            video.is_valid = False
            failed += 1
            db.commit()
            continue

        # 检查是否需要更新
        needs_update = (
            video.duration != metadata['duration'] or
            video.width != metadata['width'] or
            video.height != metadata['height'] or
            video.codec != metadata['codec'] or
            video.file_size != metadata['file_size']
        )

        if needs_update:
            # 更新元数据
            old_duration = video.duration
            old_width = video.width
            old_codec = video.codec

            video.file_name = metadata['file_name']
            video.file_size = metadata['file_size']
            video.duration = metadata['duration']
            video.width = metadata['width']
            video.height = metadata['height']
            video.format = metadata['format']
            video.codec = metadata['codec']
            video.modified_at = datetime.utcnow()
            video.file_mtime = file_mtime
            video.is_valid = True
            video.thumbnail_generated = False  # 文件变化后缩略图失效

            updated += 1
            print(f"  已更新：duration={old_duration:.1f}->{metadata['duration']:.1f}, "
                  f"width={old_width}->{metadata['width']}, "
                  f"codec={old_codec}->{metadata['codec']}")
        else:
            # 只更新修改时间和有效性
            video.file_mtime = file_mtime
            video.is_valid = True
            skipped += 1

        # 每处理 50 个视频提交一次
        if idx % 50 == 0:
            db.commit()
            print(f"\n  已处理 {idx}/{total}，更新 {updated}，跳过 {skipped}，失败 {failed}\n")

    # 提交剩余数据
    db.commit()
    db.close()

    # 打印统计
    print("\n" + "="*60)
    print("重新扫描完成！")
    print(f"  总计：{total}")
    print(f"  更新：{updated}")
    print(f"  跳过：{skipped}")
    print(f"  失败：{failed}")
    print(f"  文件不存在：{file_not_found}")
    print("="*60)


if __name__ == "__main__":
    rescan_all_videos()
