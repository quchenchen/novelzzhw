"""章节上下文构建服务 - 实现RTCO框架的智能上下文构建"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models.chapter import Chapter
from app.models.project import Project
from app.models.outline import Outline
from app.models.character import Character
from app.models.career import Career, CharacterCareer
from app.models.memory import StoryMemory
from app.models.foreshadow import Foreshadow
from app.models.identity import Identity
from app.models.identity_career import IdentityCareer
from app.models.identity_knowledge import IdentityKnowledge
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChapterContext:
    """
    章节上下文数据结构
    
    采用RTCO框架的分层设计：
    - P0-核心（必须）：大纲、衔接点、字数要求
    - P1-重要（按需）：角色、情感基调、风格
    - P2-参考（条件触发）：记忆、故事骨架、MCP资料、伏笔提醒
    """
    
    # === P0-核心信息（必须包含）===
    chapter_outline: str = ""           # 本章大纲
    continuation_point: Optional[str] = None  # 衔接锚点（增强版：含上一章摘要和结尾）
    previous_chapter_summary: Optional[str] = None  # 🔧 新增：上一章剧情摘要
    previous_chapter_events: Optional[List[str]] = None  # 🔧 新增：上一章关键事件
    target_word_count: int = 3000       # 目标字数
    min_word_count: int = 2500          # 最小字数
    max_word_count: int = 4000          # 最大字数
    narrative_perspective: str = "第三人称"  # 叙事视角
    
    # === 本章基本信息 ===
    chapter_number: int = 1             # 章节序号
    chapter_title: str = ""             # 章节标题
    
    # === 项目基本信息 ===
    title: str = ""                     # 书名
    genre: str = ""                     # 类型
    theme: str = ""                     # 主题
    
    # === P1-重要信息（按需包含）===
    chapter_characters: str = ""        # 本章涉及角色（精简）
    emotional_tone: str = ""            # 情感基调
    style_instruction: str = ""         # 写作风格指令（摘要化）
    
    # === P2-参考信息（条件触发）===
    relevant_memories: Optional[str] = None   # 相关记忆（精简版）
    story_skeleton: Optional[str] = None      # 故事骨架（50章+启用）
    mcp_references: Optional[str] = None      # MCP参考资料
    foreshadow_reminders: Optional[str] = None  # 伏笔提醒（新增）
    character_identities: Optional[str] = None  # 角色身份信息（新增）
    
    # === 元信息 ===
    context_stats: Dict[str, Any] = field(default_factory=dict)  # 统计信息
    
    def get_total_context_length(self) -> int:
        """计算总上下文长度"""
        total = 0
        for field_name in ['chapter_outline', 'continuation_point', 'chapter_characters',
                          'relevant_memories', 'story_skeleton', 'style_instruction',
                          'foreshadow_reminders', 'previous_chapter_summary', 'character_identities']:
            value = getattr(self, field_name, None)
            if value:
                total += len(value)
        return total


class ChapterContextBuilder:
    """
    章节上下文构建器
    
    实现动态裁剪逻辑，根据章节序号自动调整上下文复杂度：
    - 第1章：无前置上下文，仅提供大纲和角色
    - 第2-10章：上一章结尾300字 + 涉及角色
    - 第11-50章：上一章结尾500字 + 相关记忆3条
    - 第51章+：上一章结尾500字 + 故事骨架 + 智能记忆5条
    """
    
    # 配置常量
    ENDING_LENGTH_SHORT = 300    # 1-10章：短衔接
    ENDING_LENGTH_NORMAL = 500   # 11章+：标准衔接
    MEMORY_COUNT_LIGHT = 3       # 11-50章：轻量记忆
    MEMORY_COUNT_FULL = 5        # 51章+：完整记忆
    SKELETON_THRESHOLD = 50      # 启用故事骨架的章节阈值
    SKELETON_SAMPLE_INTERVAL = 10  # 故事骨架采样间隔
    MEMORY_IMPORTANCE_THRESHOLD = 0.7  # 记忆重要性阈值
    STYLE_MAX_LENGTH = 200       # 风格描述最大长度
    MAX_CONTEXT_LENGTH = 3000    # 总上下文最大字符数
    
    def __init__(self, memory_service=None, foreshadow_service=None):
        """
        初始化构建器
        
        Args:
            memory_service: 记忆服务实例（可选，用于检索相关记忆）
            foreshadow_service: 伏笔服务实例（可选，用于获取伏笔提醒）
        """
        self.memory_service = memory_service
        self.foreshadow_service = foreshadow_service
    
    async def build(
        self,
        chapter: Chapter,
        project: Project,
        outline: Optional[Outline],
        user_id: str,
        db: AsyncSession,
        style_content: Optional[str] = None,
        target_word_count: int = 3000,
        temp_narrative_perspective: Optional[str] = None
    ) -> ChapterContext:
        """
        构建章节生成所需的上下文
        
        Args:
            chapter: 章节对象
            project: 项目对象
            outline: 大纲对象（可选）
            user_id: 用户ID
            db: 数据库会话
            style_content: 写作风格内容（可选）
            target_word_count: 目标字数
            temp_narrative_perspective: 临时叙事视角（可选，覆盖项目默认）
        
        Returns:
            ChapterContext: 结构化的上下文对象
        """
        chapter_number = chapter.chapter_number
        logger.info(f"📝 开始构建章节上下文: 第{chapter_number}章")
        
        # 确定叙事视角
        narrative_perspective = (
            temp_narrative_perspective or
            project.narrative_perspective or
            "第三人称"
        )
        
        # 初始化上下文
        context = ChapterContext(
            chapter_number=chapter_number,
            chapter_title=chapter.title or "",
            title=project.title or "",
            genre=project.genre or "",
            theme=project.theme or "",
            target_word_count=target_word_count,
            min_word_count=max(500, target_word_count - 500),
            max_word_count=target_word_count + 1000,
            narrative_perspective=narrative_perspective
        )
        
        # === P0-核心信息（始终构建）===
        context.chapter_outline = await self._build_chapter_outline(
            chapter, outline, project.outline_mode
        )
        
        # === 衔接锚点（根据章节调整长度，增强版含摘要和事件）===
        if chapter_number == 1:
            context.continuation_point = None
            context.previous_chapter_summary = None
            context.previous_chapter_events = None
            logger.info("  ✅ 第1章无需衔接锚点")
        elif chapter_number <= 10:
            ending_info = await self._get_last_ending_enhanced(
                chapter, db, self.ENDING_LENGTH_SHORT
            )
            context.continuation_point = ending_info.get('ending_text')
            context.previous_chapter_summary = ending_info.get('summary')
            context.previous_chapter_events = ending_info.get('key_events')
            logger.info(f"  ✅ 衔接锚点（短）: {len(context.continuation_point or '')}字符, 摘要: {len(context.previous_chapter_summary or '')}字符")
        else:
            ending_info = await self._get_last_ending_enhanced(
                chapter, db, self.ENDING_LENGTH_NORMAL
            )
            context.continuation_point = ending_info.get('ending_text')
            context.previous_chapter_summary = ending_info.get('summary')
            context.previous_chapter_events = ending_info.get('key_events')
            logger.info(f"  ✅ 衔接锚点（标准）: {len(context.continuation_point or '')}字符, 摘要: {len(context.previous_chapter_summary or '')}字符")
        
        # === P1-重要信息 ===
        context.chapter_characters = await self._build_chapter_characters(
            chapter, project, outline, db
        )
        context.emotional_tone = self._extract_emotional_tone(chapter, outline)
        
        # 写作风格（摘要化）
        if style_content:
            context.style_instruction = self._summarize_style(style_content)
        
        # === P2-参考信息（条件触发）===
        if chapter_number > 10 and self.memory_service:
            memory_limit = (
                self.MEMORY_COUNT_LIGHT if chapter_number <= 50
                else self.MEMORY_COUNT_FULL
            )
            context.relevant_memories = await self._get_relevant_memories(
                user_id, project.id, chapter_number, 
                context.chapter_outline,
                limit=memory_limit
            )
            logger.info(f"  ✅ 相关记忆: {len(context.relevant_memories or '')}字符")
        
        # 故事骨架（50章+）
        if chapter_number > self.SKELETON_THRESHOLD:
            context.story_skeleton = await self._build_story_skeleton(
                project.id, chapter_number, db
            )
            logger.info(f"  ✅ 故事骨架: {len(context.story_skeleton or '')}字符")
        
        # === P2-伏笔提醒（新增）===
        if self.foreshadow_service:
            context.foreshadow_reminders = await self._get_foreshadow_reminders(
                project.id, chapter_number, db
            )
            if context.foreshadow_reminders:
                logger.info(f"  ✅ 伏笔提醒: {len(context.foreshadow_reminders)}字符")

        # === P2-角色身份信息（新增）===
        context.character_identities = await self._build_character_identities(
            chapter, project, db
        )
        if context.character_identities:
            logger.info(f"  ✅ 角色身份: {len(context.character_identities)}字符")

        # === 统计信息 ===
        context.context_stats = {
            "chapter_number": chapter_number,
            "has_continuation": context.continuation_point is not None,
            "continuation_length": len(context.continuation_point or ""),
            "characters_length": len(context.chapter_characters),
            "memories_length": len(context.relevant_memories or ""),
            "skeleton_length": len(context.story_skeleton or ""),
            "foreshadow_length": len(context.foreshadow_reminders or ""),
            "identities_length": len(context.character_identities or ""),
            "total_length": context.get_total_context_length()
        }
        
        logger.info(f"📊 上下文构建完成: 总长度 {context.context_stats['total_length']} 字符")
        
        return context
    
    async def _build_chapter_outline(
        self,
        chapter: Chapter,
        outline: Optional[Outline],
        outline_mode: str
    ) -> str:
        """
        构建本章大纲内容
        
        Args:
            chapter: 章节对象
            outline: 大纲对象
            outline_mode: 大纲模式（one-to-one/one-to-many）
        
        Returns:
            本章大纲文本
        """
        if outline_mode == 'one-to-one':
            # 一对一模式：使用大纲的 content
            return outline.content if outline else chapter.summary or '暂无大纲'
        else:
            # 一对多模式：优先使用 expansion_plan 的详细规划
            if chapter.expansion_plan:
                try:
                    plan = json.loads(chapter.expansion_plan)
                    outline_content = f"""剧情摘要：{plan.get('plot_summary', '无')}

关键事件：
{chr(10).join(f'- {event}' for event in plan.get('key_events', []))}

角色焦点：{', '.join(plan.get('character_focus', []))}
情感基调：{plan.get('emotional_tone', '未设定')}
叙事目标：{plan.get('narrative_goal', '未设定')}
冲突类型：{plan.get('conflict_type', '未设定')}"""
                    return outline_content
                except json.JSONDecodeError:
                    pass
            
            # 回退到大纲内容
            return outline.content if outline else chapter.summary or '暂无大纲'
    
    async def _get_last_ending(
        self,
        chapter: Chapter,
        db: AsyncSession,
        max_length: int
    ) -> Optional[str]:
        """
        获取上一章结尾内容作为衔接锚点（旧版本，保留兼容性）
        
        Args:
            chapter: 当前章节
            db: 数据库会话
            max_length: 最大长度
        
        Returns:
            上一章结尾内容
        """
        if chapter.chapter_number <= 1:
            return None
        
        # 查询上一章
        result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == chapter.project_id)
            .where(Chapter.chapter_number == chapter.chapter_number - 1)
        )
        prev_chapter = result.scalar_one_or_none()
        
        if not prev_chapter or not prev_chapter.content:
            return None
        
        # 提取结尾内容
        content = prev_chapter.content.strip()
        if len(content) <= max_length:
            return content
        
        return content[-max_length:]
    
    async def _get_last_ending_enhanced(
        self,
        chapter: Chapter,
        db: AsyncSession,
        max_length: int
    ) -> Dict[str, Any]:
        """
        获取增强版衔接锚点（含上一章摘要和关键事件）
        
        🔧 新增功能：
        1. 提取上一章结尾文本
        2. 获取上一章剧情摘要（从记忆或expansion_plan）
        3. 提取上一章关键事件
        
        Args:
            chapter: 当前章节
            db: 数据库会话
            max_length: 最大长度
        
        Returns:
            包含 ending_text, summary, key_events 的字典
        """
        result_info = {
            'ending_text': None,
            'summary': None,
            'key_events': []
        }
        
        if chapter.chapter_number <= 1:
            return result_info
        
        # 查询上一章
        result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == chapter.project_id)
            .where(Chapter.chapter_number == chapter.chapter_number - 1)
        )
        prev_chapter = result.scalar_one_or_none()
        
        if not prev_chapter:
            return result_info
        
        # 1. 提取结尾内容
        if prev_chapter.content:
            content = prev_chapter.content.strip()
            if len(content) <= max_length:
                result_info['ending_text'] = content
            else:
                result_info['ending_text'] = content[-max_length:]
        
        # 2. 获取上一章摘要
        # 优先从记忆中获取 chapter_summary
        summary_result = await db.execute(
            select(StoryMemory.content)
            .where(StoryMemory.project_id == chapter.project_id)
            .where(StoryMemory.chapter_id == prev_chapter.id)
            .where(StoryMemory.memory_type == 'chapter_summary')
            .limit(1)
        )
        summary_mem = summary_result.scalar_one_or_none()
        
        if summary_mem:
            result_info['summary'] = summary_mem[:300]  # 限制长度
        elif prev_chapter.summary:
            # 回退到章节的summary字段
            result_info['summary'] = prev_chapter.summary[:300]
        elif prev_chapter.expansion_plan:
            # 再回退到expansion_plan中的plot_summary
            try:
                plan = json.loads(prev_chapter.expansion_plan)
                result_info['summary'] = plan.get('plot_summary', '')[:300]
            except json.JSONDecodeError:
                pass
        
        # 3. 提取上一章关键事件
        if prev_chapter.expansion_plan:
            try:
                plan = json.loads(prev_chapter.expansion_plan)
                key_events = plan.get('key_events', [])
                if key_events:
                    result_info['key_events'] = key_events[:5]  # 最多5个事件
            except json.JSONDecodeError:
                pass
        
        # 如果没有从expansion_plan获取到，尝试从记忆中获取
        if not result_info['key_events']:
            events_result = await db.execute(
                select(StoryMemory.content)
                .where(StoryMemory.project_id == chapter.project_id)
                .where(StoryMemory.chapter_id == prev_chapter.id)
                .where(StoryMemory.memory_type == 'plot_point')
                .limit(5)
            )
            event_mems = events_result.scalars().all()
            if event_mems:
                result_info['key_events'] = [e[:100] for e in event_mems]
        
        return result_info
    
    async def _build_chapter_characters(
        self,
        chapter: Chapter,
        project: Project,
        outline: Optional[Outline],
        db: AsyncSession
    ) -> str:
        """
        构建本章涉及的角色信息（精简版）
        
        只返回本章相关的角色，而非全部角色
        
        Args:
            chapter: 章节对象
            project: 项目对象
            outline: 大纲对象
            db: 数据库会话
        
        Returns:
            本章角色信息文本
        """
        # 获取所有角色
        characters_result = await db.execute(
            select(Character).where(Character.project_id == project.id)
        )
        characters = characters_result.scalars().all()
        
        if not characters:
            return "暂无角色信息"
        
        # 提取本章相关角色名单
        filter_character_names = None
        
        # 从大纲或扩展计划中提取角色
        if project.outline_mode == 'one-to-one':
            if outline and outline.structure:
                try:
                    structure = json.loads(outline.structure)
                    filter_character_names = structure.get('characters', [])
                except json.JSONDecodeError:
                    pass
        else:
            if chapter.expansion_plan:
                try:
                    plan = json.loads(chapter.expansion_plan)
                    filter_character_names = plan.get('character_focus', [])
                except json.JSONDecodeError:
                    pass
        
        # 筛选角色
        if filter_character_names:
            characters = [c for c in characters if c.name in filter_character_names]
        
        if not characters:
            return "暂无相关角色"
        
        # 构建精简的角色信息（每个角色最多100字符）
        char_lines = []
        for c in characters[:10]:  # 最多10个角色
            role_type = "主角" if c.role_type == "protagonist" else (
                "反派" if c.role_type == "antagonist" else "配角"
            )
            
            # 性格摘要（最多50字符）
            personality_brief = ""
            if c.personality:
                personality_brief = c.personality[:50]
                if len(c.personality) > 50:
                    personality_brief += "..."
            
            char_lines.append(f"- {c.name}({role_type}): {personality_brief}")
        
        return "\n".join(char_lines)
    
    def _extract_emotional_tone(
        self,
        chapter: Chapter,
        outline: Optional[Outline]
    ) -> str:
        """
        提取本章情感基调
        
        Args:
            chapter: 章节对象
            outline: 大纲对象
        
        Returns:
            情感基调描述
        """
        # 尝试从扩展计划中提取
        if chapter.expansion_plan:
            try:
                plan = json.loads(chapter.expansion_plan)
                tone = plan.get('emotional_tone')
                if tone:
                    return tone
            except json.JSONDecodeError:
                pass
        
        # 尝试从大纲结构中提取
        if outline and outline.structure:
            try:
                structure = json.loads(outline.structure)
                tone = structure.get('emotion') or structure.get('emotional_tone')
                if tone:
                    return tone
            except json.JSONDecodeError:
                pass
        
        return "未设定"
    
    def _summarize_style(self, style_content: str) -> str:
        """
        将风格描述压缩为关键要点
        
        Args:
            style_content: 完整风格描述
        
        Returns:
            摘要化的风格描述
        """
        if not style_content:
            return ""
        
        if len(style_content) <= self.STYLE_MAX_LENGTH:
            return style_content
        
        # 简单截断（后续可以用AI提取关键词）
        return style_content[:self.STYLE_MAX_LENGTH] + "..."
    
    async def _get_relevant_memories(
        self,
        user_id: str,
        project_id: str,
        chapter_number: int,
        chapter_outline: str,
        limit: int = 3
    ) -> Optional[str]:
        """
        获取与本章最相关的记忆（精简版）
        
        策略：
        1. 仅检索与大纲语义最相关的记忆
        2. 提高重要性阈值，过滤低质量记忆
        3. 优先返回未回收的伏笔
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            chapter_number: 当前章节号
            chapter_outline: 本章大纲
            limit: 返回数量限制
        
        Returns:
            格式化的记忆文本
        """
        if not self.memory_service:
            return None
        
        try:
            # 1. 语义检索相关记忆（提高阈值）
            relevant = await self.memory_service.search_memories(
                user_id=user_id,
                project_id=project_id,
                query=chapter_outline,
                limit=limit,
                min_importance=self.MEMORY_IMPORTANCE_THRESHOLD
            )
            
            # 2. 检查即将到期的伏笔
            foreshadows = await self._get_due_foreshadows(
                user_id, project_id, chapter_number,
                lookahead=5  # 仅看5章内需要回收的
            )
            
            # 3. 合并并格式化
            return self._format_memories(relevant, foreshadows, max_length=500)
            
        except Exception as e:
            logger.error(f"❌ 获取相关记忆失败: {str(e)}")
            return None
    
    async def _get_due_foreshadows(
        self,
        user_id: str,
        project_id: str,
        chapter_number: int,
        lookahead: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取即将需要回收的伏笔
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            chapter_number: 当前章节号
            lookahead: 往前看的章节数
        
        Returns:
            待回收伏笔列表
        """
        if not self.memory_service:
            return []
        
        try:
            foreshadows = await self.memory_service.find_unresolved_foreshadows(
                user_id, project_id, chapter_number
            )
            
            # 过滤：只保留埋下时间较长（超过lookahead章）的伏笔
            due_foreshadows = []
            for fs in foreshadows:
                meta = fs.get('metadata', {})
                fs_chapter = meta.get('chapter_number', 0)
                if chapter_number - fs_chapter >= lookahead:
                    due_foreshadows.append({
                        'chapter': fs_chapter,
                        'content': fs.get('content', '')[:60],
                        'importance': meta.get('importance', 0.5)
                    })
            
            return due_foreshadows[:2]  # 最多2条
            
        except Exception as e:
            logger.error(f"❌ 获取待回收伏笔失败: {str(e)}")
            return []
    
    def _format_memories(
        self,
        relevant: List[Dict[str, Any]],
        foreshadows: List[Dict[str, Any]],
        max_length: int = 500
    ) -> str:
        """
        格式化记忆为简洁文本，严格限制长度
        
        Args:
            relevant: 相关记忆列表
            foreshadows: 待回收伏笔列表
            max_length: 最大长度
        
        Returns:
            格式化的记忆文本
        """
        lines = []
        current_length = 0
        
        # 优先添加待回收伏笔
        if foreshadows:
            lines.append("【待回收伏笔】")
            for fs in foreshadows[:2]:
                text = f"- 第{fs['chapter']}章埋下：{fs['content']}"
                if current_length + len(text) > max_length:
                    break
                lines.append(text)
                current_length += len(text)
        
        # 添加相关记忆
        if relevant and current_length < max_length:
            lines.append("【相关记忆】")
            for mem in relevant:
                content = mem.get('content', '')[:80]
                text = f"- {content}"
                if current_length + len(text) > max_length:
                    break
                lines.append(text)
                current_length += len(text)
        
        return "\n".join(lines) if lines else None
    
    async def _get_foreshadow_reminders(
        self,
        project_id: str,
        chapter_number: int,
        db: AsyncSession
    ) -> Optional[str]:
        """
        获取伏笔提醒信息用于章节生成
        
        策略：
        1. 获取计划在本章或之前回收但未回收的伏笔（超期提醒）
        2. 获取已埋入且接近需要回收的伏笔（提前提醒）
        3. 获取本章计划埋入的伏笔（埋入提醒）
        
        Args:
            project_id: 项目ID
            chapter_number: 当前章节号
            db: 数据库会话
        
        Returns:
            格式化的伏笔提醒文本
        """
        if not self.foreshadow_service:
            return None
        
        try:
            context_result = await self.foreshadow_service.build_chapter_context(
                db=db,
                project_id=project_id,
                chapter_number=chapter_number,
                include_pending=True,
                include_overdue=True,
                lookahead=5
            )
            
            context_text = context_result.get("context_text", "")
            return context_text if context_text else None
            
        except Exception as e:
            logger.error(f"❌ 获取伏笔提醒失败: {str(e)}")
            return None
    
    async def _build_story_skeleton(
        self,
        project_id: str,
        chapter_number: int,
        db: AsyncSession
    ) -> Optional[str]:
        """
        构建故事骨架（每N章采样）
        
        Args:
            project_id: 项目ID
            chapter_number: 当前章节号
            db: 数据库会话
        
        Returns:
            故事骨架文本
        """
        try:
            # 获取所有已完成章节的摘要
            result = await db.execute(
                select(Chapter.chapter_number, Chapter.title)
                .where(Chapter.project_id == project_id)
                .where(Chapter.chapter_number < chapter_number)
                .where(Chapter.content != None)
                .where(Chapter.content != "")
                .order_by(Chapter.chapter_number)
            )
            chapters = result.all()
            
            if not chapters:
                return None
            
            # 采样：每N章取一个
            skeleton_lines = ["【故事骨架】"]
            for i, (ch_num, ch_title) in enumerate(chapters):
                if i % self.SKELETON_SAMPLE_INTERVAL == 0:
                    # 尝试获取章节摘要
                    summary_result = await db.execute(
                        select(StoryMemory.content)
                        .where(StoryMemory.project_id == project_id)
                        .where(StoryMemory.story_timeline == ch_num)
                        .where(StoryMemory.memory_type == 'chapter_summary')
                        .limit(1)
                    )
                    summary = summary_result.scalar_one_or_none()
                    
                    if summary:
                        skeleton_lines.append(f"第{ch_num}章《{ch_title}》：{summary[:100]}")
                    else:
                        skeleton_lines.append(f"第{ch_num}章《{ch_title}》")
            
            if len(skeleton_lines) <= 1:
                return None
            
            return "\n".join(skeleton_lines)
            
        except Exception as e:
            logger.error(f"❌ 构建故事骨架失败: {str(e)}")
            return None

    async def _build_character_identities(
        self,
        chapter: Chapter,
        project: Project,
        db: AsyncSession
    ) -> Optional[str]:
        """
        构建本章涉及角色的身份信息（增强版：智能过滤）

        新增功能：
        1. 智能过滤：只包含本章相关的身份信息
        2. 状态感知：根据剧情进度过滤已暴露/未暴露身份
        3. 关系提示：提醒作者谁知道了哪些身份

        Args:
            chapter: 章节对象
            project: 项目对象
            db: 数据库会话

        Returns:
            格式化的角色身份信息文本
        """
        try:
            # 获取所有角色
            characters_result = await db.execute(
                select(Character).where(Character.project_id == project.id)
            )
            characters = characters_result.scalars().all()

            if not characters:
                return None

            # 提取本章相关角色名单
            filter_character_names = None

            # 从大纲或扩展计划中提取角色
            if project.outline_mode == 'one-to-one':
                outline_result = await db.execute(
                    select(Outline).where(
                        Outline.project_id == project.id,
                        Outline.chapter_number == chapter.chapter_number
                    )
                )
                outline = outline_result.scalar_one_or_none()
                if outline and outline.structure:
                    try:
                        structure = json.loads(outline.structure)
                        filter_character_names = structure.get('characters', [])
                    except json.JSONDecodeError:
                        pass
            else:
                if chapter.expansion_plan:
                    try:
                        plan = json.loads(chapter.expansion_plan)
                        filter_character_names = plan.get('character_focus', [])
                    except json.JSONDecodeError:
                        pass

            # 筛选角色
            if filter_character_names:
                characters = [c for c in characters if c.name in filter_character_names]

            if not characters:
                return None

            # 构建身份信息（增强版）
            identity_lines = []
            identity_lines.append("【角色身份信息 - 智能过滤】")

            for character in characters[:8]:  # 最多8个角色
                # 获取角色的所有身份（包括active和burned状态）
                identities_result = await db.execute(
                    select(Identity).where(
                        Identity.character_id == character.id
                    ).order_by(Identity.is_primary.desc(), Identity.created_at.asc())
                )
                identities = identities_result.scalars().all()

                if not identities:
                    continue

                # 如果只有一个主身份且状态为active，跳过（这是默认情况）
                active_identities = [i for i in identities if i.status == 'active']
                if len(identities) == 1 and identities[0].is_primary and identities[0].status == 'active':
                    continue

                # 角色有多个身份或特殊身份时，添加信息
                identity_lines.append(f"\n角色：{character.name}")

                for identity in identities:
                    # 时间线感知：根据目标章节计算身份当时的状态
                    is_exposed_at_this_chapter = identity.is_exposed_at_chapter(chapter.chapter_number)

                    # 智能过滤：隐藏身份如果未被本章角色知晓，则不显示或标记为"不应知晓"
                    should_show_identity = True
                    visibility_note = ""

                    if is_exposed_at_this_chapter:
                        visibility_note = " [已暴露]"
                    elif identity.identity_type in ('secret', 'disguise'):
                        # 检查是否有本章角色知晓这个身份
                        knowledge_result = await db.execute(
                            select(IdentityKnowledge).where(
                                IdentityKnowledge.identity_id == identity.id
                            )
                        )
                        knowledge_list = knowledge_result.scalars().all()

                        # 检查知晓者是否在本章角色列表中
                        known_by_chapter_characters = False
                        for knowledge in knowledge_list:
                            if knowledge.knower_character_id in [c.id for c in characters]:
                                known_by_chapter_characters = True
                                break

                        if not known_by_chapter_characters and filter_character_names:
                            # 隐藏身份未被本章角色知晓，添加提醒
                            visibility_note = " [本章角色不应知晓]"
                            # 仍然显示，因为作者可能需要这个上下文
                        elif knowledge_list:
                            visibility_note = f" [被{len(knowledge_list)}人知晓]"

                    # 身份类型中文映射
                    type_map = {
                        'real': '真身',
                        'public': '公开',
                        'secret': '隐藏',
                        'disguise': '伪装'
                    }
                    type_label = type_map.get(identity.identity_type, identity.identity_type)

                    # 身份标签
                    labels = [f"{type_label}"]
                    if identity.is_primary:
                        labels.append("主身份")
                    # 使用时间线感知的状态
                    status_at_chapter = identity.get_status_at_chapter(chapter.chapter_number)
                    if status_at_chapter == 'burned':
                        labels.append("已暴露")
                    elif identity.identity_type in ('secret', 'disguise'):
                        labels.append("需保密")

                    # 获取身份的职业
                    careers_result = await db.execute(
                        select(IdentityCareer).where(IdentityCareer.identity_id == identity.id)
                    )
                    identity_careers = careers_result.scalars().all()

                    career_info = ""
                    if identity_careers:
                        career_names = []
                        for ic in identity_careers:
                            career_result = await db.execute(
                                select(Career).where(Career.id == ic.career_id)
                            )
                            career = career_result.scalar_one_or_none()
                            if career:
                                stage_name = ""
                                if career.stages:
                                    try:
                                        stages = json.loads(career.stages)
                                        for stage in stages:
                                            if stage.get('level') == ic.current_stage:
                                                stage_name = f"·{stage.get('name')}"
                                                break
                                    except:
                                        pass
                                career_names.append(f"{career.name}{stage_name}")
                        if career_names:
                            career_info = f" | 职业: {', '.join(career_names)}"

                    # 获取谁知道了这个身份
                    knowledge_result = await db.execute(
                        select(IdentityKnowledge).where(IdentityKnowledge.identity_id == identity.id)
                    )
                    knowledge_list = knowledge_result.scalars().all()

                    knowledge_info = ""
                    if knowledge_list:
                        knower_names = []
                        for knowledge in knowledge_list:
                            knower_result = await db.execute(
                                select(Character).where(Character.id == knowledge.knower_character_id)
                            )
                            knower = knower_result.scalar_one_or_none()
                            if knower:
                                # 检查知晓者是否在本章角色中
                                in_chapter = knower.id in [c.id for c in characters]
                                in_chapter_mark = " ✓" if in_chapter else ""
                                level_map = {
                                    'full': '完全知晓',
                                    'partial': '部分知晓',
                                    'suspected': '怀疑'
                                }
                                knower_info = f"{knower.name}{in_chapter_mark}({level_map.get(knowledge.knowledge_level, knowledge.knowledge_level)})"
                                knower_names.append(knower_info)

                        if knower_names:
                            knowledge_info = f" | 被知晓: {', '.join(knower_names)}"

                    identity_lines.append(f"  - {identity.name} [{', '.join(labels)}]{visibility_note}{career_info}{knowledge_info}")

            # 如果只有标题没有内容，返回None
            if len(identity_lines) <= 1:
                return None

            return "\n".join(identity_lines)

        except Exception as e:
            logger.error(f"❌ 构建角色身份信息失败: {str(e)}")
            return None


class FocusedMemoryRetriever:
    """
    精简记忆检索器
    
    相比原有的memory_service，提供更精准、更简洁的记忆检索
    """
    
    def __init__(self, memory_service):
        """
        初始化检索器
        
        Args:
            memory_service: 基础记忆服务实例
        """
        self.memory_service = memory_service
    
    async def get_relevant_memories(
        self,
        user_id: str,
        project_id: str,
        chapter_number: int,
        chapter_outline: str,
        limit: int = 3
    ) -> str:
        """
        获取与本章最相关的记忆
        
        策略：
        1. 仅检索与大纲语义最相关的记忆
        2. 提高重要性阈值，过滤低质量记忆
        3. 优先返回未回收的伏笔
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            chapter_number: 当前章节号
            chapter_outline: 本章大纲
            limit: 返回数量限制
        
        Returns:
            格式化的记忆文本
        """
        # 1. 语义检索相关记忆（提高阈值）
        relevant = await self.memory_service.search_memories(
            user_id=user_id,
            project_id=project_id,
            query=chapter_outline,
            limit=limit,
            min_importance=0.7  # 从0.4提高到0.7
        )
        
        # 2. 检查即将到期的伏笔
        due_foreshadows = await self._get_due_foreshadows(
            user_id, project_id, chapter_number,
            lookahead=5  # 仅看5章内需要回收的
        )
        
        # 3. 合并并格式化
        return self._format_memories(relevant, due_foreshadows, max_length=500)
    
    async def _get_due_foreshadows(
        self,
        user_id: str,
        project_id: str,
        chapter_number: int,
        lookahead: int = 5
    ) -> List[Dict[str, Any]]:
        """获取即将需要回收的伏笔"""
        foreshadows = await self.memory_service.find_unresolved_foreshadows(
            user_id, project_id, chapter_number
        )
        
        # 过滤：只保留埋下时间较长的伏笔
        due_foreshadows = []
        for fs in foreshadows:
            meta = fs.get('metadata', {})
            fs_chapter = meta.get('chapter_number', 0)
            if chapter_number - fs_chapter >= lookahead:
                due_foreshadows.append({
                    'chapter': fs_chapter,
                    'content': fs.get('content', '')[:60],
                    'importance': meta.get('importance', 0.5)
                })
        
        return due_foreshadows[:2]  # 最多2条
    
    def _format_memories(
        self,
        relevant: List[Dict[str, Any]],
        foreshadows: List[Dict[str, Any]],
        max_length: int = 500
    ) -> str:
        """格式化为简洁文本，严格限制长度"""
        lines = []
        current_length = 0
        
        # 优先添加待回收伏笔
        if foreshadows:
            lines.append("【待回收伏笔】")
            for fs in foreshadows[:2]:
                text = f"- 第{fs['chapter']}章埋下：{fs['content']}"
                if current_length + len(text) > max_length:
                    break
                lines.append(text)
                current_length += len(text)
        
        # 添加相关记忆
        if relevant and current_length < max_length:
            lines.append("【相关记忆】")
            for mem in relevant:
                content = mem.get('content', '')[:80]
                text = f"- {content}"
                if current_length + len(text) > max_length:
                    break
                lines.append(text)
                current_length += len(text)
        
        return "\n".join(lines) if lines else ""