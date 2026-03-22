"""
批量转码归档脚本

功能：
1. 扫描所有视频目录
2. 找出 browser_supported=False 的视频
3. 批量转码为 MP4
4. 原视频移动到归档目录

用法：
    python batch_transcode.py --scan-dir /path/to/videos --archive-mode subdir
    python batch_transcode.py --all-dirs --archive-mode subdir  # 使用各目录下的.archive子目录
    python batch_transcode.py --scan-dir /path/to/videos --archive-mode custom --archive-path /path/to/archive
    python batch_transcode.py --scan-dir /path/to/videos --archive-mode delete  # 转码后删除原视频
    python batch_transcode.py --scan-dir /path/to/videos --archive-mode keep  # 保留原视频
    python batch_transcode.py --all-dirs --dry-run  # 预览模式

归档模式：
    keep    - 保留原视频（当前行为）
    subdir  - 移动到同目录 .archive/ 子目录
    custom  - 移动到指定归档路径（需要 --archive-path）
    delete  - 删除原视频
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root / 'app'))

from sqlalchemy.orm import Session
from models import Video, ScanDirectory, TranscodeTask, SessionLocal
from services.transcoder import (
    TranscoderService,
    BROWSER_SUPPORTED_FORMATS,
    NEEDS_TRANSCODE_FORMATS
)


def get_unsupported_videos(db: Session, directory_path: str) -> List[Video]:
    """
    获取指定目录下所有浏览器不支持的格式的视频

    Args:
        db: 数据库会话
        directory_path: 目录路径

    Returns:
        需要转码的视频列表
    """
    videos = db.query(Video).filter(
        Video.file_path.startswith(directory_path),
        Video.is_valid == True
    ).all()

    unsupported = []
    for video in videos:
        ext = video.format.lower() if video.format else ''
        if ext in NEEDS_TRANSCODE_FORMATS:
            # 检查是否已存在转码任务
            existing_task = db.query(TranscodeTask).filter(
                TranscodeTask.video_id == video.id,
                TranscodeTask.status.in_(['pending', 'running', 'completed'])
            ).first()

            if not existing_task:
                # 检查转码后的MP4是否已存在
                dir_name = os.path.dirname(video.file_path)
                base_name = os.path.splitext(os.path.basename(video.file_path))[0]
                mp4_path = os.path.join(dir_name, f"{base_name}.mp4")

                if not os.path.exists(mp4_path):
                    unsupported.append(video)

    return unsupported


def create_transcode_task(
    db: Session,
    video: Video,
    archive_mode: str = 'keep',
    archive_path: Optional[str] = None
) -> Optional[TranscodeTask]:
    """
    创建转码任务

    Args:
        db: 数据库会话
        video: 视频记录
        archive_mode: 归档模式
        archive_path: 自定义归档路径

    Returns:
        转码任务对象，或 None 如果创建失败
    """
    try:
        # 检查是否已存在待处理或运行中的任务
        existing = db.query(TranscodeTask).filter(
            TranscodeTask.video_id == video.id,
            TranscodeTask.status.in_(['pending', 'running'])
        ).first()

        if existing:
            print(f"  [跳过] 视频 {video.file_name} 已有待处理任务")
            return None

        # 创建新任务
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

        return task

    except Exception as e:
        print(f"  [错误] 创建转码任务失败：{e}")
        db.rollback()
        return None


def process_single_video(
    db: Session,
    video: Video,
    archive_mode: str = 'keep',
    archive_path: Optional[str] = None,
    dry_run: bool = False
) -> bool:
    """
    处理单个视频：转码并归档

    Args:
        db: 数据库会话
        video: 视频记录
        archive_mode: 归档模式
        archive_path: 自定义归档路径
        dry_run: 是否仅预览

    Returns:
        是否成功
    """
    print(f"\n处理视频：{video.file_name}")
    print(f"  原路径：{video.file_path}")
    print(f"  格式：{video.format}")
    print(f"  归档模式：{archive_mode}")

    if dry_run:
        print("  [预览模式] 跳过实际执行")
        return True

    # 创建转码任务
    task = create_transcode_task(db, video, archive_mode, archive_path)
    if not task:
        return False

    # 执行转码
    transcoder = TranscoderService()
    output_path = transcoder.get_output_path(video.file_path)

    def progress_callback(vid: int, progress: int):
        if progress % 10 == 0:
            print(f"    转码进度：{progress}%")

    success = transcoder.transcode_with_archive(
        video_id=video.id,
        original_path=video.file_path,
        output_path=output_path,
        archive_mode=archive_mode,
        archive_path=archive_path,
        callback=progress_callback
    )

    if success:
        # 更新任务状态
        task.status = 'completed'
        task.transcoded_path = output_path
        task.progress = 100
        task.completed_at = datetime.utcnow()

        # 更新视频记录
        video.file_path = output_path
        video.file_name = os.path.basename(output_path)
        video.format = '.mp4'
        video.modified_at = datetime.utcnow()

        db.commit()
        print(f"  [成功] 转码完成并已归档")
        return True
    else:
        task.status = 'failed'
        task.error_message = "转码失败"
        task.completed_at = datetime.utcnow()
        db.commit()
        print(f"  [失败] 转码失败")
        return False


def process_directory(
    db: Session,
    directory_path: str,
    archive_mode: str = 'keep',
    archive_path: Optional[str] = None,
    dry_run: bool = False
) -> dict:
    """
    处理单个目录

    Args:
        db: 数据库会话
        directory_path: 目录路径
        archive_mode: 归档模式
        archive_path: 自定义归档路径
        dry_run: 是否仅预览

    Returns:
        处理统计信息
    """
    print(f"\n{'='*60}")
    print(f"扫描目录：{directory_path}")
    print(f"{'='*60}")

    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0
    }

    # 获取需要转码的视频
    videos = get_unsupported_videos(db, directory_path)
    stats['total'] = len(videos)

    print(f"\n找到 {len(videos)} 个需要转码的视频\n")

    if dry_run:
        for video in videos:
            ext = video.format.lower() if video.format else ''
            output_name = os.path.splitext(os.path.basename(video.file_path))[0] + '.mp4'
            print(f"[预览] {video.file_name} -> {output_name}")
            if archive_mode == 'subdir':
                print(f"       原文件将归档到: .archive/")
            elif archive_mode == 'custom' and archive_path:
                print(f"       原文件将归档到: {archive_path}/")
            elif archive_mode == 'delete':
                print(f"       原文件将被删除")
        return stats

    # 实际处理
    for idx, video in enumerate(videos, 1):
        print(f"\n[{idx}/{len(videos)}] ", end='')

        # 如果是子目录模式，使用视频所在目录的.archive子目录
        current_archive_path = archive_path
        if archive_mode == 'subdir':
            current_archive_path = None  # transcode_with_archive会自动处理

        success = process_single_video(
            db, video, archive_mode, current_archive_path, dry_run=False
        )

        if success:
            stats['success'] += 1
        else:
            stats['failed'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='批量转码归档脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 预览模式
  python batch_transcode.py --scan-dir /path/to/videos --dry-run

  # 转码并归档到子目录
  python batch_transcode.py --scan-dir /path/to/videos --archive-mode subdir

  # 转码并归档到自定义目录
  python batch_transcode.py --scan-dir /path/to/videos --archive-mode custom --archive-path /path/to/archive

  # 转码后删除原视频
  python batch_transcode.py --scan-dir /path/to/videos --archive-mode delete

  # 处理所有配置的扫描目录
  python batch_transcode.py --all-dirs --archive-mode subdir
        """
    )

    parser.add_argument(
        '--scan-dir',
        type=str,
        help='要扫描的目录路径'
    )

    parser.add_argument(
        '--all-dirs',
        action='store_true',
        help='处理所有配置的扫描目录'
    )

    parser.add_argument(
        '--archive-mode',
        type=str,
        choices=['keep', 'subdir', 'custom', 'delete'],
        default='keep',
        help='归档模式：keep=保留, subdir=归档到子目录, custom=自定义路径, delete=删除'
    )

    parser.add_argument(
        '--archive-path',
        type=str,
        help='自定义归档路径（archive-mode=custom时使用）'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际执行转码'
    )

    args = parser.parse_args()

    # 验证参数
    if not args.scan_dir and not args.all_dirs:
        print("错误：必须指定 --scan-dir 或 --all-dirs")
        parser.print_help()
        sys.exit(1)

    if args.archive_mode == 'custom' and not args.archive_path:
        print("错误：使用 --archive-mode custom 时必须指定 --archive-path")
        parser.print_help()
        sys.exit(1)

    # 开始处理
    print("\n" + "="*60)
    print("批量转码归档脚本")
    print("="*60)
    print(f"归档模式: {args.archive_mode}")
    if args.archive_path:
        print(f"归档路径: {args.archive_path}")
    if args.dry_run:
        print("模式: 预览模式（不实际执行）")
    print("="*60 + "\n")

    db = SessionLocal()
    try:
        total_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        if args.all_dirs:
            # 处理所有配置的扫描目录
            directories = db.query(ScanDirectory).filter(
                ScanDirectory.is_active == True
            ).all()

            for directory in directories:
                stats = process_directory(
                    db,
                    directory.path,
                    args.archive_mode,
                    args.archive_path,
                    args.dry_run
                )

                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
        else:
            # 处理单个目录
            stats = process_directory(
                db,
                args.scan_dir,
                args.archive_mode,
                args.archive_path,
                args.dry_run
            )
            total_stats = stats

        # 输出总结
        print("\n" + "="*60)
        print("处理完成")
        print("="*60)
        print(f"总视频数: {total_stats['total']}")
        print(f"成功: {total_stats['success']}")
        print(f"失败: {total_stats['failed']}")
        print(f"跳过: {total_stats['skipped']}")
        print("="*60)

    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
