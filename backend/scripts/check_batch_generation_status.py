#!/usr/bin/env python3
"""检查批量生成任务状态的脚本

用法:
    python scripts/check_batch_generation_status.py --project-id <project_id>
    python scripts/check_batch_generation_status.py --batch-id <batch_id>
    python scripts/check_batch_generation_status.py --list-all
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.models.batch_generation_task import BatchGenerationTask
from app.models.chapter import Chapter
from app.logger import get_logger

logger = get_logger(__name__)


async def check_batch_status(batch_id: str = None, project_id: str = None, list_all: bool = False):
    """检查批量生成任务状态"""

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        if list_all:
            # 列出所有最近的批量任务
            result = await session.execute(
                select(BatchGenerationTask)
                .order_by(BatchGenerationTask.created_at.desc())
                .limit(20)
            )
            tasks = result.scalars().all()

            print("\n" + "=" * 80)
            print(f"{'最近20个批量生成任务':^80}")
            print("=" * 80)

            for task in tasks:
                status_emoji = {
                    'pending': '⏳',
                    'running': '🔄',
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '🛑'
                }.get(task.status, '❓')

                print(f"\n{status_emoji} [{task.status.upper()}] 任务ID: {task.id[:8]}...")
                print(f"   项目ID: {task.project_id}")
                print(f"   总章节数: {task.total_chapters} | 已完成: {task.completed_chapters}")
                print(f"   创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if task.started_at:
                    elapsed = (task.completed_at or datetime.now()) - task.started_at
                    print(f"   运行时长: {elapsed}")
                if task.status == 'failed':
                    print(f"   ❌ 错误: {task.error_message}")
                if task.failed_chapters:
                    print(f"   失败章节: {task.failed_chapters}")

        elif batch_id:
            # 查看指定任务详情
            result = await session.execute(
                select(BatchGenerationTask).where(BatchGenerationTask.id == batch_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                print(f"❌ 未找到任务: {batch_id}")
                return

            print("\n" + "=" * 80)
            print(f"{'批量生成任务详情':^80}")
            print("=" * 80)

            status_emoji = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🛑'
            }.get(task.status, '❓')

            print(f"\n{status_emoji} 状态: {task.status.upper()}")
            print(f"📋 任务ID: {task.id}")
            print(f"📁 项目ID: {task.project_id}")
            print(f"📊 进度: {task.completed_chapters}/{task.total_chapters} 章")

            if task.current_chapter_id:
                print(f"📍 当前章节ID: {task.current_chapter_id}")
            if task.current_chapter_number:
                print(f"📍 当前章节号: 第{task.current_chapter_number}章")
            if task.current_retry_count > 0:
                print(f"🔄 当前重试次数: {task.current_retry_count}")

            print(f"\n⏰ 时间信息:")
            print(f"   创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.started_at:
                print(f"   开始时间: {task.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.completed_at:
                print(f"   完成时间: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if task.started_at:
                    elapsed = task.completed_at - task.started_at
                    print(f"   总耗时: {elapsed}")

            print(f"\n⚙️ 配置:")
            print(f"   目标字数: {task.target_word_count}")
            print(f"   最大重试: {task.max_retries}次")
            print(f"   启用分析: {task.enable_analysis}")

            if task.error_message:
                print(f"\n❌ 错误信息:")
                print(f"   {task.error_message}")

            if task.failed_chapters:
                print(f"\n❌ 失败章节详情:")
                for failed in task.failed_chapters:
                    print(f"   - 第{failed.get('chapter_number', '?')}章: {failed.get('error', '未知错误')}")

            # 显示待生成章节列表
            if task.chapter_ids:
                print(f"\n📝 待生成章节 ({len(task.chapter_ids)}个):")
                for i, ch_id in enumerate(task.chapter_ids[:10], 1):
                    chapter_result = await session.execute(
                        select(Chapter).where(Chapter.id == ch_id)
                    )
                    ch = chapter_result.scalar_one_or_none()
                    if ch:
                        status_mark = "✅" if ch.content else "⏳"
                        print(f"   {i}. {status_mark} 第{ch.chapter_number}章《{ch.title}》")
                if len(task.chapter_ids) > 10:
                    print(f"   ... 还有 {len(task.chapter_ids) - 10} 个章节")

        elif project_id:
            # 查看项目的所有批量任务
            result = await session.execute(
                select(BatchGenerationTask)
                .where(BatchGenerationTask.project_id == project_id)
                .order_by(BatchGenerationTask.created_at.desc())
            )
            tasks = result.scalars().all()

            print("\n" + "=" * 80)
            print(f"{'项目批量生成任务历史':^80}")
            print(f"{'项目ID: ' + project_id:^80}")
            print("=" * 80)

            if not tasks:
                print(f"\n   该项目没有批量生成任务记录")
            else:
                for task in tasks:
                    status_emoji = {
                        'pending': '⏳',
                        'running': '🔄',
                        'completed': '✅',
                        'failed': '❌',
                        'cancelled': '🛑'
                    }.get(task.status, '❓')

                    print(f"\n{status_emoji} [{task.status.upper()}] {task.id[:8]}... | {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   进度: {task.completed_chapters}/{task.total_chapters}")
                    if task.status == 'failed':
                        print(f"   ❌ {task.error_message[:100]}...")

    await engine.dispose()


def main():
    parser = ArgumentParser(description="检查批量生成任务状态")
    parser.add_argument("--project-id", help="项目ID")
    parser.add_argument("--batch-id", help="批量任务ID")
    parser.add_argument("--list-all", action="store_true", help="列出所有最近的任务")

    args = parser.parse_args()

    if not any([args.project_id, args.batch_id, args.list_all]):
        parser.print_help()
        print("\n请至少指定一个参数: --project-id, --batch-id, 或 --list-all")
        sys.exit(1)

    asyncio.run(check_batch_status(
        batch_id=args.batch_id,
        project_id=args.project_id,
        list_all=args.list_all
    ))


if __name__ == "__main__":
    main()
