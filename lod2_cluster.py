#!/usr/bin/env python3
"""
lod2_cluster.py — LOD 2(戦略分岐)を複数生成して cos クラスタリング
                  (community_experiment.py の手法と接続)

LOD_ARCHITECTURE.md §2.1 の LOD2 例
  「技術で攻める / 人脈で攻める / 大企業で守る / 公務員で守る」
を、固定 LOD0(1981年生まれ)× LOD1(攻める=Fight / 守る=Flight)の上で複数生成し、
ペルソナを埋め込みベクトル化して、community_experiment.py の cos / greedy_clusters で
「LOD2 戦略空間がどう構造化されるか」を観る。

問い: LOD2 の戦略空間は Fight(攻める)/ Flight(守る)で割れるか?
      = 上位 LOD(LOD1 応答方向)が下位 LOD(LOD2 戦略)を組織化するか?
      (community_experiment が「閉鎖度=離散の組織化軸」を見たのと同型の問い)

位置づけ: マーケティング応用の LOD1〜2 事例(§2.3)。統計的実証ではなく機構の出力例示。

Run: arch -arm64 python3.12 lod2_cluster.py   (OpenAI 利用)
"""
from __future__ import annotations
import sys
import json
import itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import lod_persona as LP
import community_experiment as CE   # cos / greedy_clusters / embed を再利用(LOD1〜2 と接続)

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache" / "lod2_cluster_cache.json"
BIRTH = 1981

# (応答方向, 戦略) — §2.1 の4戦略 + 各陣営1つずつ補強 = 6点(攻める3 / 守る3)
STRATEGIES = [
    ("Fight", "技術で攻める"),
    ("Fight", "人脈で攻める"),
    ("Fight", "独立・フリーランスで攻める"),
    ("Flight", "大企業で守る"),
    ("Flight", "公務員で守る"),
    ("Flight", "資格で守る"),
]


def persona_text(p: dict) -> str:
    """埋め込み対象: 解釈の中身(summary / narrative / provenance)。"""
    return json.dumps({k: p.get(k) for k in ("summary", "narrative", "provenance")},
                      ensure_ascii=False)


def main():
    cache = json.load(open(CACHE, encoding="utf-8")) if CACHE.exists() else {"personas": {}, "embeds": {}}
    personas, embeds = cache["personas"], cache["embeds"]
    labels = [(f"{o}:{s}", o) for o, s in STRATEGIES]

    # ── LOD2 ペルソナ生成(LOD0=1981 固定、cumulative で安定化) ──
    for (orient, strat), (key, _) in zip(STRATEGIES, labels):
        if key in personas:
            print(f"[cache] {key}")
            continue
        print(f"[gen]   {key}")
        c = LP.LODConstraints(birth_year=BIRTH, lod1_response=orient, lod2_strategy=strat)
        r = LP.solve(c, max_retries=4, cumulative=True)
        if r["status"] != "SAT":
            print(f"  [skip] UNSAT: {r.get('reason')}")
            continue
        personas[key] = r["persona"]

    # ── 埋め込み ──
    for key in list(personas):
        if key not in embeds:
            embeds[key] = CE.embed(persona_text(personas[key]))
            print(f"[embed] {key}")
    CACHE.parent.mkdir(exist_ok=True)
    json.dump({"personas": personas, "embeds": embeds}, open(CACHE, "w", encoding="utf-8"),
              ensure_ascii=False)

    keys = [k for k, _ in labels if k in embeds]
    orient_of = dict(labels)
    vecs = {k: embeds[k] for k in keys}

    def short(k):
        return k.split(":")[1]

    # ── cos 類似度行列 ──
    print("\n" + "=" * 74)
    print("  LOD2 戦略ペルソナ間 cos 類似度(全て LOD0=1981 を共有)")
    print("=" * 74)
    print("            " + "".join(f"{short(k)[:5]:>7}" for k in keys))
    for a in keys:
        print(f"  {short(a)[:9]:<11}" + "".join(f"{CE.cos(vecs[a], vecs[b]):>7.3f}" for b in keys))

    # ── クラスタ(cos 閾値別) ──
    print("\n" + "=" * 74)
    print("  クラスタ構造(cos 閾値別)")
    print("=" * 74)
    veclist = [vecs[k] for k in keys]
    for th in (0.86, 0.90, 0.93):
        cl = CE.greedy_clusters(keys, veclist, th)
        print(f"  th{th}: {len(cl)}塊  " + " | ".join("{" + ",".join(short(s) for s in g) + "}" for g in cl))

    # ── Fight/Flight 組織化の検定(同陣営 vs 異陣営の平均 cos) ──
    same, cross = [], []
    for a, b in itertools.combinations(keys, 2):
        v = CE.cos(vecs[a], vecs[b])
        (same if orient_of[a] == orient_of[b] else cross).append(v)
    mean = lambda L: sum(L) / len(L) if L else 0.0
    print("\n" + "=" * 74)
    print("  Fight(攻める)/ Flight(守る) は LOD2 戦略空間を組織化するか")
    print("=" * 74)
    print(f"  同陣営(攻める同士 / 守る同士)平均 cos = {mean(same):.3f}")
    print(f"  異陣営(攻める × 守る)        平均 cos = {mean(cross):.3f}")
    print(f"  差 = {mean(same) - mean(cross):+.3f}  → 正なら LOD1(Fight/Flight)が LOD2 を組織化")


if __name__ == "__main__":
    main()
