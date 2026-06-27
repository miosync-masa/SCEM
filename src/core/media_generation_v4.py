"""
年齢同期型メディア世代論 — v3
- 領域別感受性カーブ
- REFRAMEのアンカー深度 × トリガー感受性
- 作用ベクトル独立性チェック
- LLM用プロンプト生成

Run:
    python media_generation_v3.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Iterable
import math
import json


# ───────────────────────────────────────────────
# 軸1: 領域
# ───────────────────────────────────────────────
class Domain(Enum):
    MEDIA = "メディア技術"
    EDUCATION = "教育制度"
    ECONOMY = "経済雇用"
    DISASTER = "災害危機"
    POLITICS = "政治制度"
    HEALTH = "公衆衛生"
    FOOD = "食料供給"
    PLATFORM = "プラットフォーム"
    LIFESTYLE = "生活文化"
    PRICE = "物価価格"
    FINANCE = "金融資産"
    GEOPOLITICS = "国際環境"


# ───────────────────────────────────────────────
# 軸2: 作用モード
# ───────────────────────────────────────────────
class Mode(Enum):
    PASSIVE = "受動着弾"
    ACTIVE = "能動分岐"
    REFRAME = "参照点書き換え"


@dataclass(frozen=True)
class SensitivityCurve:
    """非対称な山型感受性カーブ。

    peak:
        最も刺さる年齢
    left_width:
        peak以前の立ち上がり幅。小さいほど早熟に刺さる。
    right_width:
        peak以後の減衰幅。大きいほど成人後も残る。
    floor:
        成人後/幼少期にも残る最低感受性
    """
    peak: float
    left_width: float
    right_width: float
    floor: float = 0.10

    def __call__(self, age: float) -> float:
        if age < 0:
            return 0.0
        width = self.left_width if age <= self.peak else self.right_width
        value = math.exp(-((age - self.peak) ** 2) / (2 * width ** 2))
        return max(self.floor, value)


# 領域 × 作用モードごとの感受性ピーク。
# ここが粗1の修正点。
CURVES: dict[tuple[Domain, Mode], SensitivityCurve] = {
    # メディアは思春期ピーク。身体記憶〜人格形成に強く刺さる。
    (Domain.MEDIA, Mode.PASSIVE): SensitivityCurve(peak=14, left_width=9, right_width=17, floor=0.15),
    (Domain.MEDIA, Mode.ACTIVE): SensitivityCurve(peak=18, left_width=7, right_width=14, floor=0.12),
    (Domain.MEDIA, Mode.REFRAME): SensitivityCurve(peak=16, left_width=9, right_width=18, floor=0.15),

    # 教育制度は中高〜進路選択期がピーク。
    (Domain.EDUCATION, Mode.PASSIVE): SensitivityCurve(peak=13, left_width=7, right_width=10, floor=0.08),
    (Domain.EDUCATION, Mode.ACTIVE): SensitivityCurve(peak=16, left_width=5, right_width=8, floor=0.08),
    (Domain.EDUCATION, Mode.REFRAME): SensitivityCurve(peak=17, left_width=5, right_width=10, floor=0.08),

    # 経済雇用は就活・初職・キャリア初期がピーク。
    (Domain.ECONOMY, Mode.PASSIVE): SensitivityCurve(peak=23, left_width=7, right_width=15, floor=0.12),
    (Domain.ECONOMY, Mode.ACTIVE): SensitivityCurve(peak=22, left_width=4, right_width=12, floor=0.10),
    (Domain.ECONOMY, Mode.REFRAME): SensitivityCurve(peak=24, left_width=8, right_width=18, floor=0.12),

    # 災害は「安全観」の書き換えなら若年でも強いが、意思決定歪曲は成人期にも刺さる。
    (Domain.DISASTER, Mode.PASSIVE): SensitivityCurve(peak=12, left_width=8, right_width=18, floor=0.18),
    (Domain.DISASTER, Mode.ACTIVE): SensitivityCurve(peak=24, left_width=8, right_width=20, floor=0.18),
    (Domain.DISASTER, Mode.REFRAME): SensitivityCurve(peak=16, left_width=9, right_width=24, floor=0.20),

    # 政治制度は「主体になった瞬間」が18歳前後。
    (Domain.POLITICS, Mode.PASSIVE): SensitivityCurve(peak=18, left_width=7, right_width=16, floor=0.08),
    (Domain.POLITICS, Mode.ACTIVE): SensitivityCurve(peak=18, left_width=4, right_width=10, floor=0.08),
    (Domain.POLITICS, Mode.REFRAME): SensitivityCurve(peak=18, left_width=5, right_width=12, floor=0.08),

    # 公衆衛生/食料供給は「身体安全」と「生活インフラ」の混合。
    (Domain.HEALTH, Mode.PASSIVE): SensitivityCurve(peak=12, left_width=8, right_width=20, floor=0.15),
    (Domain.HEALTH, Mode.ACTIVE): SensitivityCurve(peak=24, left_width=8, right_width=20, floor=0.15),
    (Domain.HEALTH, Mode.REFRAME): SensitivityCurve(peak=16, left_width=9, right_width=24, floor=0.18),

    (Domain.FOOD, Mode.PASSIVE): SensitivityCurve(peak=8, left_width=7, right_width=18, floor=0.12),
    (Domain.FOOD, Mode.ACTIVE): SensitivityCurve(peak=26, left_width=10, right_width=18, floor=0.12),
    (Domain.FOOD, Mode.REFRAME): SensitivityCurve(peak=18, left_width=10, right_width=20, floor=0.12),

    # プラットフォーム(SNS/検索/EC/動画)はメディアより少し遅れ、社会接続〜成人初期に効く。
    (Domain.PLATFORM, Mode.PASSIVE): SensitivityCurve(peak=16, left_width=9, right_width=17, floor=0.15),
    (Domain.PLATFORM, Mode.ACTIVE): SensitivityCurve(peak=20, left_width=7, right_width=15, floor=0.12),
    (Domain.PLATFORM, Mode.REFRAME): SensitivityCurve(peak=18, left_width=9, right_width=18, floor=0.15),

    # 生活文化(消費/生活インフラ/娯楽様式)は思春期〜成人初期に広く刺さる。
    (Domain.LIFESTYLE, Mode.PASSIVE): SensitivityCurve(peak=15, left_width=9, right_width=18, floor=0.13),
    (Domain.LIFESTYLE, Mode.ACTIVE): SensitivityCurve(peak=22, left_width=8, right_width=16, floor=0.12),
    (Domain.LIFESTYLE, Mode.REFRAME): SensitivityCurve(peak=18, left_width=9, right_width=20, floor=0.13),

    # 物価価格(消費税/為替/物価)は家計を持つ成人期がピーク。REFRAMEが主。
    (Domain.PRICE, Mode.PASSIVE): SensitivityCurve(peak=25, left_width=10, right_width=20, floor=0.12),
    (Domain.PRICE, Mode.ACTIVE): SensitivityCurve(peak=28, left_width=8, right_width=18, floor=0.10),
    (Domain.PRICE, Mode.REFRAME): SensitivityCurve(peak=28, left_width=12, right_width=22, floor=0.14),

    # 金融資産(株/金利/投資制度)は投資・住宅を考える25-45歳がピーク。
    (Domain.FINANCE, Mode.PASSIVE): SensitivityCurve(peak=30, left_width=10, right_width=20, floor=0.10),
    (Domain.FINANCE, Mode.ACTIVE): SensitivityCurve(peak=30, left_width=9, right_width=18, floor=0.10),
    (Domain.FINANCE, Mode.REFRAME): SensitivityCurve(peak=32, left_width=12, right_width=22, floor=0.12),

    # 国際環境(戦争/地政学)は「世界観ショック」系。災害に近いが成人期にも強い。
    (Domain.GEOPOLITICS, Mode.PASSIVE): SensitivityCurve(peak=18, left_width=9, right_width=22, floor=0.15),
    (Domain.GEOPOLITICS, Mode.ACTIVE): SensitivityCurve(peak=24, left_width=9, right_width=20, floor=0.14),
    (Domain.GEOPOLITICS, Mode.REFRAME): SensitivityCurve(peak=20, left_width=10, right_width=24, floor=0.16),
}


@dataclass
class Event:
    name: str
    year: int
    domain: Domain
    mode: Mode
    agency: float
    description: str

    # REFRAME用
    reframe_group: Optional[str] = None
    reference_value: Optional[float] = None

    # 文脈補正
    region_dependent: bool = False
    reversible: bool = True
    salience: float = 1.0  # 歴史的・社会的な大きさ。0.0-1.5程度を想定。

    # 作用ベクトル。MECE/独立性判定の本体。
    # 値は 0.0-1.0。似た作用ならcosine similarityが上がる。
    effect_vector: dict[str, float] = field(default_factory=dict)


AGE_BANDS = [
    (0, 5, "原風景期"),
    (6, 11, "身体記憶期"),
    (12, 17, "人格形成期"),
    (18, 22, "社会接続期"),
    (23, 29, "成人初期適応期"),
    (30, 39, "社会実装期"),
    (40, 200, "再定義期"),
]


def life_stage(age: int) -> str:
    for lo, hi, label in AGE_BANDS:
        if lo <= age <= hi:
            return label
    return "未到達"


def sensitivity(age: int, domain: Domain, mode: Mode) -> float:
    curve = CURVES.get((domain, mode))
    if curve is None:
        curve = SensitivityCurve(peak=18, left_width=8, right_width=18, floor=0.10)
    return curve(age)


def mode_weight(ev: Event, age: int) -> float:
    s = sensitivity(age, ev.domain, ev.mode)

    if ev.mode is Mode.PASSIVE:
        # 選べない着弾。主成分は感受性と社会的サリエンス。
        return s * ev.salience

    if ev.mode is Mode.ACTIVE:
        # 意思決定を強制される作用。agencyと領域別感受性が両方効く。
        return s * (0.30 + 0.70 * ev.agency) * ev.salience

    if ev.mode is Mode.REFRAME:
        # アンカーの刺さり具合。発火は別関数で、後の差分と掛ける。
        return s * (0.50 + 0.50 * ev.agency) * ev.salience

    raise ValueError(f"unknown mode: {ev.mode}")


def norm(vec: dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vec.values()))


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    denom = norm(a) * norm(b)
    if denom == 0:
        return 0.0
    return dot / denom


def overlap_action(sim: float, year_gap: int, same_mode: bool) -> str:
    """作用被りの機械判定。作用ベクトルのcos類似度のみで判定し、domainには依存しない
    (domain純化: 旧版は same_domain を要件にしていたが、類似性は cos が連続で測るため冗長だった)。

    duplicate:
        同じチャンクに寄せるべき。両方入れると二重計上リスク。
    sibling:
        同じ親チャンクの下位分岐として扱うべき。
    interference:
        被ってはいないが、同時着弾として干渉ノードにする。
    independent:
        独立事象として併存。
    """
    close = year_gap <= 3
    if close and same_mode and sim >= 0.82:
        return "duplicate"
    if close and sim >= 0.70:
        return "sibling"
    if close and sim >= 0.35:
        return "interference"
    return "independent"


def compute_overlap_report(hits: list[dict]) -> list[dict]:
    rows = []
    for i in range(len(hits)):
        for j in range(i + 1, len(hits)):
            a, b = hits[i], hits[j]
            ea, eb = a["ev"], b["ev"]
            sim = cosine(ea.effect_vector, eb.effect_vector)
            gap = abs(ea.year - eb.year)
            action = overlap_action(
                sim=sim,
                year_gap=gap,
                same_mode=ea.mode is eb.mode,
            )
            if action != "independent":
                rows.append({
                    "pair": (ea.name, eb.name),
                    "years": (ea.year, eb.year),
                    "age_range": (min(a["age"], b["age"]), max(a["age"], b["age"])),
                    "similarity": round(sim, 3),
                    "year_gap": gap,
                    "action": action,
                    "reason": explain_overlap(action),
                })
    priority = {"duplicate": 0, "sibling": 1, "interference": 2}
    rows.sort(key=lambda r: (priority[r["action"]], -r["similarity"], r["year_gap"]))
    return rows


def explain_overlap(action: str) -> str:
    return {
        "duplicate": "作用がほぼ同じ。代表事象に統合し、二重計上を避ける。",
        "sibling": "同じ親チャンクの下位事象。親カテゴリを作ってから枝として扱う。",
        "interference": "作用は別だが同時期に近接。世代の質感を作る干渉ノードにする。",
        "independent": "独立事象として扱う。",
    }[action]


def band_width(stage_label: str) -> int:
    for lo, hi, label in AGE_BANDS:
        if label == stage_label:
            return hi - lo + 1
    return 6


def compute_interferences(hits: list[dict], overlap_report: list[dict]) -> list[dict]:
    """問題B修正: 干渉は『事象の年が近い』ではなく
    『その人の同じ認知段階バンドに着弾したか』で判定する。
    これで干渉が世代依存になる。同じPS×阪神淡路でも、
    13-14歳(人格形成期)で食らった人と0-1歳(原風景期)で食らった人では別物。
    """
    duplicate_pairs = {tuple(r["pair"]) for r in overlap_report if r["action"] == "duplicate"}
    duplicate_pairs |= {tuple(reversed(r["pair"])) for r in overlap_report if r["action"] == "duplicate"}

    interferences = []
    for i in range(len(hits)):
        for j in range(i + 1, len(hits)):
            a, b = hits[i], hits[j]
            ea, eb = a["ev"], b["ev"]
            if (ea.name, eb.name) in duplicate_pairs:
                continue

            # ── 核心: 同じ認知段階バンドに両方着弾したか ──
            if a["stage"] != b["stage"]:
                continue

            # バンド内での同時着弾度。同じ年に来たほど干渉は濃い。
            age_gap = abs(a["age"] - b["age"])
            bw = band_width(a["stage"])
            proximity = 1.0 - min(age_gap / bw, 1.0)

            sim = cosine(ea.effect_vector, eb.effect_vector)
            cross_domain = ea.domain is not eb.domain  # 記述用タグ。スコアには非関与(domain純化)。
            base = (a["weight"] + b["weight"]) / 2
            # 作用が違うほど干渉は濃い。作用直交性を1項に統合した
            # (旧版は cross_domain 1.6倍 と 独立性ボーナス が別軸だったが、domain廃止により
            #  両者ともcos由来=二重計上になるため統合)。
            # cos=0(直交作用)→1.6 / cos=1(同一作用=被り)→0.55。
            dissimilarity = 1.6 - 1.05 * min(sim, 1.0)
            score = (
                base
                * dissimilarity
                * (0.5 + 0.5 * proximity)   # バンド内近接ボーナス
            )

            interferences.append({
                "pair": (ea.name, eb.name),
                "stage": a["stage"],
                "age_range": (min(a["age"], b["age"]), max(a["age"], b["age"])),
                "age_gap": age_gap,
                "proximity": round(proximity, 2),
                "cross_domain": cross_domain,
                "similarity": round(sim, 3),
                "score": round(score, 3),
            })

    interferences.sort(key=lambda x: -x["score"])
    return interferences


def reference_distance(anchor: Event, trigger: Event) -> float:
    """REFRAMEの差分。数値があれば比率差、なければ年差を代理にする。"""
    if anchor.reference_value and trigger.reference_value:
        # 為替や価格のような倍率差に効く。70→140ならlog2相当でほぼ1に近い。
        ratio = max(anchor.reference_value, trigger.reference_value) / min(anchor.reference_value, trigger.reference_value)
        return min(1.0, math.log(ratio) / math.log(2.0))
    return min(1.0, abs(trigger.year - anchor.year) / 10.0)


def compute_reframe_fires(hits: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for h in hits:
        ev = h["ev"]
        if ev.mode is Mode.REFRAME and ev.reframe_group:
            groups.setdefault(ev.reframe_group, []).append(h)

    fires = []
    for group, members in groups.items():
        members.sort(key=lambda h: h["ev"].year)
        if len(members) < 2:
            continue

        # すべての過去アンカー × 後続トリガーを見る。
        for i in range(len(members) - 1):
            anchor = members[i]
            for trigger in members[i + 1:]:
                anchor_ev = anchor["ev"]
                trigger_ev = trigger["ev"]

                anchor_depth = anchor["weight"]             # 粗2: アンカーを領域別感受性込みにする
                trigger_sensitivity = trigger["weight"]     # 後の発火側も感受性込み
                delta = reference_distance(anchor_ev, trigger_ev)

                # 差分がないと発火しない。アンカーが浅くても発火しにくい。
                fire = anchor_depth * (0.35 + 0.65 * trigger_sensitivity) * delta

                fires.append({
                    "group": group,
                    "anchor": (anchor_ev.name, anchor["age"], round(anchor_depth, 3)),
                    "trigger": (trigger_ev.name, trigger["age"], round(trigger_sensitivity, 3)),
                    "delta": round(delta, 3),
                    "fire": round(fire, 3),
                })

    fires.sort(key=lambda x: -x["fire"])
    return fires


def analyze(birth_year: int, events: list[Event]):
    hits = []
    for ev in events:
        age = ev.year - birth_year
        if age < 0:
            continue
        sens = sensitivity(age, ev.domain, ev.mode)
        w = mode_weight(ev, age)
        hits.append({
            "ev": ev,
            "age": age,
            "stage": life_stage(age),
            "sens": round(sens, 3),
            "weight": round(w, 3),
        })

    overlap_report = compute_overlap_report(hits)
    interferences = compute_interferences(hits, overlap_report)
    reframe_fires = compute_reframe_fires(hits)

    return hits, interferences, reframe_fires, overlap_report


def serializable_event_hit(hit: dict) -> dict:
    ev = hit["ev"]
    return {
        "name": ev.name,
        "year": ev.year,
        "age": hit["age"],
        "stage": hit["stage"],
        "domain": ev.domain.value,
        "mode": ev.mode.value,
        "agency": ev.agency,
        "sensitivity": hit["sens"],
        "weight": hit["weight"],
        "description": ev.description,
        "reversible": ev.reversible,
        "region_dependent": ev.region_dependent,
        "effect_vector": ev.effect_vector,
    }


def build_llm_payload(birth_year: int, events: list[Event]) -> dict:
    hits, interferences, reframe_fires, overlap_report = analyze(birth_year, events)

    top_hits = sorted(hits, key=lambda h: -h["weight"])[:12]

    return {
        "task": "年齢同期型メディア世代論に基づく世代プロファイルの説明と名称化",
        "birth_year": birth_year,
        "schema_version": "v3",
        "core_principle": "世代は出生年ではなく、技術・制度・危機が何歳の認知段階に着弾したかで決まる。事象そのものではなく、作用ベクトルが独立しているかを見る。",
        "interpretation_modes": {
            "PASSIVE": "選んでいないが身体や原風景に刷り込まれたもの。質感・懐かしさ・当たり前感を作る。",
            "ACTIVE": "進路・就職・経営・政治参加など、意思決定を強制されたもの。人生分岐の傷や癖を作る。",
            "REFRAME": "基準値を書き換えたもの。後続事象との差分で発火し、隠れた『普通』の物差しになる。",
        },
        "top_hits": [serializable_event_hit(h) for h in top_hits],
        "interference_nodes": interferences[:8],
        "reframe_fires": reframe_fires[:8],
        "overlap_report": overlap_report[:12],
        "output_requirements": {
            "generation_name": "20字以内で1つ。可能なら複合語。",
            "summary": "300字程度。身体化された文化、能動分岐、参照点書き換えを必ず含める。",
            "texture": "干渉ノードから、この人物世代の質感を2-4項目で説明。",
            "hidden_standards": "reframe_firesから、この人物の隠れた基準値を説明。",
            "avoid": "X世代/Y世代/Z世代のような単純ラベルだけで終わらせない。"
        },
    }


def build_llm_prompt(birth_year: int, events: list[Event]) -> str:
    payload = build_llm_payload(birth_year, events)
    return (
        "あなたは社会学・メディア史・労働史に強い分析者です。\n"
        "以下のJSONを読み、年齢同期型メディア世代論として説明と名称化をしてください。\n"
        "JSON内のoverlap_reportでduplicateやsiblingとされたものは二重計上せず、"
        "interferenceは『同時期の異なる作用が重なった質感』として説明してください。\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def report(birth_year: int, events: list[Event]):
    hits, interferences, reframe_fires, overlap_report = analyze(birth_year, events)

    print(f"{'=' * 72}")
    print(f"  {birth_year}年生まれ — 作用プロファイル v3")
    print(f"{'=' * 72}\n")

    print("【着弾した事象: weight順】")
    for h in sorted(hits, key=lambda x: -x["weight"]):
        ev = h["ev"]
        print(
            f"  [{h['weight']:.3f}] {ev.name:<24} "
            f"{h['age']:>2}歳 {h['stage']:<8} "
            f"{ev.mode.value:<8} {ev.domain.value:<8} sens={h['sens']:.2f}"
        )

    print("\n【作用被りチェック】")
    if not overlap_report:
        print("  (被り候補なし)")
    for r in overlap_report[:8]:
        print(
            f"  [{r['action']:<12}] sim={r['similarity']:.2f} gap={r['year_gap']}年 "
            f"{r['pair'][0]} × {r['pair'][1]} — {r['reason']}"
        )

    print("\n【干渉ノード — 同じ認知段階バンドへの同時着弾(世代依存)】")
    if not interferences:
        print("  (干渉なし)")
    for it in interferences[:8]:
        x = "領域横断⚡" if it["cross_domain"] else "同領域"
        lo, hi = it["age_range"]
        print(
            f"  [{it['score']:.3f}] {it['stage']:<6} sim={it['similarity']:.2f} prox={it['proximity']:.2f} "
            f"{it['pair'][0]} × {it['pair'][1]} ({lo}-{hi}歳, {x})"
        )

    print("\n【参照点書き換えの発火】")
    if not reframe_fires:
        print("  (発火なし)")
    for r in reframe_fires:
        print(
            f"  [{r['fire']:.3f}] {r['group']}: "
            f"{r['anchor'][0]}({r['anchor'][1]}歳 depth={r['anchor'][2]}) "
            f"→ {r['trigger'][0]}({r['trigger'][1]}歳 sens={r['trigger'][2]}) "
            f"Δ={r['delta']:.2f}"
        )

    print("\n【LLM投入用プロンプト冒頭】")
    prompt = build_llm_prompt(birth_year, events)
    print(prompt[:1800] + "\n...")


# ───────────────────────────────────────────────
# 事象リスト例
# ───────────────────────────────────────────────
EVENTS = [
    Event(
        "ファミコン", 1983, Domain.MEDIA, Mode.PASSIVE, 0.10,
        "家庭用ゲーム文化の原風景。親が買う",
        salience=0.9,
        effect_vector={"play_interface": 1.0, "home_media": 0.8, "peer_culture": 0.6},
    ),
    Event(
        "スーパーファミコン", 1990, Domain.MEDIA, Mode.PASSIVE, 0.25,
        "2D表現の成熟。攻略本・友達の家文化",
        salience=1.0,
        effect_vector={"play_interface": 1.0, "home_media": 0.7, "peer_culture": 0.9, "visual_expression": 0.4},
    ),
    Event(
        "PlayStation", 1994, Domain.MEDIA, Mode.PASSIVE, 0.40,
        "3D・CD-ROM・映像表現の身体化",
        salience=1.05,
        effect_vector={"play_interface": 0.8, "home_media": 0.5, "peer_culture": 0.7, "visual_expression": 1.0, "tech_embodiment": 0.7},
    ),
    Event(
        "Windows95", 1995, Domain.MEDIA, Mode.PASSIVE, 0.20,
        "家庭・学校へのPC大衆化",
        salience=1.0,
        effect_vector={"pc_literacy": 1.0, "internet_prewire": 0.5, "work_tool": 0.5, "home_media": 0.4, "tech_embodiment": 0.8},
    ),
    Event(
        "iモード", 1999, Domain.MEDIA, Mode.PASSIVE, 0.30,
        "携帯ネット文化の形成",
        salience=0.95,
        effect_vector={"mobile_connectivity": 1.0, "social_contact": 0.7, "internet_prewire": 0.8},
    ),
    Event(
        "YouTube/Web2.0", 2005, Domain.MEDIA, Mode.PASSIVE, 0.35,
        "動画共有・参加型ネット",
        salience=1.0,
        effect_vector={"user_generated_content": 1.0, "video_platform": 1.0, "creator_economy": 0.4, "algorithmic_media": 0.3},
    ),
    Event(
        "iPhone", 2007, Domain.MEDIA, Mode.PASSIVE, 0.40,
        "スマホ時代の始まり",
        salience=1.0,
        effect_vector={"mobile_connectivity": 1.0, "touch_interface": 1.0, "app_ecosystem": 0.8, "camera_life": 0.5},
    ),
    Event(
        "LINE", 2011, Domain.MEDIA, Mode.PASSIVE, 0.30,
        "日常連絡インフラ化",
        salience=1.0,
        effect_vector={"mobile_connectivity": 0.8, "social_contact": 1.0, "daily_infra": 1.0},
    ),
    Event(
        "ChatGPT/生成AI", 2022, Domain.MEDIA, Mode.PASSIVE, 0.55,
        "存在論の再定義トリガー",
        salience=1.15,
        effect_vector={"ai_cognition": 1.0, "work_tool": 0.7, "creation_tool": 0.9, "ontology_shift": 1.0},
    ),

    Event(
        "偏差値・業者テスト追放", 1993, Domain.EDUCATION, Mode.ACTIVE, 0.80,
        "外部指標なしで進路を自分で決めさせられた",
        reversible=False,
        salience=0.9,
        effect_vector={"school_selection": 1.0, "self_decision": 0.9, "evaluation_system": 1.0},
    ),
    Event(
        "ゆとり教育 完全実施", 2002, Domain.EDUCATION, Mode.PASSIVE, 0.40,
        "カリキュラム構造の変更",
        reversible=False,
        salience=0.8,
        effect_vector={"curriculum": 1.0, "school_norm": 0.7, "evaluation_system": 0.5},
    ),

    Event(
        "就職氷河期 (就活直撃)", 2003, Domain.ECONOMY, Mode.ACTIVE, 0.90,
        "就職という意思決定が氷河期で歪む",
        reversible=False,
        salience=1.2,
        effect_vector={"employment_gate": 1.0, "career_entry": 1.0, "scarcity": 0.9, "self_decision": 0.8},
    ),
    Event(
        "リーマンショック", 2008, Domain.ECONOMY, Mode.ACTIVE, 0.60,
        "雇用・消費の判断を直撃",
        salience=1.0,
        effect_vector={"employment_market": 0.8, "asset_risk": 0.8, "consumption_restraint": 0.7, "scarcity": 0.7},
    ),
    Event(
        "働き方改革", 2019, Domain.ECONOMY, Mode.ACTIVE, 0.50,
        "労働の意思決定枠の変更",
        reversible=False,
        salience=0.9,
        effect_vector={"work_rule": 1.0, "labor_time": 0.9, "management": 0.7},
    ),

    Event(
        "ドル円70円台", 2011, Domain.ECONOMY, Mode.REFRAME, 0.50,
        "超円高を身体で経験=基準アンカー",
        reframe_group="円相場",
        reference_value=76.0,
        salience=0.9,
        effect_vector={"currency_anchor": 1.0, "price_reference": 0.8, "global_economy": 0.6},
    ),
    Event(
        "ドル円140円台", 2022, Domain.ECONOMY, Mode.REFRAME, 0.50,
        "円安。70円を知る身体だけ『やばい』が起動",
        reframe_group="円相場",
        reference_value=145.0,
        salience=1.0,
        effect_vector={"currency_anchor": 1.0, "price_reference": 0.8, "global_economy": 0.7},
    ),

    Event(
        "阪神淡路+地下鉄サリン", 1995, Domain.DISASTER, Mode.PASSIVE, 0.45,
        "安全神話の崩壊",
        region_dependent=True,
        reversible=False,
        salience=1.1,
        effect_vector={"safety_myth": 1.0, "urban_risk": 0.9, "terror_risk": 0.7, "media_shock": 0.7},
    ),
    Event(
        "東日本大震災+原発", 2011, Domain.DISASTER, Mode.REFRAME, 0.55,
        "災害観の基準書き換え",
        region_dependent=True,
        reversible=False,
        reframe_group="震災",
        salience=1.2,
        effect_vector={"safety_myth": 1.0, "energy_risk": 1.0, "supply_chain": 0.8, "regional_risk": 0.8},
    ),
    Event(
        "コロナ", 2020, Domain.DISASTER, Mode.ACTIVE, 0.70,
        "受験・就活・経営判断を全面的に歪めた",
        reversible=False,
        salience=1.25,
        effect_vector={"public_health": 1.0, "mobility_restriction": 1.0, "work_school_disruption": 1.0, "governance_emergency": 0.8, "supply_chain": 0.5},
    ),
    Event(
        "鳥インフル", 2020, Domain.HEALTH, Mode.PASSIVE, 0.20,
        "公衆衛生・食料供給リスクとしての着弾。コロナと同じ危機でも作用は異なる。",
        region_dependent=True,
        salience=0.55,
        effect_vector={"public_health": 0.6, "food_supply": 1.0, "animal_disease": 1.0, "price_reference": 0.4},
    ),

    Event(
        "選挙権18歳", 2016, Domain.POLITICS, Mode.ACTIVE, 0.75,
        "意思決定主体になる年齢が制度で動いた",
        reversible=False,
        salience=0.75,
        effect_vector={"civic_agency": 1.0, "legal_age": 0.7, "self_decision": 0.5},
    ),
    Event(
        "成人年齢18歳", 2022, Domain.POLITICS, Mode.ACTIVE, 0.70,
        "成人の境界が制度で動いた",
        reversible=False,
        salience=0.8,
        effect_vector={"legal_age": 1.0, "contract_agency": 1.0, "civic_agency": 0.5},
    ),
]


if __name__ == "__main__":
    report(1981, EVENTS)
