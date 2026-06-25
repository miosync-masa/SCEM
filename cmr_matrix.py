#!/usr/bin/env python3
"""
cmr_matrix.py — Same Event × Community → mode 変換マトリクス(Paper 2 Figure 2 素材)

「同一の社会事象が Community(=前提レイヤー premise)によって PASSIVE/ACTIVE/REFRAME へ
変換される」を、interpretations_{country}.jsonl の実データから直接ピボットして示す。
LLM 呼び出しなし・捏造なし。データに無い (event, community) セルは "—"。

Community ラベルは実データ premise へのトークン照合で対応づける(近似・下に定義を明示)。

Run: python3 cmr_matrix.py --country us
"""
from __future__ import annotations
import argparse
import json
import collections
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

# Community → premise トークンパターン(いずれかのトークン集合を全て含む premise が該当)
COMMUNITIES = {
    "us": [
        ("Coastal Liberal",   [["coastal"]]),
        ("Bible Belt Evang",  [["evangelical"], ["bible_belt"]]),
        ("Rust Belt WWC",     [["rust_belt"]]),
        ("Black community",   [["black"]]),
        ("Latino Immigrant",  [["hispanic"], ["immigrant"]]),
    ],
    # UK は実データ premise 語彙(class/london/working/middle/immigrant/russell/oxbridge…)に較正。
    # Scotland/Northern Ireland は現データで 2-4 件と希薄なため除外(データ拡張が必要)。
    "uk": [
        ("London",            [["london"]]),
        ("Middle Class",      [["middle", "class"]]),
        ("Working Class",     [["working", "class"]]),
        ("Univ-educated",     [["russell"], ["oxbridge"]]),
        ("Immigrant/Commonw", [["immigrant"], ["commonwealth"], ["eu"]]),
    ],
}

# イベントラベル → event_name 部分文字列
EVENTS = {
    "us": [
        ("Same-sex marriage", "Obergefell"),
        ("9.11",              "September 11"),
        ("2008 crisis",       "Lehman"),
        ("Obama当選",          "Obama elected"),
        ("Trump当選",          "Trump elected"),
        ("BLM",               "Black Lives Matter"),
        ("Dobbs/中絶",         "Dobbs"),
        ("COVID規制",          "COVID-19 pandemic restrictions"),
        ("銃乱射(SandyHook)",  "Sandy Hook"),
        ("住宅価格高騰",        "Housing price surge"),
    ],
    "uk": [
        ("Brexit",            "Brexit"),
        ("7/7 bombings",      "7/7"),
        ("2008 crisis",       "Financial Crisis"),
        ("Austerity",         "Austerity"),
        ("Windrush",          "Windrush"),
        ("COVID lockdown",    "COVID"),
        ("NHS crisis",        "NHS"),
        ("Cost of living",    "Cost of Living"),
        ("Tuition fees",      "Tuition"),
        ("Same-sex marriage", "Section 28"),
    ],
}

MODE_ABBR = {"PASSIVE": "PAS", "ACTIVE": "ACT", "REFRAME": "REF"}


def premise_matches(premise: str, patterns) -> bool:
    toks = premise.split("_")
    for need in patterns:
        if all(any(t == tk or t in tk for tk in toks) for t in need):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="us")
    args = ap.parse_args()
    c = args.country

    I = [json.loads(l) for l in (DATA / f"interpretations_{c}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_event = collections.defaultdict(list)
    for it in I:
        by_event[it["event_name"]].append(it)

    comms = COMMUNITIES[c]
    events = EVENTS[c]
    comm_names = [n for n, _ in comms]

    def cell(interps, patterns):
        modes = set()
        for it in interps:
            if it.get("premise") and premise_matches(it["premise"], patterns):
                modes.add(MODE_ABBR.get(it["expected_mode"], it["expected_mode"]))
        order = {"PAS": 0, "ACT": 1, "REF": 2}
        return "/".join(sorted(modes, key=lambda m: order.get(m, 9))) if modes else "—"

    # ── マトリクス ──
    w = 18
    print("=" * 100)
    print(f"  Same Event × Community → mode 変換マトリクス  [{c.upper()}]  (実データ interpretations より)")
    print("=" * 100)
    def base_majority(interps):
        """base_mode_majority = その事象の全premise解釈の最頻 mode(略号)。"""
        ms = [MODE_ABBR.get(i["expected_mode"], i["expected_mode"]) for i in interps if i.get("premise")]
        if not ms:
            return None
        cnt = collections.Counter(ms)
        order = {"ACT": 0, "REF": 1, "PAS": 2}   # tie は priority(決断強制優先)
        return sorted(cnt, key=lambda m: (-cnt[m], order.get(m, 9)))[0]

    print(f"  {'Event':<20}" + "".join(f"{cn:<{w}}" for cn in comm_names) + "base(majority)")
    flip_events = []          # Community 間で mode が割れたイベント
    covered = 0               # 1セル以上データのあるイベント
    cells_observed = cells_flipped = 0   # Cell-level MFR 用
    for label, sub in events:
        interps = [it for ev, lst in by_event.items() if sub in ev for it in lst]
        base = base_majority(interps)
        cells = [cell(interps, pats) for _, pats in comms]
        distinct = set(m for cl in cells for m in cl.split("/") if m != "—")
        has_data = any(cl != "—" for cl in cells)
        if has_data:
            covered += 1
        if len(distinct) >= 2:
            flip_events.append((label, len(distinct)))
        # Cell-level: 観測セルごとに resolved != base_majority か
        for cl in cells:
            if cl == "—":
                continue
            cells_observed += 1
            if base and any(m != base for m in cl.split("/")):
                cells_flipped += 1
        mark = " ⚡" if len(distinct) >= 2 else ("" if has_data else " (データなし)")
        print(f"  {label:<20}" + "".join(f"{cl:<{w}}" for cl in cells) + f"{base or '—':<10}" + mark)

    ev_mfr = len(flip_events) / covered if covered else 0.0
    cell_mfr = cells_flipped / cells_observed if cells_observed else 0.0
    print("\n" + "-" * 100)
    print(f"  Event-level MFR(Community間で mode 分岐したイベント / データのあるイベント)= "
          f"{len(flip_events)}/{covered} = {ev_mfr:.0%}")
    print(f"  Cell-level  MFR(resolved≠base_majority のセル / 観測セル)= "
          f"{cells_flipped}/{cells_observed} = {cell_mfr:.0%}")
    print("  ※ 対象は selected high-contention events(争点イベント集合)。社会事象全体の母数ではない。")
    print("  分岐イベント(mode種類数): " + ", ".join(f"{l}({n})" for l, n in sorted(flip_events, key=lambda x: -x[1])))

    print("\n  ※ Community→premise 対応(近似・トークン照合):")
    for n, pats in comms:
        print(f"     {n:<18} ⇐ premise tokens {pats}")
    print("  ※ '—' = その (event, community) を明示モデル化した interpretation がデータに無い")


if __name__ == "__main__":
    main()
