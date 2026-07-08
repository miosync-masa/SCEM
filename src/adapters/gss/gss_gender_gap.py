#!/usr/bin/env python3
"""
gss_gender_gap.py — V1: GSS 態度の gender gap × 性別拡張グリッド(GFR / emphasis距離)の事象横断照合。

問い(プロダクト側検証・現行論文には入れない):
  grid の Gendered Mode Flip Rate / Gendered Emphasis Distance は、
  GSS 上の態度 gender gap と事象横断で対応するか。

事前固定(最小仮説・実行前に宣言):
  H1: |gap(gunlaw)| > |gap(abany)|      … GSS 側の古典的知見の再確認
  Prediction: grid 側の GFR / emphasis距離も gun/mass-shooting > Dobbs/abortion の順。

方針(巴レビュー):
  - まず絶対値(gap の大きさ)。方向(どちらが支持的か)は第二段階の記述。
  - 単純版 = pooled mean(female) - mean(male)。period をならす版 = 調査年内 gap の N加重平均(年FE同等)。
  - outcome コーディングは既存規約を再利用(ssm_approve / abany・gunlaw の {1,2}→{1,0})。
  - unweighted(リポジトリの GSS 規約に従う)。記述統計 + rank 対応が目的。精密推定はしない。

対応表(最小3事象):
  gunlaw ↔ us_sandy_hook_2012 / abany ↔ us_dobbs_2022 / ssm(spliced) ↔ us_obergefell_2015

Run: python3 src/adapters/gss/gss_gender_gap.py
出力: data/gss_results/gender_gap_by_event.csv / gender_gap_overlay.csv / gender_gap_summary.json
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
sys.path.insert(0, str(ROOT / "src" / "adapters" / "gss"))
import gss_segments as SEG   # ssm_approve(3変数接続)を再利用

DATA = ROOT / "data"
OUT = DATA / "gss_results"

# 事前固定の対応表(grid 事象 ↔ GSS item)。Trump は GSS 側にきれいな変数が無いため V1 から除外。
MAPPING = [
    ("gunlaw", "us_sandy_hook_2012", "Sandy Hook / gun control"),
    ("abany",  "us_dobbs_2022",      "Dobbs / abortion (any reason)"),
    ("ssm",    "us_obergefell_2015", "Obergefell / same-sex marriage"),
]


def outcomes(df: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "gunlaw": df["gunlaw"].map({1: 1.0, 2: 0.0}),   # 銃所持許可制に賛成(=規制支持)
        "abany":  df["abany"].map({1: 1.0, 2: 0.0}),    # 任意の理由での中絶に賛成
        "ssm":    SEG.ssm_approve(df).astype("float"),   # 同性婚賛成(marsame 3変数接続)
    }


def gap_stats(y: pd.Series, female: pd.Series, year: pd.Series) -> dict:
    """pooled gap と 年FE同等(調査年内gapのN加重平均)。SE は二項近似(記述用)。"""
    m = y.notna() & female.notna()
    y, female, year = y[m], female[m], year[m]
    f, ml = y[female], y[~female]
    pooled = f.mean() - ml.mean()
    se = math.sqrt(f.mean() * (1 - f.mean()) / len(f) + ml.mean() * (1 - ml.mean()) / len(ml))
    # 年内 gap の N加重平均(period をならす)
    per_year = []
    for yr, g in y.groupby(year):
        fem = female[g.index]
        if fem.sum() >= 10 and (~fem).sum() >= 10:
            per_year.append((len(g), g[fem].mean() - g[~fem].mean()))
    year_adj = sum(n * v for n, v in per_year) / sum(n for n, _ in per_year)
    return {"n_female": int(len(f)), "n_male": int(len(ml)),
            "mean_female": round(float(f.mean()), 4), "mean_male": round(float(ml.mean()), 4),
            "gap_pooled": round(float(pooled), 4), "gap_se": round(float(se), 4),
            "gap_year_adjusted": round(float(year_adj), 4),
            "abs_gap": round(abs(float(year_adj)), 4)}


def main():
    df = pd.read_parquet(DATA / "gss" / "gss_slim.parquet")
    female = df["sex"] == 2      # GSS: 1=male, 2=female
    ys = outcomes(df)

    rows = {}
    for item, s in ys.items():
        rows[item] = gap_stats(s, female, df["year"])

    grid = json.loads((DATA / "gender_grid_metrics_us.json").read_text(encoding="utf-8"))
    gfr = grid["gfr_by_event"]
    emphd = grid["emphasis_distance_by_event"]

    print("=" * 88)
    print("  V1 — GSS gender gap × gender-grid (GFR / emphasis distance), event-matched")
    print("=" * 88)
    print(f"\n  {'item':<8}{'grid event':<28}{'|gap|(yrFE)':>12}{'dir(F-M)':>10}{'GFR':>7}{'emphΔ':>8}")
    overlay = []
    for item, eid, label in MAPPING:
        g = rows[item]
        print(f"  {item:<8}{label:<28}{g['abs_gap']:>12.3f}{g['gap_year_adjusted']:>+10.3f}"
              f"{gfr[eid]:>7.0%}{emphd[eid]:>8.2f}")
        overlay.append({"gss_item": item, "grid_event": eid, "label": label, **g,
                        "grid_gfr": gfr[eid], "grid_emphasis_distance": emphd[eid]})

    # ── 事前固定 H1 + rank 対応 ──
    by = {o["gss_item"]: o for o in overlay}
    h1 = by["gunlaw"]["abs_gap"] > by["abany"]["abs_gap"]
    rank_gfr = by["gunlaw"]["grid_gfr"] > by["abany"]["grid_gfr"]
    rank_emph = by["gunlaw"]["grid_emphasis_distance"] > by["abany"]["grid_emphasis_distance"]

    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0] * len(vals)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    gss_r = ranks([o["abs_gap"] for o in overlay])
    gfr_r = ranks([o["grid_gfr"] for o in overlay])
    emph_r = ranks([o["grid_emphasis_distance"] for o in overlay])
    concord_gfr = gss_r == gfr_r
    concord_emph = gss_r == emph_r

    print(f"\n  Pre-fixed H1  |gap(gunlaw)| > |gap(abany)|            : "
          f"{'satisfied' if h1 else 'NOT satisfied'} "
          f"({by['gunlaw']['abs_gap']:.3f} vs {by['abany']['abs_gap']:.3f})")
    print(f"  Prediction    grid GFR      gun > abortion             : "
          f"{'satisfied' if rank_gfr else 'NOT satisfied'}")
    print(f"  Prediction    grid emphasis gun > abortion             : "
          f"{'satisfied' if rank_emph else 'NOT satisfied'}")
    print(f"  Rank order (3 events, GSS |gap| vs grid GFR)           : "
          f"{'concordant' if concord_gfr else 'discordant'}")
    print(f"  Rank order (3 events, GSS |gap| vs emphasis distance)  : "
          f"{'concordant' if concord_emph else 'discordant'}")
    print("\n  ※ n=3 事象の記述的 rank 対応。強度は『予測対応(preliminary correspondence)』止まり。"
          "\n  ※ 方向(dir): 正 = 女性の方が支持的。")

    OUT.mkdir(exist_ok=True)
    pd.DataFrame([{"gss_item": k, **v} for k, v in rows.items()]).to_csv(
        OUT / "gender_gap_by_event.csv", index=False)
    pd.DataFrame(overlay).to_csv(OUT / "gender_gap_overlay.csv", index=False)
    (OUT / "gender_gap_summary.json").write_text(json.dumps({
        "prefixed_H1_satisfied": bool(h1),
        "prediction_gfr_satisfied": bool(rank_gfr),
        "prediction_emphasis_satisfied": bool(rank_emph),
        "rank_concordant_gfr": bool(concord_gfr),
        "rank_concordant_emphasis": bool(concord_emph),
        "overlay": overlay,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] gss_results/gender_gap_by_event.csv / gender_gap_overlay.csv / gender_gap_summary.json")


if __name__ == "__main__":
    main()
