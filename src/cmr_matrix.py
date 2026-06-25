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

DATA = Path(__file__).resolve().parent.parent / "data"

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

# grid 版の 8 community(正準 premise で完全一致)
COMMUNITIES_GRID = {
    "us": [
        ("Coastal Liberal",  "secular_white_coastal_graduate"),
        ("Bible Belt Evang", "evangelical_white_bible_belt_no_college"),
        ("Rust Belt WWC",    "mainline_protestant_white_rust_belt_no_college"),
        ("Black community",  "secular_black_urban_some_college"),
        ("Latino Immigrant", "catholic_hispanic_urban_some_college"),
        ("Mormon/Utah",      "mormon_white_mountain_west_bachelor"),
        ("Suburban MC",      "mainline_protestant_white_suburban_bachelor"),
        ("Rural Conserv",    "evangelical_white_rural_no_college"),
    ],
    "uk": [
        ("London Multicult", "middle_class_london_immigrant_2nd_gen_russell_group"),
        ("Home Counties MC", "middle_class_home_counties_native_4plus_gen_russell_group"),
        ("N.Post-indust",    "working_class_northern_england_native_4plus_gen_gcse"),
        ("Scotland",         "working_class_scotland_native_4plus_gen_gcse"),
        ("NI Catholic",      "working_class_northern_ireland_catholic_4plus_gen_gcse"),
        ("NI Protestant",    "working_class_northern_ireland_protestant_4plus_gen_gcse"),
        ("British Asian",    "middle_class_london_asian_2nd_gen_russell_group"),
        ("Brexit LeaveTown", "working_class_leave_town_native_4plus_gen_no_qualifications"),
        ("Univ Remain",      "middle_class_london_native_2nd_gen_oxbridge"),
    ],
}

# grid 版は event_id で安定マッチ(label, event_id)
EVENTS_GRID = {
    "us": [
        ("同性婚", "us_obergefell_2015"), ("9.11", "us_sept11_2001"),
        ("2008危機", "us_lehman_2008"), ("オバマ当選", "us_obama_election_2008"),
        ("トランプ当選", "us_trump_election_2016"), ("BLM", "us_blm_2013"),
        ("Dobbs/中絶", "us_dobbs_2022"), ("COVID規制", "us_covid_restrictions_2020"),
        ("銃乱射", "us_sandy_hook_2012"), ("学生ローン", "us_student_debt_2012"),
        ("住宅価格高騰", "us_housing_surge_2021"), ("公民権法", "us_civil_rights_act_1964"),
    ],
    "uk": [
        ("Brexit", "uk_brexit_2016"), ("7/7爆破", "uk_77_bombings_2005"),
        ("2008危機", "uk_financial_crisis_2008"), ("緊縮", "uk_austerity_2010"),
        ("授業料", "uk_tuition_fees_2010"), ("Section28撤廃", "uk_section28_repeal_2003"),
        ("スコット独立", "uk_scottish_referendum_2014"), ("同性婚", "uk_same_sex_marriage_2014"),
        ("移民論争", "uk_immigration_debate_2015"), ("Windrush", "uk_windrush_2018"),
        ("COVID", "uk_covid_lockdown_2020"), ("生活費危機", "uk_cost_of_living_2022"),
        ("NHS危機", "uk_nhs_crisis_2022"),
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
    ap.add_argument("--variant", default="v1", help="v1 | grid")
    args = ap.parse_args()
    c = args.country
    tag = c if args.variant == "v1" else f"{c}_{args.variant}"

    I = [json.loads(l) for l in (DATA / f"interpretations_{tag}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_event = collections.defaultdict(list)   # name → interps
    by_eid = collections.defaultdict(list)     # event_id → interps
    for it in I:
        by_event[it["event_name"]].append(it)
        if it.get("event_id"):
            by_eid[it["event_id"]].append(it)

    grid_mode = args.variant != "v1"
    comms = COMMUNITIES_GRID[c] if grid_mode else COMMUNITIES[c]
    events = EVENTS_GRID[c] if grid_mode else EVENTS[c]
    comm_names = [n for n, _ in comms]

    def interps_for(spec):
        """v1: event_name 部分文字列 / grid: event_id 完全一致。"""
        if grid_mode:
            return by_eid.get(spec, [])
        return [it for ev, lst in by_event.items() if spec in ev for it in lst]

    def matches(premise, spec):
        """grid: 正準premise完全一致 / v1: トークンパターン。"""
        return (premise == spec) if grid_mode else premise_matches(premise, spec)

    def cell(interps, spec):
        modes = set()
        for it in interps:
            if it.get("premise") and matches(it["premise"], spec):
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
        interps = interps_for(sub)
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
