#!/usr/bin/env python3
"""
ons_breadwinner_gap.py — UK 2008不況の男女失業率上昇差(breadwinner経路)を ONS 公式系列で接地する。

背景(docs/salience_extension_spec.md §6 / gender grid UK round):
  UK 性別拡張グリッドで唯一 mode が割れた事象 = 2008金融危機
  (労働者階級4共同体で F=PASSIVE / M=ACTIVE)。この breadwinner 経路の重み差を
  ONS Labour Market Statistics の実系列で接地する(LLM 数値は使わない)。

系列(ONS website JSON, Open Government Licence):
  MGSY = Male unemployment rate (16+, SA) / MGSZ = Female (同)
  https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/{id}/lms/data

事前固定の窓(実行前に宣言):
  baseline = 2008 Q1(不況入り直前) / assessment = 2009 Q4(公式不況 2008Q2–2009Q2 + 労働市場ラグ2Q)
  参考値としてピーク(2008Q2–2010Q4 内の最大)も併記。

判定基準(事前固定): 男性の上昇幅 > 女性の上昇幅 → breadwinner 経路の重み差を
  working_class × male premise の grounded 記録として data/salience_grounding_uk.jsonl へ出力。

Run: python3 src/adapters/ons/ons_breadwinner_gap.py
"""
from __future__ import annotations
import json
import urllib.request
from pathlib import Path

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
ONS_DIR = ROOT / "data" / "ons"          # 生キャッシュ(.gitignore; 再取得可能)
OUT_DIR = ROOT / "data" / "ons_results"  # 計算結果(committed)
GROUNDING = ROOT / "data" / "salience_grounding_uk.jsonl"

SERIES = {"male": "mgsy", "female": "mgsz"}
URL = "https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/{sid}/lms/data"
BASELINE = "2008 Q1"
ASSESS = "2009 Q4"
PEAK_WINDOW = ("2008 Q2", "2010 Q4")


def fetch(sid: str) -> dict:
    ONS_DIR.mkdir(parents=True, exist_ok=True)
    cache = ONS_DIR / f"{sid}_lms.json"
    if not cache.exists():
        req = urllib.request.Request(URL.format(sid=sid), headers={"User-Agent": "Mozilla/5.0"})
        cache.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    return json.loads(cache.read_text(encoding="utf-8"))


def quarters(d: dict) -> dict:
    return {x["date"]: float(x["value"]) for x in d["quarters"]}


def main():
    res = {}
    for sex, sid in SERIES.items():
        d = fetch(sid)
        q = quarters(d)
        in_window = {k: v for k, v in q.items() if PEAK_WINDOW[0] <= k <= PEAK_WINDOW[1]}
        peak_date, peak = max(in_window.items(), key=lambda x: x[1])
        res[sex] = {
            "series": sid.upper(), "title": d["description"]["title"],
            "baseline_2008Q1": q[BASELINE], "assess_2009Q4": q[ASSESS],
            "rise_pp": round(q[ASSESS] - q[BASELINE], 2),
            "peak_in_window": peak, "peak_date": peak_date,
            "rise_to_peak_pp": round(peak - q[BASELINE], 2),
        }
    ratio = res["male"]["rise_pp"] / res["female"]["rise_pp"]
    criterion = res["male"]["rise_pp"] > res["female"]["rise_pp"]

    print("=" * 80)
    print("  ONS breadwinner gap — UK 2008 recession, unemployment rise by sex")
    print("=" * 80)
    for sex, r in res.items():
        print(f"  {sex:<7} {r['series']}: {r['baseline_2008Q1']}% (2008Q1) → {r['assess_2009Q4']}% (2009Q4) "
              f"= +{r['rise_pp']}pp   [peak {r['peak_in_window']}% {r['peak_date']}]")
    print(f"\n  male rise / female rise = {ratio:.2f}×")
    print(f"  Pre-fixed criterion (male rise > female rise): {'satisfied' if criterion else 'NOT satisfied'}")

    OUT_DIR.mkdir(exist_ok=True)
    summary = {"window": {"baseline": BASELINE, "assess": ASSESS, "peak_window": list(PEAK_WINDOW)},
               "by_sex": res, "male_female_rise_ratio": round(ratio, 2),
               "criterion_male_gt_female": criterion,
               "license": "ONS, Open Government Licence v3.0"}
    (OUT_DIR / "breadwinner_gap.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")

    if criterion:
        record = {
            "event_id": "uk_financial_crisis_2008",
            "event_name": "2008 financial crisis / 2008 金融危機",
            "premise_pattern": "working_class_*_male",
            "channel": "breadwinner_role_pressure",
            "multiplier_tier": "elevated",
            "status": "grounded",
            "source": (f"ONS LMS MGSY/MGSZ (SA, 16+): male unemployment +{res['male']['rise_pp']}pp "
                       f"vs female +{res['female']['rise_pp']}pp, 2008Q1→2009Q4 ({ratio:.1f}x); "
                       f"male peak {res['male']['peak_in_window']}% {res['male']['peak_date']}"),
            "computed_by": "src/adapters/ons/ons_breadwinner_gap.py",
        }
        lines = []
        if GROUNDING.exists():
            lines = [l for l in GROUNDING.read_text(encoding="utf-8").splitlines() if l.strip()]
            lines = [l for l in lines if json.loads(l).get("event_id") != record["event_id"]]
        lines.append(json.dumps(record, ensure_ascii=False))
        GROUNDING.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n[saved] {GROUNDING.name} に grounded 記録を追加 / ons_results/breadwinner_gap.json")
    else:
        print("\n[not grounded] 基準不成立 → grounding 記録は書かない(隠さず結果のみ保存)")


if __name__ == "__main__":
    main()
