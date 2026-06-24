"""
generate_picks.py — 世代別Culture軸pickリストの自動生成＋キャッシュ

構造プロファイル(3軸)を見せて「この世代の人格形成期に着弾した文化選択肢」を
LLMに生成させる。JSONで保存し、2回目以降はキャッシュから読む。

使い方:
    # 生成(APIを叩く)
    python generate_picks.py 1981
    python generate_picks.py 2005
    
    # 一括生成(1970-2010, 5年刻み)
    python generate_picks.py --batch

    → picks_1981.json, picks_2005.json 等が生成される
    → culture_interactive.py がこれを自動で読みに行く

前提:
    pip install openai python-dotenv
    .env に OPENAI_API_KEY=sk-...
"""
from __future__ import annotations
import os
import sys
import json

from dotenv import load_dotenv
from openai import OpenAI

import media_generation_v5 as v5
import media_generation_v4 as v4
from culture_axis import build_structure_summary

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

from pathlib import Path as _Path
PICKS_DIR = str(_Path(__file__).resolve().parent.parent / "cache" / "picks_cache")

SYSTEM_PROMPT = """あなたは「年齢同期型メディア世代論」の文化選択肢を設計する担当です。

与えられた構造プロファイル(生年、3軸指紋、人格形成期の着弾事象)から、
その世代の人が思春期〜20代に実際に選択肢として持っていた文化的嗜好を、
4軸(音楽/スポーツ/文学・読書/映画・映像)の選択肢リストとして生成してください。

重要な原則:
- その世代が実際に触れた文化だけを出す(未来の文化や前世代の文化を混ぜない)
- 各選択肢に代表的な固有名詞(アーティスト名、作品名、選手名等)を2-4個付ける
- サブカル〜マス、ニッチ〜メジャーまで幅を出す(偏らない)
- 選択肢は各軸6-10個程度
- 「その他(自由記述)」を必ず末尾に含める

出力はJSONのみ(コードフェンス不要):
{
  "birth_year": 1981,
  "generation_context": "この世代のpickリストを作った背景(1-2文)",
  "axes": {
    "music": {
      "label": "音楽",
      "prompt": "思春期〜20代で一番聴いてた音楽は？(複数OK)",
      "picks": [
        "選択肢1 (固有名詞, 固有名詞...)",
        "選択肢2 (固有名詞, 固有名詞...)",
        "その他(自由記述)"
      ]
    },
    "sport": { ... },
    "literature": { ... },
    "film": { ... }
  }
}
"""


def generate_picks(birth_year: int, events: list) -> dict:
    structure = build_structure_summary(birth_year, events)
    client = OpenAI()

    user_prompt = (
        f"以下は{birth_year}年生まれの構造プロファイルです。\n"
        f"この世代用の4軸pickリストを生成してください。\n\n"
        f"## 構造プロファイル\n"
        f"{json.dumps(structure, ensure_ascii=False, indent=2)}"
    )

    base = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    attempts = [
        {**base, "temperature": 0.7, "response_format": {"type": "json_object"}},
        {**base, "response_format": {"type": "json_object"}},
        {**base},
    ]

    raw = None
    for kw in attempts:
        try:
            resp = client.chat.completions.create(**kw)
            raw = resp.choices[0].message.content
            break
        except Exception:
            continue

    if raw is None:
        return {"error": "API呼び出し失敗"}

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip().rstrip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "JSON parse失敗", "raw": raw}


def cache_path(birth_year: int) -> str:
    os.makedirs(PICKS_DIR, exist_ok=True)
    return os.path.join(PICKS_DIR, f"picks_{birth_year}.json")


def save_picks(birth_year: int, data: dict):
    path = cache_path(birth_year)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [saved] {path}")


def load_picks(birth_year: int) -> dict | None:
    path = cache_path(birth_year)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def get_or_generate_picks(birth_year: int, events: list, force: bool = False) -> dict:
    """キャッシュがあれば読み、なければ生成して保存"""
    if not force:
        cached = load_picks(birth_year)
        if cached and "axes" in cached:
            print(f"  [cache hit] picks_{birth_year}.json")
            return cached

    print(f"  [generating] {birth_year}年生まれ用pickリスト (model={MODEL})...")
    result = generate_picks(birth_year, events)
    if "error" not in result:
        save_picks(birth_year, result)
    return result


def print_picks(data: dict):
    by = data.get("birth_year", "?")
    ctx = data.get("generation_context", "")
    print(f"\n{'='*56}")
    print(f"  {by}年生まれ用 Culture軸pickリスト")
    print(f"{'='*56}")
    if ctx:
        print(f"  {ctx}\n")

    axes = data.get("axes", {})
    for key in ["music", "sport", "literature", "film"]:
        axis = axes.get(key, {})
        label = axis.get("label", key)
        prompt = axis.get("prompt", "")
        picks = axis.get("picks", [])
        print(f"\n📌 {label}: {prompt}")
        for i, p in enumerate(picks, 1):
            print(f"    {i}. {p}")


if __name__ == "__main__":
    events = v5.load_events()

    if "--batch" in sys.argv:
        years = [1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010]
        force = "--force" in sys.argv
        print(f"[batch] {len(years)}世代のpickリストを生成")
        for y in years:
            result = get_or_generate_picks(y, events, force=force)
            if "error" in result:
                print(f"  [error] {y}: {result.get('error')}")
            else:
                print(f"  [ok] {y}: {len(result.get('axes', {}))}軸")
    else:
        birth = int(sys.argv[1]) if len(sys.argv) > 1 else 1981
        force = "--force" in sys.argv
        result = get_or_generate_picks(birth, events, force=force)
        if "error" in result:
            print(f"[error] {result}")
        else:
            print_picks(result)
