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
}

SIZES = {
    "main": "2048x2048",
    "main2": "2048x2048",
    "portrait": "2048x2048",
    "map": "2560x1440",
}

def gen(name, prompt, size="2048x2048", n=1):
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "size": size,
        "response_format": "url", "n": n,
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
        fp = OUT / f"{name}_{tag}_{i}.jpeg"
        urllib.request.urlretrieve(url, fp)
        saved.append(str(fp))
        print(f"  saved: {fp}")
    return saved

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="main|main2|portrait|map")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--size", default=None, help="如 2048x2048；默认按主题：地图 2560x1440，其余 2048x2048")
    a = ap.parse_args()
    if not KEY:
        sys.exit("VOLCANO_API_KEY not set。请复制 .env.example 为 .env 并填入火山引擎方舟 API Key")
    if a.only and a.only not in PROMPTS:
        sys.exit(f"unknown --only {a.only!r}, choose from: {', '.join(PROMPTS)}")
    targets = {a.only: PROMPTS[a.only]} if a.only else PROMPTS
    for name, p in targets.items():
        size = a.size or SIZES.get(name, "2048x2048")
        print(f"[{name}] generating n={a.n} size={size} ...")
        try:
            gen(name, p, size=size, n=a.n)
        except Exception as e:
            print(f"  FAILED: {e}")
