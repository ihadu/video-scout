"""
数据库迁移脚本 - 添加新字段
"""

from app.models import engine
from sqlalchemy import text, inspect

def migrate():
    # 检查表结构
    inspector = inspect(engine)

    # 获取 scan_tasks 现有列
    scan_task_cols = [col['name'] for col in inspector.get_columns('scan_tasks')]
    print(f"scan_tasks 现有列：{scan_task_cols}")

    # 获取 videos 现有列
    video_cols = [col['name'] for col in inspector.get_columns('videos')]
    print(f"videos 现有列：{video_cols}")

    # 添加缺失的字段
    with engine.connect() as conn:
        # 为 ScanTask 添加新字段
        if 'current_file_path' not in scan_task_cols:
            try:
                conn.execute(text("ALTER TABLE scan_tasks ADD COLUMN current_file_path VARCHAR(4096)"))
                conn.commit()
                print("✓ 添加 current_file_path 字段")
            except Exception as e:
                print(f"✗ current_file_path 失败：{e}")

        if 'stop_flag' not in scan_task_cols:
            try:
                conn.execute(text("ALTER TABLE scan_tasks ADD COLUMN stop_flag BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("✓ 添加 stop_flag 字段")
            except Exception as e:
                print(f"✗ stop_flag 失败：{e}")

        if 'checkpoint' not in scan_task_cols:
            try:
                conn.execute(text("ALTER TABLE scan_tasks ADD COLUMN checkpoint INTEGER DEFAULT 0"))
                conn.commit()
                print("✓ 添加 checkpoint 字段")
            except Exception as e:
                print(f"✗ checkpoint 失败：{e}")

        # 为 Video 添加 transcode_task_id
        if 'transcode_task_id' not in video_cols:
            try:
                conn.execute(text("ALTER TABLE videos ADD COLUMN transcode_task_id INTEGER"))
                conn.commit()
                print("✓ 添加 transcode_task_id 字段")
            except Exception as e:
                print(f"✗ transcode_task_id 失败：{e}")

    print("\n数据库迁移完成！")

if __name__ == "__main__":
    migrate()
