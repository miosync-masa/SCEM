#!/usr/bin/env python3
"""
merge_paper2_data.py — SCEM Paper 2 国別 event DB 統合(ChatGPT版 × Gemini版)

Honest Structuralism の Axiom 2 (Non-overwrite) を構造的に守るため、
  LOD 0 = 事象の数理属性     → events_{country}_merged.jsonl
  LOD 1 = 解釈(source_model付)→ interpretations_{country}.jsonl
を【物理的に分離】する。解釈は必ず source_model 付きで保存し、
「事象がこうだった」と断定できないようにする。

LLM 呼び出しなし。ファイル読み書きのみ。

Usage:
    python3 merge_paper2_data.py --country us
    python3 merge_paper2_data.py --country uk   # 後日 UK 版

入力 (data/):
    events_{country}_v1.jsonl          # ChatGPT 版
    Gemini_events_{country}_v1.jsonl   # Gemini 版
出力 (data/):
    events_{country}_merged.jsonl      # LOD 0: 事象の数理属性のみ(affected_groups は含めない)
    interpretations_{country}.jsonl    # LOD 1: 解釈ベルト(source_model 付き)
    disagreements_{country}.jsonl      # 不一致レジストリ(interpretations 由来)
    merge_report_{country}.md          # 統合ログ(人間可読)
"""
from __future__ import annotations
import argparse
import json
import re
import itertools
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

# ── 必須カバー event(国別。英語 or 日本語の distinctive 部分文字列で在否チェック) ──
#   US 固有事象(Roe/Dobbs/Obama 等)を UK に当てても無意味なので国別に分ける。
REQUIRED_BY_COUNTRY = {
    "us": [
        ("Roe v. Wade", ["Roe v. Wade", "ロー対ウェイド"]),
        ("Dobbs", ["Dobbs"]),
        ("Obergefell", ["Obergefell"]),
        ("9.11 / September 11", ["September 11", "9.11", "9・11"]),
        ("Lehman / リーマン", ["Lehman", "リーマン"]),
        ("Obama当選", ["Obama elected", "Barack Obama", "Obama当選", "オバマ大統領選出"]),
        ("BLM", ["Black Lives Matter", "BLM"]),
        ("Trump当選", ["Trump elected", "Trump Presidential Election", "トランプ大統領当選", "Trump return"]),
        ("コロナ規制", ["COVID-19 pandemic restrictions", "COVID-19 Pandemic Lockdowns", "コロナ規制", "ロックダウン"]),
        ("銃乱射 (shooting)", ["shooting", "Shooting", "Massacre", "銃乱射", "銃撃"]),
        ("AIDS", ["AIDS"]),
        ("公民権法 / Civil Rights Act", ["Civil Rights Act", "公民権法"]),
        ("投票権法 / Voting Rights Act", ["Voting Rights Act", "投票権法"]),
    ],
    # UK の必須リストは未設定(Brexit/NHS/Thatcher 等を環&masamichi が後で定義)。
}

# ── premise 正規化(religion_race_region_education 順)用カテゴリ辞書 ──
RELIGION = {"evangelical", "mainline_protestant", "protestant", "secular",
            "catholic", "muslim", "jewish", "mormon", "nonreligious"}
RACE = {"white", "black", "hispanic", "asian", "native", "multiracial"}
REGION = {"bible_belt", "coastal", "urban", "rural", "suburban", "south",
          "rust_belt", "mountain_west", "west", "midwest", "northeast",
          "appalachia", "sunbelt"}
EDU = {"no_college", "some_college", "bachelor", "graduate", "college",
       "high_school", "advanced_degree"}
CATEGORY = {}
for s, c in [(RELIGION, "religion"), (RACE, "race"), (REGION, "region"), (EDU, "edu")]:
    for t in s:
        CATEGORY[t] = c
MULTIWORD = {("mainline", "protestant"), ("bible", "belt"), ("rust", "belt"),
             ("mountain", "west"), ("no", "college"), ("some", "college"),
             ("high", "school"), ("advanced", "degree")}

SCOPE_PRIORITY = ["national", "regional", "class_specific", "community_specific"]
CONF_PRIORITY = ["low", "medium", "high"]   # 左ほど保守的(低い)= 優先採用

# 既知エイリアス(正規化後の文字列 → 正規形)。表記揺れ + 人間レビュー確定マージ。
ALIASES = {
    "roe vs wade": "roe v wade",
    # ── 2026-06-25 人間レビューで確定した同一事象(Gemini 形 → ChatGPT 形)──
    "apollo 11 moon landing": "moon landing apollo 11",
    "parkland school shooting and march for our lives": "parkland shooting and march for our lives",
    "o j simpson murder trial verdict": "o j simpson trial verdict",
    "uvalde robb elementary school shooting": "uvalde robb elementary shooting",
    "sandy hook elementary school shooting": "sandy hook elementary shooting",
    "black monday stock market crash": "black monday stock crash",
    "occupy wall street movement": "occupy wall street",
    "generative ai boom and chatgpt public release": "chatgpt public release and generative ai shock",
    "affordable care act signed": "affordable care act",
    # ── UK: 人間レビューで確定した同一事象(Gemini 形 → ChatGPT 形)──
    "death of queen elizabeth ii": "queen elizabeth ii death",
    "nhs waiting list crisis": "nhs waiting list record crisis",
    "eu enlargement migration surge": "eu enlargement migration",
}


# ───────────────────────────────────────────────
# 名前正規化
# ───────────────────────────────────────────────
def normalize_name(name: str) -> str:
    """英語部分を抽出して正規化。区切りは '/' と '(' のみ。
    ハイフンは COVID-19 / Dot-com / Israel-Hamas のように語内に出るため切らない
    (切ると別事象が同一文字列へ潰れる)。"""
    s = name
    cut = len(s)
    for sep in ("/", "("):
        i = s.find(sep)
        if i != -1:
            cut = min(cut, i)
    s = s[:cut]
    s = s.lower()
    s = s.replace("&", " and ")
    s = s.replace("’", "").replace("'", "").replace("`", "")
    s = re.sub(r"[^a-z0-9]+", " ", s)        # 記号→空白
    s = re.sub(r"\bvs\b", "v", s)            # vs / v / v. を v に統一
    s = re.sub(r"\s+", " ", s).strip()
    return ALIASES.get(s, s)


def jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ───────────────────────────────────────────────
# premise 正規化(religion_race_region_education 順)
# ───────────────────────────────────────────────
def _merge_multiword(tokens: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(tokens):
        if i + 1 < len(tokens) and (tokens[i], tokens[i + 1]) in MULTIWORD:
            out.append(f"{tokens[i]}_{tokens[i + 1]}")
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    return out


def canonicalize_premise(premise: str) -> tuple[str, bool]:
    """demographic 4フィールドに綺麗に分類できれば religion_race_region_education 順へ。
    分類できない(未知トークン / カテゴリ重複 / role系premise)なら原文保持。
    返り値: (正規化後premise, 変更されたか)"""
    toks = _merge_multiword(premise.split("_"))
    slots = {"religion": None, "race": None, "region": None, "edu": None}
    for t in toks:
        if t == "any":
            continue
        cat = CATEGORY.get(t)
        if cat is None:
            return premise, False          # 未知トークン(role系等)→ 触らない
        if slots[cat] is not None:
            return premise, False          # 同カテゴリ重複(black_hispanic 等)→ 触らない
        slots[cat] = t
    canon = "_".join(slots[c] if slots[c] else "any"
                     for c in ["religion", "race", "region", "edu"])
    return canon, (canon != premise)


# ───────────────────────────────────────────────
# 数値統合ヘルパ
# ───────────────────────────────────────────────
def avg(a, b):
    return round((a + b) / 2, 4)


def merge_effect_vectors(va: dict, vb: dict) -> dict:
    out = {}
    for k in set(va) | set(vb):
        if k in va and k in vb:
            out[k] = avg(float(va[k]), float(vb[k]))
        else:
            out[k] = float(va.get(k, vb.get(k)))
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))  # 同値はキー名で決定論化


def pick_priority(a, b, order, default_first=True):
    def rank(x):
        return order.index(x) if x in order else len(order)
    return a if rank(a) <= rank(b) else b


# ───────────────────────────────────────────────
# メイン
# ───────────────────────────────────────────────
def load_jsonl(path: Path) -> tuple[list[dict], list[tuple]]:
    """壊れた行はスキップして(rows, errors)を返す。DeepResearch 出力の不正行に頑健。
    errors = [(行番号, 理由)]。"""
    rows, errors = [], []
    for ln, l in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        l = l.strip()
        if not l:
            continue
        try:
            rows.append(json.loads(l))
        except json.JSONDecodeError as e:
            errors.append((ln, str(e)[:60]))
    return rows, errors


def lod0_record(ev: dict, source_models: list[str]) -> dict:
    """events_merged.jsonl 用の LOD0 レコード(affected_groups を含めない)。"""
    return {
        "name": ev["name"],
        "year": ev.get("year"),
        "effective_year": ev.get("effective_year"),
        "domain": ev.get("domain"),
        "possible_modes": ev.get("possible_modes", []),
        "base_effect_vector": ev.get("base_effect_vector", {}),
        "agency": ev.get("agency"),
        "salience": ev.get("salience"),
        "sensitivity_peak_age": ev.get("sensitivity_peak_age"),
        "sensitivity_spread": ev.get("sensitivity_spread"),
        "reframe_group": ev.get("reframe_group"),
        "reference_value": ev.get("reference_value"),
        "source_scope": ev.get("source_scope"),
        "confidence": ev.get("confidence"),
        "source_models": source_models,
        "source_urls": ev.get("source_urls", []),
    }


def merge_consensus(cg: dict, ge: dict, warnings: list) -> dict:
    name = cg["name"]
    # year
    year = cg.get("year")
    if cg.get("year") != ge.get("year"):
        warnings.append(("year", name, f"chatgpt={cg.get('year')} gemini={ge.get('year')} → chatgpt採用"))
    # effective_year
    ce, gee = cg.get("effective_year"), ge.get("effective_year")
    if ce is not None and gee is not None:
        eff = int(round((ce + gee) / 2))
        if abs(ce - gee) >= 3:
            warnings.append(("effective_year", name, f"chatgpt={ce} gemini={gee} 差{abs(ce-gee)}年"))
    else:
        eff = ce if ce is not None else gee
    # domain
    domain = cg.get("domain")
    if cg.get("domain") != ge.get("domain"):
        warnings.append(("domain", name, f"chatgpt={cg.get('domain')} gemini={ge.get('domain')} → chatgpt採用"))
    # reframe_group
    if cg.get("reframe_group") == ge.get("reframe_group"):
        reframe = cg.get("reframe_group")
    else:
        reframe = None
        warnings.append(("reframe_group", name, f"chatgpt={cg.get('reframe_group')} gemini={ge.get('reframe_group')} → null"))
    # reference_value
    cr, gr = cg.get("reference_value"), ge.get("reference_value")
    if cr is not None and gr is not None:
        refval = avg(float(cr), float(gr))
    elif cr is not None:
        refval = cr
    elif gr is not None:
        refval = gr
    else:
        refval = None
    # numeric averages
    def avg_field(f):
        a, b = cg.get(f), ge.get(f)
        if a is None or b is None:
            return a if a is not None else b
        return avg(float(a), float(b))

    return {
        "name": name,
        "year": year,
        "effective_year": eff,
        "domain": domain,
        "possible_modes": sorted(set(cg.get("possible_modes", [])) | set(ge.get("possible_modes", []))),
        "base_effect_vector": merge_effect_vectors(cg.get("base_effect_vector", {}), ge.get("base_effect_vector", {})),
        "agency": avg_field("agency"),
        "salience": avg_field("salience"),
        "sensitivity_peak_age": avg_field("sensitivity_peak_age"),
        "sensitivity_spread": avg_field("sensitivity_spread"),
        "reframe_group": reframe,
        "reference_value": refval,
        "source_scope": pick_priority(cg.get("source_scope"), ge.get("source_scope"), SCOPE_PRIORITY),
        "confidence": pick_priority(cg.get("confidence"), ge.get("confidence"), CONF_PRIORITY),
        "source_models": ["chatgpt", "gemini"],
        "source_urls": list(dict.fromkeys((cg.get("source_urls") or []) + (ge.get("source_urls") or []))),
    }


def expand_interpretations(event_name: str, ev: dict, source_model: str, country: str,
                           premise_changes: list) -> list[dict]:
    out = []
    for ag in ev.get("affected_groups", []):
        raw = ag.get("premise", "")
        canon, changed = canonicalize_premise(raw)
        if changed:
            premise_changes.append((source_model, raw, canon))
        # effect_emphasis は UK 版用フィールド。US では存在せず null。
        emphasis = ag.get("effect_emphasis") if country != "us" else None
        out.append({
            "event_name": event_name,
            "source_model": source_model,
            "premise": canon,
            "expected_mode": ag.get("expected_mode"),
            "rationale": ag.get("rationale"),
            "effect_emphasis": emphasis,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="us", help="us | uk")
    args = ap.parse_args()
    country = args.country.lower()

    cg_path = DATA / f"events_{country}_v1.jsonl"
    ge_path = DATA / f"Gemini_events_{country}_v1.jsonl"
    for p in (cg_path, ge_path):
        if not p.exists():
            raise SystemExit(f"[error] 入力が見つかりません: {p}")

    cg_events, cg_err = load_jsonl(cg_path)
    ge_events, ge_err = load_jsonl(ge_path)
    warnings: list = []
    premise_changes: list = []

    # ── Step 1: 名前マッチング ──
    cg_norm = {}
    for ev in cg_events:
        n = normalize_name(ev["name"])
        if n in cg_norm:
            warnings.append(("name_collision_chatgpt", ev["name"], f"正規化衝突 '{n}'"))
        cg_norm.setdefault(n, ev)
    ge_norm = {}
    for ev in ge_events:
        n = normalize_name(ev["name"])
        if n in ge_norm:
            warnings.append(("name_collision_gemini", ev["name"], f"正規化衝突 '{n}'"))
        ge_norm.setdefault(n, ev)

    consensus_keys = sorted(set(cg_norm) & set(ge_norm))
    cg_only_keys = sorted(set(cg_norm) - set(ge_norm))
    ge_only_keys = sorted(set(ge_norm) - set(cg_norm))

    # Jaccard 候補(完全一致しない CG×GE のうち 0.7 以上)= 人間レビュー用、自動マージしない
    jaccard_candidates = []
    for ck in cg_only_keys:
        for gk in ge_only_keys:
            j = jaccard(ck, gk)
            if j >= 0.7:
                jaccard_candidates.append((round(j, 3), cg_norm[ck]["name"], ge_norm[gk]["name"]))
    jaccard_candidates.sort(reverse=True)

    # ── Step 2 & 3: events_merged 構築 ──
    merged_events = []          # (key, merged_record, contributing) for interpretation 展開
    for k in consensus_keys:
        rec = merge_consensus(cg_norm[k], ge_norm[k], warnings)
        merged_events.append((k, rec, {"chatgpt": cg_norm[k], "gemini": ge_norm[k]}))
    for k in cg_only_keys:
        merged_events.append((k, lod0_record(cg_norm[k], ["chatgpt"]), {"chatgpt": cg_norm[k]}))
    for k in ge_only_keys:
        merged_events.append((k, lod0_record(ge_norm[k], ["gemini"]), {"gemini": ge_norm[k]}))

    # ── Step 4: interpretations 展開 ──
    interpretations = []
    for k, rec, contrib in merged_events:
        for model in ("chatgpt", "gemini"):
            if model in contrib:
                interpretations += expand_interpretations(rec["name"], contrib[model], model, country, premise_changes)

    # ── Step 5: disagreements 抽出(consensus event のみ。片側のみ event は対象外) ──
    # スキーマ汎用化: chatgpt_value / gemini_value(mode も domain も effective_year もここに入る)。
    # premise が "_event_level" の行は event 単位の不一致(domain / effective_year / reframe_group)。
    def disagree(event_name, year, premise, dtype, cval, gval, crat=None, grat=None, note=None):
        return {
            "event_name": event_name, "year": year, "premise": premise,
            "disagreement_type": dtype,
            "chatgpt_value": cval, "gemini_value": gval,
            "chatgpt_rationale": crat, "gemini_rationale": grat,
            "interpretation_note": note,
            "interpretive_axis": None, "real_community_parallel": None, "paper2_significance": None,
        }

    disagreements = []

    # (5a) event 単位の観測者依存(consensus のみ)。
    #   これらは「矛盾」ではなく、単一の多次元 FACT のどの側面を表示タグに選んだかの分散。
    #   Paper 1 §3.4「イベントを単一カテゴリに潰さない / domain は表示タグ」の Paper 2 反復確認。
    NOTE_DOMAIN = ("単一FACTの複数次元のうちどれを表示タグに選ぶかの観測者依存。両値とも妥当な一側面であり、"
                   "domain は表示タグであって事実の本体ではない(Paper 1 §3.4 と同型)。")
    NOTE_EFFYEAR = ("「いつ着弾したか」の解釈差(成立/施行/普及のどの時点を effective_year とみなすか)。"
                    "事象の発生は単一FACTだが、効力発生時点の選択は観測者依存。")
    NOTE_REFRAME = ("同一事象をどの参照軸(基準値書き換え系列)に置くかの選択差。軸選択は解釈であり、"
                    "事象そのものは単一FACT。")
    for k, rec, contrib in merged_events:
        if not ("chatgpt" in contrib and "gemini" in contrib):
            continue
        cg, ge = contrib["chatgpt"], contrib["gemini"]
        name = rec["name"]
        if cg.get("domain") != ge.get("domain"):
            disagreements.append(disagree(name, rec["year"], "_event_level", "domain_observer_choice",
                                          cg.get("domain"), ge.get("domain"), note=NOTE_DOMAIN))
        ce, gee = cg.get("effective_year"), ge.get("effective_year")
        if ce is not None and gee is not None and ce != gee:
            disagreements.append(disagree(name, rec["year"], "_event_level", "effective_year_interpretation",
                                          ce, gee, note=NOTE_EFFYEAR))
        if cg.get("reframe_group") != ge.get("reframe_group"):
            disagreements.append(disagree(name, rec["year"], "_event_level", "reframe_group_axis_choice",
                                          cg.get("reframe_group"), ge.get("reframe_group"), note=NOTE_REFRAME))

    # (5b) premise 単位の不一致: mode / premise_only_in_*
    by_event_model = defaultdict(lambda: defaultdict(dict))  # event -> model -> {premise: interp}
    for it in interpretations:
        by_event_model[it["event_name"]][it["source_model"]][it["premise"]] = it
    for k, rec, contrib in merged_events:
        if not ("chatgpt" in contrib and "gemini" in contrib):
            continue
        name = rec["name"]
        cg_i = by_event_model[name]["chatgpt"]
        ge_i = by_event_model[name]["gemini"]
        cps, gps = set(cg_i), set(ge_i)
        for p in sorted(cps & gps):
            if cg_i[p]["expected_mode"] != ge_i[p]["expected_mode"]:
                disagreements.append(disagree(name, rec["year"], p, "mode",
                                              cg_i[p]["expected_mode"], ge_i[p]["expected_mode"],
                                              cg_i[p]["rationale"], ge_i[p]["rationale"]))
        for p in sorted(cps - gps):
            disagreements.append(disagree(name, rec["year"], p, "premise_only_in_chatgpt",
                                          cg_i[p]["expected_mode"], None, cg_i[p]["rationale"], None))
        for p in sorted(gps - cps):
            disagreements.append(disagree(name, rec["year"], p, "premise_only_in_gemini",
                                          None, ge_i[p]["expected_mode"], None, ge_i[p]["rationale"]))

    # ── 出力 ──
    def write_jsonl(path, rows):
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    ev_out = DATA / f"events_{country}_merged.jsonl"
    int_out = DATA / f"interpretations_{country}.jsonl"
    dis_out = DATA / f"disagreements_{country}.jsonl"
    rep_out = DATA / f"merge_report_{country}.md"

    write_jsonl(ev_out, [rec for _, rec, _ in merged_events])
    write_jsonl(int_out, interpretations)
    write_jsonl(dis_out, disagreements)

    # ── 集計 ──
    src_counter = Counter(it["source_model"] for it in interpretations)
    dis_counter = Counter(d["disagreement_type"] for d in disagreements)
    warn_counter = Counter(w[0] for w in warnings)
    # 必須カバー(国別。未設定の国は N/A)
    all_names = [rec["name"] for _, rec, _ in merged_events]
    blob = " || ".join(all_names)
    required = REQUIRED_BY_COUNTRY.get(country, [])
    required_status = [(label, any(kw in blob for kw in kws)) for label, kws in required]

    # ── merge_report ──
    L = []
    L.append(f"# Merge Report — Paper 2 {country.upper()} 版\n")
    L.append("## 入力\n")
    L.append(f"- ChatGPT 版 (`{cg_path.name}`): **{len(cg_events)}** 件"
             + (f" (JSON不正で{len(cg_err)}行スキップ)" if cg_err else ""))
    L.append(f"- Gemini 版 (`{ge_path.name}`): **{len(ge_events)}** 件"
             + (f" (JSON不正で{len(ge_err)}行スキップ)" if ge_err else "") + "\n")
    if cg_err or ge_err:
        L.append("> ⚠️ 入力に JSON 不正行あり(スキップ済)。捏造補修はしていない。"
                 "二モデル統合には両ファイルの健全性が必要。\n")
    L.append("## マッチング結果\n")
    L.append(f"- consensus(両方で名前一致): **{len(consensus_keys)}** 件")
    L.append(f"- chatgpt_only: **{len(cg_only_keys)}** 件")
    L.append(f"- gemini_only: **{len(ge_only_keys)}** 件")
    L.append(f"- 統合後 `events_{country}_merged.jsonl` 総数: **{len(merged_events)}** 件 "
             f"(consensus {len(consensus_keys)} + singleton {len(cg_only_keys) + len(ge_only_keys)})\n")
    L.append("> 名前正規化: `/` と `(` の手前で英語部分を抽出(ハイフンは COVID-19/Dot-com 等の語内ハイフンのため切らない)。"
             "小文字化・記号除去・`vs`→`v` 統一・空白正規化。完全一致 + エイリアスのみ自動マージ。\n")
    L.append("### 人間レビュー要: Jaccard 0.7–1.0 候補(自動マージしていない)\n")
    if jaccard_candidates:
        for j, a, b in jaccard_candidates:
            L.append(f"- `{j}`  ChatGPT「{a}」  ↔  Gemini「{b}」")
    else:
        L.append("- (なし)")
    L.append("\n### consensus events 一覧\n")
    for k in consensus_keys:
        L.append(f"- {cg_norm[k]['name']}")
    L.append("\n### chatgpt_only\n")
    for k in cg_only_keys:
        L.append(f"- {cg_norm[k]['name']}")
    L.append("\n### gemini_only\n")
    for k in ge_only_keys:
        L.append(f"- {ge_norm[k]['name']}")
    L.append("\n## interpretations\n")
    L.append(f"- 総レコード数: **{len(interpretations)}**(chatgpt {src_counter['chatgpt']} / gemini {src_counter['gemini']})")
    L.append(f"- premise 正規化(religion_race_region_education 順へ並べ替え)した件数: **{len(premise_changes)}**\n")
    L.append("## disagreements\n")
    L.append(f"- 総数: **{len(disagreements)}**")
    L.append("- premise 単位(解釈ベルト由来):")
    for t in ("mode", "premise_only_in_chatgpt", "premise_only_in_gemini"):
        L.append(f"  - {t}: {dis_counter.get(t, 0)}")
    L.append("- event 単位 = observer-dependent labeling(premise=`_event_level`。"
             "矛盾ではなく、単一FACTのどの表示タグを選んだかの分散):")
    for t in ("domain_observer_choice", "effective_year_interpretation", "reframe_group_axis_choice"):
        L.append(f"  - {t}: {dis_counter.get(t, 0)}")
    L.append("\n## Observer-dependent labeling(観測者依存ラベリング)\n")
    L.append("event 単位の不一致は **「矛盾」ではない**。単一の多次元 FACT に対して、どの次元を表示タグ"
             "(domain / effective_year の基準点 / reframe 軸)に選ぶかが観測者(LLM)ごとに分散しているだけである。"
             "`disagreements_{country}.jsonl` はこの分散を記録する **「LLM 観測者依存の証拠ファイル」** として読む。\n")
    L.append("- これは Paper 1 §3.4 設計ノート(**「イベントを単一カテゴリに潰さない / domain は表示タグであり"
             "計算には使わない」**)の **Paper 2 における反復確認**である。")
    L.append("  - 例(ACA): public_health / politics_institution / economy_employment に**同時に作用した FACT**。"
             "domain ラベルが割れるのは、複数次元のどれを表示タグに選ぶかの観測者依存にすぎない。")
    L.append("- 観察された系統的傾向: **ChatGPT は「何が起きたか」(事実層・LOD 0 寄り)**、"
             "**Gemini は「社会的に何を意味したか」(意味層・LOD 1 寄り)** に寄る。")
    L.append("  - domain: Apollo 11 / O.J. Simpson を ChatGPT=`media_technology`(技術事象)、"
             "Gemini=`lifestyle_culture`(文化的意味)。")
    L.append("  - effective_year: ACA を ChatGPT=2010(成立)、Gemini=2014(施行)。")
    L.append("  - reframe_group: Gemini は 9.11 / Katrina / January 6 を "
             "`national_security` / `trust_in_government` に集約しがち。")
    L.append("- 含意: **観測者依存は LOD 1 ではなく LOD 0(表示タグ層)から始まる**。"
             "ゆえに domain も本来 interpretation 側に属し得る(各レコードの `interpretation_note` 参照、"
             "`interpretive_axis` 列で手動分析)。")
    L.append("\n## warnings\n")
    if warnings:
        for t, c in warn_counter.most_common():
            L.append(f"- {t}: {c} 件")
    else:
        L.append("- (なし)")
    L.append(f"\n## 必須カバー event 在否({country.upper()})\n")
    if required_status:
        for label, ok in required_status:
            L.append(f"- [{'x' if ok else ' '}] {label}")
    else:
        L.append(f"- N/A({country.upper()} の必須リストは未設定)")
    rep_out.write_text("\n".join(L) + "\n", encoding="utf-8")

    # ── 標準出力(完了報告) ──
    print("=" * 64)
    print(f"  merge_paper2_data.py --country {country}  完了")
    print("=" * 64)
    if cg_err or ge_err:
        print(f"  ⚠️ JSON不正スキップ: chatgpt {len(cg_err)}行 / gemini {len(ge_err)}行(捏造補修なし)")
    print(f"[1] events_{country}_merged.jsonl: {len(merged_events)} 件 "
          f"(consensus {len(consensus_keys)} + singleton {len(cg_only_keys)+len(ge_only_keys)} "
          f"[chatgpt_only {len(cg_only_keys)} / gemini_only {len(ge_only_keys)}])")
    print(f"[2] interpretations_{country}.jsonl: {len(interpretations)} レコード "
          f"(chatgpt {src_counter['chatgpt']} / gemini {src_counter['gemini']})")
    print(f"[3] disagreements_{country}.jsonl: {len(disagreements)} 件")
    print(f"      premise単位: mode {dis_counter.get('mode',0)} / "
          f"only_chatgpt {dis_counter.get('premise_only_in_chatgpt',0)} / "
          f"only_gemini {dis_counter.get('premise_only_in_gemini',0)}")
    print(f"      event単位(observer-dependent labeling): "
          f"domain_observer_choice {dis_counter.get('domain_observer_choice',0)} / "
          f"effective_year_interpretation {dis_counter.get('effective_year_interpretation',0)} / "
          f"reframe_group_axis_choice {dis_counter.get('reframe_group_axis_choice',0)}")
    print(f"[4] Jaccard 0.7–1.0 人間レビュー候補: {len(jaccard_candidates)} 組")
    for j, a, b in jaccard_candidates:
        print(f"      {j}  「{a[:38]}」 ↔ 「{b[:38]}」")
    print(f"[5] warnings: {sum(warn_counter.values())} 件  " + dict(warn_counter).__repr__())
    if required_status:
        print(f"[6] 必須カバー: {sum(1 for _,ok in required_status if ok)}/{len(required_status)} 在")
        for label, ok in required_status:
            print(f"      {'✓' if ok else '✗'} {label}")
    else:
        print(f"[6] 必須カバー: N/A({country.upper()} の必須リスト未設定)")
    print(f"\n出力: {ev_out.name} / {int_out.name} / {dis_out.name} / {rep_out.name}")


if __name__ == "__main__":
    main()
