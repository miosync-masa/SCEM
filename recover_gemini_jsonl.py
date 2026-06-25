#!/usr/bin/env python3
"""
recover_gemini_jsonl.py — 破損した Gemini DeepResearch 出力(txt)を決定論的に復旧する。

背景: Gemini の UK 出力はシリアライズバグで以下が壊れていた(全行同一パターン):
  - "possible_modes":,        値が空
  - "source_urls":,           値が空(一部)
  - "affected_groups":, "rationale": "<R1>"}, {ag2}, ... ]
        affected_groups 配列の '[' が消え、先頭要素は rationale だけ残り
        premise/expected_mode/effect_emphasis を喪失。残りの ag は健全。

復旧方針(捏造しない):
  - possible_modes 空 → 既定 ["PASSIVE","ACTIVE","REFRAME"](全健全レコード共通値。recovery_note に明記)
  - source_urls 空   → []
  - affected_groups  → premise を持つ健全な ag のみ採用。
                       premise を喪失した先頭 ag は interpretation にせず、その rationale を
                       event_rationale_recovered として退避(由来曖昧のため premise/mode は補わない)。

Usage:
    python3 recover_gemini_jsonl.py --country uk --src data/gemini-code-1782379054633.txt
出力: data/Gemini_events_{country}_v1.jsonl(復旧版)。破損元があれば .broken.jsonl に退避。
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
DEFAULT_MODES = ["PASSIVE", "ACTIVE", "REFRAME"]


def repair_line(line: str) -> str:
    s = line.strip()
    # 空値の後ろのカンマは区切りなので保持する
    s = re.sub(r'"possible_modes":\s*,', '"possible_modes": ["PASSIVE", "ACTIVE", "REFRAME"],', s)
    s = re.sub(r'"source_urls":\s*,', '"source_urls": [],', s)
    # affected_groups 配列を復元(先頭 ag は rationale のみの {rationale:...} になる)
    s = s.replace('"affected_groups":, ', '"affected_groups": [{')
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True)
    ap.add_argument("--src", required=True, help="破損 Gemini 出力 txt(1行1イベント)")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_absolute():
        src = Path(__file__).resolve().parent / src
    lines = [l for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]

    recovered, parse_fail = [], 0
    stats = {"events": 0, "interps_kept": 0, "first_group_dropped": 0,
             "possible_modes_defaulted": 0, "source_urls_emptied": 0}
    for l in lines:
        if '"possible_modes":,' in l or '"possible_modes": ,' in l:
            stats["possible_modes_defaulted"] += 1
        if '"source_urls":,' in l or '"source_urls": ,' in l:
            stats["source_urls_emptied"] += 1
        try:
            o = json.loads(repair_line(l))
        except json.JSONDecodeError:
            parse_fail += 1
            continue
        ags = o.get("affected_groups") or []
        clean = [a for a in ags if a.get("premise")]
        dropped = [a for a in ags if not a.get("premise")]
        if dropped:
            stats["first_group_dropped"] += 1
            # premise を喪失した先頭 ag の rationale を event 側へ退避(由来曖昧・premise/mode は補わない)
            note = next((a.get("rationale") for a in dropped if a.get("rationale")), None)
            if note:
                o["event_rationale_recovered"] = note
        o["affected_groups"] = clean
        o["possible_modes"] = o.get("possible_modes") or DEFAULT_MODES
        o["recovery_note"] = ("recovered from corrupted Gemini txt; possible_modes defaulted; "
                              "first affected_group (premise/mode lost in serialization) dropped")
        recovered.append(o)
        stats["events"] += 1
        stats["interps_kept"] += len(clean)

    out = DATA / f"Gemini_events_{args.country}_v1.jsonl"
    if out.exists():
        broken = DATA / f"Gemini_events_{args.country}_v1.broken.jsonl"
        broken.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
    out.write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in recovered) + "\n", encoding="utf-8")

    print(f"[recover] {src.name} → {out.name}")
    print(f"  復旧イベント: {stats['events']} / パース失敗: {parse_fail}")
    print(f"  健全 interpretation(premise有)採用: {stats['interps_kept']}")
    print(f"  premise喪失の先頭ag破棄: {stats['first_group_dropped']} 件(rationaleはevent_rationale_recoveredへ退避)")
    print(f"  possible_modes 既定補完: {stats['possible_modes_defaulted']} 件 / source_urls 空→[]: {stats['source_urls_emptied']} 件")
    print(f"  ※ 破損元は Gemini_events_{args.country}_v1.broken.jsonl に退避")


if __name__ == "__main__":
    main()
