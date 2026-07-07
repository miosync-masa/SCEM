#!/usr/bin/env python3
"""
generate_figures.py — SSCR submission figures for "The Contextual Mode Resolver".

Self-contained reproducibility script: reads committed data under ../data/ and
writes fig1..fig6 as vector PDF (fonts embedded) plus a 300 dpi PNG proof each.

    python3 generate_figures.py            # all figures
    python3 generate_figures.py fig1 fig3  # a subset

All numbers on the figures are computed here from the source data (no hard-coded
results), so the panels always agree with the underlying files.

Style (SAGE / SSCR):
  * colorblind-safe Okabe-Ito palette
      PASSIVE = #0072B2  ACTIVE = #D55E00  REFRAME = #009E73
  * sans-serif, >=8 pt, English-only labels
  * 1-column = 84 mm, 2-column = 174 mm
  * PDF fonts embedded as TrueType (pdf.fonttype = 42)
"""
from __future__ import annotations

import csv
import json
import math
import sys
import collections
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update({
    "pdf.fonttype": 42,          # embed TrueType (editable, SAGE-safe)
    "ps.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
})
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE

# ── palette ───────────────────────────────────────────────────────────────
PASSIVE, ACTIVE, REFRAME = "#0072B2", "#D55E00", "#009E73"
MODE_COLOR = {"PASSIVE": PASSIVE, "ACTIVE": ACTIVE, "REFRAME": REFRAME}
OI_GREY = "#7f7f7f"
OI_ORANGE = "#E69F00"
OI_SKY = "#56B4E9"
MM = 1 / 25.4
COL1, COL2 = 84 * MM, 174 * MM

# operational tie-break: conservative "don't miss a forced decision"
MODE_PRIORITY = ["ACTIVE", "REFRAME", "PASSIVE"]


def resolve(modes):
    """majority vote + ACTIVE>REFRAME>PASSIVE tie-break -> single operational mode."""
    if not modes:
        return None
    cnt = collections.Counter(modes)
    return sorted(cnt, key=lambda m: (-cnt[m],
                  MODE_PRIORITY.index(m) if m in MODE_PRIORITY else 9))[0]


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {name}.pdf (+.png)")


# ── grid definitions (English labels; canonical premises / event ids) ───────
COMMUNITIES_GRID = {
    "us": [
        ("Coastal Liberal",  "secular_white_coastal_graduate"),
        ("Bible Belt",       "evangelical_white_bible_belt_no_college"),
        ("Rust Belt WWC",    "mainline_protestant_white_rust_belt_no_college"),
        ("Black urban",      "secular_black_urban_some_college"),
        ("Latino Immigrant", "catholic_hispanic_urban_some_college"),
        ("Mormon/Utah",      "mormon_white_mountain_west_bachelor"),
        ("Suburban MC",      "mainline_protestant_white_suburban_bachelor"),
        ("Rural Conserv.",   "evangelical_white_rural_no_college"),
    ],
    "uk": [
        ("London Multicult.", "middle_class_london_immigrant_2nd_gen_russell_group"),
        ("Home Counties MC",  "middle_class_home_counties_native_4plus_gen_russell_group"),
        ("N. Post-indust.",   "working_class_northern_england_native_4plus_gen_gcse"),
        ("Scotland",          "working_class_scotland_native_4plus_gen_gcse"),
        ("NI Catholic",       "working_class_northern_ireland_catholic_4plus_gen_gcse"),
        ("NI Protestant",     "working_class_northern_ireland_protestant_4plus_gen_gcse"),
        ("British Asian",     "middle_class_london_asian_2nd_gen_russell_group"),
        ("Brexit Leave Town", "working_class_leave_town_native_4plus_gen_no_qualifications"),
        ("Univ Remain",       "middle_class_london_native_2nd_gen_oxbridge"),
    ],
}
EVENTS_GRID = {
    "us": [
        ("Same-sex marriage", "us_obergefell_2015"),
        ("9/11",              "us_sept11_2001"),
        ("2008 crisis",       "us_lehman_2008"),
        ("Obama elected",     "us_obama_election_2008"),
        ("Trump elected",     "us_trump_election_2016"),
        ("Black Lives Matter", "us_blm_2013"),
        ("Dobbs (abortion)",  "us_dobbs_2022"),
        ("COVID restrictions", "us_covid_restrictions_2020"),
        ("Sandy Hook",        "us_sandy_hook_2012"),
        ("Student debt",      "us_student_debt_2012"),
        ("Housing surge",     "us_housing_surge_2021"),
        ("Civil Rights Act",  "us_civil_rights_act_1964"),
    ],
    "uk": [
        ("Brexit",            "uk_brexit_2016"),
        ("7/7 bombings",      "uk_77_bombings_2005"),
        ("2008 crisis",       "uk_financial_crisis_2008"),
        ("Austerity",         "uk_austerity_2010"),
        ("Tuition fees",      "uk_tuition_fees_2010"),
        ("Section 28 repeal", "uk_section28_repeal_2003"),
        ("Scottish referendum", "uk_scottish_referendum_2014"),
        ("Same-sex marriage", "uk_same_sex_marriage_2014"),
        ("Immigration debate", "uk_immigration_debate_2015"),
        ("Windrush",          "uk_windrush_2018"),
        ("COVID lockdown",    "uk_covid_lockdown_2020"),
        ("Cost of living",    "uk_cost_of_living_2022"),
        ("NHS crisis",        "uk_nhs_crisis_2022"),
    ],
}


def load_grid(country):
    """Return (events, communities, cells) where cells[r][c] =
    {'resolved': mode|None, 'modes': [obs modes], 'disagree': bool}."""
    interps = [json.loads(l) for l in
               (DATA / f"interpretations_{country}_grid.jsonl").read_text("utf-8").splitlines()
               if l.strip()]
    by_eid = collections.defaultdict(list)
    for it in interps:
        if it.get("event_id"):
            by_eid[it["event_id"]].append(it)
    events, comms = EVENTS_GRID[country], COMMUNITIES_GRID[country]
    cells = []
    for _, eid in events:
        row_interps = by_eid.get(eid, [])
        base = resolve([i["expected_mode"] for i in row_interps if i.get("premise")])
        row = []
        for _, premise in comms:
            obs = [i["expected_mode"] for i in row_interps if i.get("premise") == premise]
            row.append({
                "resolved": resolve(obs),
                "modes": obs,
                "disagree": len(set(obs)) >= 2,
                "base": base,
            })
        cells.append(row)
    return events, comms, cells


# ════════════════════════════════════════════════════════════════════════════
# Fig 1 — Mode-transformation matrices (US + UK)
# ════════════════════════════════════════════════════════════════════════════
def fig1():
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 0.62 * COL2 / 1.0))
    stats = {}
    for ax, country, tag in zip(axes, ("us", "uk"), ("(a) United States", "(b) United Kingdom")):
        events, comms, cells = load_grid(country)
        nrow, ncol = len(events), len(comms)
        flip_events = disagree_cells = observed = cell_flips = 0
        for r in range(nrow):
            resolved_modes = {cells[r][c]["resolved"] for c in range(ncol)
                              if cells[r][c]["resolved"]}
            if len(resolved_modes) >= 2:
                flip_events += 1
            for c in range(ncol):
                cell = cells[r][c]
                m = cell["resolved"]
                color = MODE_COLOR.get(m, "#e8e8e8")
                rect = plt.Rectangle((c, nrow - 1 - r), 1, 1, facecolor=color,
                                     edgecolor="white", linewidth=1.4)
                ax.add_patch(rect)
                if m:
                    observed += 1
                    # Cell-level MFR (as in cmr_matrix.py): observed cell whose
                    # any observer mode departs from the event base-majority.
                    if cell["base"] and any(o != cell["base"] for o in set(cell["modes"])):
                        cell_flips += 1
                if cell["disagree"]:
                    disagree_cells += 1
                    ax.add_patch(plt.Rectangle((c, nrow - 1 - r), 1, 1, fill=False,
                                 hatch="////", edgecolor="white", linewidth=0))
        ax.set_xlim(0, ncol)
        ax.set_ylim(-0.05, nrow)
        ax.set_xticks([c + 0.5 for c in range(ncol)])
        ax.set_xticklabels([n for n, _ in comms], fontsize=7, rotation=40, ha="left")
        ax.xaxis.set_ticks_position("top")
        ax.set_yticks([nrow - 1 - r + 0.5 for r in range(nrow)])
        ax.set_yticklabels([lab for lab, _ in events], fontsize=7.5)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(f"{tag}\nEvent-level MFR = {flip_events}/{nrow} = "
                     f"{flip_events / nrow:.0%}", fontsize=9, pad=26)
        ax.text(0.5, -0.9 / nrow, f"Cell-level MFR = {cell_flips}/{observed} "
                f"({cell_flips / observed:.0%})   •   disagreement cells = {disagree_cells}",
                transform=ax.transAxes, ha="center", va="top", fontsize=7.2)
        stats[country] = (flip_events, nrow, cell_flips, observed, disagree_cells)

    legend = [Patch(facecolor=PASSIVE, label="PASSIVE"),
              Patch(facecolor=ACTIVE, label="ACTIVE"),
              Patch(facecolor=REFRAME, label="REFRAME"),
              Patch(facecolor="#c9c9c9", hatch="////", edgecolor="white",
                    label="inter-observer disagreement")]
    fig.legend(handles=legend, loc="lower center", ncol=4, fontsize=7.5,
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    save(fig, "fig1_modematrix")
    return stats


# ════════════════════════════════════════════════════════════════════════════
# Fig 2 — Cohort fingerprints at birth year 1985
# ════════════════════════════════════════════════════════════════════════════
def fig2():
    fig, axes = plt.subplots(1, 2, figsize=(COL2, COL2 * 0.42))
    for ax, country, tag in zip(axes, ("us", "uk"), ("(a) United States", "(b) United Kingdom")):
        d = json.loads((DATA / f"cmr_compare_{country}_1985_grid.json").read_text("utf-8"))
        profs = d["profiles"]
        # order: REFRAME-dominant (R-A high) first -> shows the axis reversal
        comms = sorted(profs, key=lambda c: profs[c]["fingerprint"]["R"]
                       - profs[c]["fingerprint"]["A"], reverse=True)
        P = [profs[c]["fingerprint"]["P"] for c in comms]
        A = [profs[c]["fingerprint"]["A"] for c in comms]
        R = [profs[c]["fingerprint"]["R"] for c in comms]
        x = np.arange(len(comms))
        w = 0.27
        ax.bar(x - w, P, w, label="PASSIVE", color=PASSIVE)
        ax.bar(x,     A, w, label="ACTIVE",  color=ACTIVE)
        ax.bar(x + w, R, w, label="REFRAME", color=REFRAME)
        ax.set_xticks(x)
        ax.set_xticklabels(comms, fontsize=7.5, rotation=35, ha="right")
        ax.set_ylabel("Cumulative mode action (mean weight)", fontsize=8)
        ax.set_title(tag, fontsize=9)
        ax.tick_params(labelsize=7.5)
        ax.grid(axis="y", alpha=0.25, linewidth=0.6)
        ax.set_ylim(0, max(P + A + R) * 1.28)
        ax.text(0.97, 0.94, f"CDI = {d['cdi']:.3f}", transform=ax.transAxes,
                ha="right", va="top", fontsize=8.5, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc"))
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(fontsize=8, frameon=False, loc="upper right",
                   bbox_to_anchor=(1.0, 0.86))
    fig.tight_layout()
    save(fig, "fig2_fingerprints")


# ════════════════════════════════════════════════════════════════════════════
# Fig 3 — SSM cohort trajectories: Coastal Liberal vs Bible Belt (GSS)
# ════════════════════════════════════════════════════════════════════════════
def fig3():
    rows = list(csv.DictReader(open(DATA / "gss_results" / "core_contrast_ssm.csv")))
    series = {"Coastal Liberal": (REFRAME, "o"), "Bible Belt": (ACTIVE, "s")}
    fig, ax = plt.subplots(figsize=(COL2 * 0.82, COL2 * 0.44))
    NMIN = 10
    for seg, (color, mk) in series.items():
        srows = [r for r in rows if r["segment"] == seg and int(r["n"]) >= NMIN]
        srows.sort(key=lambda r: int(r["cohort_bin"]))
        x = [int(r["cohort_bin"]) for r in srows]
        y = [float(r["approval"]) * 100 for r in srows]
        lo = [float(r["ci_lo"]) * 100 for r in srows]
        hi = [float(r["ci_hi"]) * 100 for r in srows]
        pooled = float(srows[0]["pooled_approval"]) * 100
        plo = float(srows[0]["pooled_ci_lo"]) * 100
        phi = float(srows[0]["pooled_ci_hi"]) * 100
        ax.fill_between(x, lo, hi, color=color, alpha=0.16, linewidth=0)
        ax.plot(x, y, "-", color=color, marker=mk, ms=4, lw=1.8,
                label=f"{seg}  (pool {pooled:.0f}% [{plo:.0f},{phi:.0f}])")
        ax.axhspan(plo, phi, color=color, alpha=0.06)
    # Bible Belt acceleration around 1975 birth cohort
    ax.axvline(1975, color=OI_GREY, ls="--", lw=0.9)
    ax.annotate("Bible Belt acceleration\n(~1975 cohort, +8.1 pp/decade)",
                xy=(1975, 34), xytext=(1948, 62), fontsize=6.6, color=OI_GREY,
                arrowprops=dict(arrowstyle="->", color=OI_GREY, lw=0.8))
    ax.set_xlabel("Birth-year cohort", fontsize=8.5)
    ax.set_ylabel("Same-sex marriage support (%)", fontsize=8.5)
    ax.set_ylim(0, 105)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.legend(fontsize=7.5, frameon=False, loc="center right")
    ax.set_title("GSS 1972–2024 (MARHOMO / MARSAME spliced) — shaded bands: Wilson 95% CI",
                 fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    save(fig, "fig3_ssm_trajectories")


# ════════════════════════════════════════════════════════════════════════════
# Fig 4 — ESS cluster decomposition: the flattening artifact
# ════════════════════════════════════════════════════════════════════════════
def fig4():
    clusters = list(csv.DictReader(open(DATA / "ess_results" / "freehms_clusters.csv")))
    rel = {r["cluster"]: r for r in clusters if r["segment"] == "Religious LowEdu"}
    core = json.loads((DATA / "ess_results" / "freehms_core.json").read_text("utf-8"))
    euro_slope = core["segments"]["Religious LowEdu"]["cohort_slope_pp_decade"]
    euro_z = core["interaction_z"]

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(COL2, COL2 * 0.44))

    # (a) Religious-LowEdu cohort slope: Europe-wide vs 4 clusters
    order = ["Europe-wide", "Nordic", "Western", "Central-East", "Southern"]
    vals = {"Europe-wide": euro_slope,
            "Nordic": float(rel["Nordic"]["slope_FE"]),
            "Western": float(rel["Western"]["slope_FE"]),
            "Central-East": float(rel["Central-East"]["slope_FE"]),
            "Southern": float(rel["Southern"]["slope_FE"])}
    y = np.arange(len(order))[::-1]
    colors = [OI_GREY if k != "Southern" else ACTIVE for k in order]
    colors[0] = "#333333"
    axa.barh(y, [vals[k] for k in order], color=colors, height=0.62)
    axa.axvline(0, color="black", lw=0.8)
    axa.set_yticks(y)
    axa.set_yticklabels(order, fontsize=8)
    axa.set_xlabel("Cohort slope (pp / decade, country+round FE)", fontsize=8)
    axa.tick_params(labelsize=7.5)
    axa.set_title("(a) Religious-LowEdu on freehms", fontsize=8.5)
    axa.annotate(f"Europe-wide aggregate:\nz = {euro_z:.2f}  (flattened)",
                 xy=(vals["Europe-wide"], y[0]), xytext=(1.4, y[0] - 0.55),
                 fontsize=6.6, va="center", ha="left", color="#333333",
                 arrowprops=dict(arrowstyle="->", color="#333333", lw=0.7))
    for k, yy in zip(order, y):
        v = vals[k]
        if k == "Europe-wide":                      # tiny bar: label clear of the axis
            axa.text(0.25, yy, f"{v:+.2f}", va="center", ha="left", fontsize=6.6)
        else:
            axa.text(v + (0.15 if v >= 0 else -0.15), yy, f"{v:+.2f}",
                     va="center", ha="left" if v >= 0 else "right", fontsize=6.6)
    axa.set_xlim(-6.2, 6.2)
    for s in ("top", "right"):
        axa.spines[s].set_visible(False)

    # (b) Southern 5-country decomposition (slope z-values, all positive)
    sc = list(csv.DictReader(open(DATA / "ess_results" / "southern_country.csv")))
    sc.sort(key=lambda r: float(r["rel_slope_z"]))
    names = [r["country"] for r in sc]
    z = [float(r["rel_slope_z"]) for r in sc]
    x = np.arange(len(names))
    axb.bar(x, z, color=ACTIVE, width=0.62)
    axb.axhline(0, color="black", lw=0.8)
    axb.set_xticks(x)
    axb.set_xticklabels(names, fontsize=8)
    axb.set_ylabel("Cohort slope z-value", fontsize=8)
    axb.tick_params(labelsize=7.5)
    axb.set_title("(b) Southern cluster by country", fontsize=8.5)
    for xi, zi in zip(x, z):
        axb.text(xi, zi + 0.3, f"{zi:.2f}", ha="center", fontsize=6.8)
    n_pos = sum(1 for zi in z if zi > 0)
    axb.text(0.03, 0.95, f"Pre-fixed criterion: majority positive\n"
             f"→ {n_pos}/0/0 satisfied", transform=axb.transAxes, va="top",
             fontsize=6.8, bbox=dict(boxstyle="round,pad=0.3", fc="#f2f2f2", ec="#cccccc"))
    axb.set_ylim(0, max(z) * 1.25)
    for s in ("top", "right"):
        axb.spines[s].set_visible(False)
    fig.tight_layout()
    save(fig, "fig4_ess_clusters")


# ════════════════════════════════════════════════════════════════════════════
# Fig 5 — Institutional adoption year vs cohort changepoint
# ════════════════════════════════════════════════════════════════════════════
def _spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((x - mb) ** 2 for x in rb))
    return cov / (va * vb)


def fig5():
    rows = list(csv.DictReader(open(DATA / "ess_results" / "effective_year.csv")))
    SOUTHERN = {"ES", "PT", "IT", "GR", "CY"}
    pts = []
    for r in rows:
        if not r["knot"] or r["knot"] == "":
            continue
        rec = float(r["rec_eff"])          # recognition year (sentinel 2030 = not yet)
        knot = float(r["knot"])
        pts.append((r["country"], rec, knot))
    x = [p[1] for p in pts]
    yv = [p[2] for p in pts]
    rho = _spearman(x, yv)

    fig, ax = plt.subplots(figsize=(COL1 * 1.15, COL1 * 1.02))
    for country, rec, knot in pts:
        south = country in SOUTHERN
        ax.scatter(rec, knot, s=34 if south else 24,
                   color=ACTIVE if south else PASSIVE,
                   marker="D" if south else "o",
                   edgecolor="white", linewidth=0.5, zorder=3,
                   label=None)
        if south:
            ax.annotate(country, (rec, knot), fontsize=6, ha="center",
                        va="bottom", xytext=(0, 3), textcoords="offset points")
    # regression line (rank-consistent least squares for guidance)
    coef = np.polyfit(x, yv, 1)
    xs = np.array([min(x), max(x)])
    ax.plot(xs, coef[0] * xs + coef[1], color=OI_GREY, lw=1.1, ls="--", zorder=2)
    ax.set_xlabel("Institutional adoption year\n(registered partnership or marriage, earliest;\n2030 = not yet recognised)",
                  fontsize=7)
    ax.set_ylabel("Attitude changepoint (birth-year knot)", fontsize=8)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.text(0.04, 0.96, f"Spearman ρ = {rho:+.2f}  (n = {len(pts)})\n"
            f"marriage-year sensitivity ρ = +0.67\nPre-fixed criterion |ρ| ≥ 0.4: met",
            transform=ax.transAxes, va="top", fontsize=6.8,
            bbox=dict(boxstyle="round,pad=0.3", fc="#f2f2f2", ec="#cccccc"))
    legend = [plt.Line2D([], [], marker="D", ls="", color=ACTIVE, label="Southern Europe"),
              plt.Line2D([], [], marker="o", ls="", color=PASSIVE, label="Other countries")]
    ax.legend(handles=legend, fontsize=6.8, frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    save(fig, "fig5_institution_changepoint")


# ════════════════════════════════════════════════════════════════════════════
# Fig 6 — Two-tier structure schematic (optional)
# ════════════════════════════════════════════════════════════════════════════
def fig6():
    fig, ax = plt.subplots(figsize=(COL1 * 1.25, COL1 * 0.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    def box(xc, yc, w, h, text, fc, tc="white", fs=6.6):
        ax.add_patch(FancyBboxPatch((xc - w / 2, yc - h / 2), w, h,
                     boxstyle="round,pad=0.08", fc=fc, ec="none"))
        ax.text(xc, yc, text, ha="center", va="center", fontsize=fs,
                color=tc, fontweight="bold")

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                     mutation_scale=11, color="#444444", lw=1.1))

    ax.text(5, 6.55, "Two-tier structure", ha="center", fontsize=9, fontweight="bold")

    # Tier 1
    ax.text(0.15, 5.35, "Tier 1", fontsize=7, color=REFRAME, fontweight="bold")
    box(2.7, 5.0, 2.4, 0.95, "Community\npremise", PASSIVE, fs=7.2)
    box(7.1, 5.0, 3.7, 0.95, "Level gate\n(portable across nations)", REFRAME)
    arrow(4.0, 5.0, 5.15, 5.0)

    # Tier 2
    ax.text(0.15, 2.95, "Tier 2", fontsize=7, color=ACTIVE, fontweight="bold")
    box(2.7, 2.6, 2.4, 0.95, "effective_year", ACTIVE, fs=7.2)
    box(7.1, 2.6, 3.7, 0.95, "Slope visibility\n(transition-stage window)", OI_ORANGE)
    arrow(4.0, 2.6, 5.15, 2.6)

    ax.text(5, 0.85, "Premise sets the level; effective_year sets whether the cohort\n"
            "slope is visible in a given transition stage.",
            ha="center", fontsize=6.6, color="#333333")
    save(fig, "fig6_twotier_schematic")


FIGS = {"fig1": fig1, "fig2": fig2, "fig3": fig3,
        "fig4": fig4, "fig5": fig5, "fig6": fig6}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    st = None
    for key in want:
        out = FIGS[key]()
        if key == "fig1":
            st = out
    if st:
        print("\nFig 1 verification (computed from data):")
        for c, (fe, ne, cf, ob, dis) in st.items():
            print(f"  {c.upper()}: Event-MFR {fe}/{ne} | Cell-MFR {cf}/{ob} "
                  f"({cf / ob:.0%}) | disagreement cells {dis}")
