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
    cols = [np.ones(len(d)), d["cohort_c"].values]
    for fc in fe_cols:
        if fc in d:
            for lv in sorted(d[fc].dropna().unique())[1:]:
                cols.append((d[fc].values == lv).astype(float))
    X = np.column_stack(cols)
    w = d["_w"].values
    W = np.sqrt(w)[:, None]
    Xw = X * W; yw = d[ycol].values * np.sqrt(w)
    try:
        XtX_inv = np.linalg.inv(Xw.T @ Xw)
        beta = XtX_inv @ Xw.T @ yw
        resid = yw - Xw @ beta
        n, kk = X.shape
        V = XtX_inv @ (Xw.T @ (Xw * (resid ** 2)[:, None])) @ XtX_inv * (n / (n - kk))
        return (beta[1], math.sqrt(V[1, 1]), len(d))
    except np.linalg.LinAlgError:
        return (float("nan"), float("nan"), len(d))


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
        state = ("飽和/平坦" if (pp >= 0.90 or pp <= 0.10) else
                 ("移行中" if (not math.isnan(sl) and sl > 0 and abs(sl) > 1.96 * se) else "弱/不明瞭"))
        summary["segments"][seg] = {"pool_tolerant": round(pp, 3), "pool_ci": [round(plo, 3), round(phi, 3)],
                                    "cohort_slope_pp_decade": None if math.isnan(sl) else round(sl * 1000, 2),
                                    "n": n, "state": state}
        print(f"\n── {seg}  プール寛容 {pp:.0%} [{plo:.0%},{phi:.0%}]  "
              f"スロープ {('NA' if math.isnan(sl) else f'{sl*1000:+.1f}')} pp/10年  → {state}")
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

    res = ROOT / "data" / "ess_results"; res.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(res / "freehms_core.csv", index=False)
    (res / "freehms_core.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] data/ess_results/freehms_core.csv / .json")
    print("  ※ 記述+CI+スロープまで。検定最終確定せず(spin防止)。freehms=単発型で出生年軸OK。")
    print("  ※ 次: step2 euftf / step3 移民index(§B 反復=flat誤読しない)/ step4 overlay。")


if __name__ == "__main__":
    main()
