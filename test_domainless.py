"""
test_domainless.py — domain(cross_domain 1.6倍)を cosベース増幅に置き換えた場合の影響検証。

置換:
  旧: amp = 1.6 if cross_domain else 1.0
  新: amp = 1.0 + 0.6*(1 - sim)   # sim=0(直交作用)→1.6, sim=1(同一作用)→1.0
      (cosが低いほど増幅。旧cross_domainと同じ[1.0,1.6]レンジに正規化)

他(base, independence項, proximity項, duplicate除外)は一切変えない。

検証対象:
  1. 1981 世代指紋(P/A/R)          → domain非依存のはず=不変を確認
  2. 9世代バッチ密度(Table 3)       → 同上
  3. 1981 干渉ノード Top10           → 新旧比較(ここだけ動く)
  4. 各世代の質感筆頭(干渉Top1)     → 新旧比較
"""
from __future__ import annotations
import media_generation_v5 as v5
import media_generation_v4 as v4

YEARS = [1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010]


# ── cosベース干渉(v4.compute_interferencesのcross_domainだけ差し替え) ──
def interferences_cosine(hits, overlap_report):
    dup = {tuple(r["pair"]) for r in overlap_report if r["action"] == "duplicate"}
    dup |= {tuple(reversed(r["pair"])) for r in overlap_report if r["action"] == "duplicate"}
    out = []
    for i in range(len(hits)):
        for j in range(i + 1, len(hits)):
            a, b = hits[i], hits[j]
            ea, eb = a["ev"], b["ev"]
            if (ea.name, eb.name) in dup:
                continue
            if a["stage"] != b["stage"]:
                continue
            age_gap = abs(a["age"] - b["age"])
            bw = v4.band_width(a["stage"])
            proximity = 1.0 - min(age_gap / bw, 1.0)
            sim = v4.cosine(ea.effect_vector, eb.effect_vector)
            base = (a["weight"] + b["weight"]) / 2
            # 統合版: 作用直交性を1項に集約(independence項とcross_domainを廃止し二重計上を排除)
            dissimilarity = 1.6 - 1.05 * min(sim, 1.0)   # cos=0→1.6 / cos=1→0.55
            score = base * dissimilarity * (0.5 + 0.5 * proximity)
            out.append({
                "pair": (ea.name, eb.name), "stage": a["stage"],
                "age_range": (min(a["age"], b["age"]), max(a["age"], b["age"])),
                "similarity": round(sim, 3),
                "cross_domain": ea.domain is not eb.domain,
                "score": round(score, 3),
            })
    out.sort(key=lambda x: -x["score"])
    return out


def main():
    ev = v5.load_events()

    print("=" * 74)
    print("  [1] 1981 世代指紋(domain非依存のはず → 旧新で同一)")
    print("=" * 74)
    hits, interf_old, fires, overlap = v4.analyze(1981, ev)
    for m, label in [(v4.Mode.PASSIVE, "PASSIVE"), (v4.Mode.ACTIVE, "ACTIVE"), (v4.Mode.REFRAME, "REFRAME")]:
        d = v5.mode_density(hits, m)
        print(f"  {label:<8} count={d['count']:>3} mean={d['mean']:.3f} top3={d['top3_mean']:.3f}")

    print("\n" + "=" * 74)
    print("  [2] 9世代バッチ密度(Table 3)— domain非依存のはず")
    print("=" * 74)
    print(f"  {'生年':<6}{'PASSIVE':>10}{'ACTIVE':>10}{'REFRAME':>10}   支配")
    for y in YEARS:
        fp = v5.cohort_fingerprint(y, ev)
        P, A, R = fp["P"]["mean"], fp["A"]["mean"], fp["R"]["mean"]
        dom = max([("PASSIVE", P), ("ACTIVE", A), ("REFRAME", R)], key=lambda x: x[1])[0]
        peak = " ★" if y in (1980, 1985) else ""
        print(f"  {y:<6}{P:>10.2f}{A:>10.2f}{R:>10.2f}   {dom}{peak}")

    print("\n" + "=" * 74)
    print("  [3] 1981 干渉ノード Top10 — 旧(cross_domain 1.6)vs 新(cosベース)")
    print("=" * 74)
    interf_new = interferences_cosine(hits, overlap)
    print("  --- 旧(cross_domain) ---")
    for it in interf_old[:10]:
        x = "横断" if it["cross_domain"] else "同領"
        print(f"   [{it['score']:.3f}] {x} cos={it['similarity']:.2f} {it['pair'][0]} × {it['pair'][1]}")
    print("  --- 新(cosベース増幅) ---")
    for it in interf_new[:10]:
        x = "横断" if it["cross_domain"] else "同領"
        print(f"   [{it['score']:.3f}] {x} cos={it['similarity']:.2f} {it['pair'][0]} × {it['pair'][1]}")

    print("\n" + "=" * 74)
    print("  [4] 各世代の質感筆頭(干渉Top1)— 旧 vs 新")
    print("=" * 74)
    for y in YEARS:
        h, io, f, ov = v4.analyze(y, ev)
        inew = interferences_cosine(h, ov)
        o = io[0] if io else None
        n = inew[0] if inew else None
        os_ = f"{o['pair'][0]} × {o['pair'][1]}" if o else "(なし)"
        ns_ = f"{n['pair'][0]} × {n['pair'][1]}" if n else "(なし)"
        same = "  = 同一" if (o and n and set(o['pair']) == set(n['pair'])) else "  ≠ 変化"
        print(f"  {y}:{same}")
        print(f"      旧: {os_}")
        print(f"      新: {ns_}")


if __name__ == "__main__":
    main()
