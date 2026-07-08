#!/usr/bin/env python3
"""
merge_gender_grid.py — 性別拡張グリッド(解釈のみ)の専用マージャ。

設計(docs/paper2_gender_grid_spec.md §4/§7):
  - LOD0(事象の数理属性)は既存 events_{c}_grid_merged.jsonl を無改変で再利用。
    cmr_compare が variant タグで読めるよう events_{c}_gender_grid_merged.jsonl として複製する
    (複製はこの1点のみ・出所は本ヘッダに明記)。
  - 観測者 = ChatGPT × Claude(Gemini は不使用)。入力は解釈のみの JSONL:
      data/observers/ChatGPT_interps_{c}_gender_grid.jsonl
      data/observers/Claude_interps_{c}_gender_grid.jsonl
  - 出力:
      data/interpretations_{c}_gender_grid.jsonl   (event × premise × observer の解釈)
      data/disagreements_{c}_gender_grid.jsonl     (同一セルで観測者のmodeが割れた記録)
      data/merge_report_{c}_gender_grid.md         (人間可読サマリ)

Run: python3 merge_gender_grid.py --country us
"""
from __future__ import annotations
import argparse
import json
import collections
from pathlib import Path

import cmr_matrix as CM

DATA = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent / "data"
OBSERVERS = [("chatgpt", "ChatGPT"), ("claude", "Claude")]
MODES = {"PASSIVE", "ACTIVE", "REFRAME"}


def load_observer(model_file: str, country: str) -> dict:
    """{event_id: {premise: interp}} を返す。スキーマ違反は即エラー(黙って落とさない)。"""
    path = DATA / "observers" / f"{model_file}_interps_{country}_gender_grid.jsonl"
    expected = {p + g for _, p in CM.COMMUNITIES_GRID[country] for g in ("_female", "_male")}
    out: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        eid = o["event_id"]
        ags = {a["premise"]: a for a in o["affected_groups"]}
        if set(ags) != expected:
            raise ValueError(f"{path.name} {eid}: premise集合が仕様と不一致 "
                             f"(missing={expected - set(ags)}, extra={set(ags) - expected})")
        bad = [a["expected_mode"] for a in ags.values() if a["expected_mode"] not in MODES]
        if bad:
            raise ValueError(f"{path.name} {eid}: 不正mode {bad}")
        out[eid] = ags
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="us")
    args = ap.parse_args()
    c = args.country

    # LOD0 再利用: 既存 grid の merged events(event_id → name などのメタ)
    src_events = DATA / f"events_{c}_grid_merged.jsonl"
    merged_events = [json.loads(l) for l in src_events.read_text(encoding="utf-8").splitlines() if l.strip()]
    name_of = {o["event_id"]: o["name"] for o in merged_events}

    obs = {}
    for model, file_prefix in OBSERVERS:
        obs[model] = load_observer(file_prefix, c)

    eids = [o["event_id"] for o in merged_events]
    for model, d in obs.items():
        missing = set(eids) - set(d)
        if missing:
            raise ValueError(f"{model}: 事象が欠けている {missing}")

    premises = [p + g for _, p in CM.COMMUNITIES_GRID[c] for g in ("_female", "_male")]

    interps, disagreements = [], []
    agree = cells = 0
    for eid in eids:
        for premise in premises:
            cells += 1
            per_model = {}
            for model, _ in OBSERVERS:
                a = obs[model][eid][premise]
                interps.append({
                    "event_name": name_of[eid],
                    "source_model": model,
                    "premise": premise,
                    "expected_mode": a["expected_mode"],
                    "rationale": a.get("rationale", ""),
                    "effect_emphasis": a.get("effect_emphasis", []),
                    "rationale_scope": a.get("rationale_scope", "community_interpretation"),
                    "event_id": eid,
                })
                per_model[model] = a
            modes = {m: a["expected_mode"] for m, a in per_model.items()}
            if len(set(modes.values())) == 1:
                agree += 1
            else:
                disagreements.append({
                    "event_name": name_of[eid], "event_id": eid, "premise": premise,
                    "disagreement_type": "mode_chatgpt_vs_claude",
                    "chatgpt_value": modes["chatgpt"], "claude_value": modes["claude"],
                    "chatgpt_rationale": per_model["chatgpt"].get("rationale", "")[:200],
                    "claude_rationale": per_model["claude"].get("rationale", "")[:200],
                })

    # 出力
    (DATA / f"interpretations_{c}_gender_grid.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in interps) + "\n", encoding="utf-8")
    (DATA / f"disagreements_{c}_gender_grid.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in disagreements) + ("\n" if disagreements else ""),
        encoding="utf-8")
    # LOD0 複製(cmr_compare の tag 規約に合わせる。出所=既存 grid・無改変)
    (DATA / f"events_{c}_gender_grid_merged.jsonl").write_text(
        src_events.read_text(encoding="utf-8"), encoding="utf-8")

    dis_by_event = collections.Counter(d["event_id"] for d in disagreements)
    report = [
        f"# merge report — {c} gender grid (ChatGPT × Claude, interpretation-only)",
        "",
        f"- cells: {cells} (events {len(eids)} × gendered premises {len(premises)})",
        f"- observer agreement: {agree}/{cells} = {agree / cells:.0%}",
        f"- mode disagreements: {len(disagreements)}",
        f"- LOD0: reused from events_{c}_grid_merged.jsonl (copied to events_{c}_gender_grid_merged.jsonl, unmodified)",
        "",
        "## disagreements by event",
    ] + [f"- {eid}: {n}" for eid, n in dis_by_event.most_common()]
    (DATA / f"merge_report_{c}_gender_grid.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"[merge] cells={cells}  agree={agree} ({agree / cells:.0%})  disagreements={len(disagreements)}")
    print(f"[saved] interpretations_{c}_gender_grid.jsonl / disagreements_{c}_gender_grid.jsonl / "
          f"events_{c}_gender_grid_merged.jsonl / merge_report_{c}_gender_grid.md")


if __name__ == "__main__":
    main()
