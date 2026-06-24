"""
community_experiment.py — Community最小実装の「判断材料」実験(Paper 1には触らない)

2つの駆動パラメータが、ペルソナ空間にどんな構造を生むかを実測する:

  軸A 情報伝播速度 (Python側): effective_year に地域オフセット [速0 / 中+1 / 遅+2年]
       → 伝播で広がる事象(diffusion/media/infrastructure/lifestyle系)だけずらす。
         日付固定事象(災害shock/法institution/価格price等)はずらさない。
       → 同じ事象が違う年齢に着弾し、感受性カーブ上の重みが変わる(既存エンジンそのまま)。

  軸B 閉鎖特性 (LLM側): generate_picks/persona に「閉鎖度」を渡し選択肢空間の広さを変える
       [開放 / 中 / 閉鎖] → 閉鎖だと都市サブカル(横乗り・渋谷系・洋楽)が選択肢から消え、
         地元の定番が残る。

固定条件: 1981年生まれ / 嗜好= 横乗り×洋楽ロック

手順:
  1. 3(速)×3(閉鎖)=9セルで構造プロファイル(offset適用)+ LLMペルソナ生成
  2. 9ペルソナを embedding でベクトル化
  3. cos類似度行列 → クラスタリング
  4. 収束(3-4塊) / グラデーション / 砂(無秩序) を判定
     → 精密化(連続パラメータで足りる)か 細分化(離散カテゴリ追加)か の判断材料

Run:
  python3 community_experiment.py            # キャッシュ優先
  python3 community_experiment.py --force    # 生成しなおし
"""
from __future__ import annotations
import os
import sys
import json
import math
import itertools

from dotenv import load_dotenv
from openai import OpenAI

import event_loader as L
import media_generation_v5 as v5
from culture_axis import build_structure_summary

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
EMBED_MODEL = "text-embedding-3-small"
CACHE = "community_experiment_cache.json"

client = OpenAI()

# 情報伝播で「広がる」事象型だけにオフセットを当てる(日付固定事象は除外)
PROPAGATION_TYPES = {
    "diffusion", "media", "infrastructure", "lifestyle", "creator_economy",
    "mobility", "home_infrastructure", "work_infrastructure",
    "health_lifestyle", "health_infrastructure", "social_norm",
}

SPEEDS = [("速", 0), ("中", 1), ("遅", 2)]          # effective_year += offset(年)
CLOSURES = ["開放", "中", "閉鎖"]
BIRTH = 1981
PREFERENCE = "横乗り系(スケート/スノボ文化・PUNK/ミクスチャー)× 洋楽ロック"


# ── 軸A: offset適用でイベントを読み込む(events_patched.jsonlは編集しない) ──
def load_events_with_offset(offset: int):
    out = []
    for line in open("events_patched.jsonl", encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue
        obj = json.loads(line)
        et = obj.get("effective_year_type")
        if offset and et in PROPAGATION_TYPES and isinstance(obj.get("effective_year"), (int, float)):
            obj["effective_year"] = obj["effective_year"] + offset
        le = L.parse_event(obj)
        if le:
            out.append(v5.to_v4_event(le))
    return out


CLOSURE_DESC = {
    "開放": "都市的で選択肢が広い。横乗り・渋谷系・洋楽ロック等の都市サブカルにフルアクセスでき、実際にシーンへ参加できる。",
    "中": "都市サブカルに一部アクセスできるが、地元志向や入手制約も混じる。一部は雑誌・通販・少数の同好で実践する。",
    "閉鎖": "閉鎖的共同体。都市サブカル(横乗り・渋谷系・洋楽の現場)は選択肢から実質的に消え、地元の定番(オリコンHIT・地元の人間関係・地縁の娯楽)が残る。嗜好はあっても入手・実践が強く制約される。",
}

SYSTEM = """あなたは「年齢同期型メディア世代論」の文化×共同体分析担当です。
構造層(Pythonが計算した着弾プロファイル)と、対象者の固定嗜好、そして居住共同体の閉鎖度を受け取り、
その人物が実際にどんな文化的自己になったかのペルソナを生成します。
重要: 同じ嗜好・同じ生年でも、情報伝播の速さ(事象が何歳で着弾したか)と共同体の閉鎖度で、
実際に実践できた文化と自己提示は変わります。閉鎖度が高いほど都市サブカルは選択肢から脱落し、地元定番が残ります。
出力は必ず以下のJSONのみ(コードフェンス無し):
{
  "identity_label": "この人物の文化的自己を一言で(構造的に)",
  "actual_music": ["実際に聴いた音楽系統を固有名詞込みで3-5個"],
  "actual_board_or_sport": ["横乗り嗜好が実際どう実践/断念されたか2-4個"],
  "values_self_presentation": "価値観と自己提示の傾向(2-3文)",
  "community_relation": "地元共同体との関係・距離の取り方(2-3文)",
  "preference_realization": "横乗り×洋楽ロック嗜好が、この伝播速度と閉鎖度の下でどう実現/変形/断念されたか(2-3文)"
}"""


def gen_persona(speed_label, offset, closure):
    events = load_events_with_offset(offset)
    structure = build_structure_summary(BIRTH, events)
    user = (
        f"## 対象者\n生年: {BIRTH} / 固定嗜好: {PREFERENCE}\n\n"
        f"## 情報伝播速度\n{speed_label}(伝播事象の着弾を +{offset}年ずらした構造)\n\n"
        f"## 共同体の閉鎖度\n{closure}: {CLOSURE_DESC[closure]}\n\n"
        f"## 構造プロファイル(offset適用済)\n{json.dumps(structure, ensure_ascii=False)}"
    )
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    base = {"model": MODEL, "messages": msgs}
    for kw in ({**base, "response_format": {"type": "json_object"}}, dict(base)):
        try:
            r = client.chat.completions.create(**kw)
            raw = r.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                raw = raw[4:] if raw.startswith("json") else raw
                raw = raw.strip().rstrip("`").strip()
            return json.loads(raw)
        except Exception as e:
            last = e
            continue
    return {"_error": str(last)}


def embed(text: str):
    r = client.embeddings.create(model=EMBED_MODEL, input=text)
    return r.data[0].embedding


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def pearson(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = math.sqrt(sum((x - mx) ** 2 for x in xs)); vy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (vx * vy) if vx and vy else 0.0


def greedy_clusters(labels, vecs, thresh):
    """cos >= thresh を同一クラスタにまとめる単純な凝集(判断材料用)。"""
    n = len(labels); parent = list(range(n))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if cos(vecs[i], vecs[j]) >= thresh:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(labels[i])
    return list(groups.values())


def main():
    force = "--force" in sys.argv
    cells = []  # (speed_idx, closure_idx, speed_label, offset, closure)
    for si, (sl, off) in enumerate(SPEEDS):
        for ci, cl in enumerate(CLOSURES):
            cells.append((si, ci, sl, off, cl))

    cache = {}
    if os.path.exists(CACHE) and not force:
        cache = json.load(open(CACHE, encoding="utf-8"))

    personas = {}
    for si, ci, sl, off, cl in cells:
        key = f"{sl}_{cl}"
        if key in cache.get("personas", {}):
            personas[key] = cache["personas"][key]
            print(f"[cache] {key}")
        else:
            print(f"[gen]   {key} (speed={sl}+{off}, closure={cl}) model={MODEL}")
            personas[key] = gen_persona(sl, off, cl)

    # embedding
    embeds = (cache.get("embeds") or {})
    for key, p in personas.items():
        if key in embeds:
            continue
        if p.get("_error"):
            print(f"[skip embed] {key}: {p['_error']}")
            continue
        embeds[key] = embed(json.dumps(p, ensure_ascii=False))
        print(f"[embed] {key}")

    json.dump({"personas": personas, "embeds": embeds},
              open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

    keys = [f"{sl}_{cl}" for si, ci, sl, off, cl in cells if f"{sl}_{cl}" in embeds]
    idx = {f"{sl}_{cl}": (si, ci) for si, ci, sl, off, cl in cells}
    vecs = [embeds[k] for k in keys]

    # ── cos類似度行列 ──
    print("\n" + "=" * 70)
    print("  ペルソナ間 cos類似度行列(9セル)")
    print("=" * 70)
    print("        " + "".join(f"{k:>9}" for k in keys))
    for i, k in enumerate(keys):
        row = "".join(f"{cos(vecs[i], vecs[j]):>9.3f}" for j in range(len(keys)))
        print(f"  {k:<6}{row}")

    # ── グラデーション度: パラメータ距離 vs (1-cos) の相関 ──
    pd, cd = [], []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = idx[keys[i]], idx[keys[j]]
            pdist = abs(a[0] - b[0]) + abs(a[1] - b[1])   # (速,閉鎖)グリッドのManhattan距離
            pd.append(pdist); cd.append(1 - cos(vecs[i], vecs[j]))
    r = pearson(pd, cd)

    # ── クラスタリング(複数閾値) ──
    print("\n" + "=" * 70)
    print("  クラスタ構造(cos閾値別の凝集)")
    print("=" * 70)
    for th in (0.80, 0.85, 0.90, 0.93):
        cl = greedy_clusters(keys, vecs, th)
        print(f"  閾値{th}: {len(cl)}塊  " + " | ".join("{" + ",".join(g) + "}" for g in cl))

    sims = [cos(vecs[i], vecs[j]) for i in range(len(keys)) for j in range(i + 1, len(keys))]
    print("\n" + "=" * 70)
    print("  判定材料")
    print("=" * 70)
    print(f"  ペア類似度: min={min(sims):.3f} max={max(sims):.3f} mean={sum(sims)/len(sims):.3f} 幅={max(sims)-min(sims):.3f}")
    print(f"  グラデーション相関 r(パラメータ距離, 1-cos) = {r:+.3f}")
    print("    r>0.5      → グラデーション(連続的に効く=精密化向き)")
    print("    クラスタ収束 → 3-4塊で安定(離散タイプが実在=細分化向き)")
    print("    幅小&r≈0   → 砂(無秩序=パラメータが構造を生まない)")


if __name__ == "__main__":
    main()
