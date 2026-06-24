"""
event_loader.py — Gemini DeepResearch の JSON Lines を v4 Event に流し込むアダプタ

設計方針(ご主人さまの「呑気」を構造で保証する):
  - 個別値(sensitivity_peak_age/spread)が来たら使う
  - 無ければ領域別CURVESにフォールバック     ← ハイブリッド
  - 新Domain(LIFESTYLE/PLATFORM/.../PRICE)が来ても落ちない
  - year_type/effective_year を吸収し、作用計算は effective_year を優先
  - 手書きの reframe_group / overlap_notes はそのまま保持
  - キー欠損・型ゆれ・未知enum値があっても1行スキップで継続(全体は止めない)

使い方:
    python event_loader.py events.jsonl 1981
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import math
import sys


# ── Domain: プロンプト準拠の11領域に拡張(未知名も動的に許容) ──
class Domain(Enum):
    MEDIA = "メディア技術"
    EDUCATION = "教育制度"
    ECONOMY = "経済雇用"
    DISASTER = "災害危機"
    POLITICS = "政治制度"
    LIFESTYLE = "生活文化"
    PLATFORM = "プラットフォーム"
    GEOPOLITICS = "国際環境"
    HEALTH = "公衆衛生"
    FINANCE = "金融資産"
    PRICE = "物価価格"
    FOOD = "食料供給"
    UNKNOWN = "未分類"   # 未知Domainの受け皿(落とさない)


class Mode(Enum):
    PASSIVE = "受動着弾"
    ACTIVE = "能動分岐"
    REFRAME = "参照点書き換え"


@dataclass(frozen=True)
class SensitivityCurve:
    peak: float
    left_width: float
    right_width: float
    floor: float = 0.10

    def __call__(self, age: float) -> float:
        if age < 0:
            return 0.0
        width = self.left_width if age <= self.peak else self.right_width
        return max(self.floor, math.exp(-((age - self.peak) ** 2) / (2 * width ** 2)))


# 領域別フォールバックCURVES(個別値が無いとき用)。プロンプトの感受性ピーク目安に準拠。
DEFAULT_PEAK = {
    Domain.MEDIA: (14, 7), Domain.EDUCATION: (16, 5), Domain.ECONOMY: (22, 5),
    Domain.DISASTER: (16, 9), Domain.POLITICS: (18, 6), Domain.LIFESTYLE: (15, 8),
    Domain.PLATFORM: (16, 7), Domain.GEOPOLITICS: (22, 10), Domain.HEALTH: (16, 9),
    Domain.FINANCE: (32, 10), Domain.PRICE: (28, 10), Domain.FOOD: (10, 8),
    Domain.UNKNOWN: (18, 8),
}


@dataclass
class Event:
    name: str
    year: int                     # 作用年(effective_year優先で確定済み)
    domain: Domain
    mode: Mode
    agency: float
    description: str = ""
    # 個別感受性(あれば優先)
    peak_age: Optional[float] = None
    spread: Optional[float] = None
    # REFRAME
    reframe_group: Optional[str] = None
    reference_value: Optional[float] = None
    # 文脈
    region_dependent: bool = False
    reversible: bool = True
    salience: float = 1.0
    effect_vector: dict[str, float] = field(default_factory=dict)
    # リサーチ手書きメタ(保持して検算に使う)
    parent_cluster: Optional[str] = None
    overlap_notes: Optional[str] = None
    confidence: float = 1.0
    raw_year: Optional[int] = None        # 元のlaunch年(記録用)

    def sensitivity(self, age: int) -> float:
        if self.peak_age is not None:
            spread = self.spread if self.spread else 6.0
            curve = SensitivityCurve(self.peak_age, spread, spread * 1.4)
        else:
            peak, spr = DEFAULT_PEAK.get(self.domain, (18, 8))
            curve = SensitivityCurve(peak, spr, spr * 1.6)
        return curve(age)


# ── 安全パーサ: 何が来ても落とさない ──
def _to_domain(s: str) -> Domain:
    if not s:
        return Domain.UNKNOWN
    key = str(s).strip().upper()
    try:
        return Domain[key]
    except KeyError:
        # 日本語値で来た場合も拾う
        for d in Domain:
            if d.value == s:
                return d
        return Domain.UNKNOWN


def _to_mode(s: str) -> Optional[Mode]:
    if not s:
        return None
    key = str(s).strip().upper()
    try:
        return Mode[key]
    except KeyError:
        for m in Mode:
            if m.value == s:
                return m
        return None


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def parse_event(obj: dict) -> Optional[Event]:
    name = obj.get("name")
    mode = _to_mode(obj.get("mode"))
    if not name or mode is None:
        return None  # 名前とモードは必須。無ければスキップ

    # year: effective_year を作用年として優先、無ければ year
    eff = obj.get("effective_year")
    launch = obj.get("year")
    year = eff if isinstance(eff, (int, float)) else launch
    if not isinstance(year, (int, float)):
        return None

    ev_vec = obj.get("effect_vector") or {}
    if isinstance(ev_vec, dict):
        ev_vec = {k: float(v) for k, v in ev_vec.items() if _num(v) is not None}
    else:
        ev_vec = {}

    return Event(
        name=str(name),
        year=int(year),
        domain=_to_domain(obj.get("domain")),
        mode=mode,
        agency=_num(obj.get("agency"), 0.3),
        description=str(obj.get("description", "")),
        peak_age=_num(obj.get("sensitivity_peak_age")),
        spread=_num(obj.get("sensitivity_spread")),
        reframe_group=obj.get("reframe_group"),
        reference_value=_num(obj.get("reference_value")),
        region_dependent=bool(obj.get("region_dependent", False)),
        reversible=bool(obj.get("reversible", True)),
        salience=_num(obj.get("salience"), 1.0),
        effect_vector=ev_vec,
        parent_cluster=obj.get("parent_cluster"),
        overlap_notes=obj.get("overlap_notes"),
        confidence=_num(obj.get("confidence"), 1.0),
        raw_year=int(launch) if isinstance(launch, (int, float)) else None,
    )


def load_jsonl(path: str) -> tuple[list[Event], list[dict]]:
    events, errors = [], []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append({"line": ln, "reason": f"JSON parse error: {e}", "raw": line[:80]})
                continue
            ev = parse_event(obj)
            if ev is None:
                errors.append({"line": ln, "reason": "missing name/mode/year", "raw": line[:80]})
                continue
            events.append(ev)
    return events, errors


def validate(events: list[Event]) -> dict:
    """流し込み後の健康診断。ご主人さまが見るのはこれだけでいい。"""
    from collections import Counter
    by_domain = Counter(e.domain.value for e in events)
    by_mode = Counter(e.mode.value for e in events)
    no_vec = [e.name for e in events if not e.effect_vector]
    no_peak = [e.name for e in events if e.peak_age is None]
    reframe_groups = Counter(e.reframe_group for e in events if e.reframe_group)
    # REFRAMEなのに相方がいない(発火しない孤児)を検出
    lonely_reframe = [g for g, c in reframe_groups.items() if c < 2]
    unknown_domain = [e.name for e in events if e.domain is Domain.UNKNOWN]
    return {
        "total": len(events),
        "by_domain": dict(by_domain),
        "by_mode": dict(by_mode),
        "missing_effect_vector": no_vec,
        "using_curve_fallback": len(no_peak),
        "lonely_reframe_groups": lonely_reframe,
        "unknown_domain_events": unknown_domain,
    }


if __name__ == "__main__":
    from pathlib import Path
    path = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / "data" / "events_patched.jsonl")
    birth = int(sys.argv[2]) if len(sys.argv) > 2 else 1981
    events, errors = load_jsonl(path)
    report = validate(events)

    print(f"=== ローダー健康診断 ({path}) ===")
    print(f"読み込み成功: {report['total']}件 / エラー: {len(errors)}件\n")
    print("領域別:", report["by_domain"])
    print("モード別:", report["by_mode"])
    print(f"\neffect_vector欠損: {len(report['missing_effect_vector'])}件", 
          report["missing_effect_vector"][:5], "..." if len(report["missing_effect_vector"]) > 5 else "")
    print(f"個別peak未指定→CURVESフォールバック: {report['using_curve_fallback']}件")
    print(f"未知Domain: {report['unknown_domain_events'][:5]}")
    print(f"発火しないREFRAME孤児: {report['lonely_reframe_groups']}")
    if errors:
        print("\n--- スキップ行 ---")
        for e in errors[:10]:
            print(f"  L{e['line']}: {e['reason']} | {e['raw']}")
