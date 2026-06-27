#!/usr/bin/env python3
"""
ess_effective_year.py — freehms 変化点/スロープ × 国の LGBT 制度モーメント年(依頼 2026-06-27)。

目的:「事象の着弾年(effective_year)が国で違う → REFRAME 移行段階が違う → スロープ可視性が違う」を検証。
     = Paper1 effective_year + Paper3 (c)時間発展 の同時裏取り。**探索的(国 n 小・操作化に幅)→ suggestive 止まり。**

判定(事前固定・後付けしない):
  制度年と変化点/スロープに単調対応 → effective_year が移行段階を駆動=(c)時間発展支持(強いが exploratory)
  バラバラ                          → ESS では支持されず・正直に保留
  サンプル薄国(Rel N<300)は判定除外・N明記。飽和近傍スロープ除外(過適合)。

⚠️ 制度年は公的立法記録に基づく**著者コーディング**。論文化前に一次資料で要検証(注に出典)。
   recognition_year = 同性カップルへの最初の実質的国法上の地位(登録パートナー or 婚姻)。None=2024時点で無し。
   ssm_year = 同性婚合法化年(感度用。シビルユニオン先行国は両方見る)。

作法:制度年=事象の着弾年であって個人の mode でない(混同しない)。変化点閾値は本体分解と同一。
     spin しない・確証と書かない・綻び記録。
Run: python3 src/ess_effective_year.py → data/ess_results/effective_year.csv / .json / figures/ess_effective_year.png
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Hiragino Sans"; plt.rcParams["axes.unicode_minus"] = False

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ess_segments as S
from ess_core_validation import wls_slope, changepoint, wmean_ci, CENTER

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
SLIM = ROOT / "data" / "ess" / "ess_slim.parquet"
MIN_N = 300
NONE_SENTINEL = 2030     # 2024時点で制度なし=「まだ/very late」の代理(感度で別集計)

# (recognition_year, ssm_year)。None=無し。⚠️論文化前に一次資料で検証。
LEGAL = {
    "DK": (1989, 2012), "NO": (1993, 2009), "SE": (1995, 2009), "IS": (1996, 2010),
    "NL": (1998, 2001), "FR": (1999, 2013), "BE": (2000, 2003), "DE": (2001, 2017),
    "FI": (2002, 2017), "GB": (2005, 2014), "ES": (2005, 2005), "CZ": (2006, None),
    "SI": (2006, 2022), "CH": (2007, 2022), "HU": (2009, None), "AT": (2010, 2019),
    "PT": (2010, 2010), "IE": (2011, 2015), "HR": (2014, None), "CY": (2015, None),
    "GR": (2015, 2024), "IT": (2016, None), "EE": (2016, 2024), "ME": (2021, None),
    "LV": (2024, None), "IL": (None, None), "PL": (None, None), "LT": (None, None),
    "SK": (None, None), "BG": (None, None), "RS": (None, None), "MK": (None, None),
    "RU": (None, None),
}


def rank(a):
    order = np.argsort(a, kind="mergesort"); r = np.empty(len(a)); r[order] = np.arange(len(a))
    # 平均順位(タイ)
    a = np.asarray(a, float)
    for v in np.unique(a):
        m = a == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~np.isnan(x) & ~np.isnan(y)
    if m.sum() < 4:
        return float("nan"), int(m.sum())
    rx, ry = rank(x[m]), rank(y[m])
    rx, ry = rx - rx.mean(), ry - ry.mean()
    denom = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return (float((rx * ry).sum() / denom) if denom > 0 else float("nan")), int(m.sum())


def rel_cell(d):
    sub = d[S.segment_mask(d, "Religious LowEdu")].copy()
    sub["_y"] = S.freehms_tolerant(sub); sub["cohort_c"] = (S.cohort_bin(sub, 1) - CENTER); sub["_w"] = S.weight(sub)
    valid = sub.dropna(subset=["_y"]); n = len(valid)
    if n < 40:
        return None
    pool = wmean_ci(valid["_y"], valid["_w"])[0]
    sl, se, _ = wls_slope(sub, "_y"); cp = changepoint(sub, "_y")
    sat = pool >= 0.90
    return {"n": n, "pool": round(pool, 3),
            "slope_z": None if (math.isnan(sl) or se == 0 or sat) else round(sl / se, 2),
            "slope_pp": None if (math.isnan(sl) or sat) else round(sl * 1000, 1),
            "knot": cp.get("knot"), "cp_improve": cp.get("sse_improve_vs_linear"), "thin": n < 500}


def main():
    if not SLIM.exists():
        raise SystemExit("先に ESS_USER_ID=... python3 src/ess_acquire.py")
    df = pd.read_parquet(SLIM)
    rows = []
    for c in sorted(set(df["cntry"].astype(str))):
        if c not in LEGAL:
            continue
        r = rel_cell(df[df["cntry"].astype(str) == c])
        if not r or r["n"] < MIN_N:
            continue
        rec, ssm = LEGAL[c]
        rows.append({"country": c, "recognition_year": rec, "ssm_year": ssm,
                     "rec_eff": rec if rec else NONE_SENTINEL, **r})
    R = pd.DataFrame(rows).sort_values("rec_eff")

    print("=" * 100)
    print("  freehms 変化点/スロープ × LGBT 制度モーメント年(Religious LowEdu, 探索的)")
    print("  予測: 制度年が遅い/無い国ほど 移行中(正スロープ大・変化点が若い)。早い国ほど 完了(スロープ~0)")
    print("=" * 100)
    print(f"\n  {'国':<4}{'承認年':>7}{'同性婚':>7}{'Rel N':>7}{'寛容':>7}{'スロープz':>10}{'変化点':>8}")
    for _, r in R.iterrows():
        rec = r["recognition_year"] if r["recognition_year"] else "無"
        ssm = r["ssm_year"] if r["ssm_year"] else "無"
        z = "—(飽和)" if r["slope_z"] is None else f"{r['slope_z']:+.1f}"
        print(f"  {r['country']:<4}{str(rec):>7}{str(ssm):>7}{r['n']:>7}{r['pool']:>7.0%}{z:>10}{str(r['knot']):>8}"
              + ("  ⚠薄" if r["thin"] else ""))

    # 相関(事前固定):recognition_year(sentinel込) vs slope_z / 変化点年
    sp_z, n1 = spearman(R["rec_eff"], R["slope_z"])
    sp_k, n2 = spearman(R["rec_eff"], R["knot"])
    # 制度ありの国のみ(sentinel 除外)で頑健性
    leg = R[R["recognition_year"].notna()]
    sp_z_leg, n3 = spearman(leg["rec_eff"], leg["slope_z"])
    # 感度:effective_year を「承認年」でなく「同性婚年」にした版(操作化の幅を潰す)
    R["ssm_eff"] = R["ssm_year"].fillna(NONE_SENTINEL)
    sp_z_ssm, n4 = spearman(R["ssm_eff"], R["slope_z"])
    sp_k_ssm, n5 = spearman(R["ssm_eff"], R["knot"])
    print("\n" + "-" * 100)
    print(f"  Spearman(承認年 vs スロープz)= {sp_z:+.2f} (n={n1})  ※予測:正(遅い国ほど正スロープ大)")
    print(f"  Spearman(承認年 vs 変化点出生年)= {sp_k:+.2f} (n={n2})  ※予測:正(遅い国ほど若い変化点)")
    print(f"  制度あり国のみ Spearman(承認年 vs スロープz)= {sp_z_leg:+.2f} (n={n3})")
    print(f"  [感度] 同性婚年版 Spearman(婚姻年 vs スロープz)= {sp_z_ssm:+.2f} (n={n4}) / vs 変化点= {sp_k_ssm:+.2f}")
    print(f"         → 承認年版と同符号・近似なら操作化(パートナー vs 婚姻)に頑健")

    # 事前固定判定
    if not math.isnan(sp_z) and sp_z >= 0.4:
        concl = f"単調対応あり(ρ={sp_z:+.2f}) → effective_year が移行段階を駆動=(c)時間発展 支持(exploratory/suggestive)"
    elif not math.isnan(sp_z) and abs(sp_z) < 0.2:
        concl = f"対応バラバラ(ρ={sp_z:+.2f}) → ESS では支持されず・正直に保留"
    else:
        concl = f"弱い対応(ρ={sp_z:+.2f}) → suggestive 止まり・保留寄り"
    print(f"  → {concl}")
    print("  ※ 制度年=事象着弾年であって個人 mode でない。制度年は著者コーディング(論文化前に一次資料で要検証)。")
    print("  ※ 探索的(国 n 小・操作化に幅・GR/CY 等 2 波)→ 確証と書かない。")

    res = ROOT / "data" / "ess_results"; res.mkdir(exist_ok=True)
    R.to_csv(res / "effective_year.csv", index=False)
    (res / "effective_year.json").write_text(json.dumps(
        {"spearman_rec_vs_slopez": round(sp_z, 3), "spearman_rec_vs_knot": round(sp_k, 3),
         "spearman_legalized_only": round(sp_z_leg, 3),
         "sensitivity_ssm_vs_slopez": round(sp_z_ssm, 3), "sensitivity_ssm_vs_knot": round(sp_k_ssm, 3),
         "conclusion": concl, "n_countries": len(R), "rows": rows,
         "coding_source": "docs/ess_legal_coding.md (verified vs Wikipedia 'Recognition of same-sex unions in Europe' which cites national legislation, + ILGA-Europe). Definitional choices documented there."},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # 散布図
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    sub = R[R["slope_z"].notna()]
    ax.scatter(sub["rec_eff"], sub["slope_z"], s=40, c="#c0392b")
    for _, r in sub.iterrows():
        ax.annotate(r["country"], (r["rec_eff"], r["slope_z"]), fontsize=8,
                    xytext=(3, 3), textcoords="offset points")
    ax.axhline(0, color="#888", lw=0.8); ax.axvline(NONE_SENTINEL, color="#bbb", ls=":", lw=0.8)
    ax.text(NONE_SENTINEL, ax.get_ylim()[1], "制度なし→", fontsize=7, ha="right", va="top", color="#888")
    ax.set_xlabel("LGBT 承認年(登録パートナー/婚姻の早い方。2030=制度なし)")
    ax.set_ylabel("freehms 出生年スロープ z(Religious LowEdu)")
    ax.set_title(f"effective_year × 移行段階(Religious LowEdu, 探索的)\n"
                 f"Spearman(承認年, スロープz)= {sp_z:+.2f} / 予測:遅い国ほど正スロープ大(移行中)", fontsize=10)
    ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(ROOT / "figures" / "ess_effective_year.png", dpi=200, bbox_inches="tight"); plt.close(fig)
    print(f"\n[saved] data/ess_results/effective_year.csv / .json / figures/ess_effective_year.png")


if __name__ == "__main__":
    main()
