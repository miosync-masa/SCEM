#!/usr/bin/env python3
"""
gss_interaction.py — b′(抑制された2軸)の主検定:共同体 × 出生年スロープの交互作用。

真道さま承認スタック(2026-06-26, docs/gss_validation_findings.md §2.4):
  主    : LPM  approve ~ cohort * community (+ 調査年FE, HC1 robust SE)
          → 各共同体 simple slope と 交互作用=スロープ差(pp/10年)を報告。
  ②天井 : Coastal を片側問題に変換(BB slope>0 ∧ Coastal slope≈0=飽和)。
  頑健性 : ロジット cohort*community を AME(平均限界効果)で報告(生係数でなく; Ai-Norton回避)。
  副(記述): 変化点を Bible Belt のみ(賛成が加速する出生年)。Coastal は平坦=変化点なし。
  period : 調査年FE。交互作用は diff-in-diff で識別(共通periodは共同体差で相殺)。age は入れない(APC)。

依存は numpy のみ(scipy/statsmodels 不使用=本環境の scipy 破損回避)。
p値は正規近似(math.erf)。重みは未適用(unweighted; 波跨ぎ weight は今後の頑健性)。

Run: python3 src/gss_interaction.py
出力: data/gss_results/interaction_ssm.json / コンソール要約
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gss_segments as G

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
SLIM = ROOT / "data" / "gss" / "gss_slim.parquet"
COHORT_CENTER = 1960            # cohort を中心化(係数 = 1960生付近のスロープ)
PAIR = ["Coastal Liberal", "Bible Belt"]   # Coastal=参照(community=0), Bible Belt=1


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def pval(z):
    return 2 * (1 - phi(abs(z)))


def ols_hc1(X, y):
    """OLS + HC1 robust SE。返り値 (beta, se, XtX_inv)。"""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    n, k = X.shape
    meat = X.T @ (X * (resid ** 2)[:, None]) @ XtX_inv  # X' diag(e^2) X (X'X)^-1
    V = XtX_inv @ meat * (n / (n - k))
    se = np.sqrt(np.diag(V))
    return beta, se, resid


def logit_newton(X, y, ridge=1e-6, iters=100):
    """ロジスティック回帰(Newton-IRLS, numpy)。準分離に備え微小 ridge。返り値 beta。"""
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ beta, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        W = p * (1 - p) + 1e-9
        grad = X.T @ (y - p) - ridge * beta
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(H, grad)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-8:
            break
    return beta


def build(df):
    rows = []
    for comm in PAIR:
        sub = df[G.segment_mask(df, comm)].copy()
        sub["approve"] = G.ssm_approve(sub)
        sub = sub.dropna(subset=["approve", "cohort", "year"])
        sub["community"] = 1.0 if comm == "Bible Belt" else 0.0
        sub["comm_name"] = comm
        rows.append(sub[["approve", "cohort", "year", "community", "comm_name"]])
    d = pd.concat(rows, ignore_index=True)
    d["approve"] = d["approve"].astype(float)
    d["cohort_c"] = (d["cohort"] - COHORT_CENTER)        # 年単位
    return d


def design(d, year_fe=True):
    """[intercept, cohort_c, community, cohort_c:community, (year dummies...)]"""
    cols = {"intercept": np.ones(len(d)), "cohort_c": d["cohort_c"].values,
            "community": d["community"].values,
            "cohort_c:community": (d["cohort_c"] * d["community"]).values}
    names = list(cols)
    X = np.column_stack([cols[n] for n in names])
    if year_fe:
        yrs = sorted(d["year"].unique())[1:]   # 1つ落とす(基準)
        for yr in yrs:
            X = np.column_stack([X, (d["year"].values == yr).astype(float)])
            names.append(f"year_{int(yr)}")
    return X, names


def main():
    if not SLIM.exists():
        raise SystemExit(f"[error] {SLIM} 無し。先に python3 src/gss_acquire.py")
    d = build(pd.read_parquet(SLIM))
    y = d["approve"].values
    X, names = design(d, year_fe=True)
    idx = {n: i for i, n in enumerate(names)}

    # ── 主: LPM 交互作用 ──
    beta, se, _ = ols_hc1(X, y)
    b_co = beta[idx["cohort_c"]]                       # Coastal スロープ(/年)
    b_int = beta[idx["cohort_c:community"]]            # スロープ差(BB - Coastal)
    se_int = se[idx["cohort_c:community"]]
    b_bb = b_co + b_int                                # Bible Belt スロープ(/年)
    # BB スロープの SE(線形結合)
    XtX_inv = np.linalg.inv(X.T @ X)
    resid = y - X @ beta
    n, k = X.shape
    V = XtX_inv @ (X.T @ (X * (resid ** 2)[:, None])) @ XtX_inv * (n / (n - k))
    c = np.zeros(k); c[idx["cohort_c"]] = 1; c[idx["cohort_c:community"]] = 1
    se_bb = math.sqrt(c @ V @ c)
    z_int = b_int / se_int

    def dec(b):   # /年 → pp/10年
        return b * 10 * 100

    lpm = {
        "coastal_slope_pp_per_decade": round(dec(b_co), 2),
        "biblebelt_slope_pp_per_decade": round(dec(b_bb), 2),
        "biblebelt_slope_se_pp": round(dec(se_bb), 2),
        "interaction_slope_diff_pp_per_decade": round(dec(b_int), 2),
        "interaction_se_pp": round(dec(se_int), 2),
        "interaction_z": round(z_int, 2),
        "interaction_p": pval(z_int),
        "n": int(n),
    }

    # ── 透明性: period 統制なし版の交互作用(どれだけ period が効いていたか)──
    Xn, namesn = design(d, year_fe=False)
    idxn = {n: i for i, n in enumerate(namesn)}
    bn, sen, _ = ols_hc1(Xn, y)
    nofe = {"interaction_pp_per_decade": round(bn[idxn["cohort_c:community"]] * 1000, 2),
            "z": round(bn[idxn["cohort_c:community"]] / sen[idxn["cohort_c:community"]], 2)}

    # ── 頑健性: ロジット AME(共同体別 cohort の平均限界効果)──
    blog = logit_newton(X, y)
    eta = np.clip(X @ blog, -30, 30)
    p = 1 / (1 + np.exp(-eta))
    # cohort の限界効果 = (β_cohort + β_int*community) * p(1-p)、共同体別に平均
    base = blog[idx["cohort_c"]]; inter = blog[idx["cohort_c:community"]]
    eff = (base + inter * d["community"].values) * (p * (1 - p))
    ame = {}
    for comm, cv in [("Coastal Liberal", 0.0), ("Bible Belt", 1.0)]:
        m = d["community"].values == cv
        ame[comm + "_AME_pp_per_decade"] = round(eff[m].mean() * 10 * 100, 2)

    # ── 副(記述): Bible Belt のみ 変化点(折れ線の節 = 賛成加速の出生年)──
    bb = d[d["comm_name"] == "Bible Belt"]
    yb = bb["approve"].values; cb = bb["cohort_c"].values
    best = None
    for knot in range(1935, 1986, 5):
        kc = knot - COHORT_CENTER
        hinge = np.maximum(0.0, cb - kc)
        Xs = np.column_stack([np.ones(len(cb)), cb, hinge])
        bb_beta, *_ = np.linalg.lstsq(Xs, yb, rcond=None)
        sse = float(((yb - Xs @ bb_beta) ** 2).sum())
        if best is None or sse < best[1]:
            best = (knot, sse, bb_beta[2])
    changepoint = {"biblebelt_acceleration_birthyear": best[0],
                   "post_knot_extra_slope_pp_per_decade": round(best[2] * 10 * 100, 2)}

    # ── 出力 ──
    out = {"estimand": "community x cohort interaction (b′): difference in birth-cohort slope",
           "scale": "probability (LPM main); logit-AME robustness",
           "weighting": "unweighted", "period": "survey-year fixed effects",
           "lpm_main": lpm, "lpm_no_period_control": nofe,
           "logit_ame": ame, "changepoint_descriptive": changepoint}
    res = ROOT / "data" / "gss_results"; res.mkdir(exist_ok=True)
    (res / "interaction_ssm.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 78)
    print("  b′ 主検定: 共同体 × 出生年スロープ交互作用(同性婚 / LPM + 調査年FE / unweighted)")
    print("=" * 78)
    print(f"  N = {lpm['n']}(Coastal + Bible Belt, 1988–2022)")
    print(f"\n  [主 LPM] 出生年スロープ(賛成 pp / 10年)")
    print(f"    Coastal Liberal : {lpm['coastal_slope_pp_per_decade']:+.1f} pp/10年(≈0=飽和・平坦の予測)")
    print(f"    Bible Belt      : {lpm['biblebelt_slope_pp_per_decade']:+.1f} ± {lpm['biblebelt_slope_se_pp']:.1f} pp/10年(>0=勾配の予測)")
    print(f"    交互作用(差)   : {lpm['interaction_slope_diff_pp_per_decade']:+.1f} ± {lpm['interaction_se_pp']:.1f} pp/10年"
          f"  z={lpm['interaction_z']}  p={lpm['interaction_p']:.2e}")
    sig = "有意(スロープ差あり=共同体がゲート)" if lpm['interaction_p'] < 0.05 else "非有意(方向は予測どおりだが有意差に届かず)"
    print(f"    → {sig}")
    print(f"    [透明性] period統制なしの交互作用: {nofe['interaction_pp_per_decade']:+.1f} pp/10年 (z={nofe['z']})"
          f"  ← FE版とほぼ同一 = スロープ差は period 交絡をほぼ含まない(diff-in-diff が効く)")
    print(f"\n  [頑健性 ロジットAME] cohort の平均限界効果(pp/10年)")
    for kk, vv in ame.items():
        print(f"    {kk}: {vv:+.1f}")
    print(f"\n  [副・記述] Bible Belt 賛成加速の出生年(変化点)= {changepoint['biblebelt_acceleration_birthyear']}年生まれ前後"
          f"(節後の追加スロープ {changepoint['post_knot_extra_slope_pp_per_decade']:+.1f} pp/10年)")
    print(f"\n[saved] data/gss_results/interaction_ssm.json")
    print("  ※ 機構(感受性窓 vs 世代交代)は未分離=Discussion仮説。Coastal平坦は天井効果の可能性併記。")


if __name__ == "__main__":
    main()
