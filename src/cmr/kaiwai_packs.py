#!/usr/bin/env python3
"""
kaiwai_packs.py — 界隈インフラ(Exposure Packs)の loader。

data/events_kaiwai_overlay.jsonl(schema kaiwai_overlay_v0.1):
  - core_existing    : 既存 events_patched.jsonl の事象への界隈オーバーレイ(pack所属 + v3情報)
  - kaiwai_candidate : 界隈インフラ級の新規イベント(年・作用年・domain・base_mode を持つ)

設計原則(activation / safety フィールドに準拠):
  - Pack は【ユーザーの明示 opt-in でのみ】有効化。デモグラから推定しない
    (activation.infer_from_demographics=false / display_rule)。
  - sensitive_exposure な pack は UI で注意書きつき表示。
  - v3 と同じ数値規律: salience は名前のみ・ungrounded は m=1.0。
  - not_personal_history: 表示は「文脈的な曝露経路」であって個人史の断定ではない。

API:
  packs()                    -> [{id, label, n_events, sensitive}]
  records(pack_ids)          -> 選択packに属する全レコード
  landed_for(pack_ids)       -> {event_name: {aspects, channels, axes, weight, kaiwai, packs}}
  new_event_dicts(pack_ids)  -> kaiwai_candidate の生 dict 列(呼び出し側で v4.Event 化)
Run(検証): python3 kaiwai_packs.py
"""
from __future__ import annotations
import json
from pathlib import Path

DATA = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent / "data"
FILE = DATA / "events_kaiwai_overlay.jsonl"


def _load() -> list[dict]:
    rows = [json.loads(l) for l in FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        v3 = r.get("v3_overlay") or {}
        if v3.get("grounding_status", "ungrounded") == "ungrounded" and v3.get("default_multiplier", 1.0) != 1.0:
            raise ValueError(f"{r['event_name']}: ungrounded は multiplier=1.0 固定")
    return rows


def packs() -> list[dict]:
    agg: dict = {}
    for r in _load():
        for pid, lab in zip(r["pack_ids"], r["pack_labels_ja"]):
            a = agg.setdefault(pid, {"id": pid, "label": lab, "n_events": 0, "sensitive": False})
            a["n_events"] += 1
            if (r.get("activation") or {}).get("sensitive_exposure"):
                a["sensitive"] = True
    return list(agg.values())


def records(pack_ids: list[str]) -> list[dict]:
    sel = set(pack_ids or [])
    return [r for r in _load() if sel & set(r["pack_ids"])]


def landed_for(pack_ids: list[str]) -> dict:
    """選択packの三層情報。既存 v3_overlay(landed_as)に union-merge される側。"""
    out: dict = {}
    for r in records(pack_ids):
        v3 = r.get("v3_overlay") or {}
        labels = [lab for pid, lab in zip(r["pack_ids"], r["pack_labels_ja"]) if pid in set(pack_ids)]
        out[r["event_name"]] = {
            "aspects": v3.get("exposure_aspects") or [],
            "channels": v3.get("salience_channels") or [],
            "axes": v3.get("relevant_axes") or [],
            "weight": {"status": v3.get("grounding_status", "ungrounded")},
            "kaiwai": True,
            "packs": labels,
        }
    return out


def new_event_dicts(pack_ids: list[str]) -> list[dict]:
    return [r for r in records(pack_ids) if r.get("event_status") == "kaiwai_candidate"]


def main():
    base = {json.loads(l)["name"] for l in (DATA / "events_patched.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    rows = _load()
    print(f"records: {len(rows)}  (core_existing={sum(1 for r in rows if r['event_status']=='core_existing')}, "
          f"kaiwai_candidate={sum(1 for r in rows if r['event_status']=='kaiwai_candidate')})")
    orphans = [r["event_name"] for r in rows if r["event_status"] == "core_existing" and r["event_name"] not in base]
    print("⚠️ base不一致 core_existing:", orphans) if orphans else print("✅ core_existing 全件が base と join 可能")
    for p in packs():
        print(f"  {p['id']:42s} {p['label']:14s} n={p['n_events']:2d}" + ("  ⚠sensitive" if p["sensitive"] else ""))
    missing = [r["event_name"] for r in rows if r["event_status"] == "kaiwai_candidate"
               and not all(k in r for k in ("year", "effective_year", "domain", "base_mode", "agency"))]
    print("⚠️ 新規イベントの数理属性欠落:", missing) if missing else print("✅ kaiwai_candidate 6件とも数理属性あり")


if __name__ == "__main__":
    main()
