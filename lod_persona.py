#!/usr/bin/env python3
"""
lod_persona.py — SCEM LOD ペルソナ生成プロトタイプ(Paper 2 素材 / MVP)

LOD_ARCHITECTURE.md §3(4戒律)・§4(CSP)・§7(実装仕様)に準拠。

役割分担(§1.1):
  LOD 0 = 数理 = 固定 = 曝露構造        … Paper 1 エンジン(v4/v5)で計算
  LOD 1〜3 = 解釈 = 分岐 = ペルソナ表現  … LLM(OpenAI)で生成

設計境界:
  - Paper 1 のエンジン(media_generation_v4.py / v5.py)には一切触らない(import のみ)
  - events_patched.jsonl にも触らない
  - 本ファイル単独で完結

CSP 定式化(§4):
  変数   = 各 LOD の解釈
  制約   = 4戒律 + ユーザー指定(lod1_response / lod2_strategy / lod3_context)
  SAT    = 全制約充足 → ペルソナ返却
  UNSAT  = 矛盾 → 理由付きでリジェクト

UNSAT 検出の3経路(§4.3):
  (1) 制約セット自体の矛盾   → 決定論的な時間アンカー検査(未来矛盾の検出)
  (2) LLM の Axiom 違反判断 → LLM が status=UNSAT を返す(自己認識のズレ等)
  (3) LLM の幻覚            → Projection Consistency 不足の backstop

Run:
    python3 lod_persona.py
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Paper 1 エンジンは reorg 後 src/ にある。import only(無改変)。
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv
from openai import OpenAI

import media_generation_v4 as v4
import media_generation_v5 as v5

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

DATA = Path(__file__).resolve().parent / "data"   # US/UK の merged / interpretations 置き場
FORMATIVE_CAP = 22          # 社会接続期(18-22)の上限。これ以降に着弾した事象は人格形成アンカーになり得ない
PROJECTION_THRESHOLD = 0.70  # §7.3 MVP の一致率閾値
MAX_RETRIES = 3


# ───────────────────────────────────────────────
# 入力(§7.1)
# ───────────────────────────────────────────────
@dataclass
class LODConstraints:
    birth_year: int
    lod1_response: Optional[str] = None      # "Fight" | "Flight" | None
    lod2_strategy: Optional[str] = None      # "技術で攻める" 等
    lod3_context: Optional[dict] = None       # {profession, region, formative_anchor, ...}
    lod0_exposure: Optional[dict] = None      # None なら build_lod0_exposure で自動構築
    country: str = "jp"                       # "jp"(Paper1 Japan) | "us" | "uk"
    premise: Optional[str] = None             # us/uk のみ。個人の religion_race_region_education。
                                              # None なら全premise集約(一般person)。


# ───────────────────────────────────────────────
# LOD 0 = 曝露構造(数理アンカー)
#   v5 に build_exposure_profile は無いため、既存関数を合成して構築する:
#     v5.load_events() → v4.analyze() → v5.mode_density()
# ───────────────────────────────────────────────
def build_lod0_exposure(birth_year: int, events=None) -> dict:
    """Japan(Paper 1)LOD0。v5.load_events()(events_patched.jsonl)を既定で読む。"""
    if events is None:
        events = v5.load_events()
    return _lod0_from_v4_events(birth_year, events)


def _lod0_from_v4_events(birth_year: int, events) -> dict:
    """v4.Event のリストから LOD0 プロファイルを構築(Japan/US 共通。Paper 1 エンジン無改変)。"""
    hits, interferences, reframe_fires, _overlap = v4.analyze(birth_year, events)
    dP = v5.mode_density(hits, v4.Mode.PASSIVE)
    dA = v5.mode_density(hits, v4.Mode.ACTIVE)
    dR = v5.mode_density(hits, v4.Mode.REFRAME)
    top = sorted(hits, key=lambda h: -h["weight"])[:10]

    def _mode_top(mode, n=5):
        ms = sorted((h for h in hits if h["ev"].mode is mode), key=lambda h: -h["weight"])[:n]
        return [
            {"name": h["ev"].name, "age": h["age"], "stage": h["stage"],
             "domain": h["ev"].domain.value, "weight": h["weight"]}
            for h in ms
        ]

    return {
        "birth_year": birth_year,
        "fingerprint": {"PASSIVE": dP["mean"], "ACTIVE": dA["mean"], "REFRAME": dR["mean"]},
        "top_events": [
            {
                "name": h["ev"].name, "age": h["age"], "stage": h["stage"],
                "mode": h["ev"].mode.value, "domain": h["ev"].domain.value,
                "weight": h["weight"],
            }
            for h in top
        ],
        # mode別 top: weight順の top_events は PASSIVE に潰れがちなので、
        # ACTIVE(=意思決定を強制された痕跡)・REFRAME を明示的に可視化する。
        "top_active": _mode_top(v4.Mode.ACTIVE),
        "top_reframe": _mode_top(v4.Mode.REFRAME),
        "interference": [
            {"pair": list(it["pair"]), "stage": it["stage"]} for it in interferences[:5]
        ],
        "reframe_fires": [
            {"group": r["group"], "anchor": r["anchor"][0], "trigger": r["trigger"][0]}
            for r in reframe_fires[:5]
        ],
    }


# ───────────────────────────────────────────────
# US/UK LOD0 = Contextual Mode Resolver(論文 §2.5)
#   US merged は単一 mode を持たない(possible_modes のみ)。事象の mode は
#   個人の premise で interpretations から解決される(Event × premise → ResolvedImpact)。
#   解決済み mode で v4.Event を組み、既存 Paper 1 エンジン(v4.analyze)に投入する。
# ───────────────────────────────────────────────
from collections import Counter as _Counter

_MODE_PRIORITY = ["ACTIVE", "REFRAME", "PASSIVE"]   # 不一致時のtie-break(決断強制を優先)

# US ドメイン文字列 → v4.Domain(表示タグのみ。purified エンジンでは計算に非関与)
_US_DOMAIN_MAP = {
    "politics_institution": "POLITICS", "international_geopolitics": "GEOPOLITICS",
    "media_technology": "MEDIA", "finance_assets": "FINANCE", "prices": "PRICE",
    "education_system": "EDUCATION", "disaster_crisis": "DISASTER",
    "economy_employment": "ECONOMY", "public_health": "HEALTH",
    "platform": "PLATFORM", "lifestyle_culture": "LIFESTYLE",
}


def _resolve_mode(event_name: str, premise: Optional[str], interp_index: dict):
    """Event × premise → ResolvedImpact の mode。
    premise 指定: その premise の interpretation から解決。両モデル一致→確定、
                  不一致→多数決+priority で tie-break(由来は disagreement に既出)。
    premise None: その事象の全 interpretation(全premise・両モデル)を多数決で集約。
    interpretation 無し: PASSIVE(ambient = 国家的事象への受動曝露の既定)。"""
    cands = interp_index.get(event_name, [])
    matched = [i for i in cands if (premise is None or i["premise"] == premise)]
    if not matched:
        return "PASSIVE", "default_ambient", None
    cnt = _Counter(i["expected_mode"] for i in matched)
    if len(cnt) == 1:
        return next(iter(cnt)), "resolved_agree", None
    best = sorted(cnt, key=lambda m: (-cnt[m], _MODE_PRIORITY.index(m) if m in _MODE_PRIORITY else 9))[0]
    return best, "resolved_disagree", dict(cnt)


def build_us_v4_events(country: str, premise: Optional[str]):
    """events_{country}_merged.jsonl + interpretations_{country}.jsonl から
    mode 解決済みの v4.Event リストを作る。返り値: (events, resolution_log)。"""
    merged = [json.loads(l) for l in (DATA / f"events_{country}_merged.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]
    interps = [json.loads(l) for l in (DATA / f"interpretations_{country}.jsonl")
               .read_text(encoding="utf-8").splitlines() if l.strip()]
    interp_index: dict = {}
    for it in interps:
        interp_index.setdefault(it["event_name"], []).append(it)

    events, log = [], []
    for o in merged:
        mode, how, detail = _resolve_mode(o["name"], premise, interp_index)
        dom_name = _US_DOMAIN_MAP.get(o.get("domain"), "POLITICS")
        try:
            dom = v4.Domain[dom_name]
        except KeyError:
            dom = v4.Domain.POLITICS
        ev = v4.Event(
            name=o["name"],
            year=int(o.get("effective_year") or o.get("year")),   # 作用年で着弾年齢を計算
            domain=dom,
            mode=v4.Mode[mode],
            agency=float(o.get("agency") or 0.3),
            description="",
            reframe_group=o.get("reframe_group"),
            reference_value=o.get("reference_value"),
            salience=float(o.get("salience") or 1.0),
            effect_vector=dict(o.get("base_effect_vector") or {}),
        )
        # v5.patched_mode_weight が読む個別感受性ブリッジ属性
        ev._peak_age = o.get("sensitivity_peak_age")   # type: ignore[attr-defined]
        ev._spread = o.get("sensitivity_spread")        # type: ignore[attr-defined]
        events.append(ev)
        log.append((o["name"], mode, how))
    return events, log


def build_us_lod0(birth_year: int, country: str, premise: Optional[str]):
    """US/UK LOD0 を構築。返り値: (lod0_dict, v4_events, resolution_log)。"""
    events, log = build_us_v4_events(country, premise)
    lod0 = _lod0_from_v4_events(birth_year, events)
    how_counter = _Counter(h for _, _, h in log)
    lod0["resolution"] = {
        "country": country, "premise": premise or "(全premise集約)",
        "events_total": len(events),
        "resolved_agree": how_counter.get("resolved_agree", 0),
        "resolved_disagree": how_counter.get("resolved_disagree", 0),
        "default_ambient": how_counter.get("default_ambient", 0),
    }
    return lod0, events, log


def core_anchor_events(lod0: dict) -> list[str]:
    """Projection の判定基準となる core 事象(上位重み事象 Top8)。
    §7.3 の『核となる事象(上位重み事象)』に対応。"""
    return [e["name"] for e in lod0["top_events"][:8]]


# ───────────────────────────────────────────────
# (1) 決定論的 制約整合検査 — 未来矛盾(時間アンカー違反)の検出
#   Axiom 1 Anchor Preservation: 成人後に出会った事象を人格形成アンカーにはできない
# ───────────────────────────────────────────────
def check_constraints(constraints: LODConstraints, events) -> Optional[str]:
    ctx = constraints.lod3_context or {}
    anchor = ctx.get("formative_anchor")
    if not anchor:
        return None
    for ev in events:
        if anchor in ev.name or ev.name in anchor:
            age = ev.year - constraints.birth_year   # ev.year は effective_year(作用年)
            if age < 0:
                return (f"formative_anchor『{ev.name}』は{constraints.birth_year}年生まれの出生前"
                        f"(着弾年齢{age})。存在しない事象を人格形成アンカーにできない"
                        f"(Axiom 1 Anchor Preservation 違反)。")
            if age > FORMATIVE_CAP:
                return (f"formative_anchor『{ev.name}』の着弾年齢は{age}歳"
                        f"(>{FORMATIVE_CAP}=社会接続期の上限)。"
                        f"成人後({age}歳)に出会った事象を人格形成の核に据えることはできない"
                        f"(Axiom 1 Anchor Preservation 違反 / 未来矛盾)。")
            return None
    return None  # DB に無い anchor は検査対象外(LLM 側に委ねる)


# ───────────────────────────────────────────────
# (3) Projection Consistency — project(LOD3 → LOD0) ≈ LOD0 か(§3 Axiom3 / §7.3)
# ───────────────────────────────────────────────
def project_to_lod0(persona: dict, lod0: dict) -> tuple[float, list, list]:
    """生成ペルソナの provenance から LOD0 事象を抽出し、core 事象のカバー率を返す。"""
    prov_text = json.dumps(persona.get("provenance", ""), ensure_ascii=False)
    core = core_anchor_events(lod0)
    matched = [name for name in core if name in prov_text]
    rate = len(matched) / len(core) if core else 0.0
    return rate, matched, core


# ───────────────────────────────────────────────
# LLM 呼び出し(culture_axis.py と同じフォールバック方式; gpt-5.5 等の temperature 制約に対応)
# ───────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは SCEM(Situated Cohort Exposure Model)の LOD ペルソナ生成器です。

役割分担(厳守):
  LOD 0 = 数理が計算した曝露構造(事象・着弾年齢・作用モード・重み)。これは【不動の骨格】。
  LOD 1〜3 = あなたが足す解釈(応答方向 / 戦略 / 個人文脈)。情報を【足す】ことはできるが、
             LOD 0 を【書き換える】ことはできない。

あなたは以下の4戒律(SCEM Axioms)を必ず守る:
  Axiom 1 Anchor Preservation: LOD0 の事象・年齢・mode・weight は保存する。成人後に着弾した
          事象を人格形成の核に据えるなど、LOD0 と矛盾する解釈をしてはならない。
  Axiom 2 Non-overwrite: LOD0 の数値(例 PASSIVE 0.81)を変更しない。解釈は足すだけ。
  Axiom 3 Projection Consistency: あなたの解釈を要約すると LOD0 に戻れること。すなわち
          provenance は LOD0 の主要事象に紐づいていること。
  Axiom 4 Provenance Traceability: 各解釈要素が LOD0 のどの事象から導かれたかを明示する。

判断:
  - 与えられた制約(LOD1/2/3)が LOD0 と矛盾する(例: 成人後にしか着弾していない事象を
    人格形成・コアアイデンティティの前提にしている)なら、status="UNSAT" と reason を返す。
  - 【自己認識のズレ(self-perception mismatch)の検出】: ACTIVE モードの事象は
    「意思決定を強制された」ことを意味する。指定された応答方向や lod3 の自己申告が、
    LOD0 の高重み ACTIVE 事象の存在を否定する(例: Flight =「一度も決断を迫られず
    ただ流されてきた」と主張するが、LOD0 には高重みの ACTIVE 事象が刻まれている)場合、
    これは Axiom 1 Anchor Preservation 違反である。status="UNSAT" を返し、reason に
    「構造的には決断を強制された痕跡(Fight 寄り)があるのに Flight/無決断を自認している」
    という自己認識のズレを、該当する LOD0 の ACTIVE 事象名とともに具体的に明記する。
    解釈で取り繕って無理に SAT にしてはならない(これはカウンセリング応用の設計機能)。
  - 矛盾しないなら、LOD0 に根ざしたペルソナを生成し status="SAT" を返す。

出力は必ず次の JSON のみ(コードフェンス禁止):
{
  "status": "SAT" | "UNSAT",
  "reason": "UNSAT の場合の理由(SAT なら空文字)",
  "persona": {
    "summary": "この人物の一言要約(構造に根ざして)",
    "narrative": "2-4文。LOD0 の主要事象がどの年齢で着弾し、指定された応答方向・戦略が
                  どう表れるか。LOD0 の数値は変えない。",
    "provenance": [
      {"interpretation": "解釈要素", "derived_from": ["LOD0の事象名(正確に)", "..."]}
    ]
  }
}
provenance の derived_from には、提示された LOD0 の top_events / interference / reframe の
事象名を【正確な表記のまま】用いること。"""


def _call_llm(user_prompt: str) -> dict:
    client = OpenAI()
    base = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    attempts = [
        {**base, "temperature": 0.7, "response_format": {"type": "json_object"}},
        {**base, "response_format": {"type": "json_object"}},
        {**base},
    ]
    last = None
    for kw in attempts:
        try:
            resp = client.chat.completions.create(**kw)
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                raw = raw[4:] if raw.startswith("json") else raw
                raw = raw.strip().rstrip("`").strip()
            return json.loads(raw)
        except Exception as e:  # noqa: BLE001
            last = e
            continue
    raise RuntimeError(f"LLM 全 attempt 失敗: {last}")


def build_user_prompt(c: LODConstraints, lod0: dict, missing: Optional[list] = None,
                      best_persona: Optional[dict] = None) -> str:
    lines = [
        "## LOD 0(数理が計算した曝露構造 = 不動の骨格)",
        json.dumps(lod0, ensure_ascii=False, indent=2),
        "",
        "## 追加制約(CSP: LOD が上がるごとに解空間が狭まる)",
        f"- LOD1 応答方向: {c.lod1_response or '(未指定)'}",
        f"- LOD2 戦略: {c.lod2_strategy or '(未指定)'}",
        f"- LOD3 個人文脈: {json.dumps(c.lod3_context, ensure_ascii=False) if c.lod3_context else '(未指定)'}",
        "",
        "上記 LOD0 を保存したまま(Axiom 1/2)、指定された応答方向・戦略・文脈を解釈として足し、"
        "provenance で LOD0 事象への由来を明示(Axiom 4)してペルソナを生成してください。"
        "制約が LOD0 と矛盾する場合は status=UNSAT を返してください。",
    ]
    if best_persona is not None and missing:
        # 累積方式(cumulative augment best-so-far): whack-a-mole 対策。
        # ゼロから再生成せず、これまでで最も LOD0 をカバーした最良ペルソナを土台に、
        # 既存 provenance を一切削らず、不足 core 事象だけを追記させる(単調非減少)。
        lines += [
            "",
            "## 【累積改善 — 直前までの最良ペルソナを土台に追記(削除厳禁)】",
            "以下はこれまでで最も LOD0 をカバーしたあなたの生成です。",
            json.dumps(best_persona, ensure_ascii=False, indent=2),
            "この summary / narrative / provenance を【一字も削らず】保持したまま、",
            "下記の不足 core 事象についてのみ、provenance に項目を追加し、narrative に",
            "該当年齢での着弾を追記してください(既存の正しい紐づけは絶対に落とさない):",
            "  " + " / ".join(missing),
            "LOD0 の事実(年齢・mode)に忠実に。作り話で埋めない。",
        ]
    elif missing:
        # 誘導された自己修正(directed self-correction, 再生成方式): 不足 core 事象を
        # 差し戻して必ず含めさせる(ただし毎回ゼロから生成するため別事象を落とし得る=whack-a-mole)。
        lines += [
            "",
            "## 【前回生成の不足 — Projection Consistency 未達(再生成)】",
            "前回の provenance には、LOD0 の核となる事象のうち次が現れませんでした:",
            "  " + " / ".join(missing),
            "今回は上記の各事象について、それがこの人物に何歳でどう着弾し、指定の応答方向・"
            "戦略にどう効くかを narrative と provenance に【必ず】明示してください(Axiom 3/4)。"
            "ただし作り話で埋めず、LOD0 の事実(年齢・mode)に忠実に。",
        ]
    return "\n".join(lines)


# ───────────────────────────────────────────────
# CSP ソルバー本体: 制約検査 → LLM 生成 → Projection 検証ループ(§7.2)
# ───────────────────────────────────────────────
def solve(constraints: LODConstraints, max_retries: int = MAX_RETRIES,
          cumulative: bool = False) -> dict:
    """cumulative=False: 誘導された自己修正(毎回再生成。whack-a-mole あり)
       cumulative=True : 累積方式(最良ペルソナに不足分を追記。単調非減少を狙う)"""
    if constraints.country in ("us", "uk"):
        # Contextual Mode Resolver(§2.5): premise で mode 解決 → US LOD0
        if constraints.lod0_exposure:
            lod0 = constraints.lod0_exposure
            events, _log = build_us_v4_events(constraints.country, constraints.premise)
        else:
            lod0, events, _log = build_us_lod0(constraints.birth_year, constraints.country, constraints.premise)
    else:
        events = v5.load_events()
        lod0 = constraints.lod0_exposure or build_lod0_exposure(constraints.birth_year, events)

    # (1) 決定論的 制約整合検査(未来矛盾)
    reason = check_constraints(constraints, events)
    if reason:
        return {"status": "UNSAT", "stage": "constraint_precheck",
                "reason": reason, "attempts": 0, "persona": None}

    # (2)(3) LLM 生成 + Projection 検証ループ
    last_reason = None
    attempts = 0
    missing = None          # 前回不足の core 事象。retry 時にプロンプトへ差し戻す。
    rate_trace = []         # 各 attempt の projection 率(品質向上ループの可視化用)
    best_persona, best_rate, best_matched = None, -1.0, []   # 累積方式の最良解
    for attempts in range(1, max_retries + 1):
        prompt = build_user_prompt(
            constraints, lod0, missing,
            best_persona=best_persona if cumulative else None,
        )
        out = _call_llm(prompt)

        # (2) LLM 自己判定の UNSAT(Axiom 違反)
        if str(out.get("status", "")).upper() == "UNSAT":
            return {"status": "UNSAT", "stage": "llm_axiom",
                    "reason": out.get("reason", "LLM が Axiom 違反と判断"),
                    "attempts": attempts, "persona": None}

        persona = out.get("persona") or out
        rate, matched, core = project_to_lod0(persona, lod0)
        rate_trace.append(round(rate, 3))

        # best-so-far 更新(累積方式は最良解を土台に追記していく)
        if rate > best_rate:
            best_rate, best_persona, best_matched = rate, persona, matched

        # 採否は「これまでの最良」で判定(累積方式が単調になる)
        eff_rate = best_rate if cumulative else rate
        eff_persona = best_persona if cumulative else persona
        eff_matched = best_matched if cumulative else matched
        if eff_rate >= PROJECTION_THRESHOLD:
            return {
                "status": "SAT", "attempts": attempts, "persona": eff_persona,
                "projection": {
                    "rate": round(eff_rate, 2), "threshold": PROJECTION_THRESHOLD,
                    "matched": eff_matched, "core": core, "rate_trace": rate_trace,
                },
            }
        # (3) 不足 core 事象を次回プロンプトへ差し戻す
        missing = [name for name in core if name not in eff_matched]
        last_reason = (f"Projection Consistency 不足: core事象 {len(eff_matched)}/{len(core)} "
                       f"({eff_rate:.0%}) しか provenance に現れず(閾値 {PROJECTION_THRESHOLD:.0%})。"
                       f"trace={rate_trace}")

    # (3) backstop: max_retries 超過
    return {"status": "UNSAT", "stage": "projection",
            "reason": last_reason, "attempts": attempts, "persona": None}


# ───────────────────────────────────────────────
# 表示
# ───────────────────────────────────────────────
def print_result(title: str, constraints: LODConstraints, result: dict):
    print("=" * 72)
    print(f"  {title}")
    c = constraints
    print(f"  生年{c.birth_year} / LOD1={c.lod1_response} / LOD2={c.lod2_strategy} "
          f"/ LOD3={c.lod3_context}")
    print("=" * 72)
    print(f"status: {result['status']}  (attempts={result['attempts']}"
          + (f", stage={result['stage']}" if result.get('stage') else "") + ")")
    if result["status"] == "SAT":
        p = result["persona"]
        proj = result["projection"]
        print(f"\n[summary] {p.get('summary')}")
        print(f"\n[narrative]\n{p.get('narrative')}")
        print(f"\n[projection] core一致 {proj['rate']:.0%} (閾値{proj['threshold']:.0%}) "
              f"→ matched={proj['matched']}")
        print("\n[provenance] (各解釈 → LOD0 事象)")
        for pr in p.get("provenance", []):
            print(f"  ・{pr.get('interpretation')}  ⇐ {pr.get('derived_from')}")
    else:
        print(f"\n[UNSAT reason]\n  {result['reason']}")
    print()


# ───────────────────────────────────────────────
def run_cli(args):
    by = args.birth_year or (1990 if args.country in ("us", "uk") else 1981)
    c = LODConstraints(
        birth_year=by, lod1_response=args.response, lod2_strategy=args.strategy,
        country=args.country, premise=args.premise,
    )
    title = f"{args.country.upper()} {by} × {args.response} × {args.strategy}"
    if args.premise:
        title += f"  [premise={args.premise}]"
    if args.country in ("us", "uk"):
        lod0, _ev, _log = build_us_lod0(by, args.country, args.premise)
        r = lod0["resolution"]
        print("=" * 72)
        print(f"  Contextual Mode Resolver — {r['country'].upper()}  premise={r['premise']}")
        print("=" * 72)
        print(f"  事象 {r['events_total']} 件の mode 解決: "
              f"両モデル一致 {r['resolved_agree']} / 不一致tie-break {r['resolved_disagree']} / "
              f"ambient既定PASSIVE {r['default_ambient']}")
        print(f"  LOD0 指紋: PASSIVE {lod0['fingerprint']['PASSIVE']} / "
              f"ACTIVE {lod0['fingerprint']['ACTIVE']} / REFRAME {lod0['fingerprint']['REFRAME']}\n")
        c.lod0_exposure = lod0
    print_result(title, c, solve(c, cumulative=args.cumulative))


def run_japan_demos():
    # ── SAT: 1981年生まれ × Fight × 「技術で攻める」 ──
    sat = LODConstraints(
        birth_year=1981,
        lod1_response="Fight",
        lod2_strategy="技術で攻める",
    )
    print_result("SAT 例: 1981 × Fight × 技術で攻める", sat, solve(sat))

    # ── UNSAT: 1981年で「TikTok 起業家(10代でTikTokに没入して起業)」= 未来矛盾 ──
    #   TikTok普及(2020)は1981年生まれには39歳で着弾 → 人格形成アンカーにできない
    unsat = LODConstraints(
        birth_year=1981,
        lod1_response="Fight",
        lod2_strategy="技術で攻める",
        lod3_context={
            "profession": "TikTok起業家",
            "formative_anchor": "TikTok普及",
            "note": "10代でTikTokに没入し、それを原体験に起業した世代として",
        },
    )
    print_result("UNSAT 例: 1981 で TikTok起業家(未来矛盾)", unsat, solve(unsat))

    # ── UNSAT(LLM自己判定): Flight 指定 + 「一度も決断を迫られず流されてきた」自認 ──
    #   構造的には高重み ACTIVE 事象(=決断を強制された痕跡)があり Fight 寄り。
    #   自己認識(Flight/無決断)と LOD0 構造のズレを LLM が Axiom 1 違反として捕捉する。
    mismatch = LODConstraints(
        birth_year=1981,
        lod1_response="Flight",
        lod2_strategy="リスクを避けてやり過ごす",
        lod3_context={
            "self_report": ("自分は人生で一度も大きな決断を迫られたことがなく、ただ流されて"
                            "生きてきた。就職も進路も投資も、社会の出来事は自分に何も要求しなかった。"),
        },
    )
    print_result("UNSAT 例(LLM自己判定): Flight自認 vs 構造的Fight(自己認識のズレ)",
                 mismatch, solve(mismatch))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SCEM LOD ペルソナ生成(Japan/US/UK)")
    ap.add_argument("--country", default="jp", help="jp(Paper1 Japan) | us | uk")
    ap.add_argument("--birth_year", type=int, default=None)
    ap.add_argument("--response", default=None, help="Fight | Flight")
    ap.add_argument("--strategy", default=None)
    ap.add_argument("--premise", default=None, help="us/uk: 個人の religion_race_region_education(省略=全premise集約)")
    ap.add_argument("--cumulative", action="store_true", help="retry を累積方式に")
    args = ap.parse_args()

    # 引数が来たら単発実行。完全に無引数(jp/全None)なら従来の Japan デモスイート。
    if args.country != "jp" or args.birth_year or args.response or args.strategy:
        run_cli(args)
    else:
        run_japan_demos()
