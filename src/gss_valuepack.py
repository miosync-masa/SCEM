#!/usr/bin/env python3
"""
gss_valuepack.py — 徳用パック(事象保持型プール・変化点主候補)。b′ の検出力を稼ぐ横展開。

真道さま確定(2026-06-26, findings doc §2.5 を受けて):
  A. 4事象(同性婚/中絶/銃/移民)× 主力6共同体で出生年スロープ+変化点を推定。
  B. **変化点を主候補に格上げ**(線形スロープ差は均しで保守的=BB 1975加速が証拠)。
     変化点の有無/位置の共同体差を主軸、線形スロープ差は頑健性で併走。検出法は複数を記述的に。
     Coastal 天井=「変化点が定義できない(飽和)」を正直に=それ自体 REFRAME 署名。
  C. **事象保持型プール(均さない)**。CMR は「事象ごとに解決が違う」が主張 → 均すと自滅。
     主検証=「コードが抵抗する共同体ほど勾配/変化点が露出」という同一パターンが 4事象を跨いで
     繰り返すか。方向一致なら単一p値より強い(同性婚のまぐれを殺す)。事象で割れたら**潰さず報告**
     (=CMR の事象依存の証拠)。

共通:period 耐性は FE版/非統制版を全事象で併記(diff-in-diff 識別の確認)。記述+CI+推定量まで。
検定の最終確定はしない(spin 防止)。重みは未適用。依存は numpy のみ(scipy 破損回避)。

Run: python3 src/gss_valuepack.py
出力: data/gss_results/valuepack_matrix.csv / valuepack_summary.json / figures/gss_valuepack_slopes.png
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gss_segments as G
from gss_interaction import ols_hc1, pval, COHORT_CENTER

ROOT = Path(__file__).resolve().parent.parent
SLIM = ROOT / "data" / "gss" / "gss_slim.parquet"

# 進歩派方向への二値化(approve=1)。各事象の「規範コードが抵抗しうる方向」を 1 に揃える。
def ssm(d):   return G.ssm_approve(d)                         # 同性婚の権利に賛成(marsame/marsame1接続)
def abort(d): return d["abany"].map({1: 1.0, 2: 0.0})        # 任意の理由での中絶に賛成
def guns(d):  return d["gunlaw"].map({1: 1.0, 2: 0.0})       # 銃所持許可制に賛成(=銃規制支持)
def immig(d):                                                 # 移民を増やすべき(letin1a 1,2)
    v = d["letin1a"]; out = pd.Series(pd.NA, index=d.index, dtype="Float64")
    out[v.isin([1, 2])] = 1.0; out[v.isin([3, 4, 5])] = 0.0; return out

EVENTS = {"同性婚": (ssm, "REFRAME(SSM)"), "中絶": (abort, "分岐(Dobbs系)"),
          "銃規制": (guns, "ACTIVE(gun)"), "移民増": (immig, "分岐(immigration)")}
PRIMARY = G.PRIMARY        # 主力6
SUPP = G.SUPPLEMENTARY     # Mormon / Latino(プールのみ)


def cohort_slope(sub, year_fe=True):
    """1事象×1共同体の出生年スロープ(LPM, pp/10年)+ HC1 SE。返り (slope, se, n)。"""
    sub = sub.dropna(subset=["approve", "cohort", "year"])
    if len(sub) < 30 or sub["approve"].nunique() < 2:
        return (float("nan"), float("nan"), len(sub))
    cc = (sub["cohort"] - COHORT_CENTER).values
    y = sub["approve"].astype(float).values
    cols = [np.ones(len(sub)), cc]
    if year_fe:
        for yr in sorted(sub["year"].unique())[1:]:
            cols.append((sub["year"].values == yr).astype(float))
    X = np.column_stack(cols)
    try:
        beta, se, _ = ols_hc1(X, y)
    except np.linalg.LinAlgError:
        return (float("nan"), float("nan"), len(sub))
    return (beta[1] * 1000, se[1] * 1000, len(sub))   # /年→pp/10年


def changepoint(sub):
    """変化点(賛成が加速する出生年)を二段折れ線のグリッドで。複数の記述的読みを返す。
    飽和(プール賛成が極端)なら「変化点なし(飽和)」を返す=REFRAME署名 / 天井。"""
    sub = sub.dropna(subset=["approve", "cohort"])
    p_pool = sub["approve"].mean()
    if len(sub) < 60:
        return {"knot": None, "note": "N不足", "pool": round(p_pool, 3)}
    if p_pool >= 0.90 or p_pool <= 0.10:
        return {"knot": None, "note": "飽和(変化点が定義できない=平坦/天井)", "pool": round(p_pool, 3)}
    cc = (sub["cohort"] - COHORT_CENTER).values
    y = sub["approve"].astype(float).values
    lin = np.column_stack([np.ones(len(cc)), cc])
    sse_lin = float(((y - lin @ np.linalg.lstsq(lin, y, rcond=None)[0]) ** 2).sum())
    best = None
    for knot in range(1940, 1991, 5):
        kc = knot - COHORT_CENTER
        X = np.column_stack([np.ones(len(cc)), cc, np.maximum(0.0, cc - kc)])
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((y - X @ b) ** 2).sum())
        if best is None or sse < best[1]:
            best = (knot, sse, b[2])
    improve = (sse_lin - best[1]) / sse_lin if sse_lin > 0 else 0.0
    return {"knot": best[0], "post_extra_slope_pp_decade": round(best[2] * 1000, 1),
            "sse_improve_vs_linear": round(improve, 3),
            "note": ("変化点あり" if improve >= 0.02 else "線形で十分(明瞭な節なし)"),
            "pool": round(p_pool, 3)}


def main():
    if not SLIM.exists():
        raise SystemExit("先に python3 src/gss_acquire.py")
    df = pd.read_parquet(SLIM)
    rows, summary = [], {}

    for ename, (recode, mode_tag) in EVENTS.items():
        summary[ename] = {"mode_tag": mode_tag, "communities": {}}
        for comm in PRIMARY:
            sub = df[G.segment_mask(df, comm)].copy()
            sub["approve"] = recode(sub)
            s_fe, se_fe, n = cohort_slope(sub, year_fe=True)
            s_no, se_no, _ = cohort_slope(sub, year_fe=False)
            cp = changepoint(sub.dropna(subset=["approve"]))
            z = s_fe / se_fe if (se_fe and not math.isnan(se_fe) and se_fe > 0) else float("nan")
            rec = {"event": ename, "mode_tag": mode_tag, "community": comm, "n": n,
                   "pool_approval": cp["pool"],
                   "slope_pp_decade_FE": None if math.isnan(s_fe) else round(s_fe, 1),
                   "slope_se_FE": None if math.isnan(se_fe) else round(se_fe, 1),
                   "slope_z_FE": None if math.isnan(z) else round(z, 2),
                   "slope_p_FE": None if math.isnan(z) else round(pval(z), 4),
                   "slope_pp_decade_noFE": None if math.isnan(s_no) else round(s_no, 1),
                   "changepoint_knot": cp["knot"], "changepoint_note": cp["note"],
                   "cp_post_extra_slope": cp.get("post_extra_slope_pp_decade"),
                   "cp_sse_improve": cp.get("sse_improve_vs_linear")}
            # 「移行中」判定(記述): スロープが有意に正 かつ 非飽和
            transition = (rec["slope_p_FE"] is not None and rec["slope_p_FE"] < 0.05
                          and rec["slope_pp_decade_FE"] is not None and rec["slope_pp_decade_FE"] > 0
                          and 0.10 < cp["pool"] < 0.90)
            rec["state"] = "移行中(勾配/変化点)" if transition else (
                "飽和/平坦" if (cp["pool"] >= 0.90 or cp["pool"] <= 0.10) else "弱/不明瞭")
            rows.append(rec)
            summary[ename]["communities"][comm] = {
                "slope_FE": rec["slope_pp_decade_FE"], "p": rec["slope_p_FE"],
                "pool": cp["pool"], "knot": cp["knot"], "state": rec["state"]}

    # 補助2(プールのみ・時系列せず)
    supp = []
    for comm in SUPP:
        for ename, (recode, _) in EVENTS.items():
            sub = df[G.segment_mask(df, comm)].copy(); sub["approve"] = recode(sub)
            s = sub["approve"].dropna()
            supp.append({"community": comm, "event": ename, "n": int(s.size),
                         "pool_approval": round(float(s.mean()), 3) if s.size else None})

    res = ROOT / "data" / "gss_results"; res.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(res / "valuepack_matrix.csv", index=False)
    pd.DataFrame(supp).to_csv(res / "valuepack_supplementary.csv", index=False)

    # ── 群方向一致の要約(均さない:事象ごとの「移行中」集合を並べる)──
    print("=" * 92)
    print("  徳用パック: 事象 × 共同体 出生年スロープ / 変化点(LPM+調査年FE, unweighted)")
    print("=" * 92)
    print(f"\n  {'共同体':<16}" + "".join(f"{e:<14}" for e in EVENTS))
    for comm in PRIMARY:
        cells = []
        for e in EVENTS:
            c = summary[e]["communities"][comm]
            sl = c["slope_FE"]
            mark = "•" if c["state"].startswith("移行") else ("=" if c["state"].startswith("飽和") else "·")
            cells.append(f"{mark}{'' if sl is None else f'{sl:+.1f}'}".ljust(14))
        print(f"  {comm:<16}" + "".join(cells))
    print("\n  凡例: •=移行中(有意勾配・非飽和) / ==飽和・平坦(REFRAME署名/天井) / ·=弱・不明瞭。数値=slope pp/10年(FE)")

    # 事象保持型の方向一致: 各事象で「移行中」の共同体集合
    print("\n  [事象保持プール] 各事象で『移行中(勾配/変化点)』の共同体:")
    for e in EVENTS:
        trans = [c for c in PRIMARY if summary[e]["communities"][c]["state"].startswith("移行")]
        flat = [c for c in PRIMARY if summary[e]["communities"][c]["state"].startswith("飽和")]
        print(f"    {e:<7} 移行中: {trans or '—'}")
        print(f"    {'':<7} 飽和/平坦: {flat or '—'}")

    # 共同体ごと「何事象で移行中か」= パターン反復(均さず数える)
    print("\n  [方向一致] 共同体が『移行中』だった事象数(4事象中):")
    rep = {}
    for comm in PRIMARY:
        k = sum(summary[e]["communities"][comm]["state"].startswith("移行") for e in EVENTS)
        rep[comm] = k
        print(f"    {comm:<16}: {k}/4")
    summary["_repetition_transition_count"] = rep

    (res / "valuepack_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 図: 事象×共同体 スロープ ヒートマップ ──
    plt.rcParams["font.family"] = "Hiragino Sans"; plt.rcParams["axes.unicode_minus"] = False
    M = np.full((len(PRIMARY), len(EVENTS)), np.nan)
    for i, comm in enumerate(PRIMARY):
        for j, e in enumerate(EVENTS):
            v = summary[e]["communities"][comm]["slope_FE"]
            if v is not None:
                M[i, j] = v
    fig, ax = plt.subplots(figsize=(7.5, 5))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-8, vmax=8, aspect="auto")
    ax.set_xticks(range(len(EVENTS))); ax.set_xticklabels(list(EVENTS), fontsize=10)
    ax.set_yticks(range(len(PRIMARY))); ax.set_yticklabels(PRIMARY, fontsize=9)
    for i in range(len(PRIMARY)):
        for j, e in enumerate(EVENTS):
            v = M[i, j]
            if not np.isnan(v):
                st = summary[e]["communities"][PRIMARY[i]]["state"]
                tag = "•" if st.startswith("移行") else ("=" if st.startswith("飽和") else "")
                ax.text(j, i, f"{v:+.1f}{tag}", ha="center", va="center", fontsize=8.5,
                        color="black" if abs(v) < 5 else "white")
    ax.set_title("徳用パック: 出生年スロープ(賛成 pp/10年, LPM+FE)\n"
                 "•=移行中(有意勾配) ==飽和/平坦。事象で割れる=CMRの事象依存", fontsize=10)
    fig.colorbar(im, label="出生年スロープ pp/10年")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "gss_valuepack_slopes.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\n[saved] data/gss_results/valuepack_matrix.csv / valuepack_summary.json / figures/gss_valuepack_slopes.png")
    print("  ※ 均していない(事象保持)。検定の最終確定はしない。機構は未分離(Discussion仮説)。")


if __name__ == "__main__":
    main()
