"""
culture_interactive.py — 対話型Culture軸ペルソナ生成

フリーテキスト＋4軸(音楽/スポーツ/文学/映画)の選択式＋LLM追加質問の3層入力。
ユーザーが答えるたびにLLMが深掘り質問し、解像度が上がっていく。

使い方:
    python culture_interactive.py 1981
    python culture_interactive.py 2005

前提:
    pip install openai python-dotenv
    .env に OPENAI_API_KEY=sk-... を置く
    同フォルダに media_generation_v4.py, media_generation_v5.py,
    event_loader.py, events_patched.jsonl を配置
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

# ───────────────────────────────────────────────
# 4軸 pickリスト（世代によって選択肢を変える余地あり）
# ───────────────────────────────────────────────
CULTURE_AXES = {
    "music": {
        "label": "音楽",
        "prompt": "思春期〜20代で一番聴いてた音楽は？(複数OK、自由記述も可)",
        "picks": [
            "ビジュアル系 (X JAPAN, LUNA SEA, GLAY, ラルク...)",
            "HIPHOP/R&B (Zeebra, RHYMESTER, 宇多田, MISIA...)",
            "横乗りPUNK/ミクスチャー (Hi-STANDARD, Dragon Ash, 山嵐...)",
            "オリコンJ-POP (小室, ミスチル, スピッツ, 安室, 浜崎...)",
            "渋谷系/サブカル (小沢健二, Cornelius, くるり, ナンバガ...)",
            "ゲーム音楽/アニソン/ボカロ系",
            "洋楽ロック (Nirvana, Oasis, Green Day, Linkin Park...)",
            "クラブ/テクノ/トランス/ハウス",
            "レゲエ/スカ/ダブ",
            "その他(自由記述)",
        ],
    },
    "sport": {
        "label": "スポーツ",
        "prompt": "学生時代の部活・応援してたスポーツは？",
        "picks": [
            "サッカー部/Jリーグ世代",
            "野球部/甲子園・プロ野球",
            "バスケ部 (スラムダンク世代)",
            "テニス部",
            "水泳/陸上/個人競技系",
            "格闘技 (K-1, PRIDE, 格ゲー含む)",
            "スケボー/スノボ/サーフィン (横乗り系)",
            "帰宅部/インドア/ゲーム",
            "その他(自由記述)",
        ],
    },
    "literature": {
        "label": "文学・読書",
        "prompt": "読書スタイルに近いのは？",
        "picks": [
            "話題作は買う (1Q84は積んだ)",
            "漫画中心 (ジャンプ/マガジン/アフタヌーン...)",
            "ラノベ/SF/ファンタジー",
            "純文学・文芸 (村上春樹, 吉本ばなな, よしもとばなな...)",
            "ビジネス書・自己啓発",
            "思想・哲学・学術寄り",
            "ほぼ読まない(映像/音楽派)",
            "その他(自由記述)",
        ],
    },
    "film": {
        "label": "映画・映像",
        "prompt": "映画の観方に近いのは？",
        "picks": [
            "ヒット作は映画館で (タイタニック, マトリックス...)",
            "レンタルで掘る (TSUTAYA通い)",
            "ミニシアター/単館系",
            "アニメ映画中心 (ジブリ, エヴァ, 攻殻...)",
            "洋画アクション/SF中心",
            "邦画ドラマ/恋愛映画",
            "配信で観る派 (Netflix以降)",
            "あまり観ない",
            "その他(自由記述)",
        ],
    },
}


def collect_preferences(birth_year: int = None, events: list = None) -> dict:
    """CLI対話で4軸の嗜好を収集。世代別pickリストがあればそちらを優先"""
    from generate_picks import get_or_generate_picks

    # 世代別pickリストを取得(キャッシュ or 生成)
    axes_data = CULTURE_AXES  # フォールバック
    if birth_year and events:
        try:
            picks_data = get_or_generate_picks(birth_year, events)
            if "axes" in picks_data:
                # キャッシュの形式をCULTURE_AXESと同じ形に合わせる
                axes_data = picks_data["axes"]
                ctx = picks_data.get("generation_context", "")
                if ctx:
                    print(f"  📋 {ctx}")
        except Exception as e:
            print(f"  [pickリスト取得スキップ: {e}、デフォルトリストを使用]")

    print("\n" + "=" * 56)
    print("  Culture軸ヒアリング — あなたの文化的嗜好を教えてください")
    print("=" * 56)
    print("  番号で選択(複数はカンマ区切り)、自由記述もOK\n")

    prefs = {}
    for key in ["music", "sport", "literature", "film"]:
        axis = axes_data.get(key)
        if not axis:
            continue
        label = axis.get("label", key)
        prompt = axis.get("prompt", "")
        picks = axis.get("picks", [])

        print(f"\n📌 {label}: {prompt}")
        for i, pick in enumerate(picks, 1):
            print(f"    {i}. {pick}")
        print(f"    0. スキップ")

        ans = input(f"\n  → {label}: ").strip()
        if ans == "0" or ans == "":
            prefs[key] = None
            continue

        # 番号 or 自由記述を解析
        parts = [a.strip() for a in ans.replace("、", ",").split(",")]
        selected = []
        freetext = []
        for p in parts:
            try:
                idx = int(p)
                if 1 <= idx <= len(picks):
                    selected.append(picks[idx - 1])
                else:
                    freetext.append(p)
            except ValueError:
                freetext.append(p)

        result = ", ".join(selected + freetext)
        prefs[key] = result
        print(f"  ✓ {result}")

    # 自由記述の追加ヒント
    print(f"\n📌 追加で伝えたいこと (ファッション/ゲーム/趣味/価値観など、なんでも)")
    extra = input("  → (なければEnter): ").strip()
    prefs["freetext"] = extra if extra else None

    return prefs


def format_preferences(prefs: dict) -> str:
    """嗜好をLLM用テキストに整形"""
    lines = []
    axis_map = {"music": "音楽", "sport": "スポーツ", "literature": "文学・読書", "film": "映画・映像"}
    for key, label in axis_map.items():
        val = prefs.get(key)
        if val:
            lines.append(f"- {label}: {val}")
    ft = prefs.get("freetext")
    if ft:
        lines.append(f"- その他: {ft}")
    return "\n".join(lines) if lines else "(嗜好入力なし)"


# ───────────────────────────────────────────────
# 対話型ペルソナ生成: LLMが追加質問して解像度を上げる
# ───────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは「年齢同期型メディア世代論」に基づくマーケティングペルソナ分析ツールです。

このツールは2層で動きます:
1. 構造層(Python計算): 社会事象が何歳の認知段階に着弾したか → 3軸世代指紋(PASSIVE/ACTIVE/REFRAME)
2. 文化層(あなたの担当): 音楽/スポーツ/文学/映画の4軸嗜好 → 同世代内の文化サブクラスタを位置づけ

あなたの仕事:
- 構造プロファイル(3軸)と文化嗜好(4軸)を受け取る
- この組み合わせから、この人の消費・価値観・自己提示・人間関係のパターンを推定する
- もし情報が足りなければ、1-2個の追加質問をする(質問は具体的に)
- 最終的にペルソナを出力する

重要な原則:
- 世代を一枚岩で語らない。同じ1981でも音楽×スポーツの組み合わせで全く別の消費者になる
- 構造プロファイルの着弾事象に紐付けて説明する(後付けの物語ではなく、何歳で何が着弾したからこうなった、という接続)
- 「Z世代は〜」「ミレニアルは〜」的な生年一括り表現は使わない

出力形式:
追加質問が必要な場合:
{"mode": "question", "questions": ["質問1", "質問2"]}

ペルソナ出力の場合(JSONのみ、コードフェンス不要):
{
  "mode": "persona",
  "segment_name": "このセグメントの名前(キャッチーかつ構造に根差したもの)",
  "one_liner": "この人を一言で言うと",
  "structural_root": "3軸のどの着弾がこの人の基盤を作ったか",
  "culture_position": {
    "music": "音楽嗜好がどの文化系統に位置するか＋その意味",
    "sport": "スポーツ嗜好が示す身体性・仲間関係の傾向",
    "literature": "読書スタイルが示す知的消費の傾向",
    "film": "映画の観方が示す文化消費の傾向"
  },
  "consumption_pattern": "この人の消費行動パターン(何に金を使い、何に使わないか)",
  "self_presentation": "この人の自己提示スタイル(SNS/対面/仕事)",
  "relationship_style": "この人の人間関係の傾向(広く浅く/狭く深く/場による使い分け)",
  "media_touchpoint": "この人に届くメディア・チャネル・メッセージ",
  "blindspot": "この人に見えにくい/響きにくいもの(マーケ的な盲点)",
  "cross_generation_note": "隣接世代の同じ嗜好の人との違い"
}
"""


def call_llm(client: OpenAI, messages: list) -> dict:
    """フォールバック付きLLM呼び出し"""
    base = {"model": MODEL, "messages": messages}
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
        return {"mode": "error", "raw": "API呼び出し失敗"}
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"mode": "error", "raw": raw}


def run_interactive(birth_year: int, events: list):
    structure = build_structure_summary(birth_year, events)
    prefs = collect_preferences(birth_year, events)
    pref_text = format_preferences(prefs)

    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"## 構造プロファイル ({birth_year}年生まれ)\n"
            f"{json.dumps(structure, ensure_ascii=False, indent=2)}\n\n"
            f"## 文化的嗜好(4軸)\n{pref_text}\n\n"
            f"上記を分析し、追加質問が必要なら質問を、十分ならペルソナを出力してください。"
        )},
    ]

    print("\n\n🔄 分析中...\n")

    # 対話ループ(最大3往復)
    for turn in range(4):
        result = call_llm(client, messages)

        if result.get("mode") == "question":
            qs = result.get("questions", [])
            print("💬 もう少し教えてください：\n")
            answers = []
            for i, q in enumerate(qs, 1):
                print(f"  Q{i}: {q}")
                a = input(f"  → A{i}: ").strip()
                answers.append(f"Q: {q}\nA: {a}")
            # 回答をメッセージに追加してもう1回
            messages.append({"role": "assistant", "content": json.dumps(result, ensure_ascii=False)})
            messages.append({"role": "user", "content": "\n".join(answers)})
            print("\n🔄 深掘り分析中...\n")
            continue

        if result.get("mode") == "persona":
            print_persona(result, birth_year)
            return result

        if result.get("mode") == "error":
            print(f"[error] {result.get('raw', '不明')[:300]}")
            return result

        # modeが不明な場合もペルソナとして扱ってみる
        print_persona(result, birth_year)
        return result

    print("[timeout] 対話回数上限。最後の出力を表示します。")
    print_persona(result, birth_year)
    return result


def print_persona(p: dict, birth_year: int):
    print("=" * 62)
    print(f"  {birth_year}年生まれ ペルソナ: {p.get('segment_name', '?')}")
    print("=" * 62)
    print(f"\n  💡 {p.get('one_liner', '')}\n")

    sr = p.get("structural_root")
    if sr:
        print(f"【構造的基盤】\n  {sr}\n")

    cp = p.get("culture_position", {})
    if cp:
        print("【文化座標(4軸)】")
        for axis, desc in cp.items():
            icon = {"music": "🎵", "sport": "⚽", "literature": "📚", "film": "🎬"}.get(axis, "•")
            label = {"music": "音楽", "sport": "スポーツ", "literature": "文学", "film": "映画"}.get(axis, axis)
            print(f"  {icon} {label}: {desc}")
        print()

    for key, label in [
        ("consumption_pattern", "💰 消費パターン"),
        ("self_presentation", "🪞 自己提示スタイル"),
        ("relationship_style", "🤝 人間関係の傾向"),
        ("media_touchpoint", "📡 有効なタッチポイント"),
        ("blindspot", "🚫 盲点(この人に届きにくいもの)"),
        ("cross_generation_note", "🔄 隣接世代との差"),
    ]:
        val = p.get(key)
        if val:
            print(f"【{label}】\n  {val}\n")

    print()


if __name__ == "__main__":
    birth = int(sys.argv[1]) if len(sys.argv) > 1 else 1981
    events = v5.load_events()
    print(f"[info] {len(events)}件・{birth}年生まれ・モデル={MODEL}")
    result = run_interactive(birth, events)

    out_file = f"persona_{birth}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[saved] {out_file}")
