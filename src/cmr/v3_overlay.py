#!/usr/bin/env python3
"""
v3_overlay.py — 日本DB(events_patched.jsonl)への V3 増築レイヤーの loader。

設計(docs/salience_extension_spec.md / 巴レビュー):
  - events_patched.jsonl(Paper 1 固定mode・数理DB)は【一切書き換えない】。
  - events_v3_overlay.jsonl が CMR/V3 用の追加情報を event_name で外付けする:
      exposure_aspects   … 同じイベントが分解される意味チャンネル(landed-as 候補)
      salience_channels  … 重み差の候補(名前のみ・数値なし)
      relevant_axes      … premise 解決に効く軸
      grounding_status   … grounded / estimated / ungrounded
  - ungrounded の乗数は常に 1.0(エンジンは推測しない)。
  - 接地済み weight は将来 salience_grounding_jp.jsonl(別ファイル)が持つ。

API:
  load_overlay() -> {event_name: v3_overlay dict}
  attach(events) -> [{**event, "v3": overlay|None}]   # base(dict列) に外付け
Run(検証): python3 v3_overlay.py   # overlay と base の join を検査
"""
from __future__ import annotations
import json
from pathlib import Path

DATA = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent / "data"
OVERLAY = DATA / "events_v3_overlay.jsonl"
BASE = DATA / "events_patched.jsonl"

REQUIRED = {"cmr_candidate", "mode_variation_expected", "emphasis_variation_expected",
            "salience_variation_expected", "relevant_axes", "exposure_aspects",
            "salience_channels", "grounding_status", "default_multiplier"}
STATUS = {"grounded", "estimated", "ungrounded"}


def load_overlay() -> dict:
    out = {}
    for line in OVERLAY.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        v3 = o["v3_overlay"]
        missing = REQUIRED - set(v3)
        if missing:
            raise ValueError(f"{o['event_name']}: overlay欠落 {missing}")
        if v3["grounding_status"] not in STATUS:
            raise ValueError(f"{o['event_name']}: 不正 grounding_status {v3['grounding_status']}")
        if v3["grounding_status"] == "ungrounded" and v3["default_multiplier"] != 1.0:
            raise ValueError(f"{o['event_name']}: ungrounded は multiplier=1.0 固定(推測禁止)")
        out[o["event_name"]] = {"event_id": o.get("event_id"), **v3}
    return out


def attach(events: list[dict]) -> list[dict]:
    """base イベント(dict列)に v3 を外付け。overlay の無い事象は v3=None(従来どおり)。"""
    ov = load_overlay()
    return [{**e, "v3": ov.get(e["name"])} for e in events]


def main():
    base_names = {json.loads(l)["name"] for l in BASE.read_text(encoding="utf-8").splitlines() if l.strip()}
    ov = load_overlay()
    orphans = [n for n in ov if n not in base_names]
    print(f"overlay: {len(ov)} 件 / base: {len(base_names)} 件")
    if orphans:
        print(f"⚠️ base に存在しない overlay(要修正): {orphans}")
        raise SystemExit(1)
    print("✅ 全 overlay が base と join 可能(event_name 完全一致)")
    for n, v in ov.items():
        print(f"  {n:24s} mode変動={v['mode_variation_expected']:<16s} "
              f"aspects={len(v['exposure_aspects'])} channels={len(v['salience_channels'])} "
              f"[{v['grounding_status']}]")


if __name__ == "__main__":
    main()
