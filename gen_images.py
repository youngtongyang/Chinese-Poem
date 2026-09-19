#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedream 5.0-lite 出图脚本 — 古诗页插画 / 作者像 / 诗文地图底图
用法: python3 gen_images.py [--only main|main2|portrait|map] [--n 2]

需要环境变量 VOLCANO_API_KEY（火山引擎方舟 API Key）。
可复制 .env.example 为 .env 后：export $(cat .env | xargs)
"""
import os, sys, json, base64, time, argparse, urllib.request, urllib.error
from pathlib import Path

API = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-lite-260128"


def load_dotenv(path: Path):
    """极简 .env 加载：不引入第三方依赖。"""
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv(Path(__file__).parent / '.env')

KEY = os.environ.get("VOLCANO_API_KEY", "")
OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)

# ── 画风约束（所有 prompt 共用，确保风格统一）────────────────
STYLE = (
    "中国新国潮水墨插画风格，融合传统水墨晕染与现代商业插画精致感。"
    "整体色调低饱和度，仿古宣纸米黄色底，暖赭石色与淡墨青为主。"
    "画面叠加明显的古旧宣纸颗粒纹理质感，古朴典雅。"
    "写意水墨笔法，留白为主，意境悠远。"
    "中国古典绘画审美，无任何文字、无印章、无人物。"
)

PROMPTS = {
    # 主插画：庐山香炉峰 + 瀑布 + 紫烟
    "main": (
        "李白《望庐山瀑布》诗意场景。「日照香炉生紫烟，遥看瀑布挂前川。飞流直下三千尺，疑是银河落九天。」"
        "画面主体：庐山香炉峰高耸入云，山体巍峨险峻，一道巨大白色瀑布从千仞高峰直泻而下，"
        "水雾弥漫升腾。阳光自画面左上方照射山峰，山间升腾起淡淡紫色烟雾，"
        "紫烟与云雾交融弥漫于峰顶。远景群山连绵淡墨渲染，近景松树点缀。"
        "瀑布如白练垂挂，水势磅礴，下方深潭水雾弥漫。"
        + STYLE +
        "横幅构图 16:9，山峰与瀑布位于画面中部偏上，画面右侧留出天空留白区域，画面下部留出水面与雾气空间以便放置文字。"
    ),
    # 主插画备选：更写意、更留白
    "main2": (
        "中国水墨山水画，庐山瀑布意境。高耸的香炉峰，一道长长的白色瀑布从峰顶垂挂而下，"
        "如同银河坠落。山间紫烟缭绕，阳光穿云照射。远山淡墨，云雾弥漫，大面积极简留白。"
        + STYLE +
        "横幅构图 16:9，大量留白，构图简约空灵，画面左侧三分之二为山峰瀑布，右侧留白。"
    ),
    # 作者画像：李白
    "portrait": (
        "唐代诗人李白的中国画全身肖像。中年文人，头戴唐代幞头（软翅纱帽），"
        "身着白色宽袍大袖、腰束丝绦，手持折扇或酒盏，身姿飘逸洒脱，"
        "面庞清癯有神，长须微飘，目光望天，有仙风道骨之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅，以墨色与淡彩为主。"
        "低饱和度，仿古宣纸米黄底色，画面有宣纸颗粒纹理。"
        "全身像，无文字、无印章。"
    ),
    # 诗文地图底图：只出四周山水氛围，轮廓与标注由 map.html 叠加
    "map": (
        "古旧宣纸上的国风装饰长卷，不是现代地图。"
        "画面四周环绕写意远山、松树、云雾，四角有淡墨山水点缀，中央大面积浅青绿与暖米留白，"
        "便于后期叠放示意图形。不要出现国界、行政区、城市、道路、文字、印章、旗帜、人物。"
        + STYLE +
        "横幅构图 16:9，右侧约五分之一为云雾留白，左上角天空留白。"
    ),
    "portrait-liuyuxi": (
        "唐代诗人刘禹锡的中国画全身肖像。中年文人，头戴唐代幞头，身着青灰宽袍大袖，"
        "腰束丝绦，手持一卷诗笺，神情清峻沉稳，面容清癯，短须，目光坚定。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅，以墨色与淡青为主。"
        "低饱和度，仿古宣纸米黄底色，画面有宣纸颗粒纹理。全身像，无文字、无印章。"
    ),
    "portrait-dufu": (
        "唐代诗人杜甫的中国画全身肖像。中年文人，面容清瘦忧思，头戴软巾，"
        "身着深褐宽袍，腰束布带，双手负后或持竹杖，神情沉郁而宽厚，短须微白。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条苍劲，色彩淡雅，以墨色与赭石为主。"
        "低饱和度，仿古宣纸米黄底色，画面有宣纸颗粒纹理。全身像，无文字、无印章。"
    ),
    "portrait-menghaoran": (
        "唐代诗人孟浩然的中国画全身肖像。中年隐士文人，头戴幅巾，身着浅色宽袍，"
        "神情冲淡闲远，面容和煦，长须疏朗，手持竹杖或酒葫芦，有山林之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅，以墨色与浅青为主。"
        "低饱和度，仿古宣纸米黄底色，画面有宣纸颗粒纹理。全身像，无文字、无印章。"
    ),
    "dongting": (
        "刘禹锡《望洞庭》诗意场景。秋夜洞庭湖，湖面平静如未磨的铜镜，"
        "秋月与湖光相映。远处君山如一枚青螺浮于银色湖面。水色淡青，月色清冷，远山极简。"
        + STYLE +
        "横幅构图 16:9，湖面与君山位于画面中部偏左，右侧大面积留白以便放置文字。"
    ),
    "yueyang-lou": (
        "杜甫《登岳阳楼》诗意场景。岳阳楼临湖耸立，飞檐朱柱写意点染，楼下洞庭湖浩渺无际，"
        "水天相接，吴楚烟波。楼在画面左中，湖面开阔，远山淡墨。"
        + STYLE +
        "横幅构图 16:9，楼阁偏左，右侧与下部留出湖天空白以便放置文字。无人物。"
    ),
    "dongting-vast": (
        "孟浩然《望洞庭湖赠张丞相》诗意场景。八月洞庭湖水与岸齐平，水天涵混，"
        "湖上水汽蒸腾如云，波浪隐约拍向远岸城郭。气势开阔，不画人物。"
        + STYLE +
        "横幅构图 16:9，湖面铺满中景，右侧天空留白以便放置文字。"
    ),
    # 地图引线外侧地点卡片：方形小品，贴在标签旁
    "vignette-lushan": (
        "中国水墨小品插画，庐山香炉峰与瀑布。山峰高耸，一道白色瀑布自峰顶垂落，"
        "山腰有小亭，近景松树两株，远山淡墨。画面饱满、居中构图，四周略留宣纸边。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-dongting": (
        "中国水墨小品插画，洞庭湖畔岳阳楼。三层飞檐朱瓦楼阁临水而立，"
        "楼下湖面开阔，远处君山如青螺，近岸芦苇淡墨点染。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    # 地图陆块上的水墨点景：与 vignette 同一套出图风格，四周虚化以便叠在陆地上
    "map-land-west": (
        "中国水墨山水小品，西部高原远山连绵，近景两株苍松，云雾横陈。"
        "浅青绿与米黄宣纸底，四周边缘渐虚融入底色，不要实边、不要画框。"
        "不要楼阁、不要湖泊、不要瀑布、不要人物、不要文字、不要印章。"
        + STYLE +
        "正方形构图 1:1。"
    ),
    "map-land-north": (
        "中国水墨山水小品，北方远山淡墨层叠，山脚疏林，云气空濛。"
        "浅青绿与米黄宣纸底，四周边缘渐虚融入底色，不要实边、不要画框。"
        "不要楼阁、不要湖泊、不要瀑布、不要人物、不要文字、不要印章。"
        + STYLE +
        "正方形构图 1:1。"
    ),
    "map-land-south": (
        "中国水墨山水小品，江南丘陵与松树，远山一抹，云雾轻笼。"
        "浅青绿与米黄宣纸底，四周边缘渐虚融入底色，不要实边、不要画框。"
        "不要楼阁、不要湖泊、不要瀑布、不要人物、不要文字、不要印章。"
        + STYLE +
        "正方形构图 1:1。"
    ),

    # ── 二、三年级课文场景 ────────────────────────────────
    "deng-guanque-lou": (
        "王之涣《登鹳雀楼》诗意场景。黄河中游高楼临河，夕阳贴着西山落下，"
        "河水浩荡东去，远山一抹。楼阁飞檐写意点染，不画人物。"
        + STYLE +
        "横幅构图 16:9，楼与河在画面中部偏左，右侧天空与河面留白以便放置文字。"
    ),
    "ye-su-shan-si": (
        "李白《夜宿山寺》诗意场景。高山之巅一座危楼佛寺，夜空繁星低垂，"
        "楼高如可摘星。山势陡峭，云气在腰，月光清冷，殿檐淡墨。"
        + STYLE +
        "横幅构图 16:9，危楼偏左上，右侧大片夜空留白以便放置文字。无人物。"
    ),
    "chile-ge": (
        "北朝民歌《敕勒歌》诗意场景。阴山脚下敕勒川草原，天空如穹庐笼盖四野，"
        "天苍苍野茫茫，风吹草低，隐约可见牛羊背影于草浪中。不必画人脸与人体，"
        "只见辽阔草地、远山一脉、风过草伏。"
        + STYLE +
        "横幅构图 16:9，草原铺满中景，右侧天空留白以便放置文字。"
    ),
    "cun-ju": (
        "高鼎《村居》诗意场景。江南二月村落，草长莺飞，杨柳拂堤，春烟淡荡。"
        "村口纸鸢几只飘在天空，不画人物。柳丝、茅檐、小桥流水。"
        + STYLE +
        "横幅构图 16:9，村落与柳堤偏左，右侧春空留白以便放置文字。"
    ),
    "yong-liu": (
        "贺知章《咏柳》诗意场景。一树新柳如碧玉妆成，万条绿丝绦低垂，"
        "二月春风剪出细叶。岸边春水，远景淡烟。不画人物。"
        + STYLE +
        "横幅构图 16:9，柳树主体偏左，右侧春空留白以便放置文字。"
    ),
    "xiao-chu-jingci": (
        "杨万里《晓出净慈寺送林子方》诗意场景。六月西湖，接天莲叶无穷碧，"
        "映日荷花别样红。晓光、荷塘、远堤与保俶塔淡影。不画人物。"
        + STYLE +
        "横幅构图 16:9，荷叶荷花铺满中左，右侧湖光留白以便放置文字。"
    ),
    "jueju-huangli": (
        "杜甫《绝句》诗意场景。成都草堂春日：翠柳上黄鹂，青天上白鹭一行，"
        "窗含西岭千秋雪，门泊东吴万里船。草堂茅檐、江船、远雪山。"
        + STYLE +
        "横幅构图 16:9，草堂与江景偏左，右侧天空留白以便放置文字。无人物。"
    ),
    "shan-xing": (
        "杜牧《山行》诗意场景。寒山石径斜上，白云生处有疏落人家，"
        "晚秋枫林如火，霜叶红于二月花。小径、枫树、远山。不画人物。"
        + STYLE +
        "横幅构图 16:9，枫林山径偏左，右侧云山留白以便放置文字。"
    ),
    "zeng-liu-jingwen": (
        "苏轼《赠刘景文》诗意场景。初冬庭园：荷尽只剩枯梗，残菊犹有傲霜枝，"
        "橙黄橘绿累累。一年好景的清寒。不画人物。"
        + STYLE +
        "横幅构图 16:9，庭树枝实偏左，右侧留白以便放置文字。"
    ),
    "ye-shu-suo-jian": (
        "叶绍翁《夜书所见》诗意场景。秋夜江村，梧叶萧萧，江上秋风，"
        "篱落间一盏灯火微明，促织隐于草间。客舟夜泊的清冷。不画人物。"
        + STYLE +
        "横幅构图 16:9，篱落灯火偏左下，右侧夜空与江面留白以便放置文字。"
    ),
    "wang-tianmen-shan": (
        "李白《望天门山》诗意场景。长江东流，天门两山中断如劈开，"
        "碧水至此回旋，两岸青山相对，一片孤帆从日边驶来。气势开阔。"
        + STYLE +
        "横幅构图 16:9，两山夹江偏左，右侧江天留白以便放置文字。无人物。"
    ),
    "yin-hu-shang": (
        "苏轼《饮湖上初晴后雨》诗意场景。西湖晴雨各半：一侧水光潋滟，"
        "一侧山色空蒙。远山如西子淡妆，堤柳、湖面、烟雨。不画人物。"
        + STYLE +
        "横幅构图 16:9，湖山偏左，右侧烟雨留白以便放置文字。"
    ),
    "jueju-chiri": (
        "杜甫《绝句》迟日江山丽诗意场景。春日草堂：迟日江山明丽，花草芬芳，"
        "燕子贴水而飞，鸳鸯睡于暖沙。江岸、春花、远山。不画人物面容，"
        "燕子鸳鸯可点染。"
        + STYLE +
        "横幅构图 16:9，江岸春色偏左，右侧留白以便放置文字。"
    ),
    "huichong-chunjiang": (
        "苏轼《惠崇春江晚景》诗意场景。竹外桃花三两枝，春江水暖，"
        "鸭子浮于江面，蒌蒿满地芦芽短。惠崇小景的江南春江。不画人物。"
        + STYLE +
        "横幅构图 16:9，竹桃春江偏左，右侧江天留白以便放置文字。"
    ),
    "sanqu-daozhong": (
        "曾几《三衢道中》诗意场景。梅子黄时江南晴日，小溪行尽转入山径，"
        "绿阴浓密，黄鹂四五声于林间。衢州山道的清润。不画人物。"
        + STYLE +
        "横幅构图 16:9，溪山绿阴偏左，右侧留白以便放置文字。"
    ),
    "yuan-ri": (
        "王安石《元日》诗意场景。新年清晨庭院：爆竹余烟，屠苏酒盏置于案，"
        "千门万户桃符换新，曈曈朝日。朱红门楣与新桃符，不画人物。"
        + STYLE +
        "横幅构图 16:9，门庭桃符偏左，右侧晨光留白以便放置文字。"
    ),
    "qingming": (
        "杜牧《清明》诗意场景。清明时节雨纷纷，石板路湿，杏花村酒帘隐约，"
        "远处牧野与杏花。行人不必画清，只见雨丝、酒旗、花村。"
        + STYLE +
        "横幅构图 16:9，雨巷杏村偏左，右侧烟雨留白以便放置文字。"
    ),
    "chongyang": (
        "王维《九月九日忆山东兄弟》诗意场景。重阳登高，异乡山岗，"
        "茱萸插满秋枝，远山如眉，长安城郭淡影于烟霭。思念的空阔。不画人物。"
        + STYLE +
        "横幅构图 16:9，秋山茱萸偏左，右侧天空留白以便放置文字。"
    ),

    "portrait-wangzhihuan": (
        "唐代诗人王之涣的中国画全身肖像。盛唐边塞诗人，头戴幞头，"
        "身着赭青宽袍，气宇高朗，短须，目光远望如登楼看河。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-gaoding": (
        "清代诗人高鼎的中国画全身肖像。布衣文人，头戴幅巾，身着浅褐长袍，"
        "神情闲淡，微须，手持纸鸢线轴或折扇，有村居春日之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-hezhizhang": (
        "唐代诗人贺知章的中国画全身肖像。老年文人，号四明狂客，头戴幅巾，"
        "身着浅色宽袍，面容清癯和蔼，白须飘然，手持酒盏，疏狂而温。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-yangwanli": (
        "南宋诗人杨万里的中国画全身肖像。中年文人，号诚斋，头戴方巾，"
        "身着青灰宽袍，神情活泼明朗，微须，手持折扇，有诚斋活泼诗风。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-sushi": (
        "宋代文学家苏轼的中国画全身肖像。中年文人，头戴东坡巾，"
        "身着宽袍大袖，面庞丰润，长须，神情旷达幽默，手持卷册或藤杖。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅，以墨色与暖赭为主。"
        "低饱和度，仿古宣纸米黄底。全身像，无文字、无印章。"
    ),
    "portrait-yeshaoweng": (
        "南宋诗人叶绍翁的中国画全身肖像。文人隐逸，头戴幅巾，"
        "身着浅青长袍，神情清寂，微须，手持诗卷，有江湖夜雨之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-dumu": (
        "唐代诗人杜牧的中国画全身肖像。中年文人，字牧之，头戴幞头，"
        "身着红褐与青灰宽袍，俊朗清癯，短须，风神俊逸，手持折扇。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-zengji": (
        "南宋诗人曾几的中国画全身肖像。老年文人，号茶山，头戴幅巾，"
        "身着素袍，面容清癯慈和，白须，手持竹杖，有山林清气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-wanganshi": (
        "宋代政治家文学家王安石的中国画全身肖像。中年执政者风貌，"
        "头戴幞头，身着深色公服宽袍，面容清峻，短须，神情刚毅沉静。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条苍劲，色彩淡雅，以墨色与深青为主。"
        "低饱和度，仿古宣纸米黄底。全身像，无文字、无印章。"
    ),
    "portrait-wangwei": (
        "唐代诗人王维的中国画全身肖像。中年文人，字摩诘，头戴幅巾或软脚幞头，"
        "身着浅色宽袍，面容清癯冲淡，短须，手持卷轴，有诗佛山水之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅，以墨色与浅青为主。"
        "低饱和度，仿古宣纸米黄底。全身像，无文字、无印章。"
    ),

    "vignette-guanque": (
        "中国水墨小品插画，黄河边鹳雀楼。高楼飞檐临河，夕阳与远山，"
        "河水东去。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-yinshan": (
        "中国水墨小品插画，阴山敕勒川。远山一脉横陈，草原苍茫，"
        "风吹草低。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-xihu": (
        "中国水墨小品插画，杭州西湖。荷叶、堤柳、远山宝塔淡影，"
        "湖水平静。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-caotang": (
        "中国水墨小品插画，成都杜甫草堂。茅檐竹篱，溪桥，远雪山一抹，"
        "江岸泊船。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-tianmen": (
        "中国水墨小品插画，安徽天门山。两山夹江中断，一片孤帆，"
        "碧水回旋。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-quzhou": (
        "中国水墨小品插画，浙江衢州山道。梅黄时节，小溪、绿阴、山径。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-changan": (
        "中国水墨小品插画，唐长安城郭。远楼阙、秋山、茱萸枝，"
        "城阙淡墨。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-bianjing": (
        "中国水墨小品插画，北宋汴京新年。朱红门楣桃符，晨光，"
        "庭院余烟。画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-jiangnan": (
        "中国水墨小品插画，江南水乡。柳堤、小桥、杏花、烟雨村舍。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),

    # ── 一、二年级补入场景 ────────────────────────────────
    "yong-e": (
        "骆宾王《咏鹅》诗意场景。江南水塘，白鹅曲项向天，白毛浮于绿水，"
        "红掌拨清波。塘边芦苇淡墨，水色青绿。可画鹅，不画人物。"
        + STYLE +
        "横幅构图 16:9，水塘与鹅偏左，右侧水面留白以便放置文字。"
    ),
    "jiangnan-yuefu": (
        "汉乐府《江南》诗意场景。江南荷塘采莲时节，莲叶田田铺满水面，"
        "鱼在莲叶间东西南北游戏。水色碧绿，荷叶饱满。不画人物。"
        + STYLE +
        "横幅构图 16:9，荷塘偏左，右侧水面留白以便放置文字。"
    ),
    "hua": (
        "唐诗《画》诗意场景。一幅画中的山水：远山有色，溪水无声，"
        "春花不谢，枝上栖鸟安静。像真景又静得不像真的。不画人物。"
        + STYLE +
        "横幅构图 16:9，画中山水偏左，右侧留白以便放置文字。"
    ),
    "minnong-er": (
        "李绅《悯农》其二诗意场景。正午田垄，禾苗成行，锄头倚于田埂，"
        "汗滴落入土中的意象，烈日当空。劳作者只画极小背影或不画人脸。"
        + STYLE +
        "横幅构图 16:9，田垄偏左，右侧天空留白以便放置文字。"
    ),
    "gu-lang-yue-xing": (
        "李白《古朗月行》诗意场景。夜空一轮圆月如白玉盘，又如飞在青云端的镜子，"
        "云气淡荡，月光明洁。童心看月的清朗。不画人物。"
        + STYLE +
        "横幅构图 16:9，明月偏左上，右侧夜空留白以便放置文字。"
    ),
    "feng": (
        "李峤《风》诗意场景。风本身看不见：秋叶纷落，春花乍开，"
        "江上千尺浪，万竿竹尽斜。同一阵风的四季本事。不画人物。"
        + STYLE +
        "横幅构图 16:9，竹浪与落叶偏左，右侧天空留白以便放置文字。"
    ),
    "chun-xiao": (
        "孟浩然《春晓》诗意场景。襄阳春晨，窗外鸟鸣，夜来风雨过后花瓣散落，"
        "窗棂半开，庭院湿润。人仍在枕上，春天已到。不画人物面容。"
        + STYLE +
        "横幅构图 16:9，窗与落花偏左，右侧春空留白以便放置文字。"
    ),
    "zeng-wang-lun": (
        "李白《赠汪伦》诗意场景。安徽泾县桃花潭，客舟将行，碧水深潭，"
        "岸上桃花，踏歌的声息只以空岸与花影暗示。不画清晰人脸。"
        + STYLE +
        "横幅构图 16:9，潭与舟偏左，右侧江天留白以便放置文字。"
    ),
    "jing-ye-si": (
        "李白《静夜思》诗意场景。客舍床前洒满明月之光，地上如霜，"
        "窗外一轮明月，夜色清冷。思乡的静。不画人物。"
        + STYLE +
        "横幅构图 16:9，月光与窗偏左，右侧夜空留白以便放置文字。"
    ),
    "xun-yin-zhe-bu-yu": (
        "贾岛《寻隐者不遇》诗意场景。松下空山，云气深深，药篮或小径隐于雾中，"
        "隐者不见，只见山与云。不画人物。"
        + STYLE +
        "横幅构图 16:9，松山云气偏左，右侧留白以便放置文字。"
    ),
    "chi-shang": (
        "白居易《池上》诗意场景。池塘白莲，一艘小艇，浮萍被撑开一道水路，"
        "偷采的踪迹留在水面上。小娃只画背影或不画人脸。"
        + STYLE +
        "横幅构图 16:9，莲池与小艇偏左，右侧水面留白以便放置文字。"
    ),
    "xiao-chi": (
        "杨万里《小池》诗意场景。泉眼细流无声，树阴照水，"
        "小荷才露尖尖角，一只蜻蜓立在上头。晴柔的初夏。不画人物。"
        + STYLE +
        "横幅构图 16:9，小池荷角偏左，右侧留白以便放置文字。"
    ),
    "hua-ji": (
        "唐寅《画鸡》诗意场景。一只雪白大公鸡，头上红冠，立于门槛或庭院晨光中，"
        "千门万户将晓。可画鸡，不画人物。"
        + STYLE +
        "横幅构图 16:9，公鸡偏左，右侧晨光留白以便放置文字。"
    ),
    "mei-hua": (
        "王安石《梅花》诗意场景。墙角数枝梅凌寒独开，白雪似的花，"
        "暗香浮动。冬日庭院，冷而清。不画人物。"
        + STYLE +
        "横幅构图 16:9，墙角梅偏左，右侧雪空留白以便放置文字。"
    ),
    "xiao-er-chui-diao": (
        "胡令能《小儿垂钓》诗意场景。河边莓苔，青草映岸，一根钓竿斜出，"
        "蓬头稚子侧坐，只画背影，不画面容。水面微澜，怕惊了鱼。"
        + STYLE +
        "横幅构图 16:9，河岸垂钓偏左，右侧水面留白以便放置文字。"
    ),
    "jiang-xue": (
        "柳宗元《江雪》诗意场景。千山万径覆雪，鸟绝人踪，"
        "寒江上一叶孤舟，蓑笠翁极小，独钓。天地皆白，一点墨。"
        + STYLE +
        "横幅构图 16:9，寒江孤舟偏左，右侧雪空留白以便放置文字。"
    ),
    "fude-guyuan-cao": (
        "白居易《赋得古原草送别》诗意场景。古原上离离春草，野火烧过又生，"
        "春风吹拂新绿。旷野、草浪、远天。不画人物。"
        + STYLE +
        "横幅构图 16:9，原上草偏左，右侧天空留白以便放置文字。"
    ),
    "minnong-yi": (
        "李绅《悯农》其一诗意场景。春天播种的田与秋天金黄的穗，"
        "四海田垄无闲，却仍有空粮仓的意象。丰收与饥馑并置。不画人脸。"
        + STYLE +
        "横幅构图 16:9，田亩偏左，右侧天空留白以便放置文字。"
    ),
    "zhou-ye-shu-suo-jian": (
        "查慎行《舟夜书所见》诗意场景。月黑之夜，河上一盏渔灯如萤，"
        "微风簇起细浪，灯光碎成满河星。夜色深，光点散开。不画人物。"
        + STYLE +
        "横幅构图 16:9，渔灯与河偏左，右侧夜空留白以便放置文字。"
    ),

    "portrait-luobinwang": (
        "唐代诗人骆宾王的中国画全身肖像。初唐文人，头戴幞头，"
        "身着浅色宽袍，面容清俊，微须，神情英发，少年才气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-lishen": (
        "唐代诗人李绅的中国画全身肖像。中唐文人，头戴幞头，"
        "身着青灰宽袍，面容清癯，短须，神情忧悯而沉稳。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-liqiao": (
        "唐代诗人李峤的中国画全身肖像。初唐文人，头戴幞头，"
        "身着深青宽袍，面容端谨，短须，神情沉静如咏物。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-jiadao": (
        "唐代诗人贾岛的中国画全身肖像。中唐苦吟诗人，头戴幅巾，"
        "身着素袍，面容清瘦，微须，神情专注如推敲，有僧气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条苍劲，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-baijuyi": (
        "唐代诗人白居易的中国画全身肖像。中年文人，号香山居士，头戴幅巾，"
        "身着浅色宽袍，面容和煦丰润，短须，神情乐天，手持诗卷。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-tangyin": (
        "明代画家诗人唐寅的中国画全身肖像。吴中才子，头戴文士巾，"
        "身着浅色儒袍，面容清俊风流，微须，手持折扇，有唐伯虎才情。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-hulingneng": (
        "唐代诗人胡令能的中国画全身肖像。隐逸工匠文人，头戴幅巾，"
        "身着布袍，面容朴厚，微须，手可持钓竿或工具，有田园之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),
    "portrait-liuzongyuan": (
        "唐代文学家柳宗元的中国画全身肖像。中唐文人，字子厚，头戴幞头，"
        "身着深青宽袍，面容清峻，短须，神情孤冷而有骨。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条苍劲，色彩淡雅，以墨色与深青为主。"
        "低饱和度，仿古宣纸米黄底。全身像，无文字、无印章。"
    ),
    "portrait-zhashenxing": (
        "清代诗人查慎行的中国画全身肖像。清初文人，号初白，头戴幅巾，"
        "身着浅青长袍，面容清癯，白须疏朗，手持诗卷，有舟夜观灯之气。"
        "立姿全身像，居中构图，背景为纯色做旧宣纸底，无任何背景景物。"
        "中国工笔人物画风格，线条流畅，色彩淡雅。低饱和度，仿古宣纸米黄底。"
        "全身像，无文字、无印章。"
    ),

    "vignette-yiwu": (
        "中国水墨小品插画，浙东义乌水塘。白鹅、绿水、红掌，塘边芦苇。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-xiangyang": (
        "中国水墨小品插画，湖北襄阳春晓。汉水、城郭淡影、春花与啼鸟于枝。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-taohuatan": (
        "中国水墨小品插画，泾县桃花潭。深潭碧水，岸上桃花，一叶客舟。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-yongzhou": (
        "中国水墨小品插画，湖南永州江雪。寒江、孤舟、千山覆雪。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-jinling": (
        "中国水墨小品插画，金陵墙角梅花。数枝凌寒，暗香，雪意。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
    "vignette-putian": (
        "中国水墨小品插画，中原圃田河岸。莓苔、青草、钓竿斜出水面。"
        "画面饱满、居中构图。"
        + STYLE +
        "正方形构图 1:1，适合做地图标签旁的小插画。无文字、无印章、无人物、无边框。"
    ),
}

SIZES = {
    "main": "2048x2048",
    "main2": "2048x2048",
    "portrait": "2048x2048",
    "portrait-liuyuxi": "2048x2048",
    "portrait-dufu": "2048x2048",
    "portrait-menghaoran": "2048x2048",
    "dongting": "2048x2048",
    "yueyang-lou": "2048x2048",
    "dongting-vast": "2048x2048",
    "vignette-lushan": "2048x2048",
    "vignette-dongting": "2048x2048",
    "map-land-west": "2048x2048",
    "map-land-north": "2048x2048",
    "map-land-south": "2048x2048",
    "map": "2560x1440",
}

def is_good_jpeg(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 20000:
        return False
    data = path.read_bytes()
    return data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"


def gen(name, prompt, size="2048x2048", n=1, dest=None, retries=3):
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "size": size,
        "response_format": "url", "n": n, "watermark": False,
    }).encode()
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            last = RuntimeError(f"HTTP {e.code}: {detail}")
        except Exception as e:
            last = e
        time.sleep(2 * (attempt + 1))
    else:
        raise last
    saved = []
    for i, item in enumerate(d.get("data", [])):
        url = item["url"]
        tag = time.strftime("%H%M%S")
        fp = OUT / dest if dest and n == 1 else OUT / f"{name}_{tag}_{i}.jpeg"
        data = None
        dl_err = None
        for attempt in range(retries):
            try:
                req_img = urllib.request.Request(url)
                with urllib.request.urlopen(req_img, timeout=120) as img:
                    data = img.read()
                if len(data) < 20000 or data[:2] != b"\xff\xd8":
                    raise RuntimeError(f"bad jpeg {len(data)} bytes")
                break
            except Exception as e:
                dl_err = e
                data = None
                time.sleep(2 * (attempt + 1))
        if data is None:
            raise RuntimeError(f"download failed: {dl_err}") from dl_err
        fp.write_bytes(data)
        saved.append(str(fp))
        print(f"  saved: {fp} ({len(data)} bytes)", flush=True)
    return saved

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="逗号分隔主题名，或 grade23 / grade12")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--size", default=None, help="如 2048x2048；默认按主题：地图 2560x1440，其余 2048x2048")
    a = ap.parse_args()
    if not KEY:
        sys.exit("VOLCANO_API_KEY not set。请复制 .env.example 为 .env 并填入火山引擎方舟 API Key")
    GRADE23 = [
        "deng-guanque-lou", "ye-su-shan-si", "chile-ge", "cun-ju", "yong-liu",
        "xiao-chu-jingci", "jueju-huangli", "shan-xing", "zeng-liu-jingwen",
        "ye-shu-suo-jian", "wang-tianmen-shan", "yin-hu-shang", "jueju-chiri",
        "huichong-chunjiang", "sanqu-daozhong", "yuan-ri", "qingming", "chongyang",
        "portrait-wangzhihuan", "portrait-gaoding", "portrait-hezhizhang",
        "portrait-yangwanli", "portrait-sushi", "portrait-yeshaoweng",
        "portrait-dumu", "portrait-zengji", "portrait-wanganshi", "portrait-wangwei",
        "vignette-guanque", "vignette-yinshan", "vignette-xihu", "vignette-caotang",
        "vignette-tianmen", "vignette-quzhou", "vignette-changan",
        "vignette-bianjing", "vignette-jiangnan",
    ]
    GRADE12 = [
        "yong-e", "jiangnan-yuefu", "hua", "minnong-er", "gu-lang-yue-xing",
        "feng", "chun-xiao", "zeng-wang-lun", "jing-ye-si", "xun-yin-zhe-bu-yu",
        "chi-shang", "xiao-chi", "hua-ji", "mei-hua", "xiao-er-chui-diao",
        "jiang-xue", "fude-guyuan-cao", "minnong-yi", "zhou-ye-shu-suo-jian",
        "portrait-luobinwang", "portrait-lishen", "portrait-liqiao",
        "portrait-jiadao", "portrait-baijuyi", "portrait-tangyin",
        "portrait-hulingneng", "portrait-liuzongyuan", "portrait-zhashenxing",
        "vignette-yiwu", "vignette-xiangyang", "vignette-taohuatan",
        "vignette-yongzhou", "vignette-jinling", "vignette-putian",
    ]
    if a.only:
        if a.only.strip() == "grade23":
            names = list(GRADE23)
        elif a.only.strip() == "grade12":
            names = list(GRADE12)
        else:
            names = [s.strip() for s in a.only.split(',') if s.strip()]
        unknown = [n for n in names if n not in PROMPTS]
        if unknown:
            sys.exit(f"unknown --only {unknown!r}, choose from: {', '.join(PROMPTS)} or grade23/grade12")
        targets = {n: PROMPTS[n] for n in names}
    else:
        targets = {k: PROMPTS[k] for k in ("main", "main2", "portrait", "map")}
    CANON = {
        "portrait-liuyuxi": "portrait-liuyuxi.jpeg",
        "portrait-dufu": "portrait-dufu.jpeg",
        "portrait-menghaoran": "portrait-menghaoran.jpeg",
        "dongting": "dongting.jpeg",
        "yueyang-lou": "yueyang-lou.jpeg",
        "dongting-vast": "dongting-vast.jpeg",
        "vignette-lushan": "vignette-lushan.jpeg",
        "vignette-dongting": "vignette-dongting.jpeg",
        "map-land-west": "map-land-west.jpeg",
        "map-land-north": "map-land-north.jpeg",
        "map-land-south": "map-land-south.jpeg",
    }
    failed = []
    for name, p in targets.items():
        size = a.size or SIZES.get(name, "2048x2048")
        dest = (CANON.get(name) or (name + ".jpeg")) if a.n == 1 else None
        if dest and is_good_jpeg(OUT / dest):
            print(f"[{name}] skip existing {dest}", flush=True)
            continue
        if dest and (OUT / dest).exists():
            (OUT / dest).unlink()
            print(f"[{name}] drop incomplete {dest}", flush=True)
        print(f"[{name}] generating n={a.n} size={size} ...", flush=True)
        try:
            gen(name, p, size=size, n=a.n, dest=dest)
        except Exception as e:
            print(f"  FAILED: {e}", flush=True)
            failed.append(name)
        time.sleep(0.4)
    if failed:
        print("FAILED_LIST " + ",".join(failed), flush=True)
        sys.exit(1)
