-- 添加扫描目录自动转码配置字段
-- 执行时间: 2026-03-22

-- 添加 auto_transcode 字段
ALTER TABLE scan_directories
ADD COLUMN IF NOT EXISTS auto_transcode BOOLEAN DEFAULT FALSE;

-- 添加 archive_mode 字段
ALTER TABLE scan_directories
ADD COLUMN IF NOT EXISTS archive_mode VARCHAR(32) DEFAULT 'keep';

-- 添加 archive_path 字段
ALTER TABLE scan_directories
ADD COLUMN IF NOT EXISTS archive_path VARCHAR(1024);

-- 添加注释（PostgreSQL 支持）
COMMENT ON COLUMN scan_directories.auto_transcode IS '是否自动转码';
COMMENT ON COLUMN scan_directories.archive_mode IS '归档模式: keep|subdir|custom|delete';
COMMENT ON COLUMN scan_directories.archive_path IS '自定义归档路径';

-- 验证迁移
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'scan_directories'
ORDER BY ordinal_position;
