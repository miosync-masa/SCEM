#!/usr/bin/env python3
"""
generate_claude_observer.py — 第2(第3)観測者 Claude の grid 解釈を出力する。

背景: Gemini は grid 出力で毎回先頭共同体を破損で落とした(US Coastal Liberal /
UK London Multicultural)。その欠落セルを ChatGPT 単独(=単一観測者)のまま残さず、
Claude を観測者として埋める。Gemini オミット決定(2026-06-25)の第一歩。

設計上の位置づけ:
  - これは LLM-as-annotator の正規手続き(ChatGPT/Gemini と同列の観測者)。捏造ではない。
  - 判定は Claude(本ファイルの著者)が各 (event, community) を独立に推論したもの。
    ChatGPT の一律 REFRAME を写さず、共同体前提から社会学的に解決した。
  - 出力は Gemini と同じ event-level スキーマ(affected_groups に当該共同体)。
    source_model は merge 側で "claude" を付与する。
  - 解像度は community_interpretation(個人の断定ではなく「その共同体が持ちやすい着弾相」)。

Usage:
    python3 generate_claude_observer.py --country us
    python3 generate_claude_observer.py --country uk
出力: data/Claude_events_{country}_grid.jsonl(対象共同体のみ。merge が解釈として畳み込む)
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_MODES = ["PASSIVE", "ACTIVE", "REFRAME"]

# 各 community(canonical premise)について {event_id: (mode, [effect_emphasis], rationale)}。
# Claude が共同体前提から独立に解決した判定。ChatGPT との一致/不一致は観測者依存の信号。
JUDGMENTS = {
    "us": {
        # Coastal Liberal = 世俗・白人・沿岸・大卒(都市進歩派の専門職層)
        "secular_white_coastal_graduate": {
            "us_civil_rights_act_1964": ("PASSIVE", ["civic_norm", "racial_consciousness"],
                "この層には生得の進歩的市民規範=継承されたベースラインとして身体化されており、決断も基準書換も伴わず前提として受動的に持っている。"),
            "us_sept11_2001": ("REFRAME", ["security_baseline", "civil_liberties"],
                "安全と自由/監視のトレードオフという基準値が書き換わり、以後の外交観・市民的自由観の参照点になった。"),
            "us_obama_election_2008": ("ACTIVE", ["political_efficacy", "racial_progress"],
                "投票・運動への能動的関与として経験され、『自分たちが動かした』という政治的自己効力感を刻んだ。"),
            "us_lehman_2008": ("REFRAME", ["economic_trust", "institutional_faith"],
                "規制緩和型資本主義への信頼の基準値が書き換わり、後の進歩派経済観の参照点となった。"),
            "us_student_debt_2012": ("ACTIVE", ["economic_pressure", "mobility_aspiration"],
                "学位とローンを抱える当事者として、進路・住居・返済をめぐる能動的意思決定を迫られた。"),
            "us_sandy_hook_2012": ("ACTIVE", ["civic_norm", "safety"],
                "銃規制運動への能動的動員として着弾し、政治的態度表明と行動を促した。"),
            "us_blm_2013": ("REFRAME", ["racial_consciousness", "civic_norm"],
                "白人沿岸高学歴層には、構造的人種差別の理解そのものの基準値を書き換える参照点として作用した。"),
            "us_obergefell_2015": ("REFRAME", ["civic_norm", "identity_recognition"],
                "自分たちの規範が国家規範になったことの確認=参照点が自層に一致する方向へ移動した。"),
            "us_trump_election_2016": ("REFRAME", ["national_self_image", "political_efficacy"],
                "『この国はそうではなかった』という国家自己像の基準値が崩れ、以後の前提が書き換わった。"),
            "us_covid_restrictions_2020": ("PASSIVE", ["public_health_norm", "institutional_faith"],
                "在宅勤務が可能な専門職層には公衆衛生規範を受容・身体化する受動的曝露が主で、経済的打撃は相対的に小さかった。"),
            "us_housing_surge_2021": ("ACTIVE", ["economic_pressure", "mobility_aspiration"],
                "高額都市圏で住居取得・転居の能動的意思決定を迫られ、生活設計の再計算を強いられた。"),
            "us_dobbs_2022": ("REFRAME", ["civic_norm", "identity_recognition"],
                "権利は拡大こそすれ後退しないという基準値が破られ、参照点が書き換わった(動員=ACTIVEを誘発する基層のREFRAME)。"),
        },
    },
    "uk": {
        # London Multicultural = 中産・ロンドン・移民二世・ラッセルグループ
        "middle_class_london_immigrant_2nd_gen_russell_group": {
            "uk_77_bombings_2005": ("REFRAME", ["safety_baseline", "belonging"],
                "多文化都市の安全感と『監視される共同体』としての所属基準が同時に書き換わった。"),
            "uk_financial_crisis_2008": ("ACTIVE", ["career_recalculation", "economic_pressure"],
                "金融都市の高学歴層には雇用不安とキャリア選択の再計算という能動的意思決定として作用した。"),
            "uk_austerity_2010": ("REFRAME", ["mobility_aspiration", "institutional_faith"],
                "公共投資が上昇を担保するという暗黙の約束=メリトクラシーのベースラインが書き換わった(上昇志向の移民二世に固有)。"),
            "uk_tuition_fees_2010": ("ACTIVE", ["mobility_aspiration", "economic_pressure"],
                "ラッセルグループ志向の家族上昇戦略として、債務を前提に進学を選ぶ能動的決定を迫った。"),
            "uk_section28_repeal_2003": ("REFRAME", ["civic_norm", "identity_recognition"],
                "学校で語れる範囲が変わる公教育コードの転換=制度的前提の書き換え。"),
            "uk_scottish_referendum_2014": ("PASSIVE", ["belonging"],
                "直接の投票当事者ではなく、英国の構成を考える背景的政治記憶として受動的に受容された。"),
            "uk_same_sex_marriage_2014": ("PASSIVE", ["civic_norm"],
                "支持が既に広がる層では当然の権利確定として日常規範に滑り込み、受動的に受容された。"),
            "uk_immigration_debate_2015": ("REFRAME", ["belonging", "racial_consciousness"],
                "移民が政策対象ではなく自分の所属条件を問う言説として響き、『英国的であること』の基準値が揺らいだ。"),
            "uk_brexit_2016": ("REFRAME", ["belonging", "national_self_image"],
                "開放的英国という所属基準が揺らぎ、欧州移動・多文化都市の当然性が書き換わった。"),
            "uk_windrush_2018": ("REFRAME", ["belonging", "racial_consciousness"],
                "形式的合法性だけでは所属が保証されないという、人種化された市民権の基準変更として着弾した。"),
            "uk_covid_lockdown_2020": ("REFRAME", ["public_health", "racial_consciousness"],
                "多世代世帯・前線労働・少数民族の高死亡率が露わになり、『誰が守られるか』の基準値が書き換わった。"),
            "uk_cost_of_living_2022": ("ACTIVE", ["economic_pressure", "mobility_aspiration"],
                "家賃・食費・家族支援の再配分を迫り、都市生活の維持戦略を能動的に変えた。"),
            "uk_nhs_crisis_2022": ("ACTIVE", ["public_health", "institutional_faith"],
                "家族の医療アクセス・民間医療利用・介護判断という能動的意思決定を迫った。"),
        },
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True, help="us | uk")
    ap.add_argument("--variant", default="grid")
    args = ap.parse_args()
    country, variant = args.country.lower(), args.variant.lower()
    tag = country if variant == "v1" else f"{country}_{variant}"

    src = DATA / f"events_{country}_{variant}.jsonl"   # ChatGPT grid = event メタの出所
    meta = {}
    for l in src.read_text(encoding="utf-8").splitlines():
        if l.strip():
            o = json.loads(l)
            meta[o["event_id"]] = o

    judg = JUDGMENTS.get(country, {})
    records = []
    n_cells = 0
    for premise, ev_map in judg.items():
        for eid, (mode, emphasis, rationale) in ev_map.items():
            m = meta.get(eid)
            if not m:
                raise SystemExit(f"[error] event_id がデータに無い: {eid}")
            records.append({
                "event_id": eid,
                "country": country.upper(),
                "name": m["name"],
                "event_cluster": m.get("event_cluster"),
                "exposure_type": m.get("exposure_type"),
                "year": m.get("year"),
                "effective_year": m.get("effective_year"),
                "domain": m.get("domain"),
                "possible_modes": m.get("possible_modes") or DEFAULT_MODES,
                "base_effect_vector": m.get("base_effect_vector", {}),
                "affected_groups": [{
                    "premise": premise,
                    "expected_mode": mode,
                    "effect_emphasis": emphasis,
                    "rationale": rationale,
                    "rationale_scope": "community_interpretation",
                }],
                "observer_note": "Claude as second observer; independent judgment from community premise (not copied from ChatGPT). Fills Gemini recovery gap.",
            })
            n_cells += 1

    # event_id ごとに1レコードへ畳む(同一eventに複数共同体がある将来に備え affected_groups を統合)
    by_eid = {}
    for r in records:
        if r["event_id"] in by_eid:
            by_eid[r["event_id"]]["affected_groups"] += r["affected_groups"]
        else:
            by_eid[r["event_id"]] = r

    out = DATA / f"Claude_events_{tag}.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in by_eid.values()) + "\n",
                   encoding="utf-8")
    print(f"[claude observer] {out.name}: events {len(by_eid)} / cells {n_cells} "
          f"/ communities {len(judg)}")
    for premise in judg:
        modes = [v[0] for v in judg[premise].values()]
        from collections import Counter
        print(f"  {premise}: " + dict(Counter(modes)).__repr__())


if __name__ == "__main__":
    main()
