#!/usr/bin/env python3
"""
make_paper2_figures.py — Paper 2 Figure 2: Same Event × Community → mode 変換マトリクス(色図)

cmr_matrix.py と同じ実データ(interpretations_{country}.jsonl)から、
イベント(行)× Community(列)の resolved mode をセル色で描く。
同じ行(=同一イベント)で色が変われば「Community で mode が変換された」一撃。

LLM 呼び出しなし・捏造なし。'—' = データに無い (event, community)。

Run: python3 make_paper2_figures.py   → fig_p2_modematrix_us.png / _uk.png
"""
from __future__ import annotations
import json
import collections
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import cmr_matrix as CM   # COMMUNITIES / EVENTS / premise_matches / MODE_ABBR を再利用

plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False
DATA = Path(__file__).resolve().parent / "data"

# mode → 色(単一)。混合は別色。
MODE_COLOR = {"PAS": "#3b6fb0", "ACT": "#c0392b", "REF": "#2e8b57"}
MIXED = "#9b59b6"   # 複数 mode が同セルに
NODATA = "#e8e8e8"


def cell_modes(interps, spec, grid_mode):
    modes = set()
    for it in interps:
        p = it.get("premise")
        if p and ((p == spec) if grid_mode else CM.premise_matches(p, spec)):
            modes.add(CM.MODE_ABBR.get(it["expected_mode"], it["expected_mode"]))
    order = {"PAS": 0, "ACT": 1, "REF": 2}
    return sorted(modes, key=lambda m: order.get(m, 9))


def build(country, variant="v1"):
    grid_mode = variant != "v1"
    tag = country if not grid_mode else f"{country}_{variant}"
    I = [json.loads(l) for l in (DATA / f"interpretations_{tag}.jsonl")
         .read_text(encoding="utf-8").splitlines() if l.strip()]
    by_event = collections.defaultdict(list)
    by_eid = collections.defaultdict(list)
    for it in I:
        by_event[it["event_name"]].append(it)
        if it.get("event_id"):
            by_eid[it["event_id"]].append(it)
    comms = CM.COMMUNITIES_GRID[country] if grid_mode else CM.COMMUNITIES[country]
    events = CM.EVENTS_GRID[country] if grid_mode else CM.EVENTS[country]
    comm_names = [n for n, _ in comms]
    ev_labels = [lab for lab, _ in events]
    grid = []   # [row][col] = list of modes
    for _, spec in events:
        interps = by_eid.get(spec, []) if grid_mode else [it for ev, lst in by_event.items() if spec in ev for it in lst]
        grid.append([cell_modes(interps, cspec, grid_mode) for _, cspec in comms])
    return ev_labels, comm_names, grid


def draw(country, title, variant="v1"):
    ev_labels, comm_names, grid = build(country, variant)
    nrow, ncol = len(ev_labels), len(comm_names)
    fig, ax = plt.subplots(figsize=(1.7 * ncol + 3.5, 0.62 * nrow + 2))
    flips = 0
    covered = 0
    for r in range(nrow):
        row_modes = set(m for c in range(ncol) for m in grid[r][c])
        if row_modes:
            covered += 1
        if len(row_modes) >= 2:
            flips += 1
        for c in range(ncol):
            modes = grid[r][c]
            if not modes:
                color, txt = NODATA, "—"
            elif len(modes) == 1:
                color, txt = MODE_COLOR[modes[0]], modes[0]
            else:
                color, txt = MIXED, "/".join(modes)
            ax.add_patch(plt.Rectangle((c, nrow - 1 - r), 1, 1, facecolor=color,
                                       edgecolor="white", linewidth=2))
            ax.text(c + 0.5, nrow - 1 - r + 0.5, txt, ha="center", va="center",
                    fontsize=9, color="white" if modes else "#999",
                    fontweight="bold")
    ax.set_xlim(0, ncol); ax.set_ylim(0, nrow)
    ax.set_xticks([c + 0.5 for c in range(ncol)])
    ax.set_xticklabels(comm_names, fontsize=9.5, rotation=20, ha="left")
    ax.xaxis.set_ticks_position("top"); ax.xaxis.set_label_position("top")
    ax.set_yticks([nrow - 1 - r + 0.5 for r in range(nrow)])
    ax.set_yticklabels(ev_labels, fontsize=10)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    mfr = flips / covered if covered else 0
    ax.set_title(f"{title}\nMode Flip Rate(Community間で mode 分岐)= {flips}/{covered} = {mfr:.0%}",
                 fontsize=12, pad=28)
    legend = [Patch(facecolor=MODE_COLOR["PAS"], label="PASSIVE(受動)"),
              Patch(facecolor=MODE_COLOR["ACT"], label="ACTIVE(能動)"),
              Patch(facecolor=MODE_COLOR["REF"], label="REFRAME(基準書換)"),
              Patch(facecolor=MIXED, label="混合(モデル/前提で割れ)"),
              Patch(facecolor=NODATA, label="— データなし")]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              fontsize=9, frameon=False)
    fig.tight_layout()
    suffix = country if variant == "v1" else f"{country}_{variant}"
    out = Path(__file__).resolve().parent / "figures" / f"fig_p2_modematrix_{suffix}.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {out.name}  (MFR {flips}/{covered}={mfr:.0%})")


def draw_fingerprints(country, birth_year, variant="v1"):
    """Figure 3: Same Birth Year, Different Community — 指紋(P/A/R)を Community 別に並べる。
    cmr_compare_{country}_{by}[_grid].json(cmr_compare.py 出力)を読む。"""
    import numpy as np
    grid_mode = variant != "v1"
    src = DATA / (f"cmr_compare_{country}_{birth_year}_grid.json" if grid_mode
                  else f"cmr_compare_{country}_{birth_year}.json")
    if not src.exists():
        print(f"[skip fig3 {country}] {src.name} が無い(先に cmr_compare.py を実行)")
        return
    d = json.loads(src.read_text(encoding="utf-8"))
    profs = d["profiles"]
    comms = list(profs.keys())
    P = [profs[c]["fingerprint"]["P"] for c in comms]
    A = [profs[c]["fingerprint"]["A"] for c in comms]
    R = [profs[c]["fingerprint"]["R"] for c in comms]
    x = np.arange(len(comms)); w = 0.26
    fig, ax = plt.subplots(figsize=(1.5 * len(comms) + 3, 5))
    ax.bar(x - w, P, w, label="PASSIVE", color="#3b6fb0")
    ax.bar(x,     A, w, label="ACTIVE",  color="#c0392b")
    ax.bar(x + w, R, w, label="REFRAME", color="#2e8b57")
    ax.set_xticks(x); ax.set_xticklabels(comms, fontsize=9.5, rotation=15, ha="right")
    ax.set_ylabel("作用モード密度(平均weight)")
    ax.set_title(f"Same Birth Year, Different Community — {country.upper()} {birth_year}年生まれ"
                 + ("  [grid]" if grid_mode else "")
                 + f"\nContextual Divergence Index = {d['cdi']:.3f}", fontsize=12)
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.25)
    ax.set_ylim(0, max(P + A + R) * 1.2)
    fig.tight_layout()
    suffix = f"{country}_{birth_year}" if not grid_mode else f"{country}_{birth_year}_grid"
    out = DATA.parent / "figures" / f"fig_p2_fingerprints_{suffix}.png"
    fig.savefig(out, dpi=200); plt.close(fig)
    print(f"[saved] {out.name}")


if __name__ == "__main__":
    draw("us", "Same Event × Community → Resolved Mode  [US]")
    draw("uk", "Same Event × Community → Resolved Mode  [UK]")
    draw("us", "Same Event × Community → Resolved Mode  [US grid 8×12]", variant="grid")
    draw("uk", "Same Event × Community → Resolved Mode  [UK grid 9×13]", variant="grid")
    draw_fingerprints("us", 1985)
    draw_fingerprints("uk", 1985)
    draw_fingerprints("us", 1985, variant="grid")
    draw_fingerprints("uk", 1985, variant="grid")
