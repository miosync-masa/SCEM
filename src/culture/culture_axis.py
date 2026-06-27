"""
culture_axis.py — 構造(3軸プロファイル) × 文化(嗜好系統) の2層化

役割分担:
  Python(media_generation_v5) = 構造層: 何歳で何が着弾したか → 世代指紋(3軸)
  OpenAI(このモジュール)        = 文化層: 同じ指紋の中で、どの嗜好クラスタに分岐したか

ご主人さまの観察(80-85世代は音楽だけで4軸に割れる: ビジュアル系/HIPHOP・R&B/
横乗りPUNK・ミクスチャー/オリコンHIT)を一般化し、
「同じ着弾を受けた人が、どの文化系統に流れたかで人格の尾の引き方が変わる」を出力する。

前提:
  pip install openai python-dotenv
  .env に OPENAI_API_KEY=sk-... を置く
  ローカル実行: python culture_axis.py 1981
"""
from __future__ import annotations
import os
import sys
import json

from dotenv import load_dotenv
from openai import OpenAI

import pathlib as _pl
sys.path.insert(0, str(next(_p for _p in _pl.Path(__file__).resolve().parents if _p.name == "src") / "core"))
import media_generation_v5 as v5
import media_generation_v4 as v4

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


# ───────────────────────────────────────────────
# 構造層: v5の3軸プロファイルをLLM入力用に要約
# ───────────────────────────────────────────────
def build_structure_summary(birth_year: int, events: list) -> dict:
    hits, interferences, reframe_fires, _ = v4.analyze(birth_year, events)

    def top_by_mode(mode, n=6):
        ms = sorted((h for h in hits if h["ev"].mode is mode), key=lambda h: -h["weight"])[:n]
        return [{"name": h["ev"].name, "age": h["age"], "stage": h["stage"],
                 "weight": h["weight"], "domain": h["ev"].domain.value} for h in ms]

    fp = v5.cohort_fingerprint(birth_year, events)
    return {
        "birth_year": birth_year,
        "fingerprint": {
            "PASSIVE": {"mean": fp["P"]["mean"], "count": fp["P"]["count"]},
            "ACTIVE": {"mean": fp["A"]["mean"], "count": fp["A"]["count"]},
            "REFRAME": {"mean": fp["R"]["mean"], "count": fp["R"]["count"]},
        },
        "passive_top": top_by_mode(v4.Mode.PASSIVE),
        "active_top": top_by_mode(v4.Mode.ACTIVE),
        "reframe_fires": [{"group": r["group"], "fire": r["fire"]} for r in reframe_fires[:5]],
        "interference_top": [
            {"pair": list(it["pair"]), "stage": it["stage"], "cross_domain": it["cross_domain"]}
            for it in interferences[:5]
        ],
        "formative_events": [
            {"name": h["ev"].name, "age": h["age"], "domain": h["ev"].domain.value}
            for h in sorted((h for h in hits if h["stage"] == "人格形成期"),
                            key=lambda h: -h["weight"])[:6]
        ],
    }


# ───────────────────────────────────────────────
# 文化層: OpenAIに「同世代内の文化サブクラスタ」を出させる
# ───────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは「年齢同期型メディア世代論」の文化分析担当です。

このモデルは、世代を出生年ではなく「社会事象が何歳の認知段階に、どの作用モード
(PASSIVE=刷り込み / ACTIVE=意思決定 / REFRAME=基準値書き換え)で着弾したか」で分析します。

あなたの役割は構造層(Pythonが計算した3軸プロファイル)を受け取り、その上に【文化層】を載せることです。

重要な前提:
同じ世代・同じ事象着弾を受けても、人は単一の文化に流れるわけではありません。
例えば1980-85年生まれは、思春期の音楽嗜好だけでも複数の系統に分岐しました:
ビジュアル系 / HIPHOP・R&B / 横乗り系PUNK・ミクスチャー / オリコンHIT系。
そして、どの系統に流れたかが、その後の価値観・消費・自己提示・人間関係のパターンを
長く規定します(「尾を引く」)。

したがってあなたの仕事は、世代を一枚岩で語ることではなく、
「この構造プロファイルを持つ世代の内部に、どのような文化サブクラスタが分岐しうるか」
を複数提示し、各クラスタが構造(着弾事象)とどう接続しているかを説明することです。

出力は必ず以下のJSON形式のみ(前後の説明やmarkdownのコードフェンスは一切付けない):
{
  "generation_label": "この世代の構造ベースの呼称(キャッチーでなく構造的に)",
  "structural_summary": "3軸構成比から見たこの世代の質感(2-3文)",
  "culture_clusters": [
    {
      "name": "文化サブクラスタ名",
      "music_axis": "代表的な音楽系統",
      "structural_root": "どの着弾事象/作用モードがこのクラスタの素地になったか",
      "long_tail": "この嗜好が後年まで引きずる価値観・消費・自己提示の傾向",
      "estimated_share": "同世代内の概算シェア(主観でよい, 例:中規模)"
    }
  ],
  "cross_generation_note": "この世代の文化分岐が、隣接世代と何が違うか"
}
"""


def build_user_prompt(structure: dict, preference_hint: str | None) -> str:
    lines = [
        "以下は構造層(Python計算)の世代プロファイルです。これに文化層を載せてください。",
        "",
        "## 構造プロファイル",
        json.dumps(structure, ensure_ascii=False, indent=2),
    ]
    if preference_hint:
        lines += [
            "",
            "## 対象者の文化的嗜好性ヒント(あれば優先的に位置づける)",
            preference_hint,
            "",
            "上記の嗜好性が、提示する culture_clusters のどれに該当するかを明示してください。",
        ]
    return "\n".join(lines)


def analyze_culture(birth_year: int, events: list, preference_hint: str | None = None) -> dict:
    structure = build_structure_summary(birth_year, events)
    client = OpenAI()  # APIキーは環境変数 OPENAI_API_KEY から自動取得

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(structure, preference_hint)},
    ]

    # モデルによって対応パラメータが違う(gpt-5.5系はtemperature=1固定、等)。
    # まず理想形で投げ、弾かれたらパラメータを段階的に外して再試行する。
    base_kwargs = {"model": MODEL, "messages": messages}
    attempts = [
        {**base_kwargs, "temperature": 0.7, "response_format": {"type": "json_object"}},
        {**base_kwargs, "response_format": {"type": "json_object"}},  # temperature外す
        {**base_kwargs},  # response_formatも外す(最終手段)
    ]

    last_err = None
    raw = None
    for kw in attempts:
        try:
            resp = client.chat.completions.create(**kw)
            raw = resp.choices[0].message.content
            break
        except Exception as e:  # BadRequest等はここで吸収して次のattemptへ
            last_err = e
            continue

    if raw is None:
        return {"_parse_error": True, "raw": f"全attempt失敗: {last_err}"}

    # response_formatを外した場合、markdownコードフェンスが付くことがあるので剥がす
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip().rstrip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw": raw}


def pretty_print(result: dict):
    if result.get("_parse_error"):
        print("[JSON parse失敗] 生出力:")
        print(result["raw"])
        return
    print("=" * 68)
    print(f"  世代呼称: {result.get('generation_label', '?')}")
    print("=" * 68)
    print(f"\n{result.get('structural_summary', '')}\n")
    print("【文化サブクラスタ】")
    for c in result.get("culture_clusters", []):
        print(f"\n  ◆ {c.get('name')} ({c.get('estimated_share', '?')})")
        print(f"     音楽系統: {c.get('music_axis')}")
        print(f"     構造的素地: {c.get('structural_root')}")
        print(f"     尾の引き方: {c.get('long_tail')}")
    note = result.get("cross_generation_note")
    if note:
        print(f"\n【隣接世代との差】\n  {note}")
    print()


if __name__ == "__main__":
    birth = int(sys.argv[1]) if len(sys.argv) > 1 else 1981
    # 第2引数に嗜好ヒントを渡せる(任意): python culture_axis.py 1981 "ビジュアル系とミクスチャーが好き"
    hint = sys.argv[2] if len(sys.argv) > 2 else None

    events = v5.load_events()
    print(f"[info] {len(events)}件・{birth}年生まれ・モデル={MODEL}\n")
    result = analyze_culture(birth, events, hint)
    pretty_print(result)

    # 構造層だけ確認したいとき用に保存
    with open(f"culture_result_{birth}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[saved] culture_result_{birth}.json")
