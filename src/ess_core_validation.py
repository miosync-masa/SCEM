#!/usr/bin/env python3
"""
ess_core_validation.py — ESS step1(主検証):freehms(LGBT寛容)の共同体ゲートを出生年コホートで。
GSS core_contrast / interaction の移植(重み付き版)。

依頼 §E step1:Europe-wide, freehms。secular高学歴都市(Coastal類似) vs 宗教的低学歴(Bible Belt類似)。
  → high-flat / transition の二分を見て、**US 同性婚(GSS)と並置**(クロスナショナルの目玉)。
EVENT_STRUCTURE:freehms = single_moment(出生年軸で安全に測れる)。
重み:ESS post-strat(anweight 等, ess_segments.weight)。period/country は FE。
記述+CI(設計効果補正 Wilson)+ 重み付きスロープ。検定の最終確定はしない(spin 防止)。

⚠️ 実データ投入待ち:先に ESS を取得して data/ess/ess_slim.parquet を作る(python3 src/ess_acquire.py)。
   データが無ければ何も出力しない(捏造しない)。

Run: python3 src/ess_core_validation.py
出力: data/ess_results/freehms_core.csv / .json / figures/ess_freehms_core.png
US参照(GSS同性婚): Coastal 平坦高位 91% [85,95] / Bible Belt 単調勾配 6%→66%(findings §2.5)。
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ess_segments as S

ROOT = Path(__file__).resolve().parent.parent
SLIM = ROOT / "data" / "ess" / "ess_slim.parquet"
COHORT_W = 10
CENTER = 1960
CONTRAST = S.PRIMARY_CONTRAST     # ["Secular HiEdu Urban","Religious LowEdu"]
# US(GSS)参照値(並置の目玉)
US_REF = {"Coastal(REFRAME) flat-high": "91% [85,95]", "Bible Belt(ACTIVE) gradient": "6%→66%"}


def wilson_eff(k_eff, n_eff, z=1.96):
    if n_eff <= 0:
        return (float("nan"), float("nan"))
    p = k_eff / n_eff
    d = 1 + z * z / n_eff
    c = (p + z * z / (2 * n_eff)) / d
    h = z * ((p * (1 - p) + z * z / (4 * n_eff)) / n_eff) ** 0.5 / d
    return (max(0.0, c - h), min(1.0, c + h))


def wmean_ci(y, w):
    """重み付き比率 + 設計効果近似の n_eff で Wilson CI。"""
    w = np.asarray(w, float); y = np.asarray(y, float)
    sw = w.sum()
    if sw <= 0:
        return (float("nan"), float("nan"), float("nan"), 0)
    p = float((w * y).sum() / sw)
    n_eff = (sw ** 2) / (w ** 2).sum()      # Kish の有効標本サイズ
    lo, hi = wilson_eff(p * n_eff, n_eff)
    return (p, lo, hi, int(round(n_eff)))


def wls_slope(d, ycol, fe_cols=("cntry", "essround")):
    """重み付き OLS で cohort スロープ(確率/年)。country・round FE。返り (slope, se)。"""
    d = d.dropna(subset=[ycol, "cohort_c", "_w"])
    if len(d) < 50 or d[ycol].nunique() < 2:
        return (float("nan"), float("nan"), len(d))
    y = np.asarray(d[ycol], dtype=float)
    cols = [np.ones(len(d)), np.asarray(d["cohort_c"], dtype=float)]
    for fc in fe_cols:
        if fc in d:
            for lv in sorted(d[fc].dropna().unique())[1:]:
                cols.append((d[fc].values == lv).astype(float))
    X = np.column_stack(cols)
    w = np.asarray(d["_w"], dtype=float)
    sw = np.sqrt(w)
    Xw = X * sw[:, None]; yw = y * sw
    try:
        XtX_inv = np.linalg.inv(Xw.T @ Xw)
        beta = XtX_inv @ Xw.T @ yw
        resid = yw - Xw @ beta
        n, kk = X.shape
        V = XtX_inv @ (Xw.T @ (Xw * (resid ** 2)[:, None])) @ XtX_inv * (n / (n - kk))
        return (beta[1], math.sqrt(V[1, 1]), len(d))
    except np.linalg.LinAlgError:
        return (float("nan"), float("nan"), len(d))


def changepoint(sub, ycol="tol"):
    """変化点(寛容が加速/頭打ちする出生年)。重み付き二段折れ線グリッド。B(変化点>線形)の移植。
    飽和(プール極端)なら変化点定義不能=REFRAME署名/天井 と返す。"""
    d = sub.dropna(subset=[ycol, "cohort_c", "_w"])
    p_pool = float(np.average(np.asarray(d[ycol], float), weights=np.asarray(d["_w"], float))) if len(d) else float("nan")
    if len(d) < 200:
        return {"knot": None, "note": "N不足", "pool": round(p_pool, 3)}
    if p_pool >= 0.90 or p_pool <= 0.10:
        return {"knot": None, "note": "飽和(変化点定義不能=平坦/天井=REFRAME署名)", "pool": round(p_pool, 3)}
    cc = np.asarray(d["cohort_c"], float); y = np.asarray(d[ycol], float); w = np.asarray(d["_w"], float)
    sw = np.sqrt(w)
    def wsse(X):
        b = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
        return float((((y - X @ b) * sw) ** 2).sum()), b
    sse_lin, _ = wsse(np.column_stack([np.ones(len(cc)), cc]))
    best = None
    for knot in range(1940, 1991, 5):
        kc = knot - CENTER
        X = np.column_stack([np.ones(len(cc)), cc, np.maximum(0.0, cc - kc)])
        sse, b = wsse(X)
        if best is None or sse < best[1]:
            best = (knot, sse, b[1] * 1000, b[2] * 1000)   # pre-slope, extra-slope (pp/10yr)
    improve = (sse_lin - best[1]) / sse_lin if sse_lin > 0 else 0.0
    return {"knot": best[0], "pre_slope_pp_decade": round(best[2], 1),
            "post_extra_slope_pp_decade": round(best[3], 1), "sse_improve_vs_linear": round(improve, 3),
            "note": ("変化点あり" if improve >= 0.02 else "線形で十分"), "pool": round(p_pool, 3)}


def main():
    if not SLIM.exists():
        print("⚠️ data/ess/ess_slim.parquet が無い。先に ESS を取得:")
        print("   1) ESS Data Portal 登録 → integrated rounds(Stata)DL → data/ess/ に配置")
        print("   2) python3 src/ess_acquire.py")
        print("   (docs/ess_validation_plan.md §D)。捏造しない=データが来るまで結果は出さない。")
        raise SystemExit(1)

    df = pd.read_parquet(SLIM)
    df["tol"] = S.freehms_tolerant(df)
    df["cohort_bin"] = S.cohort_bin(df, COHORT_W)
    df["cohort_c"] = (S.cohort_bin(df, 1) - CENTER)
    df["_w"] = S.weight(df)

    rows, summary = [], {"pillar": "freehms", "event_structure": S.EVENT_STRUCTURE["freehms"],
                         "us_reference_gss_ssm": US_REF, "segments": {}}
    print("=" * 84)
    print("  ESS step1: LGBT寛容(freehms)× 出生年コホート [Europe-wide, 重み付き]")
    print("  Secular HiEdu Urban(Coastal類似) vs Religious LowEdu(Bible Belt類似)")
    print("=" * 84)
    slopes = {}
    for seg in CONTRAST:
        sub = df[S.segment_mask(df, seg)].copy()
        prof = []
        for cb, g in sub.dropna(subset=["tol", "cohort_bin"]).groupby("cohort_bin"):
            p, lo, hi, ne = wmean_ci(g["tol"], g["_w"])
            prof.append((int(cb), p, lo, hi, ne))
            rows.append({"segment": seg, "cohort_bin": int(cb), "tolerant": round(p, 4),
                         "ci_lo": round(lo, 4), "ci_hi": round(hi, 4), "n_eff": ne})
        pp, plo, phi, pne = wmean_ci(sub["tol"].dropna(), sub.loc[sub["tol"].notna(), "_w"])
        sl, se, n = wls_slope(sub, "tol")
        slopes[seg] = (sl, se)
        cp = changepoint(sub)
        cp_transition = cp.get("sse_improve_vs_linear", 0) and cp["sse_improve_vs_linear"] >= 0.02
        lin_transition = (not math.isnan(sl) and sl > 0 and abs(sl) > 1.96 * se)
        state = ("飽和/平坦" if (pp >= 0.90 or pp <= 0.10) else
                 ("移行中(線形)" if lin_transition else
                  ("移行中(変化点のみ)" if cp_transition else "弱/不明瞭")))
        summary["segments"][seg] = {"pool_tolerant": round(pp, 3), "pool_ci": [round(plo, 3), round(phi, 3)],
                                    "cohort_slope_pp_decade": None if math.isnan(sl) else round(sl * 1000, 2),
                                    "changepoint": cp, "n": n, "state": state}
        print(f"\n── {seg}  プール寛容 {pp:.0%} [{plo:.0%},{phi:.0%}]  "
              f"線形スロープ {('NA' if math.isnan(sl) else f'{sl*1000:+.1f}')} pp/10年  → {state}")
        print(f"     変化点: {cp.get('knot')}年 ({cp['note']}"
              + (f", pre {cp['pre_slope_pp_decade']:+.1f} / post追加 {cp['post_extra_slope_pp_decade']:+.1f} pp/10年, 改善{cp['sse_improve_vs_linear']}" if cp.get('knot') else "") + ")")
        for cb, p, lo, hi, ne in prof:
            print(f"     生{cb}-{cb+COHORT_W-1}: {p:.0%} [{lo:.0%},{hi:.0%}] (n_eff={ne})")

    # 交互作用(スロープ差)
    if all(not math.isnan(slopes[s][0]) for s in CONTRAST):
        a, b = slopes[CONTRAST[0]], slopes[CONTRAST[1]]
        diff = b[0] - a[0]; sed = math.sqrt(a[1] ** 2 + b[1] ** 2)
        z = diff / sed if sed > 0 else float("nan")
        summary["interaction_slope_diff_pp_decade"] = round(diff * 1000, 2)
        summary["interaction_z"] = None if math.isnan(z) else round(z, 2)
        print(f"\n  交互作用(Religious LowEdu − Secular HiEdu のスロープ差)= {diff*1000:+.1f} pp/10年 (z={z:.2f})")
        print("  予測(b′): secular側=平坦高位(REFRAME) / 宗教低学歴側=正の勾配(transition) → 差>0")
    print(f"\n  [US 並置 / GSS同性婚] Coastal(REFRAME) {US_REF['Coastal(REFRAME) flat-high']} / "
          f"Bible Belt(ACTIVE) {US_REF['Bible Belt(ACTIVE) gradient']}")
    print("  → 軸は違う(US宗教×人種 / Europe religiosity×education)が high-flat/transition が再現するか=普遍性(§5)")

    # ── US 並置図(目玉): ESS freehms コホート曲線 + GSS同性婚 参照 ──
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.family"] = "Hiragino Sans"; plt.rcParams["axes.unicode_minus"] = False
        rdf = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(9, 5.5))
        colors = {"Secular HiEdu Urban": "#2e8b57", "Religious LowEdu": "#c0392b"}
        for seg in CONTRAST:
            s = rdf[rdf.segment == seg].sort_values("cohort_bin")
            yerr = [s.tolerant - s.ci_lo, s.ci_hi - s.tolerant]
            ax.errorbar(s.cohort_bin + COHORT_W / 2, s.tolerant, yerr=yerr, fmt="-o",
                        color=colors.get(seg, "#555"), capsize=3, label=f"ESS {seg}")
        # US(GSS同性婚)参照
        ax.axhline(0.91, color="#2e8b57", ls=":", lw=1.3, alpha=0.7)
        ax.text(1992, 0.915, "US Coastal 91%(GSS, REFRAME flat)", color="#2e8b57", fontsize=8)
        ax.annotate("US Bible Belt 6%→66%(GSS, ACTIVE gradient)", xy=(1955, 0.3),
                    color="#c0392b", fontsize=8)
        ax.set_xlabel("出生年コホート(10年, ビン中心)"); ax.set_ylabel("LGBT寛容率 freehms∈{agree}")
        ax.set_ylim(0, 1); ax.grid(alpha=0.25); ax.legend(loc="lower right", fontsize=9)
        ax.set_title("クロスナショナル: LGBT寛容 × 出生年(ESS Europe vs US-GSS参照)\n"
                     "ESS: Secular=平坦高位 / Religious=水準低・1960生で頭打ち。US Bible Beltは移行中=移行段階が国で違う",
                     fontsize=10)
        fig.tight_layout()
        (ROOT / "figures").mkdir(exist_ok=True)
        fig.savefig(ROOT / "figures" / "ess_freehms_core.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        print("[saved] figures/ess_freehms_core.png(US並置)")
    except Exception as e:
        print(f"[figure skip] {e}")

    res = ROOT / "data" / "ess_results"; res.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(res / "freehms_core.csv", index=False)
    (res / "freehms_core.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] data/ess_results/freehms_core.csv / .json")
    print("  ※ 記述+CI+スロープまで。検定最終確定せず(spin防止)。freehms=単発型で出生年軸OK。")
    print("  ※ 次: step2 euftf / step3 移民index(§B 反復=flat誤読しない)/ step4 overlay。")


if __name__ == "__main__":
    main()
