-- 为 scan_tasks 表添加新字段
ALTER TABLE scan_tasks ADD COLUMN IF NOT EXISTS current_file_path VARCHAR(4096);
ALTER TABLE scan_tasks ADD COLUMN IF NOT EXISTS stop_flag BOOLEAN DEFAULT FALSE;
ALTER TABLE scan_tasks ADD COLUMN IF NOT EXISTS checkpoint INTEGER DEFAULT 0;

-- 为 videos 表添加新字段
ALTER TABLE videos ADD COLUMN IF NOT EXISTS transcode_task_id INTEGER;

-- 验证迁移结果
SELECT '迁移完成' AS status;
