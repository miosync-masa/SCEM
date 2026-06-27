#!/usr/bin/env python3
"""
ess_valuepack.py — ESS step1.5/2/3:3本柱(freehms/euftf/移民)× セグメント + country clusters。
GSS valuepack の移植。**EVENT_STRUCTURE を事前にかける**(反復イベントの flat を「CMR外れ」と誤読しない)。

依頼 §E:
  step1.5 country clusters(freehms を地域クラスタで分解 — Europe-wide 均しの影響を見る)
  step2   euftf(EU統合, 反復疑い)/ step3 immigration_index(反復濃厚)
共通:重み付き(anweight)・country+round FE・記述+CI+スロープ+変化点。検定最終確定せず(spin防止)。

Run: python3 src/ess_valuepack.py(先に ess_acquire.py)
出力: data/ess_results/valuepack_matrix.csv / freehms_clusters.csv / valuepack_summary.json
      figures/ess_valuepack.png
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ess_segments as S
from ess_core_validation import wls_slope, changepoint, wmean_ci, CENTER, COHORT_W

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
SLIM = ROOT / "data" / "ess" / "ess_slim.parquet"

SEGS = ["Secular HiEdu Urban", "Religious LowEdu", "Immigrant-bg", "Native HiEdu Urban"]

# country クラスタ(ISO2)。ESS に在るものだけ使う。
CLUSTERS = {
    "Nordic": ["SE", "NO", "DK", "FI", "IS"],
    "Western": ["GB", "IE", "FR", "NL", "BE", "DE", "AT", "CH", "LU"],
    "Southern": ["ES", "PT", "IT", "GR", "CY"],
    "Central-East": ["PL", "CZ", "SK", "HU", "SI", "EE", "LT", "LV", "HR", "BG", "RO", "RS", "ME", "MK", "AL"],
}


def wmean(y, w):
    y = np.asarray(y, float); w = np.asarray(w, float)
    m = ~np.isnan(y) & ~np.isnan(w)
    return float((y[m] * w[m]).sum() / w[m].sum()) if w[m].sum() > 0 else float("nan")


def classify(pool, sl, se, cp, binary):
    if binary and (pool >= 0.90 or pool <= 0.10):
        return "飽和/平坦(REFRAME署名)"
    if not math.isnan(sl) and sl > 0 and abs(sl) > 1.96 * se:
        return "移行中(線形)"
    if cp.get("sse_improve_vs_linear", 0) and cp["sse_improve_vs_linear"] >= 0.02:
        return "移行中(変化点のみ)"
    return "弱/不明瞭"


def analyze(df, pillar, recode, kind, seg):
    sub = df[S.segment_mask(df, seg)].copy()
    sub["_y"] = recode(sub)
    sub["cohort_c"] = (S.cohort_bin(sub, 1) - CENTER)
    sub["_w"] = S.weight(sub)
    binary = (kind == "binary")
    valid = sub.dropna(subset=["_y"])
    if binary:
        pool, lo, hi, _ = wmean_ci(valid["_y"], valid["_w"])
    else:
        pool = wmean(valid["_y"], valid["_w"]); lo = hi = float("nan")
    sl, se, n = wls_slope(sub, "_y")
    cp = changepoint(sub, "_y") if binary else changepoint_cont(sub, "_y")
    state = classify(pool, sl, se, cp, binary)
    return {"pillar": pillar, "segment": seg, "kind": kind, "n": n,
            "level": round(pool, 3), "ci_lo": None if math.isnan(lo) else round(lo, 3),
            "ci_hi": None if math.isnan(hi) else round(hi, 3),
            "slope_FE": None if math.isnan(sl) else round(sl * (1000 if binary else 10), 2),
            "slope_z": None if (math.isnan(sl) or se == 0) else round(sl / se, 2),
            "cp_knot": cp.get("knot"), "cp_improve": cp.get("sse_improve_vs_linear"), "state": state}


def changepoint_cont(sub, ycol):
    """連続 outcome 用の変化点(飽和判定なし)。重み付き二段折れ線。"""
    d = sub.dropna(subset=[ycol, "cohort_c", "_w"])
    if len(d) < 200:
        return {"knot": None, "note": "N不足"}
    cc = np.asarray(d["cohort_c"], float); y = np.asarray(d[ycol], float); sw = np.sqrt(np.asarray(d["_w"], float))
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
            best = (knot, sse, b[1], b[2])
    improve = (sse_lin - best[1]) / sse_lin if sse_lin > 0 else 0.0
    return {"knot": best[0], "pre_slope": round(best[2] * 10, 2), "post_extra": round(best[3] * 10, 2),
            "sse_improve_vs_linear": round(improve, 3), "note": "変化点あり" if improve >= 0.02 else "線形で十分"}


def main():
    if not SLIM.exists():
        raise SystemExit("先に ESS_USER_ID=... python3 src/ess_acquire.py")
    df = pd.read_parquet(SLIM)
    rows, summary = [], {"event_structure": S.EVENT_STRUCTURE, "pillars": {}}

    print("=" * 96)
    print("  ESS 徳用パック: 3本柱 × セグメント(重み付き・country+round FE)")
    print("  ※ EVENT_STRUCTURE 事前適用:euftf/移民=反復→flat を『CMR外れ』と誤読しない")
    print("=" * 96)
    for pillar, (recode, kind, struct) in S.PILLARS.items():
        print(f"\n■ {pillar}  [{struct}]" + ("  ← 反復疑い:flat 誤読しない" if struct != "single_moment" else "  ← 単発:出生年軸OK"))
        summary["pillars"][pillar] = {"event_structure": struct, "segments": {}}
        for seg in SEGS:
            r = analyze(df, pillar, recode, kind, seg)
            rows.append(r)
            summary["pillars"][pillar]["segments"][seg] = {k: r[k] for k in ("level", "slope_FE", "slope_z", "cp_knot", "state")}
            unit = "寛容率" if kind == "binary" else "平均(0-10)"
            print(f"   {seg:<22} {unit} {r['level']:.2f}  線形 {r['slope_FE']} (z={r['slope_z']})  "
                  f"変化点{r['cp_knot']}(改善{r['cp_improve']})  → {r['state']}")

    # ── step1.5: freehms を country cluster 別に(Europe-wide 均しの影響)──
    print("\n" + "=" * 96)
    print("  step1.5: freehms スロープを country cluster × セグメントで分解")
    print("  (Europe-wide 均しで消えた移行が、どのクラスタに在るか)")
    print("=" * 96)
    crows = []
    df["_cluster"] = df["cntry"].map({c: k for k, cs in CLUSTERS.items() for c in cs})
    for cl in CLUSTERS:
        sub_cl = df[df["_cluster"] == cl]
        line = []
        for seg in ["Secular HiEdu Urban", "Religious LowEdu"]:
            r = analyze(sub_cl, "freehms", S.freehms_tolerant, "binary", seg)
            crows.append({"cluster": cl, **r})
            line.append(f"{seg.split()[0]}: {r['level']:.0%} slope{r['slope_FE']}(z{r['slope_z']}) {r['state'].split('(')[0]}")
        print(f"   {cl:<13} " + " | ".join(line))

    res = ROOT / "data" / "ess_results"; res.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(res / "valuepack_matrix.csv", index=False)
    pd.DataFrame(crows).to_csv(res / "freehms_clusters.csv", index=False)
    (res / "valuepack_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 図: 柱 × セグメント の level ヒートマップ ──
    pills = list(S.PILLARS); M = np.full((len(SEGS), len(pills)), np.nan)
    for i, seg in enumerate(SEGS):
        for j, pl in enumerate(pills):
            v = summary["pillars"][pl]["segments"][seg]["level"]
            M[i, j] = v
    fig, ax = plt.subplots(figsize=(7, 4.5))
    plt.rcParams["font.family"] = "Hiragino Sans"; plt.rcParams["axes.unicode_minus"] = False
    im = ax.imshow(M, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1 if M.max() <= 1 else 10)
    ax.set_xticks(range(len(pills))); ax.set_xticklabels([f"{p}\n[{S.PILLARS[p][2][:8]}]" for p in pills], fontsize=8)
    ax.set_yticks(range(len(SEGS))); ax.set_yticklabels(SEGS, fontsize=8)
    for i, seg in enumerate(SEGS):
        for j, pl in enumerate(pills):
            st = summary["pillars"][pl]["segments"][seg]["state"]
            tag = "•" if st.startswith("移行") else ("=" if st.startswith("飽和") else "")
            ax.text(j, i, f"{M[i,j]:.2f}{tag}", ha="center", va="center", fontsize=8)
    ax.set_title("ESS 徳用パック: 柱×セグメント level(•移行/=飽和)\nfreehms=寛容率 / euftf・移民=平均0-10", fontsize=9)
    fig.tight_layout(); fig.savefig(ROOT / "figures" / "ess_valuepack.png", dpi=200, bbox_inches="tight"); plt.close(fig)
    print(f"\n[saved] data/ess_results/valuepack_matrix.csv / freehms_clusters.csv / valuepack_summary.json")
    print("[saved] figures/ess_valuepack.png")


if __name__ == "__main__":
    main()
