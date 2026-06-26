#!/usr/bin/env python3
"""
gss_core_contrast.py — コア対比(spec §7 開始点・確定):
  Coastal Liberal(REFRAME 予測) vs Bible Belt(ACTIVE 予測) の同性婚態度プロファイルを
  出生年コホート別に**記述的に**描く。

重要(Non-overwrite / spec 6.3-6.6 は未決):
  - 本スクリプトは **記述統計のみ**。shift/polarization の検定統計量(6.3/6.4)、period の扱い(6.5)、
    多重比較(6.6)は **未決**なので一切実装しない。曲線と N を出して、次セッションの判断材料にする。
  - 重み付けは未適用(GSS は 〜2018 wtssall / 2021+ wtssps と weight 体系が変わり、波跨ぎ統合は
    設計判断。spec 6.5 の射程)。よって本図は **unweighted**。これは精緻化の余地として明示する。
  - 低 N ビンは捨てずに「N 不足」として明示(Honest Structuralism。silent truncation しない)。

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
COHORT_W = 5

PAIR = [("Coastal Liberal", "REFRAME予測", "#2e8b57"),
        ("Bible Belt", "ACTIVE予測", "#c0392b")]


def profile(df, name):
    sub = df[G.segment_mask(df, name)].copy()
    sub["approve"] = G.ssm_approve(sub)
    sub["cohort_bin"] = G.cohort_bin(sub, COHORT_W)
    sub = sub.dropna(subset=["approve", "cohort_bin"])
    g = sub.groupby("cohort_bin")["approve"]
    out = pd.DataFrame({"approval": g.mean(), "n": g.size()})
    out.index = out.index.astype(int)
    return out, len(sub), sorted(sub.year.dropna().astype(int).unique().tolist())


def main():
    if not SLIM.exists():
        raise SystemExit(f"[error] {SLIM} が無い。先に: python3 src/gss_acquire.py")
    df = pd.read_parquet(SLIM)

    plt.rcParams["font.family"] = "Hiragino Sans"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(9, 5.5))

    rows = []
    print("=" * 76)
    print("  GSS コア対比(記述): 同性婚 賛成率 × 出生年コホート  [unweighted]")
    print("  Coastal Liberal(REFRAME予測) vs Bible Belt(ACTIVE予測)")
    print("=" * 76)
    for name, pred, color in PAIR:
        prof, n_total, years = profile(df, name)
        print(f"\n── {name}  [{pred}]  marsame非欠損 N={n_total}  波={years}")
        for cb, r in prof.iterrows():
            flag = "  ⚠N不足" if r["n"] < MIN_N else ""
            print(f"   生{cb}-{cb+COHORT_W-1}: 賛成 {r['approval']:.0%}  (N={int(r['n'])}){flag}")
            rows.append({"segment": name, "prediction": pred, "cohort_bin": cb,
                         "approval": round(r["approval"], 4), "n": int(r["n"]),
                         "low_n": bool(r["n"] < MIN_N)})
        solid = prof[prof.n >= MIN_N]
        thin = prof[prof.n < MIN_N]
        ax.plot(solid.index, solid["approval"], "-o", color=color, label=f"{name}({pred})")
        ax.plot(thin.index, thin["approval"], ":o", color=color, mfc="white", alpha=0.6)

    ax.set_xlabel("出生年コホート(5年刻みの下端)")
    ax.set_ylabel("同性婚 賛成率(marsame/marsame1 接続, agree=1,2)")
    ax.set_ylim(0, 1)
    ax.set_title("コア対比(記述・unweighted): 同性婚 賛成率 × 出生年コホート\n"
                 "実線=N>=20 / 点線中抜き=N<20(N不足・参考)。検定は未実装(spec 6.3-6.6 未決)",
                 fontsize=11)
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
