#!/usr/bin/env python3
"""
cmr_compare.py — Same Birth Year, Different Community(Paper 2 §「同年生まれ・別Community」)

固定の出生年(既定1985)で、複数 Community について Contextual Mode Resolver により
各事象の mode を解決 → 解決済 v4.Event を既存 Paper 1 エンジンに投入し、
Community ごとの:
  1. resolved cohort fingerprint(PASSIVE/ACTIVE/REFRAME)
  2. Mode Flip(base集約 mode と resolved mode が変わった事象)
  3. top interference nodes
  4. top reframe fires
  5. CMR flip ログ(resolved/base/該当interp数/rationale 実LLM文)
を出し、Community 間の Contextual Divergence Index(指紋距離)を計算する。

Community は cmr_matrix.COMMUNITIES の premise トークンパターンで対応づける(近似)。
LLM 呼び出しなし・捏造なし。Paper 1 エンジン(v4/v5)・events_patched.jsonl は無改変(import のみ)。

Run: python3 cmr_compare.py --country us --birth_year 1985
"""
from __future__ import annotations
import argparse
import json
import collections
import math
from pathlib import Path

import sys
sys.path.insert(0, str(next(_p for _p in Path(__file__).resolve().parents if _p.name == "src") / "core"))
import media_generation_v4 as v4
import media_generation_v5 as v5          # v4.mode_weight を個別peak版にパッチ
import cmr_matrix as CM

DATA = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent / "data"
MODE_PRIORITY = ["ACTIVE", "REFRAME", "PASSIVE"]
US_DOMAIN_MAP = {
    "politics_institution": "POLITICS", "international_geopolitics": "GEOPOLITICS",
    "media_technology": "MEDIA", "finance_assets": "FINANCE", "prices": "PRICE",
    "education_system": "EDUCATION", "disaster_crisis": "DISASTER",
    "economy_employment": "ECONOMY", "public_health": "HEALTH",
    "platform": "PLATFORM", "lifestyle_culture": "LIFESTYLE",
}


def _resolve(modes):
    """expected_mode のリスト → 多数決 + priority。空なら None。"""
    if not modes:
        return None
    cnt = collections.Counter(modes)
    return sorted(cnt, key=lambda m: (-cnt[m], MODE_PRIORITY.index(m) if m in MODE_PRIORITY else 9))[0]


def load(country, variant="v1"):
    tag = country if variant == "v1" else f"{country}_{variant}"
    merged = [json.loads(l) for l in (DATA / f"events_{tag}_merged.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]
    interps = [json.loads(l) for l in (DATA / f"interpretations_{tag}.jsonl")
               .read_text(encoding="utf-8").splitlines() if l.strip()]
    by_name = collections.defaultdict(list)
    by_eid = collections.defaultdict(list)
    for it in interps:
        by_name[it["event_name"]].append(it)
        if it.get("event_id"):
            by_eid[it["event_id"]].append(it)
    return merged, by_name, by_eid


def make_event(o, mode):
    try:
        dom = v4.Domain[US_DOMAIN_MAP.get(o.get("domain"), "POLITICS")]
    except KeyError:
        dom = v4.Domain.POLITICS
    ev = v4.Event(
        name=o["name"], year=int(o.get("effective_year") or o.get("year")),
        domain=dom, mode=v4.Mode[mode], agency=float(o.get("agency") or 0.3),
        description="", reframe_group=o.get("reframe_group"),
        # US/UK の reference_value は Paper1 の通貨/価格 log-ratio 前提と非互換(0・負値あり)。
        # 渡すと reference_distance が math domain error。REFRAME 差分は年ベース fallback を使う。
        reference_value=None, salience=float(o.get("salience") or 1.0),
        effect_vector=dict(o.get("base_effect_vector") or {}),
    )
    ev._peak_age = o.get("sensitivity_peak_age")   # type: ignore[attr-defined]
    ev._spread = o.get("sensitivity_spread")        # type: ignore[attr-defined]
    return ev


def community_profile(birth_year, merged, by_name, by_eid, spec, grid_mode=False):
    """1 Community の解決済 LOD0 + CMR ログ。
    v1: spec=トークンパターン(premise_matches)。grid: spec=正準premise文字列(完全一致, event_idで照合)。"""
    def interps_of(o):
        return by_eid.get(o["event_id"], []) if grid_mode else by_name.get(o["name"], [])

    def is_match(premise):
        return (premise == spec) if grid_mode else CM.premise_matches(premise, spec)

    events, cmrlog = [], []
    for o in merged:
        all_modes = [i["expected_mode"] for i in interps_of(o) if i.get("premise")]
        # base_mode_majority = 全premise解釈の最頻mode。
        # (注: US/UK merged は単一の base_mode_event を持たない=possible_modes のみ。
        #  ゆえに flip 判定の基準は base_mode_majority に固定する。)
        base_majority = _resolve(all_modes)
        matched = [i for i in interps_of(o) if i.get("premise") and is_match(i["premise"])]
        comm_modes = [i["expected_mode"] for i in matched]
        resolved = _resolve(comm_modes) or "PASSIVE"   # 該当無→ambient PASSIVE
        events.append(make_event(o, resolved))
        if matched and base_majority and resolved != base_majority:
            cmrlog.append({
                "event": o["name"], "base_mode_majority": base_majority, "resolved_mode": resolved,
                "n_matched": len(matched),
                "rationale": (matched[0].get("rationale") or "")[:80],
                "source_model": matched[0].get("source_model"),
            })
    hits, interf, fires, _ = v4.analyze(birth_year, events)
    dP = v5.mode_density(hits, v4.Mode.PASSIVE)
    dA = v5.mode_density(hits, v4.Mode.ACTIVE)
    dR = v5.mode_density(hits, v4.Mode.REFRAME)
    # MFR: base集約modeを持つ全事象のうち、resolvedがbaseと変わった割合
    flips = sum(1 for e in cmrlog)
    have_base = sum(1 for o in merged if _resolve([i["expected_mode"] for i in interps_of(o) if i.get("premise")]))
    return {
        "fingerprint": {"P": dP["mean"], "A": dA["mean"], "R": dR["mean"]},
        "interference": [f"{it['pair'][0]} × {it['pair'][1]}" for it in interf[:3]],
        "reframe": [f"{r['group']}" for r in fires[:3]],
        "mfr": flips / have_base if have_base else 0.0,
        "cmrlog": cmrlog,
    }


def cdi(profiles):
    """Contextual Divergence Index = Community 指紋間の平均ユークリッド距離(3軸)。"""
    fps = [(p["fingerprint"]["P"], p["fingerprint"]["A"], p["fingerprint"]["R"]) for p in profiles.values()]
    d, n = 0.0, 0
    for i in range(len(fps)):
        for j in range(i + 1, len(fps)):
            d += math.dist(fps[i], fps[j]); n += 1
    return d / n if n else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="us")
    ap.add_argument("--birth_year", type=int, default=1985)
    ap.add_argument("--variant", default="v1", help="v1 | grid")
    args = ap.parse_args()
    c, by = args.country, args.birth_year
    grid_mode = args.variant != "v1"
    merged, by_name, by_eid = load(c, args.variant)
    comms = CM.COMMUNITIES_GRID[c] if grid_mode else CM.COMMUNITIES[c]

    profiles = {}
    for name, spec in comms:
        profiles[name] = community_profile(by, merged, by_name, by_eid, spec, grid_mode)

    print("=" * 92)
    print(f"  Same Birth Year, Different Community — {c.upper()} {by}年生まれ"
          + ("  [grid]" if grid_mode else ""))
    print("=" * 92)
    print(f"\n  {'Community':<20}{'PASSIVE':>9}{'ACTIVE':>9}{'REFRAME':>9}{'MFR':>7}   支配")
    for name, p in profiles.items():
        f = p["fingerprint"]
        dom = max([("PAS", f["P"]), ("ACT", f["A"]), ("REF", f["R"])], key=lambda x: x[1])[0]
        print(f"  {name:<20}{f['P']:>9.2f}{f['A']:>9.2f}{f['R']:>9.2f}{p['mfr']:>7.0%}   {dom}")
    print(f"\n  Contextual Divergence Index(指紋間平均距離)= {cdi(profiles):.3f}")

    for name, p in profiles.items():
        print(f"\n── {name} " + "─" * (74 - len(name)))
        print(f"   干渉 top3 : " + " | ".join(p["interference"][:3]))
        print(f"   REFRAME  : " + " | ".join(p["reframe"][:3]))
        print(f"   Mode Flip(base→resolved, {len(p['cmrlog'])}件)の例:")
        for e in p["cmrlog"][:4]:
            print(f"     {e['event'][:40]:42} {e['base_mode_majority']}→{e['resolved_mode']} "
                  f"[{e['source_model']}] {e['rationale'][:40]}")

    # JSON 保存(Paper 2 素材)
    suffix = f"{c}_{by}" if not grid_mode else f"{c}_{by}_grid"
    out = DATA / f"cmr_compare_{suffix}.json"
    out.write_text(json.dumps({"country": c, "birth_year": by, "cdi": cdi(profiles),
                               "profiles": profiles}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] {out.name}")


if __name__ == "__main__":
    main()
