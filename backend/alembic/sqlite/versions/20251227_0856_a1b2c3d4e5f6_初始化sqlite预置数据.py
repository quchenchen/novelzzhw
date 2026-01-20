"""初始化SQLite预置数据

Revision ID: a1b2c3d4e5f6
Revises: fbeb1038c728
Create Date: 2025-12-27 08:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, String, Integer, Text


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fbeb1038c728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """插入预置数据"""
    
    # ==================== 1. 插入关系类型数据 ====================
    relationship_types_table = table(
        'relationship_types',
        column('name', String),
        column('category', String),
        column('reverse_name', String),
        column('intimacy_range', String),
        column('icon', String),
        column('description', Text),
    )
    
    relationship_types_data = [
        # 家庭关系
        {"name": "父亲", "category": "family", "reverse_name": "子女", "intimacy_range": "high", "icon": "👨", "description": "父子/父女关系"},
        {"name": "母亲", "category": "family", "reverse_name": "子女", "intimacy_range": "high", "icon": "👩", "description": "母子/母女关系"},
        {"name": "兄弟", "category": "family", "reverse_name": "兄弟", "intimacy_range": "high", "icon": "👬", "description": "兄弟关系"},
        {"name": "姐妹", "category": "family", "reverse_name": "姐妹", "intimacy_range": "high", "icon": "👭", "description": "姐妹关系"},
        {"name": "子女", "category": "family", "reverse_name": "父母", "intimacy_range": "high", "icon": "👶", "description": "子女关系"},
        {"name": "配偶", "category": "family", "reverse_name": "配偶", "intimacy_range": "high", "icon": "💑", "description": "夫妻关系"},
        {"name": "恋人", "category": "family", "reverse_name": "恋人", "intimacy_range": "high", "icon": "💕", "description": "恋爱关系"},
        
        # 社交关系
        {"name": "师父", "category": "social", "reverse_name": "徒弟", "intimacy_range": "high", "icon": "🎓", "description": "师徒关系（师父视角）"},
        {"name": "徒弟", "category": "social", "reverse_name": "师父", "intimacy_range": "high", "icon": "📚", "description": "师徒关系（徒弟视角）"},
        {"name": "朋友", "category": "social", "reverse_name": "朋友", "intimacy_range": "medium", "icon": "🤝", "description": "朋友关系"},
        {"name": "同学", "category": "social", "reverse_name": "同学", "intimacy_range": "medium", "icon": "🎒", "description": "同学关系"},
        {"name": "邻居", "category": "social", "reverse_name": "邻居", "intimacy_range": "low", "icon": "🏘️", "description": "邻居关系"},
        {"name": "知己", "category": "social", "reverse_name": "知己", "intimacy_range": "high", "icon": "💙", "description": "知心好友"},
        
        # 职业关系
        {"name": "上司", "category": "professional", "reverse_name": "下属", "intimacy_range": "low", "icon": "👔", "description": "上下级关系（上司视角）"},
        {"name": "下属", "category": "professional", "reverse_name": "上司", "intimacy_range": "low", "icon": "💼", "description": "上下级关系（下属视角）"},
        {"name": "同事", "category": "professional", "reverse_name": "同事", "intimacy_range": "medium", "icon": "🤵", "description": "同事关系"},
        {"name": "合作伙伴", "category": "professional", "reverse_name": "合作伙伴", "intimacy_range": "medium", "icon": "🤜🤛", "description": "合作关系"},
        
        # 敌对关系
        {"name": "敌人", "category": "hostile", "reverse_name": "敌人", "intimacy_range": "low", "icon": "⚔️", "description": "敌对关系"},
        {"name": "仇人", "category": "hostile", "reverse_name": "仇人", "intimacy_range": "low", "icon": "💢", "description": "仇恨关系"},
        {"name": "竞争对手", "category": "hostile", "reverse_name": "竞争对手", "intimacy_range": "low", "icon": "🎯", "description": "竞争关系"},
        {"name": "宿敌", "category": "hostile", "reverse_name": "宿敌", "intimacy_range": "low", "icon": "⚡", "description": "宿命之敌"},
    ]
    
    op.bulk_insert(relationship_types_table, relationship_types_data)
    print(f"✅ SQLite: 已插入 {len(relationship_types_data)} 条关系类型数据")
    
    
    # ==================== 2. 插入全局写作风格预设 ====================
    writing_styles_table = table(
        'writing_styles',
        column('user_id', String),
        column('name', String),
        column('style_type', String),
        column('preset_id', String),
        column('description', Text),
        column('prompt_content', Text),
        column('order_index', Integer),
    )
    
    writing_styles_data = [
        {
            "user_id": None,  # NULL 表示全局预设
            "name": "自然流畅",
            "style_type": "preset",
            "preset_id": "natural",
            "description": "自然流畅的叙事风格，适合现代都市、现实题材",
            "prompt_content": """写作风格要求：
1. 语言简洁明快，贴近现代口语
2. 多用短句，节奏流畅
3. 注重情感细节的自然流露
4. 避免过度修饰和复杂句式""",
            "order_index": 1
        },
        {
            "user_id": None,
            "name": "古典优雅",
            "style_type": "preset",
            "preset_id": "classical",
            "description": "古典文雅的写作风格，适合古装、仙侠题材",
            "prompt_content": """写作风格要求：
1. 使用文言、半文言或典雅的白话
2. 适当运用古典诗词意象
3. 注重意境营造和韵味
4. 对话和描写保持古典美感""",
            "order_index": 2
        },
        {
            "user_id": None,
            "name": "现代简约",
            "style_type": "preset",
            "preset_id": "modern",
            "description": "现代简约风格，适合轻小说、网文快节奏叙事",
            "prompt_content": """写作风格要求：
1. 语言直白简练，信息密度高
2. 多用对话推进情节
3. 避免冗长描写，突出关键动作
4. 节奏明快，适合快速阅读""",
            "order_index": 3
        },
        {
            "user_id": None,
            "name": "文艺细腻",
            "style_type": "preset",
            "preset_id": "literary",
            "description": "文艺细腻风格，注重心理描写和氛围营造",
            "prompt_content": """写作风格要求：
1. 注重心理活动和情感细节
2. 善用环境描写烘托氛围
3. 语言优美，富有文学性
4. 适当使用比喻、象征等修辞手法""",
            "order_index": 4
        },
        {
            "user_id": None,
            "name": "紧张悬疑",
            "style_type": "preset",
            "preset_id": "suspense",
            "description": "紧张悬疑风格，适合推理、惊悚题材",
            "prompt_content": """写作风格要求：
1. 营造紧张压迫的氛围
2. 多用短句加快节奏
3. 善于设置悬念和伏笔
4. 注重细节描写，为推理埋下线索""",
            "order_index": 5
        },
        {
            "user_id": None,
            "name": "幽默诙谐",
            "style_type": "preset",
            "preset_id": "humorous",
            "description": "幽默诙谐风格，适合轻松搞笑题材",
            "prompt_content": """写作风格要求：
1. 语言活泼风趣，善用俏皮话
2. 注重对话的喜剧效果
3. 适当夸张和反转制造笑点
4. 保持轻松愉快的基调""",
            "order_index": 6
        },
        # ========== 番茄小说平台专用风格 ==========
        {
            "user_id": None,
            "name": "番茄爽文风",
            "style_type": "preset",
            "preset_id": "fanqie_shuangwen",
            "description": "番茄小说平台专用爽文风格，快节奏+强冲突+爽点密集",
            "prompt_content": """【番茄爽文写作指南】

**核心原则：强情绪+快节奏+获得感**

**开篇要求（黄金三章）：**
- 300字内必须出现核心冲突（死亡/背叛/危机/退婚）
- 500字内点明金手指（系统/重生/空间/异能）
- 1000字内触发首个爽点
- 快速入局，不要输出世界观设定

**爽点设置技巧：**
- 情绪要浓：让读者有强烈情绪反应
- 节奏要快：没有任何注水内容
- 先虐后爽：压抑-反击-打脸-收获
- 悬念连环：层层递进，吸引继续阅读

**写作要求：**
- 聚焦主角，减少无关人物
- 开篇明志，确定故事风格
- 用一句话讲清楚不重要内容
- 让读者一眼认出主角及其特性
- 每个爽点要有铺垫和爆发""",
            "order_index": 7
        },
        {
            "user_id": None,
            "name": "飞卢快节奏风",
            "style_type": "preset",
            "preset_id": "feilu_fast",
            "description": "飞卢风格快节奏爽文，戏剧冲突集中，节奏明快",
            "prompt_content": """【飞卢风快节奏写作指南】

**核心特点：节奏明快+戏剧冲突集中**

**开篇套路：**
- 直接抓取"装逼打脸"的快节奏模式
- 开局系统砸脸或金手指激活
- 人设和世界观构建后立即引爆冲突

**节奏控制：**
- 每天一个小卡点
- 三天一个大高潮
- 卡点之间要有铺垫和交叠
- 不拖沓交代背景
- 不演绎无关场景
- 只表现戏剧性冲突

**写作要求：**
- 不拖泥带水，直接进入冲突
- 装逼打脸节奏紧凑
- 情节推进快，反转迅速
- 信息密度高，无注水内容
- 适合系统文、都市爽文、玄幻爽文""",
            "order_index": 8
        },
        {
            "user_id": None,
            "name": "规则怪谈风",
            "style_type": "preset",
            "preset_id": "rule_horror",
            "description": "规则怪谈+无限流风格，悬疑推理+规则博弈",
            "prompt_content": """【规则怪谈+无限流写作指南】

**核心特点：规则博弈+悬疑推理+生死危机**

**设定要点：**
- 明确的规则体系：必须遵守、否则致命
- 规则的模糊性：表面规则vs隐藏规则
- 信息的稀缺性：需要推理才能发现真相
- 生死紧迫感：违反规则=死亡

**叙事结构：**
- 开篇即入局：主角突然陷入规则怪谈场景
- 规则逐步揭示：每轮发现新的规则线索
- 试错与推理：通过失败总结规律
- 反转与突破：发现规则的漏洞或深层真相

**写作要求：**
- 氛围压抑神秘
- 悬念设置密集
- 细节即是线索
- 规则描述清晰但留有解读空间
- 适合融合无限流、副本、逃脱元素""",
            "order_index": 9
        },
        {
            "user_id": None,
            "name": "都市脑洞风",
            "style_type": "preset",
            "preset_id": "urban_brainhole",
            "description": "都市脑洞文，创意新颖、情节出人意料",
            "prompt_content": """【都市脑洞文写作指南】

**核心特点：创意新颖+出人意料+现实指向**

**设定要求：**
- 突破常规思维：意想不到的金手指或设定
- 脑洞要合理：荒诞中自有逻辑
- 现实感与幻想结合：都市背景+超现实元素

**叙事特点：**
- 开篇即脑洞：第一章就让读者感受到"不一般"
- 反套路：打破传统爽文模式
- 有现实指向：脑洞背后有深层思考
- 情节出人意料但不突兀

**常见类型：**
- 特殊职业系统（如给鬼算命、帮人改命）
- 奇异物品/空间（如能进入梦境、修改过去）
- 身份突变（如变成物品、动物、概念）
- 规则类异能（如说话成真、交易寿命）

**写作要求：**
- 脑洞要新鲜，避免陈词滥调
- 节奏紧凑，快速展现脑洞魅力
- 角色反应真实可信
- 世界观自洽""",
            "order_index": 10
        },
        {
            "user_id": None,
            "name": "新媒体都市风",
            "style_type": "preset",
            "preset_id": "newmedia_urban",
            "description": "新媒体都市文风格，战神/女婿/都市生活类",
            "prompt_content": """【新媒体都市文写作指南】

**核心特点：强代入感+情绪拉扯+爽点密集**

**热门类型：**
- 战神归来：隐退战神回归都市
- 上门女婿：废柴女婿逆袭打脸
- 都市神医：医术通天的都市传奇
- 重生年代：重生回过去改变命运

**叙事套路：**
- 开篇即冲突：主角被轻视/欺辱
- 身份反差：表面普通实则不凡
- 打脸节奏：压抑-爆发-打脸循环
- 情绪拉扯：家人/爱人/敌人的态度转变

**写作要求：**
- 代入感强：让读者仿佛就是主角
- 冲突集中：每章都有矛盾爆发
- 情绪饱满：屈辱、愤怒、爽快等情绪强烈
- 节奏明快：快速推进到下一个冲突
- 适合中老年读者群体""",
            "order_index": 11
        },
    ]
    
    op.bulk_insert(writing_styles_table, writing_styles_data)
    print(f"✅ SQLite: 已插入 {len(writing_styles_data)} 条全局写作风格预设")


def downgrade() -> None:
    """删除预置数据"""
    
    # 删除写作风格预设（只删除全局预设）
    op.execute("DELETE FROM writing_styles WHERE user_id IS NULL")
    print("✅ SQLite: 已删除全局写作风格预设")
    
    # 删除关系类型
    op.execute("DELETE FROM relationship_types")
    print("✅ SQLite: 已删除关系类型数据")