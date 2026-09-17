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

def gen(name, prompt, size="2048x2048", n=1, dest=None):
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "size": size,
        "response_format": "url", "n": n, "watermark": False,
    }).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e
    saved = []
    for i, item in enumerate(d.get("data", [])):
        url = item["url"]
        tag = time.strftime("%H%M%S")
        fp = OUT / dest if dest and n == 1 else OUT / f"{name}_{tag}_{i}.jpeg"
        urllib.request.urlretrieve(url, fp)
        saved.append(str(fp))
        print(f"  saved: {fp}")
    return saved

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="逗号分隔主题名，如 portrait-dufu,dongting")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--size", default=None, help="如 2048x2048；默认按主题：地图 2560x1440，其余 2048x2048")
    a = ap.parse_args()
    if not KEY:
        sys.exit("VOLCANO_API_KEY not set。请复制 .env.example 为 .env 并填入火山引擎方舟 API Key")
    if a.only:
        names = [s.strip() for s in a.only.split(',') if s.strip()]
        unknown = [n for n in names if n not in PROMPTS]
        if unknown:
            sys.exit(f"unknown --only {unknown!r}, choose from: {', '.join(PROMPTS)}")
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
    for name, p in targets.items():
        size = a.size or SIZES.get(name, "2048x2048")
        dest = CANON.get(name) if a.n == 1 else None
        print(f"[{name}] generating n={a.n} size={size} ...")
        try:
            gen(name, p, size=size, n=a.n, dest=dest)
        except Exception as e:
            print(f"  FAILED: {e}")
