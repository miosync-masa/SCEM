#!/usr/bin/env python3
"""
gss_core_contrast.py — コア対比(spec §7 開始点・確定):
  Coastal Liberal(REFRAME 予測) vs Bible Belt(ACTIVE 予測) の同性婚態度プロファイルを
  出生年コホート別に**記述的に**描く。

Coastal の薄 N 対処(真道さま決定 2026-06-26, 案β+γ・graduate 維持・α却下):
  - **α(graduate→bachelor+ に緩める)は採らない**。"graduate" は CMR の premise 弁別記号
    (secular_white_coastal_**graduate**)であり、緩めると Suburban MC(..._suburban_bachelor)と
    学歴軸で被る。N の都合で理論定義を上書きするのは Non-overwrite 違反に近い。定義は graduate 維持。
  - **γ:** Coastal は「**平坦高位**(REFRAME 署名)」を**プール**で主張。出生年の細かい勾配は主張しない。
  - **β:** Coastal は**10 年刻み**(粗く N を稼ぐ)。平坦は解像度を落としても平坦=署名は消えない。
  - Bible Belt は N 厚いので **5 年刻みで勾配**を堂々と描く。
  - 非対称(Coastal 薄・平坦 / Bible Belt 厚・勾配)は予測と整合(REFRAME=争点ですらない vs ACTIVE=前線)。

重要(Non-overwrite / spec 6.3-6.6 は未決):
  - shift/polarization の**検定統計量**(6.3/6.4)、period(6.5)、多重比較(6.6)は **未決→未実装**。
  - 本スクリプトは記述 + **Wilson 95%信頼区間**(指摘#1「平坦は本物か薄Nのブレか」への不確実性付与。
    CI は検定統計量ではなく記述への誤差棒)。
  - 重みは未適用(〜2018 wtssall / 2021+ wtssps の波跨ぎ統合は 6.5 の射程)= **unweighted**。
  - 低 N ビンは捨てず明示(Honest Structuralism)。

Run: python3 src/gss_core_contrast.py   (先に src/gss_acquire.py で data/gss/gss_slim.parquet を用意)
出力: figures/gss_core_contrast_ssm.png / data/gss_results/core_contrast_ssm.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gss_segments as G

ROOT = Path(__file__).resolve().parent.parent
SLIM = ROOT / "data" / "gss" / "gss_slim.parquet"
MIN_N = 20          # これ未満のコホートビンは「N不足」として点線/中抜きで表示(捨てない)

# 真道さま決定(案β+γ): Coastal は graduate 維持・10年刻み・平坦高位をプールで主張 /
#                        Bible Belt は 5年刻みで勾配。width を共同体ごとに変える。
PAIR = [("Coastal Liberal", "REFRAME予測", "#2e8b57", 10),
        ("Bible Belt",      "ACTIVE予測",  "#c0392b", 5)]


def wilson(k, n, z=1.96):
    """Wilson 95% 信頼区間(二項比率)。薄 N でも端点が 0/1 を突き抜けない。"""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5 / d
    return (max(0.0, c - h), min(1.0, c + h))


def profile(df, name, width):
    sub = df[G.segment_mask(df, name)].copy()
    sub["approve"] = G.ssm_approve(sub)
    sub["cohort_bin"] = G.cohort_bin(sub, width)
    sub = sub.dropna(subset=["approve", "cohort_bin"])
    g = sub.groupby("cohort_bin")["approve"]
    out = pd.DataFrame({"approval": g.mean(), "n": g.size(), "k": g.sum()})
    out.index = out.index.astype(int)
    ci = [wilson(int(r.k), int(r.n)) for r in out.itertuples()]
    out["lo"] = [c[0] for c in ci]
    out["hi"] = [c[1] for c in ci]
    # プール推定(γ): 全コホート合算の賛成率 + CI
    k, n = int(sub["approve"].sum()), int(sub["approve"].notna().sum())
    pooled = (k / n, *wilson(k, n))
    return out, len(sub), sorted(sub.year.dropna().astype(int).unique().tolist()), pooled, width


def main():
    if not SLIM.exists():
        raise SystemExit(f"[error] {SLIM} が無い。先に: python3 src/gss_acquire.py")
    df = pd.read_parquet(SLIM)

    plt.rcParams["font.family"] = "Hiragino Sans"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(9, 5.5))

    rows = []
    print("=" * 80)
    print("  GSS コア対比(記述+Wilson95%CI): 同性婚 賛成率 × 出生年コホート  [unweighted]")
    print("  Coastal Liberal(REFRAME予測, graduate維持・10年刻み・平坦高位)")
    print("  vs Bible Belt(ACTIVE予測, 5年刻み・勾配)")
    print("=" * 80)
    for name, pred, color, width in PAIR:
        prof, n_total, years, pooled, w = profile(df, name, width)
        print(f"\n── {name}  [{pred}]  marsame非欠損 N={n_total}  幅={w}年  波={years}")
        print(f"   プール賛成率(γ): {pooled[0]:.0%}  95%CI[{pooled[1]:.0%}, {pooled[2]:.0%}]")
        for cb, r in prof.iterrows():
            flag = "  ⚠N不足" if r["n"] < MIN_N else ""
            print(f"   生{cb}-{cb+w-1}: 賛成 {r['approval']:.0%}  CI[{r['lo']:.0%},{r['hi']:.0%}]  (N={int(r['n'])}){flag}")
            rows.append({"segment": name, "prediction": pred, "cohort_bin": int(cb), "bin_width": w,
                         "approval": round(r["approval"], 4), "ci_lo": round(r["lo"], 4),
                         "ci_hi": round(r["hi"], 4), "n": int(r["n"]), "low_n": bool(r["n"] < MIN_N),
                         "pooled_approval": round(pooled[0], 4),
                         "pooled_ci_lo": round(pooled[1], 4), "pooled_ci_hi": round(pooled[2], 4)})
        x = prof.index + w / 2          # ビン中心
        yerr = [prof["approval"] - prof["lo"], prof["hi"] - prof["approval"]]
        ax.errorbar(x, prof["approval"], yerr=yerr, fmt="-o", color=color, capsize=3,
                    label=f"{name}({pred}, {w}年)")
    # Coastal のプール平坦高位を帯で重ねる(γ の可視化)
    cprof, _, _, cpooled, _ = profile(df, "Coastal Liberal", 10)
    ax.axhspan(cpooled[1], cpooled[2], color="#2e8b57", alpha=0.10)
    ax.axhline(cpooled[0], color="#2e8b57", ls="--", lw=1, alpha=0.6)

    ax.set_xlabel("出生年コホート(ビン中心。Coastal=10年 / Bible Belt=5年)")
    ax.set_ylabel("同性婚 賛成率(marsame/marsame1 接続, agree=1,2)")
    ax.set_ylim(0, 1)
    ax.set_title("コア対比(記述+Wilson95%CI・unweighted): 同性婚 賛成率 × 出生年コホート\n"
                 "Coastal=平坦高位(緑帯=プールCI, 10年刻み, graduate維持) / Bible Belt=勾配(5年刻み)。"
                 "検定は未実装(spec 6.3-6.6 未決)", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_png = ROOT / "figures" / "gss_core_contrast_ssm.png"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close(fig)

    res = ROOT / "data" / "gss_results"
    res.mkdir(exist_ok=True)
    out_csv = res / "core_contrast_ssm.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\n[saved] {out_png.relative_to(ROOT)}")
    print(f"[saved] {out_csv.relative_to(ROOT)}")
    print("\n※ 記述のみ。REFRAME=早期立ち上がり / ACTIVE=分散拡大 の検定は次セッションで統計量確定後に実装。")


if __name__ == "__main__":
    main()
