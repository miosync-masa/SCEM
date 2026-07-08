#!/usr/bin/env python3
"""
gender_grid_metrics.py — 性別拡張グリッドの主要指標(docs/paper2_gender_grid_spec.md §5-6)。

計測:
  - GFR(Gender Flip Rate): 同一共同体内で operational resolved mode が性別で割れた
    (community × event) 対の率。per-observer / operational(多数決+priority)の両方。
  - observer-robust flips: 両観測者が単独でも同じ対を同じ向き(F/Mのmode組が一致)で割った件数。
  - 事前固定基準(データ収集前に宣言・spec §6):
      P1(集中): median GFR(gender-charged) > median GFR(gender-peripheral) — 両国。
      P2(非製造): peripheral 全対プールで flip ≤ 25%。
  - 共同体内 性別指紋距離(cmr_compare_{c}_1985_gender_grid.json があれば)。

Run: python3 gender_grid_metrics.py --country us
"""
from __future__ import annotations
import argparse
import json
import collections
import math
import statistics
from pathlib import Path

import cmr_matrix as CM

DATA = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent / "data"
MODE_PRIORITY = ["ACTIVE", "REFRAME", "PASSIVE"]

# 事前固定の事象クラス(spec §6 — 収集前に宣言済み)
PREFIXED = {
    "us": {"charged": ["us_dobbs_2022", "us_obergefell_2015"],
           "peripheral": ["us_lehman_2008", "us_student_debt_2012", "us_housing_surge_2021"]},
    "uk": {"charged": ["uk_same_sex_marriage_2014", "uk_section28_repeal_2003"],
           "peripheral": ["uk_financial_crisis_2008", "uk_tuition_fees_2010", "uk_cost_of_living_2022"]},
}


def resolve(modes):
    if not modes:
        return None
    cnt = collections.Counter(modes)
    return sorted(cnt, key=lambda m: (-cnt[m], MODE_PRIORITY.index(m)))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="us")
    args = ap.parse_args()
    c = args.country

    interps = [json.loads(l) for l in
               (DATA / f"interpretations_{c}_gender_grid.jsonl").read_text(encoding="utf-8").splitlines()
               if l.strip()]
    # cell[(eid, premise)][model] = mode / emph[(eid, base_premise)][model][gender] = tags
    cell: dict = collections.defaultdict(dict)
    emph: dict = collections.defaultdict(lambda: collections.defaultdict(dict))
    for it in interps:
        cell[(it["event_id"], it["premise"])][it["source_model"]] = it["expected_mode"]
        base, g = it["premise"].rsplit("_", 1)
        emph[(it["event_id"], base)][it["source_model"]][g] = set(it.get("effect_emphasis") or [])

    comms = CM.COMMUNITIES_GRID[c]
    events = CM.EVENTS_GRID[c]
    models = sorted({it["source_model"] for it in interps})

    def pair_modes(eid, base_premise, how):
        """(F mode, M mode)。how=モデル名 or 'operational'。"""
        out = []
        for g in ("_female", "_male"):
            m = cell[(eid, base_premise + g)]
            out.append(m.get(how) if how != "operational" else resolve(list(m.values())))
        return tuple(out)

    # ── GFR ──
    rows = []          # (event_label, eid, flips_operational, flip_pairs)
    per_model_flips = {m: 0 for m in models}
    robust = 0
    total_pairs = 0
    flips_by_event = {}
    for label, eid in events:
        flips = 0
        flip_pairs = []
        for name, premise in comms:
            total_pairs += 1
            f, m_ = pair_modes(eid, premise, "operational")
            if f != m_:
                flips += 1
                flip_pairs.append((name, f, m_))
            per_obs = [pair_modes(eid, premise, m) for m in models]
            for i, m in enumerate(models):
                if per_obs[i][0] != per_obs[i][1]:
                    per_model_flips[m] += 1
            # robust: 両観測者が単独で flip し、(F,M) の組も一致
            if all(p[0] != p[1] for p in per_obs) and len(set(per_obs)) == 1:
                robust += 1
        flips_by_event[eid] = flips
        rows.append((label, eid, flips, flip_pairs))

    # ── Gendered Emphasis Distance(V1 の2本目・spec §5 拡張)──
    #   同一共同体内の F/M effect_emphasis 集合の (1 - Jaccard)。観測者・共同体で平均。
    def jac(a, b):
        return len(a & b) / len(a | b) if (a | b) else 1.0
    emph_by_event: dict = {}
    for label, eid in events:
        vals = []
        for _, premise in comms:
            for model in models:
                gs = emph[(eid, premise)].get(model, {})
                if "female" in gs and "male" in gs:
                    vals.append(1 - jac(gs["female"], gs["male"]))
        emph_by_event[eid] = sum(vals) / len(vals) if vals else 0.0

    n_comm = len(comms)
    print("=" * 84)
    print(f"  Gender-extended grid metrics — {c.upper()}  ({n_comm} communities × {len(events)} events)")
    print("=" * 84)
    print(f"\n  {'Event':<22}{'GFR(op)':>10}{'emphΔ':>7}   flipped communities (F→M)")
    for label, eid, flips, fps in rows:
        mark = " ⚡" if flips else ""
        detail = ", ".join(f"{n}({f[:3]}/{m[:3]})" for n, f, m in fps[:4])
        if len(fps) > 4:
            detail += f" +{len(fps)-4}"
        print(f"  {label:<22}{flips}/{n_comm} ={flips/n_comm:>5.0%}{emph_by_event[eid]:>7.2f}   {detail}{mark}")

    op_gfr = sum(f for _, _, f, _ in rows) / total_pairs
    print(f"\n  GFR overall (operational)     = {sum(f for _,_,f,_ in rows)}/{total_pairs} = {op_gfr:.0%}")
    for m in models:
        print(f"  GFR per-observer [{m:<8}]    = {per_model_flips[m]}/{total_pairs} = {per_model_flips[m]/total_pairs:.0%}")
    print(f"  observer-robust flips (同対同向) = {robust}/{total_pairs} = {robust/total_pairs:.0%}")

    # ── 事前固定基準 ──
    pf = PREFIXED[c]
    g_charged = [flips_by_event[e] / n_comm for e in pf["charged"]]
    g_periph = [flips_by_event[e] / n_comm for e in pf["peripheral"]]
    p1 = statistics.median(g_charged) > statistics.median(g_periph)
    pool_periph = sum(flips_by_event[e] for e in pf["peripheral"]) / (len(pf["peripheral"]) * n_comm)
    p2 = pool_periph <= 0.25
    print(f"\n  Pre-fixed criteria (declared before collection):")
    print(f"    P1 concentration : median charged {statistics.median(g_charged):.0%} "
          f"vs peripheral {statistics.median(g_periph):.0%}  → {'satisfied' if p1 else 'NOT satisfied'}")
    print(f"    P2 non-manufacture: peripheral pooled {pool_periph:.0%} (≤25%)  → "
          f"{'satisfied' if p2 else 'NOT satisfied'}")

    # ── 共同体内 性別指紋距離(cmr_compare 出力があれば) ──
    cj = DATA / f"cmr_compare_{c}_1985_gender_grid.json"
    if cj.exists():
        d = json.loads(cj.read_text(encoding="utf-8"))
        profs = d["profiles"]
        print(f"\n  Gender-CDI (all {len(profs)} gendered fingerprints) = {d['cdi']:.3f}")
        print(f"  Within-community gender fingerprint distance (birth 1985):")
        for name, _ in comms:
            fF = profs.get(f"{name} F", {}).get("fingerprint")
            fM = profs.get(f"{name} M", {}).get("fingerprint")
            if fF and fM:
                dist = math.dist((fF["P"], fF["A"], fF["R"]), (fM["P"], fM["A"], fM["R"]))
                print(f"    {name:<20} {dist:.3f}")

    out = {
        "country": c, "cells_pairs": total_pairs,
        "gfr_operational": round(op_gfr, 4),
        "gfr_per_observer": {m: round(per_model_flips[m] / total_pairs, 4) for m in models},
        "robust_flips": robust,
        "gfr_by_event": {e: round(f / n_comm, 4) for e, f in flips_by_event.items()},
        "emphasis_distance_by_event": {e: round(v, 4) for e, v in emph_by_event.items()},
        "prefixed": {"P1_satisfied": p1, "P2_satisfied": p2,
                     "charged_median": statistics.median(g_charged),
                     "peripheral_median": statistics.median(g_periph),
                     "peripheral_pooled": round(pool_periph, 4)},
    }
    (DATA / f"gender_grid_metrics_{c}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] gender_grid_metrics_{c}.json")


if __name__ == "__main__":
    main()
