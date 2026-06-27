#!/usr/bin/env python3
"""
ess_southern_country.py — Southern Europe freehms b′ の国別分解(依頼 2026-06-27)。

目的:step1.5 の Southern クラスタ religious-lowedu スロープ(z=11.78)が複数国一貫か1国偏りか。
判定(事前固定・後付けしない):
  複数国で正勾配一貫 → Southern 一般化OK(金脈確定)
  1国突出・他ゼロ     → その国固有、一般化しない
  正負混在            → クラスタ集約アーチファクト、b′ 主張から降ろす

作法:単国 → round FE のみ。飽和近傍(pool>=0.90)はスロープ不安定 → 解釈しない(水準のみ)。
N 明記・薄い国は弱主張。変化点併走(B)。spin しない・確証と書かない。

Run: python3 src/ess_southern_country.py
出力: data/ess_results/southern_country.csv / .json
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ess_segments as S
from ess_core_validation import wls_slope, changepoint, wmean_ci, CENTER

ROOT = Path(__file__).resolve().parent.parent
SLIM = ROOT / "data" / "ess" / "ess_slim.parquet"
SOUTH = ["ES", "PT", "IT", "GR", "CY", "MT"]
THIN_N = 150            # これ未満は弱主張(CI で正直に)


def cell(d, seg):
    sub = d[S.segment_mask(d, seg)].copy()
    sub["_y"] = S.freehms_tolerant(sub)
    sub["cohort_c"] = (S.cohort_bin(sub, 1) - CENTER)
    sub["_w"] = S.weight(sub)
    valid = sub.dropna(subset=["_y"])
    n = len(valid)
    if n < 40:
        return {"n": n, "pool": None, "slope": None, "z": None, "knot": None, "note": "N不足"}
    pool, lo, hi, _ = wmean_ci(valid["_y"], valid["_w"])
    sl, se, _ = wls_slope(sub, "_y")            # 単国 → round FE のみ
    cp = changepoint(sub, "_y")
    saturated = (pool >= 0.90)
    return {"n": n, "pool": round(pool, 3), "ci": [round(lo, 3), round(hi, 3)],
            "slope_pp_decade": None if (math.isnan(sl) or saturated) else round(sl * 1000, 1),
            "slope_z": None if (math.isnan(sl) or se == 0 or saturated) else round(sl / se, 2),
            "saturated": saturated, "knot": cp.get("knot"), "cp_improve": cp.get("sse_improve_vs_linear"),
            "thin": n < THIN_N}


def verdict(s):
    """Religious-LowEdu のスロープ方向判定(飽和/N不足は除外)。"""
    if s["slope_z"] is None:
        return "飽和/N不足(除外)"
    if s["slope_z"] >= 1.96 and s["slope_pp_decade"] > 0:
        return "正勾配(移行中)"
    if s["slope_z"] <= -1.96 and s["slope_pp_decade"] < 0:
        return "負勾配"
    return "ゼロ(有意でない)"


def main():
    if not SLIM.exists():
        raise SystemExit("先に ESS_USER_ID=... python3 src/ess_acquire.py")
    df = pd.read_parquet(SLIM)
    present = [c for c in SOUTH if c in set(df["cntry"].astype(str))]

    rows = []
    print("=" * 96)
    print("  Southern Europe freehms b′ 国別分解(Religious LowEdu スロープ + Secular 水準)")
    print("  判定: 複数国で正勾配一貫→一般化 / 1国突出→国固有 / 正負混在→集約アーチ(b′降ろす)")
    print("=" * 96)
    print(f"\n  {'国':<4}{'Rel N':>7}{'Rel寛容':>9}{'Relスロープ(z)':>16}  {'判定':<18}{'Sec N':>7}{'Sec寛容':>9}")
    for c in present:
        d = df[df["cntry"].astype(str) == c]
        rel = cell(d, "Religious LowEdu")
        sec = cell(d, "Secular HiEdu Urban")
        v = verdict(rel)
        rows.append({"country": c, "religious": rel, "secular": sec, "verdict": v})
        rel_sl = "—" if rel["slope_pp_decade"] is None else f"{rel['slope_pp_decade']:+.1f}({rel['slope_z']})"
        relp = "—" if rel["pool"] is None else f"{rel['pool']:.0%}"
        secp = "—" if sec["pool"] is None else f"{sec['pool']:.0%}"
        thin = " ⚠薄" if rel.get("thin") else ""
        print(f"  {c:<4}{rel['n']:>7}{relp:>9}{rel_sl:>16}  {v:<18}{sec['n']:>7}{secp:>9}{thin}")

    # ── 事前固定判定の集計 ──
    vs = [r["verdict"] for r in rows]
    pos = sum(v.startswith("正勾配") for v in vs)
    neg = sum(v.startswith("負勾配") for v in vs)
    zero = sum(v.startswith("ゼロ") for v in vs)
    excl = sum(v.startswith("飽和") for v in vs)
    scored = pos + neg + zero
    print("\n" + "-" * 96)
    print(f"  判定対象(飽和/N不足除外後)= {scored}国: 正勾配 {pos} / ゼロ {zero} / 負勾配 {neg}")
    if neg > 0 and pos > 0:
        concl = "正負混在 → クラスタ集約アーチファクトの疑い。b′ 主張から降ろす(事前基準)"
    elif pos >= 2 and neg == 0:
        concl = f"複数国({pos})で正勾配一貫 → Southern 一般化OK(b′ 金脈確定)"
    elif pos == 1 and zero >= 1:
        concl = "1国突出・他ゼロ → その国固有として記述、一般化しない(事前基準)"
    else:
        concl = "判定保留(N/飽和で対象国少)。弱主張・要追加データ"
    print(f"  → {concl}")
    print("  ※ 単国=round FE のみ・GR/CY は 2 波で period 統制弱・Secular は国別 N 薄(水準のみ)。spin しない。")

    res = ROOT / "data" / "ess_results"; res.mkdir(exist_ok=True)
    pd.DataFrame([{"country": r["country"], "verdict": r["verdict"],
                   **{f"rel_{k}": r["religious"].get(k) for k in ("n", "pool", "slope_pp_decade", "slope_z", "knot", "saturated", "thin")},
                   **{f"sec_{k}": r["secular"].get(k) for k in ("n", "pool", "saturated")}} for r in rows]
                 ).to_csv(res / "southern_country.csv", index=False)
    (res / "southern_country.json").write_text(json.dumps(
        {"present": present, "verdict_counts": {"pos": pos, "zero": zero, "neg": neg, "excluded": excl},
         "conclusion": concl, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] data/ess_results/southern_country.csv / .json")


if __name__ == "__main__":
    main()
