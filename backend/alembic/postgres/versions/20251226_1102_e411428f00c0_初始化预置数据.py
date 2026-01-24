"""初始化预置数据

Revision ID: e411428f00c0
Revises: ee0a189f1532
Create Date: 2025-12-26 11:02:24.080526

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, String, Integer, Float, Text, Boolean, DateTime


# revision identifiers, used by Alembic.
revision: str = 'e411428f00c0'
down_revision: Union[str, None] = 'ee0a189f1532'
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
    print(f"✅ 已插入 {len(relationship_types_data)} 条关系类型数据")
    
    
    # ==================== 2. 插入全局写作风格预设 ====================
    # 注意：这里需要从 WritingStyleManager 获取预设配置
    # 为了避免导入应用代码，我们直接硬编码预设风格
    
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
        # ========== V2 版本：去除 AI 痕迹的改进风格 ==========
        {
            "user_id": None,
            "name": "自然流畅 V2",
            "style_type": "preset",
            "preset_id": "natural_v2",
            "description": "自然流畅的叙事风格，适合现代都市、现实题材（去除AI痕迹版）",
            "prompt_content": """【自然流畅写作指南】

语言要像说话一样自然。别用那些书面语腔调，就想着你在给朋友讲个事。
- 把"他感到非常悲伤"改成"他低着头，半天没说话"
- 把"她迅速地跑开了"改成"她转身就跑"

句子别太长，读起来要顺畅。长句拆成短句，让读者能喘口气。
- 遇到逗号超过三个的句子，考虑拆成两句
- 一个句子只说一件事，别塞太多内容

情感藏在细节里，别直接喊出来。读者要自己感受到，不是你告诉他们。
- 不要写"他很愤怒"，写"他把杯子重重地放下"
- 不要写"她很紧张"，写"她手心出汗，手指不停地绞着衣角"

少用形容词堆砌，多写动作和对话。形容词是背景，动作才是故事。
- 不写"阳光明媚、鸟语花香的早晨"，写"早晨的阳光照在脸上，麻雀在树上叫"
- 能用动作表达的，就不用形容词描述""",
            "order_index": 12
        },
        {
            "user_id": None,
            "name": "古典优雅 V2",
            "style_type": "preset",
            "preset_id": "classical_v2",
            "description": "古风雅韵，辞藻华丽，适合古言、仙侠题材（去除AI痕迹版）",
            "prompt_content": """【古典优雅写作指南】

用词要古雅，但别堆砌辞藻。不是每个词都要找文言替代，关键是意境。
- "他走了"不用"他拂袖而去"，除非真在写古风
- 多用"只见"、"忽闻"、"原来"这些连接词

节奏要慢下来。古人说话不赶时间，写也是一样。
- 一句话写完一个动作，别急着写下一个
- 环境描写可以长，人物对话可以短

情景交融。环境不只是背景，是心情的外化。
- 下雨不是雨，是心情
- 月亮不只是月亮，是思念的载体

对话要有古意，但别太晦涩。读者要能看懂，别写成考古文献。
- 少用"你"、"我"，多用"阁下"、"在下"
- 但别过度，现代读者还是要看懂为主""",
            "order_index": 13
        },
        {
            "user_id": None,
            "name": "现代简约 V2",
            "style_type": "preset",
            "preset_id": "minimalist_v2",
            "description": "极简主义，留白写意，适合现代都市、极简风格（去除AI痕迹版）",
            "prompt_content": """【现代简约写作指南】

少即是多。能用一个字说的，别用两个字。
- 删掉所有"的"、"地"、"得"，不影响理解就去掉
- 形容词能删就删，只留最关键的

句子要短。一个句子一个意思。
- 逗号超过两个，考虑拆成两句
- 主语可以省略，读者能懂就行

留白。不写出来的比写出来的更有力量。
- 别解释角色为什么这么做，写他做了什么
- 别分析角色是什么心情，写他的表情和动作

对话要干净。没人说话带那么多修饰词。
- 别写"他愤怒地说"、"她悲伤地回答"
- 写"他说"、"她答"，让对话本身表达情绪""",
            "order_index": 14
        },
        {
            "user_id": None,
            "name": "文艺细腻 V2",
            "style_type": "preset",
            "preset_id": "literary_v2",
            "description": "细腻抒情，心理描写深入，适合文艺片风格（去除AI痕迹版）",
            "prompt_content": """【文艺细腻写作指南】

慢下来。一个眼神可以写一段。

环境要反映心情。下雨不是雨，是心情。
- 环境变化对应角色情绪变化
- 同样的环境在不同心境下有不同感觉

比喻要贴切，别为比喻而比喻。
- 比喻要新鲜，别用"心如刀绞"、"泪如雨下"
- 比喻要贴切，读者一看就懂那种感觉

对话可以少，但每句都要有分量。
- 话不说满，留一半让读者猜
- 省略号比句号更有意思

留白比说透更有意思。
- 别把所有情绪都写出来
- 让读者自己填充，他们参与的才是故事""",
            "order_index": 15
        },
        {
            "user_id": None,
            "name": "紧张悬疑 V2",
            "style_type": "preset",
            "preset_id": "suspense_v2",
            "description": "节奏紧凑，悬念迭起，适合悬疑、推理题材（去除AI痕迹版）",
            "prompt_content": """【紧张悬疑写作指南】

节奏要快。短句，更短的句。
- 一行一句话也别嫌多
- 追逐戏、发现戏尤其要快

信息要慢给。别一次性全抖出来。
- 每次只给一个线索
- 给线索的同时制造新问题

环境要压抑。不是阴森，是让人透不过气。
- 安静比吵闹更可怕
- 细节要放大：墙上的裂缝、水滴的声音

结尾要钩人。每章结尾都要留悬念。
- 不是"接下来发生了什么"，而是"为什么这样"
- 最后一句话要让读者必须翻页""",
            "order_index": 16
        },
        {
            "user_id": None,
            "name": "幽默诙谐 V2",
            "style_type": "preset",
            "preset_id": "humorous_v2",
            "description": "轻松幽默，搞笑吐槽，适合都市轻喜剧（去除AI痕迹版）",
            "prompt_content": """【幽默诙谐写作指南】

笑点要自然，别硬梗。
- 不是每句话都要搞笑
- 情境搞笑比语言搞笑更有记忆点

吐槽要到位，别隔靴搔痒。
- 说出读者想说的话
- 但要换个更有趣的方式

自黑最高级。拿自己开涮最安全也最讨喜。
- 主角可以有缺点，甚至很多缺点
- 完美的主角不好笑，笨蛋主角才可爱

节奏别拖。笑点过了就过，别重复。
- 一个梗用一次就好
- 笑完赶紧推进故事，别在那回味""",
            "order_index": 17
        },
        {
            "user_id": None,
            "name": "番茄爽文风 V2",
            "style_type": "preset",
            "preset_id": "fanqie_shuangwen_v2",
            "description": "快节奏爽文，情绪拉满，适合番茄小说平台（去除AI痕迹版）",
            "prompt_content": """【番茄爽文写作指南】

开篇就炸。前300字必须有冲突。
- 离婚、背叛、退婚、死亡，选一个直接上
- 别铺垫，别介绍世界观，直接进戏

金手指要快亮出来，别藏着。
- 前三章必须交代清楚金手指是什么
- 金手指要强，但别无敌到没故事

爽点是爽-虐-爽-虐，单边爽不行。
- 虐是铺垫，爽是释放
- 每次爽之前要先压，压得越狠爽得越猛

打脸要脆，别拖泥带水。
- 反派别废话，直接干
- 打完就收，别在那洋洋得意

读者要的是"爽"，不是"合理"。合理是爽的附加品。
- 逻辑能通就行，别为了合理牺牲爽
- 爽文不是论文，读者要的是情绪宣泄

每章一个小高潮，三章一个大反转。
- 别写流水账，每章都要有事
- 悬念要挂，让读者点下一章""",
            "order_index": 18
        },
        {
            "user_id": None,
            "name": "飞卢快节奏风 V2",
            "style_type": "preset",
            "preset_id": "feilu_fast_v2",
            "description": "超快节奏，密集爽点，适合飞卢小说平台（去除AI痕迹版）",
            "prompt_content": """【飞卢快节奏写作指南】

快。更快。还要快。

开篇300字内必须让读者知道：
- 主角是谁
- 金手指是什么
- 第一个冲突是什么

每章2000字，不能水。
- 一章至少一个爽点
- 三章一个小高潮，十章一个大事件

别写心里戏，写戏。
- 心理活动能省就省
- 动作、对话、结果，直接上

反派要强，但要有破绽。
- 反派太弱没爽感
- 反派太强打不过，要给破绽

读者要爽，不要文青。
- 别玩深沉，别玩意识流
- 爽点要直接，情绪要拉满""",
            "order_index": 19
        },
        {
            "user_id": None,
            "name": "规则怪谈风 V2",
            "style_type": "preset",
            "preset_id": "rule_horror_v2",
            "description": "规则类怪谈，诡异氛围，适合恐怖悬疑题材（去除AI痕迹版）",
            "prompt_content": """【规则怪谈写作指南】

规则要具体，别模糊。
- "不要出门"不如"晚上12点后禁止打开房门"
- 数字要精确，时间要具体

规则要有矛盾，但别太明显。
- 两条规则看似冲突，其实是不同情况
- 让读者自己去发现其中的逻辑

氛围要压抑，别靠血腥。
- 恐怖不是血肉横飞，是未知
- 声音、影子、异常，这些比鬼脸更吓人

规则要有代价。
- 违反规则的后果要写清楚
- 但后果可以多样，别每次都一样

结局要开放，别解释一切。
- 留一些谜团给读者
- 解释完了就不神秘了""",
            "order_index": 20
        },
        {
            "user_id": None,
            "name": "都市脑洞风 V2",
            "style_type": "preset",
            "preset_id": "urban_idea_v2",
            "description": "脑洞大开的都市故事，设定新颖（去除AI痕迹版）",
            "prompt_content": """【都市脑洞写作指南】

脑洞要新，别撞车。
- 上网搜一下，如果满大街都是，换一个
- 小众比大众有记忆点

设定要自洽，别前后矛盾。
- 脑洞再大，内部逻辑要通
- 读者可以接受任何设定，但不能接受随便变

别花大篇幅设定，边写边交代。
- 开篇别甩世界观设定集
- 设定服务于故事，不是故事服务于设定

转折要意外，但要合理。
- 意想不到但回头想是伏笔
- 别为反转而反转，那叫烂尾

都市感要有。别写着写着变成玄幻。
- 街道、店铺、手机、WiFi，这些元素要有
- 脑洞是点缀，都市才是底色""",
            "order_index": 21
        },
        {
            "user_id": None,
            "name": "新媒体都市风 V2",
            "style_type": "preset",
            "preset_id": "newmedia_urban_v2",
            "description": "新媒体风格，标题党，适合公众号、头条号（去除AI痕迹版）",
            "prompt_content": """【新媒体都市写作指南】

标题要吸睛，但别骗。
- 夸张可以，欺骗不行
- 数字、疑问、冲突，这些元素管用

开头3秒抓住读者。别慢慢进入主题。
- 第一句话就要有冲突或悬念
- 别写"今天我来给大家讲一个故事"

节奏要密。别有注水段落。
- 每段都要有信息量
- 能一句话说完别写一段

情绪要浓。读者要的是情绪体验。
- 愤怒、感动、爽快，选一个拉满
- 别中庸，要么极好要么极坏

结尾要有钩子。
- 要么留悬念，要么给感慨
- 让读者有转发、评论的冲动""",
            "order_index": 22
        },
    ]

    op.bulk_insert(writing_styles_table, writing_styles_data)
    print(f"✅ 已插入 {len(writing_styles_data)} 条全局写作风格预设")


def downgrade() -> None:
    """删除预置数据"""
    
    # 删除写作风格预设（只删除全局预设）
    op.execute("DELETE FROM writing_styles WHERE user_id IS NULL")
    print("✅ 已删除全局写作风格预设")
    
    # 删除关系类型
    op.execute("DELETE FROM relationship_types")
    print("✅ 已删除关系类型数据")
