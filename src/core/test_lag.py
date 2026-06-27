"""
test_lag.py — 情報-具現化ラグの味見実験(Paper本体・エンジンには触らない)

仮説: 事象には2フェーズの着弾がある
  情報着弾(知る)   ≒ launch年 (year)
  具現化着弾(なる/やる) ≒ 普及年 (effective_year)
  ラグ = effective_year − year
プラットフォーム時代ほど情報は即時化、具現化は環境依存で遅延 →
若い世代ほどラグが開く(はず)を味見する。

出力(数値のみ):
  A. 9世代 × 「人格形成期(12-17歳)に情報着弾した事象群の平均ラグ」
  B. ラグ上位/下位イベント
  C. モード別・領域別の平均ラグ
  おまけ: ラグを世代指紋の4軸目にできそうか(各世代の着弾事象の重み付き平均ラグ)

Run: python3 test_lag.py
"""
from __future__ import annotations
import json
from collections import defaultdict

from pathlib import Path
PATH = str(next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent / "data" / "events_patched.jsonl")
COHORTS = [1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010]
TEEN = (12, 17)   # 人格形成期

DOMAIN_JA = {
    "MEDIA": "メディア技術", "EDUCATION": "教育制度", "ECONOMY": "経済雇用",
    "DISASTER": "災害危機", "POLITICS": "政治制度", "LIFESTYLE": "生活文化",
    "PLATFORM": "プラットフォーム", "GEOPOLITICS": "国際環境", "HEALTH": "公衆衛生",
    "FINANCE": "金融資産", "PRICE": "物価価格", "FOOD": "食料供給",
}


def load():
    evs = []
    for line in open(PATH, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        y = o.get("year")
        if not isinstance(y, (int, float)):
            continue
        e = o.get("effective_year", y)
        if not isinstance(e, (int, float)):
            e = y
        evs.append({
            "name": o["name"],
            "launch": int(y),
            "eff": int(e),
            "lag": int(e) - int(y),
            "domain": o.get("domain", "?"),
            "mode": o.get("mode", "?"),
            "salience": float(o.get("salience", 1.0)),
            "eff_type": o.get("effective_year_type", "?"),
        })
    return evs


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    evs = load()

    # ── A. 9世代 × 人格形成期に「情報着弾」した事象群の平均ラグ ──
    print("=" * 72)
    print("  A. 9世代 × 人格形成期(12-17歳に情報着弾)した事象の平均ラグ")
    print("=" * 72)
    print(f"  {'生年':<6}{'該当数':>6}{'平均ラグ':>9}{'平均info着弾齢':>14}{'平均具現齢':>12}")
    aRows = []
    for b in COHORTS:
        teen = [e for e in evs if TEEN[0] <= (e["launch"] - b) <= TEEN[1]]
        lags = [e["lag"] for e in teen]
        infoA = [e["launch"] - b for e in teen]
        manA = [e["eff"] - b for e in teen]
        aRows.append((b, len(teen), mean(lags)))
        print(f"  {b:<6}{len(teen):>6}{mean(lags):>9.2f}{mean(infoA):>14.1f}{mean(manA):>12.1f}")
    # 単調性チェック
    vals = [r[2] for r in aRows]
    mono = all(vals[i] <= vals[i + 1] + 1e-9 for i in range(len(vals) - 1))
    print(f"\n  → 単調増加か: {'YES(若い世代ほどラグ拡大)' if mono else 'NO(非単調)'}")
    print(f"    最小{min(vals):.2f}(生年{aRows[vals.index(min(vals))][0]}) "
          f"→ 最大{max(vals):.2f}(生年{aRows[vals.index(max(vals))][0]})")

    # ── B. ラグ上位/下位イベント ──
    print("\n" + "=" * 72)
    print("  B. ラグ上位イベント(知ってから具現化までが長い)")
    print("=" * 72)
    for e in sorted(evs, key=lambda x: -x["lag"])[:12]:
        print(f"  lag={e['lag']:>2}  {e['name']:<26} {e['launch']}→{e['eff']} "
              f"[{DOMAIN_JA.get(e['domain'], e['domain'])}/{e['mode']}/{e['eff_type']}]")
    print("\n  ラグ0(情報=具現化が即時。日付固定事象)の例:")
    z = [e for e in evs if e["lag"] == 0]
    print(f"    全{len(z)}件中の例: " + " / ".join(e["name"] for e in z[:8]))

    # ── C. モード別・領域別 平均ラグ ──
    print("\n" + "=" * 72)
    print("  C-1. モード別 平均ラグ")
    print("=" * 72)
    byMode = defaultdict(list)
    for e in evs:
        byMode[e["mode"]].append(e["lag"])
    for m in ("PASSIVE", "ACTIVE", "REFRAME"):
        ls = byMode.get(m, [])
        if ls:
            pos = sum(1 for x in ls if x > 0)
            print(f"  {m:<8} 件数{len(ls):>3} 平均ラグ{mean(ls):>5.2f}  (ラグ>0は{pos}件 {100*pos/len(ls):.0f}%)")

    print("\n  C-2. 領域別 平均ラグ(降順)")
    byDom = defaultdict(list)
    for e in evs:
        byDom[e["domain"]].append(e["lag"])
    for d, ls in sorted(byDom.items(), key=lambda kv: -mean(kv[1])):
        print(f"  {DOMAIN_JA.get(d, d):<10} 件数{len(ls):>3} 平均ラグ{mean(ls):>5.2f}")

    # ── おまけ: ラグを世代指紋の4軸目にできそうか ──
    print("\n" + "=" * 72)
    print("  おまけ. 各世代の『着弾事象のラグ平均』(4軸目候補)")
    print("  ※ その世代が0歳以降に情報着弾した全事象、salience重み付き平均ラグ")
    print("=" * 72)
    print(f"  {'生年':<6}{'対象数':>6}{'重み付き平均ラグ':>16}")
    for b in COHORTS:
        seen = [e for e in evs if e["launch"] - b >= 0]
        wl = sum(e["lag"] * e["salience"] for e in seen)
        ws = sum(e["salience"] for e in seen)
        print(f"  {b:<6}{len(seen):>6}{(wl / ws if ws else 0):>16.2f}")


if __name__ == "__main__":
    main()
