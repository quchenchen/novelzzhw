#!/usr/bin/env python3
"""
将项目数据导出为单个 Markdown 文档的脚本

使用方法:
    python scripts/export_project_to_markdown.py <project_id> [output_file]

示例:
    python scripts/export_project_to_markdown.py ee00aef3-408d-4740-86cc-19e654f81c45
    python scripts/export_project_to_markdown.py ee00aef3-408d-4740-86cc-19e654f81c45 output.md
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# 使用 asyncpg 直接连接数据库，避免 SQLAlchemy 的循环导入问题
import asyncpg


async def export_project_to_markdown(
    project_id: str,
    output_file: Optional[str] = None,
    database_url: Optional[str] = None
) -> str:
    """
    导出项目数据为 Markdown 文档

    Args:
        project_id: 项目ID
        output_file: 输出文件路径（可选）
        database_url: 数据库URL（可选）

    Returns:
        生成的 Markdown 文件路径
    """
    # 默认数据库连接
    if database_url is None:
        database_url = "postgresql://mumuai:123456@localhost:5432/mumuai_novel"

    print(f"正在连接数据库...")

    # 解析数据库 URL
    # postgresql://user:password@host:port/database
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    elif database_url.startswith("postgresql://"):
        pass
    else:
        raise ValueError(f"不支持的数据库URL: {database_url}")

    conn = await asyncpg.connect(database_url)

    try:
        # 1. 获取项目基本信息
        print(f"正在获取项目 {project_id} 的基本信息...")
        project = await conn.fetchrow(
            "SELECT * FROM projects WHERE id = $1",
            project_id
        )

        if not project:
            print(f"错误: 项目 {project_id} 不存在")
            sys.exit(1)

        # 确定输出文件路径
        if output_file is None:
            safe_title = "".join(c for c in project['title'] if c.isalnum() or c in (' ', '-', '_', '，', '。', '、'))
            output_file = f"/Users/quchenchen/Documents/github/MuMu/{safe_title}_完整数据.md"

        markdown_lines = []

        # 文档标题
        markdown_lines.append(f"# {project['title']} - 项目完整数据")
        markdown_lines.append("")
        markdown_lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_lines.append(f"**项目ID**: `{project_id}`")
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")

        # 2. 项目基本信息
        print("正在整理项目基本信息...")
        markdown_lines.append("## 1. 项目基本信息")
        markdown_lines.append("")

        info_table = []
        info_table.append("| 字段 | 内容 |")
        info_table.append("|------|------|")
        info_table.append(f"| **标题** | {project['title']} |")
        if project['description']:
            info_table.append(f"| **简介** | {project['description']} |")
        if project['theme']:
            info_table.append(f"| **主题** | {project['theme']} |")
        if project['genre']:
            info_table.append(f"| **类型** | {project['genre']} |")
        info_table.append(f"| **目标字数** | {project['target_words'] or 0} 字 |")
        info_table.append(f"| **当前字数** | {project['current_words'] or 0} 字 |")
        info_table.append(f"| **创作状态** | {project['status'] or 'planning'} |")
        info_table.append(f"| **大纲模式** | {project['outline_mode'] or 'one-to-many'} |")
        info_table.append(f"| **叙事视角** | {project['narrative_perspective'] or '-'} |")
        info_table.append(f"| **计划章节数** | {project['chapter_count'] or '-'} |")
        info_table.append(f"| **角色数量** | {project['character_count'] or 0} |")
        created_at = project['created_at']
        updated_at = project['updated_at']
        info_table.append(f"| **创建时间** | {created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else '-'} |")
        info_table.append(f"| **更新时间** | {updated_at.strftime('%Y-%m-%d %H:%M:%S') if updated_at else '-'} |")

        markdown_lines.extend(info_table)
        markdown_lines.append("")

        # 世界观设定
        if any([project['world_time_period'], project['world_location'],
                project['world_atmosphere'], project['world_rules']]):
            markdown_lines.append("### 世界观设定")
            markdown_lines.append("")
            if project['world_time_period']:
                markdown_lines.append(f"**时间背景**: {project['world_time_period']}")
                markdown_lines.append("")
            if project['world_location']:
                markdown_lines.append(f"**地理位置**: {project['world_location']}")
                markdown_lines.append("")
            if project['world_atmosphere']:
                markdown_lines.append(f"**氛围基调**: {project['world_atmosphere']}")
                markdown_lines.append("")
            if project['world_rules']:
                markdown_lines.append(f"**世界规则**:")
                markdown_lines.append("")
                markdown_lines.append("```")
                markdown_lines.append(project['world_rules'])
                markdown_lines.append("```")
                markdown_lines.append("")

        markdown_lines.append("---")
        markdown_lines.append("")

        # 3. 职业体系
        print("正在整理职业体系...")
        careers = await conn.fetch(
            "SELECT * FROM careers WHERE project_id = $1 ORDER BY type, created_at",
            project_id
        )

        if careers:
            markdown_lines.append("## 2. 职业体系")
            markdown_lines.append("")

            # 主职业
            main_careers = [c for c in careers if c['type'] == 'main']
            if main_careers:
                markdown_lines.append("### 主职业")
                markdown_lines.append("")

                for career in main_careers:
                    markdown_lines.append(f"#### {career['name']}")
                    markdown_lines.append("")

                    career_table = []
                    career_table.append("| 属性 | 值 |")
                    career_table.append("|------|-----|")
                    if career['category']:
                        career_table.append(f"| **职业分类** | {career['category']} |")
                    if career['description']:
                        career_table.append(f"| **职业描述** | {career['description']} |")
                    career_table.append(f"| **最大阶段** | {career['max_stage'] or 10} |")
                    if career['requirements']:
                        career_table.append(f"| **职业要求** | {career['requirements']} |")
                    if career['special_abilities']:
                        career_table.append(f"| **特殊能力** | {career['special_abilities']} |")
                    if career['worldview_rules']:
                        career_table.append(f"| **世界观规则** | {career['worldview_rules']} |")

                    markdown_lines.extend(career_table)
                    markdown_lines.append("")

                    # 职业阶段
                    if career['stages']:
                        try:
                            stages = json.loads(career['stages']) if isinstance(career['stages'], str) else career['stages']
                            if stages and isinstance(stages, list):
                                markdown_lines.append("**职业阶段**:")
                                markdown_lines.append("")
                                stage_table = ["| 阶段 | 名称 | 描述 |", "|------|------|------|"]
                                for stage in stages:
                                    level = stage.get('level', '-')
                                    name = stage.get('name', '-')
                                    desc = stage.get('description', '-').replace('\n', ' ')
                                    stage_table.append(f"| {level} | {name} | {desc} |")
                                markdown_lines.extend(stage_table)
                                markdown_lines.append("")
                        except:
                            pass

                markdown_lines.append("")

            # 副职业
            sub_careers = [c for c in careers if c['type'] == 'sub']
            if sub_careers:
                markdown_lines.append("### 副职业")
                markdown_lines.append("")

                for career in sub_careers:
                    markdown_lines.append(f"#### {career['name']}")
                    markdown_lines.append("")

                    career_table = []
                    career_table.append("| 属性 | 值 |")
                    career_table.append("|------|-----|")
                    if career['category']:
                        career_table.append(f"| **职业分类** | {career['category']} |")
                    if career['description']:
                        career_table.append(f"| **职业描述** | {career['description']} |")
                    career_table.append(f"| **最大阶段** | {career['max_stage'] or 10} |")

                    markdown_lines.extend(career_table)
                    markdown_lines.append("")

            markdown_lines.append("---")
            markdown_lines.append("")

        # 4. 角色列表
        print("正在整理角色列表...")
        characters = await conn.fetch(
            "SELECT * FROM characters WHERE project_id = $1",
            project_id
        )

        # 分离角色和组织
        role_characters = [c for c in characters if not c['is_organization']]
        org_characters = [c for c in characters if c['is_organization']]

        # 构建角色ID到名称的映射
        char_id_to_name = {c['id']: c['name'] for c in characters}
        char_id_to_obj = {c['id']: c for c in characters}

        if role_characters:
            markdown_lines.append("## 3. 角色列表")
            markdown_lines.append("")

            # 角色总览表
            markdown_lines.append("### 角色总览")
            markdown_lines.append("")
            markdown_lines.append("| 序号 | 姓名 | 年龄 | 性别 | 角色类型 | 主职业 |")
            markdown_lines.append("|------|------|------|------|----------|--------|")

            for idx, char in enumerate(role_characters, 1):
                age = char['age'] or '-'
                gender = char['gender'] or '-'
                role_type = char['role_type'] or '-'
                main_career = ''

                # 获取主职业信息
                if char['main_career_id']:
                    career = await conn.fetchrow(
                        "SELECT name FROM careers WHERE id = $1",
                        char['main_career_id']
                    )
                    if career:
                        main_career = career['name']

                markdown_lines.append(f"| {idx} | {char['name']} | {age} | {gender} | {role_type} | {main_career} |")

            markdown_lines.append("")

            # 角色详情
            markdown_lines.append("### 角色详情")
            markdown_lines.append("")

            for char in role_characters:
                markdown_lines.append(f"#### {char['name']}")
                markdown_lines.append("")

                # 基本信息
                char_table = []
                char_table.append("| 属性 | 内容 |")
                char_table.append("|------|------|")
                char_table.append(f"| **姓名** | {char['name']} |")
                if char['age']:
                    char_table.append(f"| **年龄** | {char['age']} |")
                if char['gender']:
                    char_table.append(f"| **性别** | {char['gender']} |")
                if char['role_type']:
                    char_table.append(f"| **角色类型** | {char['role_type']} |")

                markdown_lines.extend(char_table)
                markdown_lines.append("")

                # 详细信息
                if char['personality']:
                    markdown_lines.append("**性格特点**:")
                    markdown_lines.append("")
                    markdown_lines.append(char['personality'])
                    markdown_lines.append("")

                if char['background']:
                    markdown_lines.append("**背景故事**:")
                    markdown_lines.append("")
                    markdown_lines.append(char['background'])
                    markdown_lines.append("")

                if char['appearance']:
                    markdown_lines.append("**外貌描述**:")
                    markdown_lines.append("")
                    markdown_lines.append(char['appearance'])
                    markdown_lines.append("")

                # 特征标签
                if char['traits']:
                    try:
                        traits = json.loads(char['traits']) if isinstance(char['traits'], str) else char['traits']
                        if traits and isinstance(traits, list):
                            markdown_lines.append("**特征标签**:")
                            markdown_lines.append("")
                            for trait in traits:
                                markdown_lines.append(f"- {trait}")
                            markdown_lines.append("")
                    except:
                        pass

                # 主职业信息
                if char['main_career_id']:
                    career = await conn.fetchrow(
                        "SELECT name FROM careers WHERE id = $1",
                        char['main_career_id']
                    )
                    if career:
                        markdown_lines.append(f"**主职业**: {career['name']} (阶段: {char['main_career_stage'] or 1})")
                        markdown_lines.append("")

                # 副职业信息
                if char['sub_careers']:
                    try:
                        sub_careers = json.loads(char['sub_careers']) if isinstance(char['sub_careers'], str) else char['sub_careers']
                        if sub_careers and isinstance(sub_careers, list):
                            markdown_lines.append("**副职业**:")
                            markdown_lines.append("")
                            for sc in sub_careers:
                                career_id = sc.get('career_id')
                                stage = sc.get('stage', 1)
                                career = await conn.fetchrow(
                                    "SELECT name FROM careers WHERE id = $1",
                                    career_id
                                )
                                if career:
                                    markdown_lines.append(f"- {career['name']} (阶段: {stage})")
                            markdown_lines.append("")
                    except:
                        pass

            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")

        # 5. 关系管理
        print("正在整理关系管理...")
        relationships = await conn.fetch(
            "SELECT * FROM character_relationships WHERE project_id = $1",
            project_id
        )

        if relationships:
            markdown_lines.append("## 4. 关系管理")
            markdown_lines.append("")

            # 关系列表
            markdown_lines.append("### 关系列表")
            markdown_lines.append("")
            markdown_lines.append("| 角色A | 关系 | 角色B | 亲密度 | 状态 |")
            markdown_lines.append("|-------|------|-------|--------|------|")

            for rel in relationships:
                from_name = char_id_to_name.get(rel['character_from_id'], '未知')
                to_name = char_id_to_name.get(rel['character_to_id'], '未知')
                rel_name = rel['relationship_name'] or '未定义'
                intimacy = rel['intimacy_level'] or 50
                status = rel['status'] or 'active'

                # 根据亲密度显示不同的标签
                if intimacy >= 80:
                    intimacy_label = f"🔥{intimacy}"
                elif intimacy >= 50:
                    intimacy_label = f"❤️{intimacy}"
                elif intimacy >= 20:
                    intimacy_label = f"😐{intimacy}"
                else:
                    intimacy_label = f"💔{intimacy}"

                markdown_lines.append(f"| {from_name} | {rel_name} | {to_name} | {intimacy_label} | {status} |")

            markdown_lines.append("")

            # 关系详情
            markdown_lines.append("### 关系详情")
            markdown_lines.append("")

            # 按角色分组
            rel_by_char: Dict[str, List] = {}
            for rel in relationships:
                from_id = rel['character_from_id']
                if from_id not in rel_by_char:
                    rel_by_char[from_id] = []
                rel_by_char[from_id].append(rel)

            for from_id, rels in rel_by_char.items():
                from_name = char_id_to_name.get(from_id, '未知')
                markdown_lines.append(f"#### {from_name} 的关系")
                markdown_lines.append("")

                for rel in rels:
                    to_name = char_id_to_name.get(rel['character_to_id'], '未知')
                    rel_name = rel['relationship_name'] or '未定义'

                    markdown_lines.append(f"**与 {to_name}**: {rel_name}")
                    if rel['description']:
                        markdown_lines.append(f"> {rel['description']}")
                    if rel['started_at']:
                        markdown_lines.append(f"*开始时间: {rel['started_at']}*")
                    markdown_lines.append("")

            markdown_lines.append("---")
            markdown_lines.append("")

        # 6. 组织管理
        print("正在整理组织管理...")
        if org_characters:
            markdown_lines.append("## 5. 组织管理")
            markdown_lines.append("")

            # 获取组织详情
            org_details = {}
            for char in org_characters:
                org = await conn.fetchrow(
                    "SELECT * FROM organizations WHERE character_id = $1",
                    char['id']
                )
                org_details[char['id']] = org

            # 组织总览
            markdown_lines.append("### 组织总览")
            markdown_lines.append("")
            markdown_lines.append("| 序号 | 组织名称 | 组织类型 | 势力等级 | 成员数 |")
            markdown_lines.append("|------|----------|----------|----------|--------|")

            for idx, char in enumerate(org_characters, 1):
                org_name = char['name']
                org_type = char['organization_type'] or '-'
                org = org_details.get(char['id'])
                power_level = org['power_level'] if org else 50
                member_count = org['member_count'] if org else 0

                markdown_lines.append(f"| {idx} | {org_name} | {org_type} | {power_level} | {member_count} |")

            markdown_lines.append("")

            # 组织详情
            markdown_lines.append("### 组织详情")
            markdown_lines.append("")

            for char in org_characters:
                markdown_lines.append(f"#### {char['name']}")
                markdown_lines.append("")

                org_table = []
                org_table.append("| 属性 | 内容 |")
                org_table.append("|------|------|")
                org_table.append(f"| **组织名称** | {char['name']} |")
                if char['organization_type']:
                    org_table.append(f"| **组织类型** | {char['organization_type']} |")
                if char['organization_purpose']:
                    org_table.append(f"| **组织目的** | {char['organization_purpose']} |")

                org = org_details.get(char['id'])
                if org:
                    org_table.append(f"| **势力等级** | {org['power_level'] or 50} |")
                    org_table.append(f"| **成员数量** | {org['member_count'] or 0} |")
                    if org['location']:
                        org_table.append(f"| **所在地** | {org['location']} |")
                    if org['motto']:
                        org_table.append(f"| **宗旨/口号** | {org['motto']} |")

                markdown_lines.extend(org_table)
                markdown_lines.append("")

                # 组织特性
                if char['personality']:
                    markdown_lines.append("**组织特性**:")
                    markdown_lines.append("")
                    markdown_lines.append(char['personality'])
                    markdown_lines.append("")

                # 组织成员
                if org:
                    members = await conn.fetch(
                        "SELECT * FROM organization_members WHERE organization_id = $1 ORDER BY rank DESC",
                        org['id']
                    )

                    if members:
                        markdown_lines.append("**组织成员**:")
                        markdown_lines.append("")
                        markdown_lines.append("| 角色 | 职位 | 等级 | 状态 | 忠诚度 |")
                        markdown_lines.append("|------|------|------|------|--------|")

                        for member in members:
                            member_name = char_id_to_name.get(member['character_id'], '未知')
                            position = member['position'] or '-'
                            rank = member['rank'] or 0
                            status = member['status'] or 'active'
                            loyalty = member['loyalty'] or 50

                            markdown_lines.append(f"| {member_name} | {position} | {rank} | {status} | {loyalty} |")

                        markdown_lines.append("")

            markdown_lines.append("---")
            markdown_lines.append("")

        # 7. 大纲管理
        print("正在整理大纲管理...")
        outlines = await conn.fetch(
            "SELECT * FROM outlines WHERE project_id = $1 ORDER BY order_index",
            project_id
        )

        if outlines:
            markdown_lines.append("## 6. 大纲管理")
            markdown_lines.append("")

            # 统计每个大纲关联的章节数
            outline_chapter_count = {}
            for outline in outlines:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM chapters WHERE outline_id = $1",
                    outline['id']
                )
                outline_chapter_count[outline['id']] = count

            # 大纲列表
            markdown_lines.append("### 大纲列表")
            markdown_lines.append("")
            markdown_lines.append("| 序号 | 大纲标题 | 关联章节数 |")
            markdown_lines.append("|------|----------|------------|")

            for idx, outline in enumerate(outlines, 1):
                chapter_count = outline_chapter_count.get(outline['id'], 0)
                markdown_lines.append(f"| {idx} | {outline['title']} | {chapter_count} |")

            markdown_lines.append("")

            # 大纲详情
            markdown_lines.append("### 大纲详情")
            markdown_lines.append("")

            for outline in outlines:
                markdown_lines.append(f"#### {outline['title']}")
                markdown_lines.append("")

                if outline['content']:
                    markdown_lines.append(outline['content'])
                    markdown_lines.append("")

                # 关联章节
                chapters = await conn.fetch(
                    "SELECT chapter_number, title FROM chapters WHERE outline_id = $1 ORDER BY chapter_number",
                    outline['id']
                )

                if chapters:
                    markdown_lines.append("**关联章节**:")
                    markdown_lines.append("")
                    for ch in chapters:
                        markdown_lines.append(f"- 第{ch['chapter_number']}章: {ch['title']}")
                    markdown_lines.append("")

            markdown_lines.append("---")
            markdown_lines.append("")

        # 8. 章节管理
        print("正在整理章节管理...")
        chapters = await conn.fetch(
            "SELECT * FROM chapters WHERE project_id = $1 ORDER BY chapter_number",
            project_id
        )

        if chapters:
            markdown_lines.append("## 7. 章节管理")
            markdown_lines.append("")

            # 章节列表
            markdown_lines.append("### 章节列表")
            markdown_lines.append("")
            markdown_lines.append("| 章节号 | 标题 | 字数 | 状态 |")
            markdown_lines.append("|--------|------|------|------|")

            for ch in chapters:
                status = ch['status'] or 'draft'
                status_map = {
                    'draft': '草稿',
                    'completed': '已完成',
                    'published': '已发布'
                }
                status_text = status_map.get(status, status)
                markdown_lines.append(f"| 第{ch['chapter_number']}章 | {ch['title']} | {ch['word_count'] or 0} | {status_text} |")

            markdown_lines.append("")

            # 章节详情
            markdown_lines.append("### 章节详情")
            markdown_lines.append("")

            for ch in chapters:
                markdown_lines.append(f"#### 第{ch['chapter_number']}章 {ch['title']}")
                markdown_lines.append("")

                # 基本信息
                ch_info = []
                ch_info.append(f"- **字数**: {ch['word_count'] or 0}")
                ch_info.append(f"- **状态**: {ch['status'] or 'draft'}")
                if ch['summary']:
                    ch_info.append(f"- **摘要**: {ch['summary']}")
                if ch['outline_id']:
                    outline = await conn.fetchrow(
                        "SELECT title FROM outlines WHERE id = $1",
                        ch['outline_id']
                    )
                    if outline:
                        ch_info.append(f"- **所属大纲**: {outline['title']}")
                        ch_info.append(f"- **子章节序号**: {ch['sub_index'] or 1}")

                markdown_lines.extend(ch_info)
                markdown_lines.append("")

                # 章节内容
                if ch['content']:
                    # 使用代码块来展示内容，避免Markdown格式冲突
                    markdown_lines.append("**章节内容**:")
                    markdown_lines.append("")
                    markdown_lines.append("```")
                    # 限制内容长度，避免文件过大
                    content = ch['content']
                    if len(content) > 5000:
                        content = content[:5000] + "\n\n...(内容过长，已截断，完整内容请查看数据库)"
                    markdown_lines.append(content)
                    markdown_lines.append("```")
                    markdown_lines.append("")

            markdown_lines.append("---")
            markdown_lines.append("")

        # 9. 剧情分析
        print("正在整理剧情分析...")
        plot_analyses = await conn.fetch(
            "SELECT * FROM plot_analysis WHERE project_id = $1",
            project_id
        )

        if plot_analyses:
            markdown_lines.append("## 8. 剧情分析")
            markdown_lines.append("")

            # 构建章节映射
            ch_id_to_chapter = {}
            for ch in chapters:
                ch_id_to_chapter[ch['id']] = ch

            # 按章节排序
            def get_chapter_number(pa):
                ch = ch_id_to_chapter.get(pa['chapter_id'])
                return ch['chapter_number'] if ch else 999

            plot_analyses_sorted = sorted(plot_analyses, key=get_chapter_number)

            for analysis in plot_analyses_sorted:
                chapter = ch_id_to_chapter.get(analysis['chapter_id'])
                if not chapter:
                    continue

                markdown_lines.append(f"### 第{chapter['chapter_number']}章: {chapter['title']}")
                markdown_lines.append("")

                # 基本信息
                if analysis['plot_stage']:
                    markdown_lines.append(f"**剧情阶段**: {analysis['plot_stage']}")
                    markdown_lines.append("")
                if analysis['conflict_level']:
                    markdown_lines.append(f"**冲突强度**: {analysis['conflict_level']}/10")
                    markdown_lines.append("")
                if analysis['emotional_tone']:
                    markdown_lines.append(f"**情感基调**: {analysis['emotional_tone']}")
                    markdown_lines.append("")
                if analysis['pacing']:
                    markdown_lines.append(f"**节奏**: {analysis['pacing']}")
                    markdown_lines.append("")

                # 钩子分析
                if analysis['hooks']:
                    try:
                        hooks = json.loads(analysis['hooks']) if isinstance(analysis['hooks'], str) else analysis['hooks']
                        if hooks and isinstance(hooks, list):
                            markdown_lines.append("**钩子分析**:")
                            markdown_lines.append("")
                            for hook in hooks:
                                hook_type = hook.get('type', '-')
                                content = hook.get('content', '-')
                                strength = hook.get('strength', 0)
                                position = hook.get('position', '-')
                                markdown_lines.append(f"- [{hook_type}] {content} (强度:{strength}, 位置:{position})")
                            markdown_lines.append("")
                    except:
                        pass

                # 伏笔分析
                if analysis['foreshadows_planted'] or analysis['foreshadows_resolved']:
                    markdown_lines.append("**伏笔分析**:")
                    markdown_lines.append("")
                    if analysis['foreshadows_planted']:
                        markdown_lines.append(f"- 本章埋下伏笔数: {analysis['foreshadows_planted']}")
                    if analysis['foreshadows_resolved']:
                        markdown_lines.append(f"- 本章回收伏笔数: {analysis['foreshadows_resolved']}")
                    markdown_lines.append("")

                # 质量评分
                if any([analysis['overall_quality_score'], analysis['pacing_score'],
                       analysis['engagement_score'], analysis['coherence_score']]):
                    markdown_lines.append("**质量评分**:")
                    markdown_lines.append("")
                    if analysis['overall_quality_score']:
                        markdown_lines.append(f"- 整体质量: {analysis['overall_quality_score']:.1f}/10")
                    if analysis['pacing_score']:
                        markdown_lines.append(f"- 节奏: {analysis['pacing_score']:.1f}/10")
                    if analysis['engagement_score']:
                        markdown_lines.append(f"- 吸引力: {analysis['engagement_score']:.1f}/10")
                    if analysis['coherence_score']:
                        markdown_lines.append(f"- 连贯性: {analysis['coherence_score']:.1f}/10")
                    markdown_lines.append("")

                # 分析报告
                if analysis['analysis_report']:
                    markdown_lines.append("**分析报告**:")
                    markdown_lines.append("")
                    report = analysis['analysis_report'].replace('\n', '\n> ')
                    markdown_lines.append(f"> {report}")
                    markdown_lines.append("")

                # 改进建议
                if analysis['suggestions']:
                    try:
                        suggestions = json.loads(analysis['suggestions']) if isinstance(analysis['suggestions'], str) else analysis['suggestions']
                        if suggestions and isinstance(suggestions, list):
                            markdown_lines.append("**改进建议**:")
                            markdown_lines.append("")
                            for suggestion in suggestions:
                                markdown_lines.append(f"- {suggestion}")
                            markdown_lines.append("")
                    except:
                        pass

            markdown_lines.append("---")
            markdown_lines.append("")

        # 10. 伏笔管理
        print("正在整理伏笔管理...")
        foreshadows = await conn.fetch(
            "SELECT * FROM foreshadows WHERE project_id = $1",
            project_id
        )

        if foreshadows:
            markdown_lines.append("## 9. 伏笔管理")
            markdown_lines.append("")

            # 按状态分组
            foreshadows_by_status = {
                'pending': [],
                'planted': [],
                'resolved': [],
                'partially_resolved': [],
                'abandoned': []
            }

            status_names = {
                'pending': '待埋入',
                'planted': '已埋入',
                'resolved': '已回收',
                'partially_resolved': '部分回收',
                'abandoned': '已废弃'
            }

            for fs in foreshadows:
                status = fs['status'] or 'pending'
                if status in foreshadows_by_status:
                    foreshadows_by_status[status].append(fs)

            # 统计
            markdown_lines.append("### 伏笔统计")
            markdown_lines.append("")
            markdown_lines.append("| 状态 | 数量 |")
            markdown_lines.append("|------|------|")
            for status, fs_list in foreshadows_by_status.items():
                if fs_list:
                    markdown_lines.append(f"| {status_names.get(status, status)} | {len(fs_list)} |")
            markdown_lines.append("")

            # 伏笔列表
            markdown_lines.append("### 伏笔列表")
            markdown_lines.append("")
            markdown_lines.append("| 伏笔标题 | 状态 | 类型 | 埋入章节 | 回收章节 | 重要性 |")
            markdown_lines.append("|----------|------|------|----------|----------|--------|")

            for fs in foreshadows:
                title = fs['title']
                status = status_names.get(fs['status'] or 'pending', fs['status'])
                category = fs['category'] or '-'
                plant_ch = fs['plant_chapter_number'] or '-'
                resolve_ch = fs['target_resolve_chapter_number'] or '-'
                importance = fs['importance'] or 0.5

                markdown_lines.append(f"| {title} | {status} | {category} | 第{plant_ch}章 | 第{resolve_ch}章 | {importance:.2f} |")

            markdown_lines.append("")

            # 伏笔详情
            markdown_lines.append("### 伏笔详情")
            markdown_lines.append("")

            for fs in foreshadows:
                markdown_lines.append(f"#### {fs['title']}")
                markdown_lines.append("")

                # 基本信息
                fs_table = []
                fs_table.append("| 属性 | 内容 |")
                fs_table.append("|------|------|")
                fs_table.append(f"| **状态** | {status_names.get(fs['status'] or 'pending', fs['status'])} |")
                if fs['category']:
                    fs_table.append(f"| **分类** | {fs['category']} |")
                fs_table.append(f"| **重要性** | {(fs['importance'] or 0.5):.2f} |")
                fs_table.append(f"| **伏笔强度** | {fs['strength'] or 5}/10 |")
                fs_table.append(f"| **隐藏度** | {fs['subtlety'] or 5}/10 |")
                if fs['plant_chapter_number']:
                    fs_table.append(f"| **埋入章节** | 第{fs['plant_chapter_number']}章 |")
                if fs['target_resolve_chapter_number']:
                    fs_table.append(f"| **计划回收章节** | 第{fs['target_resolve_chapter_number']}章 |")
                if fs['actual_resolve_chapter_number']:
                    fs_table.append(f"| **实际回收章节** | 第{fs['actual_resolve_chapter_number']}章 |")

                markdown_lines.extend(fs_table)
                markdown_lines.append("")

                # 伏笔内容
                if fs['content']:
                    markdown_lines.append("**伏笔描述**:")
                    markdown_lines.append("")
                    markdown_lines.append(fs['content'])
                    markdown_lines.append("")

                if fs['hint_text']:
                    markdown_lines.append("**暗示文本**:")
                    markdown_lines.append("")
                    markdown_lines.append(f"> {fs['hint_text']}")
                    markdown_lines.append("")

                if fs['resolution_text']:
                    markdown_lines.append("**回收揭示**:")
                    markdown_lines.append("")
                    markdown_lines.append(f"> {fs['resolution_text']}")
                    markdown_lines.append("")

                # 关联角色
                if fs['related_characters']:
                    try:
                        related_chars = json.loads(fs['related_characters']) if isinstance(fs['related_characters'], str) else fs['related_characters']
                        if related_chars and isinstance(related_chars, list):
                            markdown_lines.append("**涉及角色**:")
                            markdown_lines.append("")
                            for char_name in related_chars:
                                markdown_lines.append(f"- {char_name}")
                            markdown_lines.append("")
                    except:
                        pass

                # 标签
                if fs['tags']:
                    try:
                        tags = json.loads(fs['tags']) if isinstance(fs['tags'], str) else fs['tags']
                        if tags and isinstance(tags, list):
                            markdown_lines.append("**标签**:")
                            markdown_lines.append("")
                            for tag in tags:
                                markdown_lines.append(f"`{tag}` ")
                            markdown_lines.append("")
                    except:
                        pass

                # 备注
                if fs['notes']:
                    markdown_lines.append("**备注**:")
                    markdown_lines.append("")
                    markdown_lines.append(fs['notes'])
                    markdown_lines.append("")

                if fs['resolution_notes']:
                    markdown_lines.append("**回收说明**:")
                    markdown_lines.append("")
                    markdown_lines.append(fs['resolution_notes'])
                    markdown_lines.append("")

            markdown_lines.append("---")
            markdown_lines.append("")

        # 文档结尾
        markdown_lines.append("---")
        markdown_lines.append("")
        markdown_lines.append("*本文档由 MuMuAI 小说创作系统自动生成*")
        markdown_lines.append("")
        markdown_lines.append(f"**项目**: {project['title']}")
        markdown_lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 写入文件
        markdown_content = "\n".join(markdown_lines)

        print(f"正在写入文件: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"导出完成! 文件已保存到: {output_file}")
        print(f"文件大小: {len(markdown_content)} 字符")

        # 输出统计信息
        print("\n=== 导出统计 ===")
        print(f"- 项目: {project['title']}")
        print(f"- 主职业: {len([c for c in careers if c['type'] == 'main'])}")
        print(f"- 副职业: {len([c for c in careers if c['type'] == 'sub'])}")
        print(f"- 角色: {len(role_characters)}")
        print(f"- 组织: {len(org_characters)}")
        print(f"- 关系: {len(relationships)}")
        print(f"- 大纲: {len(outlines)}")
        print(f"- 章节: {len(chapters)}")
        print(f"- 剧情分析: {len(plot_analyses)}")
        print(f"- 伏笔: {len(foreshadows)}")

    finally:
        await conn.close()

    return output_file


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python export_project_to_markdown.py <project_id> [output_file]")
        print("示例: python export_project_to_markdown.py ee00aef3-408d-4740-86cc-19e654f81c45")
        sys.exit(1)

    project_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 60)
    print("MuMuAI 项目数据导出工具")
    print("=" * 60)
    print(f"项目ID: {project_id}")
    print(f"输出文件: {output_file or '自动生成'}")
    print("=" * 60)
    print()

    try:
        result = await export_project_to_markdown(project_id, output_file)
        print(f"\n成功! 导出文件: {result}")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
