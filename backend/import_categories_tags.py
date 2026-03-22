#!/usr/bin/env python3
"""
批量导入分类标签脚本

功能：
1. 导入 23 个一级分类（带 emoji 图标和 sort_order 排序）
2. 导入通用标签（分辨率、画质、时长、状态共 10 个）
3. 导入各分类专属标签（约 80+ 个）

使用方法：
    cd backend
    python import_categories_tags.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# 导入模型
from app.models import Base, Category, Tag

# ==================== 数据定义 ====================

# 23 个一级分类
CATEGORIES = [
    {"name": "探花", "icon": "📁", "sort_order": 1},
    {"name": "海角", "icon": "📁", "sort_order": 2},
    {"name": "厕拍", "icon": "📁", "sort_order": 3},
    {"name": "抄底", "icon": "📁", "sort_order": 4},
    {"name": "酒店偷拍", "icon": "📁", "sort_order": 5},
    {"name": "直播录制", "icon": "📁", "sort_order": 6},
    {"name": "推油", "icon": "📁", "sort_order": 7},
    {"name": "露出野战", "icon": "📁", "sort_order": 8},
    {"name": "打电话", "icon": "📁", "sort_order": 9},
    {"name": "短视频", "icon": "📁", "sort_order": 10},
    {"name": "自拍泄漏", "icon": "📁", "sort_order": 11},
    {"name": "女同", "icon": "📁", "sort_order": 12},
    {"name": "迷药/下药", "icon": "📁", "sort_order": 13},
    {"name": "换妻/多人", "icon": "📁", "sort_order": 14},
    {"name": "自慰", "icon": "📁", "sort_order": 15},
    {"name": "舞蹈", "icon": "📁", "sort_order": 16},
    {"name": "私拍写真", "icon": "📁", "sort_order": 17},
    {"name": "AI 生成", "icon": "📁", "sort_order": 18},
    {"name": "VR", "icon": "📁", "sort_order": 19},
    {"name": "欧美", "icon": "📁", "sort_order": 20},
    {"name": "日韩", "icon": "📁", "sort_order": 21},
    {"name": "有水印有亮点", "icon": "📁", "sort_order": 22},
    {"name": "其他", "icon": "📁", "sort_order": 23},
]

# 通用标签（10 个）
COMMON_TAGS = [
    # 分辨率
    {"name": "4K", "color": "#3b82f6"},
    {"name": "1080P", "color": "#10b981"},
    {"name": "720P", "color": "#f59e0b"},
    {"name": "480P", "color": "#ef4444"},
    {"name": "模糊", "color": "#6b7280"},
    # 画质
    {"name": "无水印", "color": "#10b981"},
    {"name": "有水印", "color": "#f59e0b"},
    {"name": "修复版", "color": "#8b5cf6"},
    {"name": "原相机", "color": "#ec4899"},
    # 时长
    {"name": "短 (<3 分钟)", "color": "#3b82f6"},
    {"name": "中 (3-15 分钟)", "color": "#10b981"},
    {"name": "长 (>15 分钟)", "color": "#ef4444"},
    # 状态
    {"name": "完整", "color": "#10b981"},
    {"name": "片段", "color": "#f59e0b"},
    {"name": "合集", "color": "#8b5cf6"},
]

# 分类专属标签
CATEGORY_SPECIFIC_TAGS = {
    # 探花专属标签
    "探花": [
        # 来源
        {"name": "探花社", "color": "#e94560"},
        {"name": "探花论坛", "color": "#e94560"},
        {"name": "网盘资源", "color": "#3b82f6"},
        # 场景
        {"name": "跟踪", "color": "#10b981"},
        {"name": "偷拍", "color": "#f59e0b"},
        {"name": "街拍", "color": "#8b5cf6"},
        # 类型
        {"name": "素人", "color": "#ec4899"},
        {"name": "网红", "color": "#f97316"},
        {"name": "模特", "color": "#06b6d4"},
    ],
    # 海角专属标签
    "海角": [
        # 来源
        {"name": "海角 01", "color": "#e94560"},
        {"name": "海角 02", "color": "#e94560"},
        {"name": "海角论坛", "color": "#3b82f6"},
        # 场景
        {"name": "酒店", "color": "#10b981"},
        {"name": "民宿", "color": "#f59e0b"},
        # 类型
        {"name": "自拍", "color": "#ec4899"},
        {"name": "互拍", "color": "#f97316"},
    ],
    # 厕拍专属标签
    "厕拍": [
        # 场景
        {"name": "商场厕所", "color": "#10b981"},
        {"name": "公司厕所", "color": "#f59e0b"},
        {"name": "学校厕所", "color": "#8b5cf6"},
        {"name": "公共厕所", "color": "#ec4899"},
        # 设备
        {"name": "隐藏摄像头", "color": "#6b7280"},
        {"name": "手机偷拍", "color": "#ef4444"},
    ],
    # 抄底专属标签
    "抄底": [
        # 来源
        {"name": "闲鱼", "color": "#e94560"},
        {"name": "拼多多", "color": "#3b82f6"},
        {"name": "淘宝", "color": "#10b981"},
        # 类型
        {"name": "U 盘资源", "color": "#f59e0b"},
        {"name": "网盘账号", "color": "#8b5cf6"},
    ],
    # 酒店偷拍专属标签
    "酒店偷拍": [
        # 场景
        {"name": "经济酒店", "color": "#10b981"},
        {"name": "连锁酒店", "color": "#f59e0b"},
        {"name": "快捷酒店", "color": "#8b5cf6"},
        # 设备
        {"name": "针孔摄像头", "color": "#6b7280"},
        {"name": "智能设备", "color": "#ef4444"},
    ],
    # 直播录制专属标签
    "直播录制": [
        # 平台
        {"name": "抖音", "color": "#e94560"},
        {"name": "快手", "color": "#3b82f6"},
        {"name": "B 站", "color": "#f59e0b"},
        {"name": "斗鱼", "color": "#10b981"},
        {"name": "虎牙", "color": "#8b5cf6"},
        # 类型
        {"name": "主播", "color": "#ec4899"},
        {"name": "秀场", "color": "#f97316"},
        {"name": "聊天", "color": "#06b6d4"},
    ],
    # 推油专属标签
    "推油": [
        # 场景
        {"name": "按摩店", "color": "#10b981"},
        {"name": "SPA 馆", "color": "#f59e0b"},
        {"name": "养生馆", "color": "#8b5cf6"},
        # 类型
        {"name": "技师", "color": "#ec4899"},
        {"name": "顾客视角", "color": "#f97316"},
    ],
    # 露出野战专属标签
    "露出野战": [
        # 场景
        {"name": "公园", "color": "#10b981"},
        {"name": "野外", "color": "#f59e0b"},
        {"name": "车内", "color": "#8b5cf6"},
        {"name": "天台", "color": "#ec4899"},
        # 类型
        {"name": "露出", "color": "#e94560"},
        {"name": "野战", "color": "#3b82f6"},
    ],
    # 打电话专属标签
    "打电话": [
        # 场景
        {"name": "办公室", "color": "#10b981"},
        {"name": "家中", "color": "#f59e0b"},
        {"name": "公共场所", "color": "#8b5cf6"},
        # 类型
        {"name": "语音", "color": "#ec4899"},
        {"name": "视频通话", "color": "#f97316"},
    ],
    # 短视频专属标签
    "短视频": [
        # 平台
        {"name": "抖音", "color": "#e94560"},
        {"name": "快手", "color": "#3b82f6"},
        {"name": "小红书", "color": "#f59e0b"},
        {"name": "Instagram", "color": "#10b981"},
        # 类型
        {"name": "舞蹈", "color": "#8b5cf6"},
        {"name": "变装", "color": "#ec4899"},
        {"name": "日常", "color": "#f97316"},
    ],
    # 自拍泄漏专属标签
    "自拍泄漏": [
        # 来源
        {"name": "社交账号", "color": "#e94560"},
        {"name": "云盘泄漏", "color": "#3b82f6"},
        {"name": "黑客入侵", "color": "#ef4444"},
        # 类型
        {"name": "自拍视频", "color": "#10b981"},
        {"name": "私密视频", "color": "#f59e0b"},
    ],
    # 女同专属标签
    "女同": [
        # 类型
        {"name": "BB", "color": "#ec4899"},
        {"name": "BG", "color": "#f97316"},
        {"name": "GG", "color": "#06b6d4"},
        # 场景
        {"name": "宿舍", "color": "#10b981"},
        {"name": "家中", "color": "#f59e0b"},
    ],
    # 迷药/下药专属标签
    "迷药/下药": [
        # 场景
        {"name": "酒吧", "color": "#ef4444"},
        {"name": "KTV", "color": "#e94560"},
        {"name": "餐厅", "color": "#f59e0b"},
        # 类型
        {"name": "下药", "color": "#6b7280"},
        {"name": "迷晕", "color": "#ef4444"},
    ],
    # 换妻/多人专属标签
    "换妻/多人": [
        # 类型
        {"name": "换妻", "color": "#e94560"},
        {"name": "换夫", "color": "#3b82f6"},
        {"name": "群 P", "color": "#ef4444"},
        {"name": "乱伦", "color": "#f59e0b"},
        # 场景
        {"name": "派对", "color": "#8b5cf6"},
        {"name": "聚会", "color": "#ec4899"},
    ],
    # 自慰专属标签
    "自慰": [
        # 类型
        {"name": "手淫", "color": "#ec4899"},
        {"name": "器具", "color": "#f97316"},
        {"name": "口交", "color": "#06b6d4"},
        # 场景
        {"name": "浴室", "color": "#10b981"},
        {"name": "卧室", "color": "#f59e0b"},
    ],
    # 舞蹈专属标签
    "舞蹈": [
        # 类型
        {"name": "钢管舞", "color": "#e94560"},
        {"name": "肚皮舞", "color": "#f59e0b"},
        {"name": "爵士舞", "color": "#8b5cf6"},
        {"name": "现代舞", "color": "#ec4899"},
        # 场景
        {"name": "夜店", "color": "#ef4444"},
        {"name": "舞台", "color": "#f97316"},
    ],
    # 私拍写真专属标签
    "私拍写真": [
        # 类型
        {"name": "写真", "color": "#ec4899"},
        {"name": "私房", "color": "#f97316"},
        {"name": "内衣", "color": "#06b6d4"},
        {"name": "泳装", "color": "#3b82f6"},
        # 场景
        {"name": "摄影棚", "color": "#10b981"},
        {"name": "家中", "color": "#f59e0b"},
        {"name": "户外", "color": "#8b5cf6"},
    ],
    # AI 生成专属标签
    "AI 生成": [
        # 技术
        {"name": "Stable Diffusion", "color": "#8b5cf6"},
        {"name": "Midjourney", "color": "#ec4899"},
        {"name": "Sora", "color": "#e94560"},
        {"name": "Runway", "color": "#3b82f6"},
        # 类型
        {"name": "虚拟主播", "color": "#06b6d4"},
        {"name": "深度伪造", "color": "#ef4444"},
    ],
    # VR 专属标签
    "VR": [
        # 设备
        {"name": "Oculus", "color": "#3b82f6"},
        {"name": "HTC Vive", "color": "#e94560"},
        {"name": "PSVR", "color": "#10b981"},
        # 类型
        {"name": "360 度", "color": "#8b5cf6"},
        {"name": "第一人称", "color": "#ec4899"},
    ],
    # 欧美专属标签
    "欧美": [
        # 国家
        {"name": "美国", "color": "#3b82f6"},
        {"name": "欧洲", "color": "#10b981"},
        {"name": "英国", "color": "#e94560"},
        # 类型
        {"name": "欧美色情", "color": "#ef4444"},
        {"name": "欧美自拍", "color": "#ec4899"},
    ],
    # 日韩专属标签
    "日韩": [
        # 国家
        {"name": "日本", "color": "#e94560"},
        {"name": "韩国", "color": "#3b82f6"},
        # 类型
        {"name": "JAV", "color": "#ef4444"},
        {"name": "韩素人", "color": "#ec4899"},
        {"name": "韩星", "color": "#f97316"},
    ],
    # 有水印有亮点专属标签
    "有水印有亮点": [
        # 类型
        {"name": "有亮点", "color": "#10b981"},
        {"name": "精华片段", "color": "#f59e0b"},
        # 来源
        {"name": "论坛分享", "color": "#3b82f6"},
        {"name": "群分享", "color": "#8b5cf6"},
    ],
    # 其他专属标签
    "其他": [
        # 类型
        {"name": "未分类", "color": "#6b7280"},
        {"name": "待整理", "color": "#f59e0b"},
        {"name": "其他来源", "color": "#9ca3af"},
    ],
}


# ==================== 导入逻辑 ====================

def get_database_url():
    """获取数据库连接 URL"""
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'ihadu')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'videoscout')

    if POSTGRES_PASSWORD:
        return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    else:
        return f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def import_categories(session, categories):
    """导入分类"""
    created = 0
    skipped = 0

    print("\n" + "=" * 50)
    print("开始导入分类...")
    print("=" * 50)

    for cat_data in categories:
        try:
            # 检查是否已存在
            existing = session.query(Category).filter_by(name=cat_data["name"]).first()

            if existing:
                # 更新现有分类的 icon 和 sort_order
                existing.icon = cat_data["icon"]
                existing.sort_order = cat_data["sort_order"]
                skipped += 1
                print(f"  ✓ 更新分类：{cat_data['name']} (图标：{cat_data['icon']}, 排序：{cat_data['sort_order']})")
            else:
                # 创建新分类
                category = Category(
                    name=cat_data["name"],
                    icon=cat_data["icon"],
                    sort_order=cat_data["sort_order"]
                )
                session.add(category)
                created += 1
                print(f"  ✓ 创建分类：{cat_data['name']} (图标：{cat_data['icon']}, 排序：{cat_data['sort_order']})")

        except IntegrityError as e:
            session.rollback()
            print(f"  ✗ 导入分类失败 {cat_data['name']}: {e}")
            continue

    session.commit()

    print("\n" + "-" * 50)
    print(f"分类导入完成：创建 {created} 个，更新/跳过 {skipped} 个")
    print("-" * 50)

    return created, skipped


def import_tags(session, tags):
    """导入标签"""
    created = 0
    skipped = 0

    for tag_data in tags:
        try:
            # 检查是否已存在
            existing = session.query(Tag).filter_by(name=tag_data["name"]).first()

            if existing:
                # 更新现有标签的颜色
                existing.color = tag_data["color"]
                skipped += 1
                print(f"  ✓ 更新标签：{tag_data['name']} (颜色：{tag_data['color']})")
            else:
                # 创建新标签
                tag = Tag(
                    name=tag_data["name"],
                    color=tag_data["color"]
                )
                session.add(tag)
                created += 1
                print(f"  ✓ 创建标签：{tag_data['name']} (颜色：{tag_data['color']})")

        except IntegrityError as e:
            session.rollback()
            print(f"  ✗ 导入标签失败 {tag_data['name']}: {e}")
            continue

    session.commit()

    print("\n" + "-" * 50)
    print(f"标签导入完成：创建 {created} 个，更新/跳过 {skipped} 个")
    print("-" * 50)

    return created, skipped


def import_category_specific_tags(session, category_specific_tags):
    """导入分类专属标签"""
    total_created = 0
    total_skipped = 0

    print("\n" + "=" * 50)
    print("开始导入分类专属标签...")
    print("=" * 50)

    for category_name, tags in category_specific_tags.items():
        print(f"\n  分类 [{category_name}] 的专属标签:")

        created, skipped = import_tags(session, tags)
        total_created += created
        total_skipped += skipped

    print("\n" + "-" * 50)
    print(f"分类专属标签导入完成：创建 {total_created} 个，更新/跳过 {total_skipped} 个")
    print("-" * 50)

    return total_created, total_skipped


def print_summary(session):
    """打印统计信息"""
    print("\n" + "=" * 60)
    print("导入完成 - 统计信息")
    print("=" * 60)

    category_count = session.query(Category).count()
    tag_count = session.query(Tag).count()

    print(f"\n  分类总数：{category_count}")
    print(f"  标签总数：{tag_count}")

    # 显示分类列表
    print("\n  分类列表:")
    categories = session.query(Category).order_by(Category.sort_order).all()
    for cat in categories:
        print(f"    {cat.sort_order:2d}. {cat.icon} {cat.name}")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("批量导入分类标签脚本")
    print("=" * 60)

    # 获取数据库连接
    database_url = get_database_url()
    print(f"\n数据库连接：{database_url}")

    # 创建引擎和会话
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # 确保表存在
        Base.metadata.create_all(bind=engine)

        # 导入分类
        cat_created, cat_skipped = import_categories(session, CATEGORIES)

        # 导入通用标签
        print("\n" + "=" * 50)
        print("开始导入通用标签...")
        print("=" * 50)
        common_created, common_skipped = import_tags(session, COMMON_TAGS)

        # 导入分类专属标签
        specific_created, specific_skipped = import_category_specific_tags(session, CATEGORY_SPECIFIC_TAGS)

        # 打印总结
        print_summary(session)

        # 打印最终统计
        print("\n" + "=" * 60)
        print("最终统计")
        print("=" * 60)
        print(f"\n  分类：创建 {cat_created} 个，更新/跳过 {cat_skipped} 个")
        print(f"  通用标签：创建 {common_created} 个，更新/跳过 {common_skipped} 个")
        print(f"  专属标签：创建 {specific_created} 个，更新/跳过 {specific_skipped} 个")
        print(f"\n  总计：创建 {cat_created + common_created + specific_created} 个，更新/跳过 {cat_skipped + common_skipped + specific_skipped} 个")
        print("\n" + "=" * 60)
        print("导入完成！")
        print("=" * 60 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n✗ 导入失败：{e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
