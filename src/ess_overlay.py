#!/usr/bin/env python3
"""
ess_overlay.py — step4(探索的):UKグリッド事前 resolved_mode × ESS UK-only 割れ の予測対応。
GSS overlay の移植。ただし **UK-only=N薄・proxy 対応・Brexit=euftf proxy** → 探索的(確証でなく)。

依頼 §7 step4 / §9:UKグリッド9共同体は再現しない(NI等は BSA/NILT 向き)。ここは UK で取れる proxy で。
照合規則(b′ 操作化):grid ACTIVE → transition(出生年勾配)/ grid REFRAME・PASSIVE → flat(動かない)。
event 対応:freehms↔同性婚 / euftf↔Brexit(proxy)/ 移民index↔移民論争。
EVENT_STRUCTURE 留意:euftf/移民は反復 → flat を「CMR外れ」と誤読しない。

Run: python3 src/ess_overlay.py(先に ess_acquire.py)
出力: data/ess_results/overlay_uk.csv / overlay_uk_summary.json
"""
from __future__ import annotations
import sys, json, math, collections
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ess_segments as S
from ess_core_validation import wls_slope, changepoint, wmean_ci, CENTER
from ess_valuepack import changepoint_cont, wmean

ROOT = Path(__file__).resolve().parent.parent
SLIM = ROOT / "data" / "ess" / "ess_slim.parquet"
GRID = ROOT / "data" / "interpretations_uk_grid.jsonl"
PRIOR = ["ACTIVE", "REFRAME", "PASSIVE"]

# ESS proxy セグメント ↔ UKグリッド premise / pillar ↔ grid event
PROXY_TO_PREMISE = {
    "Secular HiEdu Urban": "middle_class_london_native_2nd_gen_oxbridge",       # London/Univ Remain
    "Religious LowEdu": "working_class_leave_town_native_4plus_gen_no_qualifications",  # Brexit Leave Town
    "Immigrant-bg": "middle_class_london_immigrant_2nd_gen_russell_group",       # London Multicultural
}
PILLAR_TO_EVENT = {"freehms": "uk_same_sex_marriage_2014", "euftf": "uk_brexit_2016",
                   "immigration": "uk_immigration_debate_2015"}


def grid_resolved():
    I = [json.loads(l) for l in GRID.read_text(encoding="utf-8").splitlines() if l.strip()]
    cells = collections.defaultdict(list)
    for x in I:
        if x.get("premise"):
            cells[(x["event_id"], x["premise"])].append(x["expected_mode"])
    def res(ms):
        if not ms: return None
        c = collections.Counter(ms); return sorted(c, key=lambda m: (-c[m], PRIOR.index(m) if m in PRIOR else 9))[0]
    return {k: res(v) for k, v in cells.items()}


def pred_state(mode):
    return {"ACTIVE": "transition", "REFRAME": "flat", "PASSIVE": "flat"}.get(mode)


def uk_state(uk, pillar, recode, kind, seg):
    sub = uk[S.segment_mask(uk, seg)].copy()
    sub["_y"] = recode(sub); sub["cohort_c"] = (S.cohort_bin(sub, 1) - CENTER); sub["_w"] = S.weight(sub)
    valid = sub.dropna(subset=["_y"])
    if len(valid) < 60:
        return {"state": "N不足", "n": len(valid), "pool": None, "slope": None}
    pool = (wmean_ci(valid["_y"], valid["_w"])[0] if kind == "binary" else wmean(valid["_y"], valid["_w"]))
    sl, se, n = wls_slope(sub, "_y")           # UK-only → round FE のみ(country 1水準)
    cp = changepoint(sub, "_y") if kind == "binary" else changepoint_cont(sub, "_y")
    sig = (not math.isnan(sl) and sl > 0 and abs(sl) > 1.96 * se)
    cpt = cp.get("sse_improve_vs_linear", 0) and cp["sse_improve_vs_linear"] >= 0.02
    if kind == "binary" and (pool >= 0.90 or pool <= 0.10):
        st = "flat"
    else:
        st = "transition" if (sig or cpt) else "flat"
    return {"state": st, "n": n, "pool": round(pool, 3),
            "slope": None if math.isnan(sl) else round(sl * (1000 if kind == "binary" else 10), 2)}


def main():
    if not SLIM.exists():
        raise SystemExit("先に ESS_USER_ID=... python3 src/ess_acquire.py")
    uk = pd.read_parquet(SLIM)
    uk = uk[uk["cntry"].astype(str) == "GB"].copy()
    g = grid_resolved()
    rows = []
    print("=" * 92)
    print("  ESS overlay(探索的・UK-only・proxy・Brexit=euftf proxy)")
    print("  grid 事前予測 × ESS UK 観測。ACTIVE→transition / REFRAME・PASSIVE→flat")
    print("=" * 92)
    print(f"  UK N = {len(uk)}(ESS7-11 GB)")
    for pillar, (recode, kind, struct) in S.PILLARS.items():
        eid = PILLAR_TO_EVENT[pillar]
        print(f"\n■ {pillar} ↔ {eid}  [{struct}]")
        for seg, prem in PROXY_TO_PREMISE.items():
            gm = g.get((eid, prem))
            ps = pred_state(gm)
            obs = uk_state(uk, pillar, recode, kind, seg)
            hit = (ps is not None and obs["state"] in ("flat", "transition") and ps == obs["state"])
            rows.append({"pillar": pillar, "event": eid, "proxy": seg, "grid_premise": prem,
                         "grid_mode": gm, "pred_state": ps, "obs_state": obs["state"],
                         "obs_pool": obs["pool"], "obs_slope": obs["slope"], "obs_n": obs["n"], "hit": hit})
            mk = "○" if hit else ("—" if obs["state"] == "N不足" else "×")
            print(f"   {seg:<22} grid={str(gm):<8}→pred {str(ps):<11} | ESS UK={obs['state']:<11}"
                  f"(pool={obs['pool']}, slope={obs['slope']}, n={obs['n']})  {mk}")

    scored = [r for r in rows if r["pred_state"] and r["obs_state"] in ("flat", "transition")]
    hits = sum(r["hit"] for r in scored)
    print("\n" + "-" * 92)
    print(f"  予測対応(探索的): {hits}/{len(scored)}  ※UK-only・proxy・N薄。確証でなく探索。")
    print("  ※ UK(=Western)はLGBT移行完了ゆえ ACTIVE予測が flat と衝突しやすい(step1.5と整合)。")
    print("  ※ 9共同体粒度・NI等は ESS では N不足 → BSA/NILT/Understanding Society 向き(Limitation)。")

    res = ROOT / "data" / "ess_results"; res.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(res / "overlay_uk.csv", index=False)
    (res / "overlay_uk_summary.json").write_text(json.dumps(
        {"scored": f"{hits}/{len(scored)}", "scope": "UK-only, proxy segments, Brexit=euftf proxy, exploratory",
         "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] data/ess_results/overlay_uk.csv / overlay_uk_summary.json")


if __name__ == "__main__":
    main()
