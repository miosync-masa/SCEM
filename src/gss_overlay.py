#!/usr/bin/env python3
"""
gss_overlay.py — Paper 2 グリッドの【事前】resolved_mode を GSS 割れマトリクスに重ね、
                 「Code の事前予測どおりにモードが解決されたか」を照合する(§5.2 predict→check)。

真道さま確定(2026-06-26):
  - (ii) の昇格:GSS の「割れ」が "issues differ" でなく CMR の実証であることを示すには、
    割れが **Paper 2 の事前予測(GSS を見る前のグリッド resolved_mode)を追う** ことが必要。
  - 重なる事象(予測あり):同性婚=us_obergefell_2015 / 中絶=us_dobbs_2022 / 銃規制=us_sandy_hook_2012。
  - 欠ける事象:移民=US グリッドに無い → **「予測なし=探索的」として分離**(予測どおり集計を汚さない)。
  - **飽和→REFRAME と直結しない**(後付け禁止)。予測 REFRAME が GSS の flat を当てたか、を見る。

照合(b′ の操作化):
  grid ACTIVE  → 予測「transition(出生年スロープが移行中)」
  grid REFRAME → 予測「flat(出生年スロープが動かない=飽和 or 弱・平坦)」
  grid PASSIVE → 鋭い予測なし(該当あれば別掲)
GSS 観測:transition = 有意な正の出生年スロープ(線形)/ または変化点あり(改善≥0.02)・非飽和。
          flat = それ以外(飽和[天井/床] or 弱・平坦)。
線形読みと変化点読みの両方で 2×2 を出す(閾値未決のため決め打ちしない)。

Run: python3 src/gss_overlay.py   (先に gss_valuepack.py を実行)
出力: data/gss_results/overlay_predicted_vs_observed.csv / overlay_summary.json / コンソール
"""
from __future__ import annotations
import sys, json, collections
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "data" / "gss_results"
INTERP = ROOT / "data" / "interpretations_us_grid.jsonl"

PRIOR = ["ACTIVE", "REFRAME", "PASSIVE"]   # tie-break(operational, cmr_compare と同じ)
EVENTS_PRED = {"同性婚": "us_obergefell_2015", "中絶": "us_dobbs_2022", "銃規制": "us_sandy_hook_2012"}
EVENTS_EXPLORATORY = ["移民増"]            # グリッド予測なし

# 事象の時間構造(真道さま 2026-06-26):出生年×態度という GSS の観測装置と噛み合うか。
#   single_moment = 特定の歴史的瞬間に着弾(Obergefell 2015 / Dobbs 2022)
#       → 出生年で着弾年齢が変わる → 出生年勾配が出る → GSS で見える(装置の射程内)
#   recurrent_burst = 反復バースト(乱射: Columbine→VTech→Sandy Hook→Parkland→Uvalde)
#       → 全出生年が感受性窓で必ず食らう → 出生年で差がつかない → GSS では原理的に見えない(射程外)
#       grid の ACTIVE 解決は正しいが、その ACTIVE は強度/行動に出て、出生年×態度には映らない。
EVENT_STRUCTURE = {"同性婚": "single_moment", "中絶": "single_moment",
                   "銃規制": "recurrent_burst", "移民増": "single_moment"}
COMM = {
    "Coastal Liberal": "secular_white_coastal_graduate",
    "Bible Belt": "evangelical_white_bible_belt_no_college",
    "Rust Belt WWC": "mainline_protestant_white_rust_belt_no_college",
    "Black urban": "secular_black_urban_some_college",
    "Suburban MC": "mainline_protestant_white_suburban_bachelor",
    "Rural Conservative": "evangelical_white_rural_no_college",
}


def grid_resolved():
    I = [json.loads(l) for l in INTERP.read_text(encoding="utf-8").splitlines() if l.strip()]
    cells = collections.defaultdict(list)
    for x in I:
        if x.get("premise"):
            cells[(x["event_id"], x["premise"])].append(x["expected_mode"])

    def resolve(ms):
        if not ms:
            return None
        c = collections.Counter(ms)
        return sorted(c, key=lambda m: (-c[m], PRIOR.index(m) if m in PRIOR else 9))[0]
    return {k: resolve(v) for k, v in cells.items()}


def gss_state(row, reading):
    """GSS 観測を transition / flat / na に二値化。reading='linear' | 'changepoint'。"""
    pool = row["pool_approval"]
    if pd.isna(pool):
        return "na"
    saturated = (pool >= 0.90) or (pool <= 0.10)
    sig_pos = (not pd.isna(row["slope_p_FE"])) and (row["slope_p_FE"] < 0.05) \
        and (not pd.isna(row["slope_pp_decade_FE"])) and (row["slope_pp_decade_FE"] > 0)
    cp = (not pd.isna(row.get("cp_sse_improve"))) and (row["cp_sse_improve"] >= 0.02) and (not saturated)
    transition = sig_pos or (cp if reading == "changepoint" else False)
    return "transition" if transition else "flat"


def predicted_state(mode):
    return {"ACTIVE": "transition", "REFRAME": "flat"}.get(mode)   # PASSIVE→None(鋭い予測なし)


def main():
    mat = pd.read_csv(RES / "valuepack_matrix.csv")
    g = grid_resolved()
    rows = []
    for en, eid in EVENTS_PRED.items():
        for cn, pr in COMM.items():
            gm = g.get((eid, pr))
            sub = mat[(mat.event == en) & (mat.community == cn)]
            if sub.empty:
                continue
            r = sub.iloc[0]
            rec = {"event": en, "community": cn, "grid_pred_mode": gm,
                   "pred_state": predicted_state(gm), "gss_pool": r["pool_approval"],
                   "gss_slope_FE": r["slope_pp_decade_FE"], "gss_p": r["slope_p_FE"],
                   "cp_knot": r["changepoint_knot"], "cp_improve": r.get("cp_sse_improve"),
                   "gss_state_linear": gss_state(r, "linear"),
                   "gss_state_cp": gss_state(r, "changepoint")}
            rec["hit_linear"] = (rec["pred_state"] is not None
                                 and rec["pred_state"] == rec["gss_state_linear"])
            rec["hit_cp"] = (rec["pred_state"] is not None
                             and rec["pred_state"] == rec["gss_state_cp"])
            rows.append(rec)
    ov = pd.DataFrame(rows)
    ov.to_csv(RES / "overlay_predicted_vs_observed.csv", index=False)

    ov["event_structure"] = ov.event.map(EVENT_STRUCTURE)
    # ── 集計 ──
    # 装置の正当な射程 = single_moment 事象のみ(出生年×態度で見える)。
    # recurrent_burst(銃) は出生年で原理的に差がつかない → 射程外(grid失敗でなく観測装置ミスマッチ)。
    scored_all = ov[ov.pred_state.notna()]
    scored = scored_all[scored_all.event_structure == "single_moment"]   # 主集計=単発事象
    def tally(df, col):
        return int(df[col].sum()), int(len(df))
    hl, n = tally(scored, "hit_linear"); hc, _ = tally(scored, "hit_cp")
    hl_all, n_all = tally(scored_all, "hit_linear"); hc_all, _ = tally(scored_all, "hit_cp")

    print("=" * 96)
    print("  overlay: Paper 2 グリッド事前予測 × GSS 観測(予測どおりか / §5.2 predict→check)")
    print("=" * 96)
    print(f"\n  {'event':<7}{'community':<19}{'grid予測':<9}{'→pred':<11}{'GSS(lin)':<11}{'GSS(cp)':<11}{'hit(lin/cp)'}")
    for _, r in ov.iterrows():
        hl_ = "○" if r.hit_linear else "×"
        hc_ = "○" if r.hit_cp else "×"
        print(f"  {r.event:<7}{r.community:<19}{str(r.grid_pred_mode):<9}{str(r.pred_state):<11}"
              f"{r.gss_state_linear:<11}{r.gss_state_cp:<11}{hl_}/{hc_}  "
              f"(pool={r.gss_pool:.2f}, slope={r.gss_slope_FE})")

    print(f"\n  ── 予測的中率【主=単発事象のみ(装置の射程内): SSM+中絶, n={n}】──")
    print(f"     線形読み   : {hl}/{n} = {hl/n:.0%}")
    print(f"     変化点読み : {hc}/{n} = {hc/n:.0%}")
    print(f"  ── 参考(銃=反復バースト込み, n={n_all})── 変化点 {hc_all}/{n_all}={hc_all/n_all:.0%}"
          "(銃は出生年軸で原理的に不可視=装置ミスマッチ。grid失敗ではない)")
    # 事象別
    print("\n  ── 事象別(変化点読み)──")
    for en in EVENTS_PRED:
        s = scored_all[scored_all.event == en]
        tag = "" if EVENT_STRUCTURE[en] == "single_moment" else " [反復バースト=射程外]"
        print(f"     {en:<7}: {int(s.hit_cp.sum())}/{len(s)}{tag}  "
              + " ".join(f"{r.community.split()[0]}={'○' if r.hit_cp else '×'}" for _, r in s.iterrows()))
    # 2x2 混同(変化点読み, 単発事象のみ)
    print("\n  ── 2×2 混同(grid予測 × GSS観測, 変化点読み, 単発事象)──")
    conf = collections.Counter((r.pred_state, r.gss_state_cp) for _, r in scored.iterrows())
    print(f"     grid ACTIVE → GSS transition: {conf[('transition','transition')]}  / GSS flat: {conf[('transition','flat')]}")
    print(f"     grid REFRAME→ GSS flat      : {conf[('flat','flat')]}  / GSS transition: {conf[('flat','transition')]}")

    # 探索的(移民:予測なし)
    print("\n  ── 探索的(移民増:グリッド予測なし。集計に含めない)──")
    for cn in COMM:
        sub = mat[(mat.event == "移民増") & (mat.community == cn)]
        if not sub.empty:
            r = sub.iloc[0]
            print(f"     {cn:<19} GSS(cp)={gss_state(r,'changepoint'):<11} (pool={r['pool_approval']:.2f}, "
                  f"slope={r['slope_pp_decade_FE']}, cp_knot={r['changepoint_knot']})")

    out = {"events_predicted": EVENTS_PRED, "events_exploratory": EVENTS_EXPLORATORY,
           "event_structure": EVENT_STRUCTURE,
           "scope": "primary accuracy = single_moment events only (birth-year×attitude instrument valid). "
                    "recurrent_burst (guns) is out-of-scope: every cohort is hit in-window so no birth-year "
                    "variation can exist — instrument-event time-structure mismatch, NOT a grid failure.",
           "hit_linear_singlemoment": [hl, n], "hit_changepoint_singlemoment": [hc, n],
           "hit_changepoint_incl_guns": [hc_all, n_all],
           "confusion_cp_singlemoment": {f"{a}->{b}": v for (a, b), v in conf.items()},
           "note": "saturation is NOT auto-labeled REFRAME; we check whether the prior grid mode "
                   "predicted the GSS flat/transition state. immigration excluded (no grid prediction)."}
    (RES / "overlay_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] data/gss_results/overlay_predicted_vs_observed.csv / overlay_summary.json")
    print("  ※ 飽和→REFRAME と直結せず、事前予測が GSS の flat/transition を当てたかを照合。閾値は両読み併記。")


if __name__ == "__main__":
    main()
