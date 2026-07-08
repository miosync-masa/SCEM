# Premise-Resolved Salience Extension for Dynamic SCEM

**Status:** specification (v0.1, 2026-07-08). Product-side architecture; **not part of the current paper.**
**Parent:** `paper2_gender_grid_spec.md` (gender grid, both countries collected) / V1 cross-check outputs (`data/gss_results/gender_gap_*.{csv,json}`).
**One-line summary:** the gender rounds established empirically that gendered variation does **not** primarily live in `mode`; it lives in `emphasis` and — for the MeToo/Instagram class of events — in `salience`. This spec extends the CMR operator from `Event × Premise → mode` to `Event × Premise → (mode, emphasis, salience)`, with salience **grounded in external data, never emitted as an LLM number.**

---

## 1. Why mode alone is insufficient

`mode` measures the **form** of impact (PASSIVE / ACTIVE / REFRAME). The gender grids (US 192 cells, UK 234 cells; ChatGPT × Claude) showed that form is largely gender-invariant even for events whose *experience* is strongly gendered:

- **Dobbs**: both genders land in the same form in every community (GFR 0/8) — for women as bodily self-determination, for men as political mobilization, but the *form* (forced decision / reference rewrite) coincides.
- **Sandy Hook**: the form itself flips (6/8 communities; F = REFRAME via child-safety reference rewrite, M = PASSIVE/ACTIVE).
- **UK 2008 crisis**: flips only in working-class communities (4/9; F = PASSIVE, M = ACTIVE) — the **breadwinner channel**: an event we had pre-classed as "gender-peripheral economic."

A product that describes people by mode alone therefore under-describes exactly the events where gendered experience is largest but formally identical (MeToo, Instagram, body norms). *"Exposed to the same event" is not the same as "exposed in the same meaning at the same weight."*

## 2. V1 result — external anchor for the decomposition

Event-matched cross-check, pre-fixed H1 declared before running (`src/adapters/gss/gss_gender_gap.py`):

| Event | GSS \|gender gap\| (year-FE) | grid GFR | grid emphasisΔ |
|---|---|---|---|
| Sandy Hook ↔ `gunlaw` | **13.1 pp** (F pro-regulation) | **75%** | **0.30** |
| Obergefell ↔ `marsame` (spliced) | 5.4 pp | 0% | 0.06 |
| Dobbs ↔ `abany` | **1.5 pp** (M slightly higher) | **0%** | **0.03** |

- H1 (|gap(gunlaw)| > |gap(abany)|): **satisfied.** Rank order of GSS gaps vs grid GFR and vs emphasisΔ: **concordant across all three events** (GFR with a tie at 0%).
- Reading: the observers did not apply the naive "body issues ⇒ gendered" prior; they reproduced the classic attitude-gap structure (abortion ≈ no gap, guns large gap). The failure of pre-fixed P1 in the grid round was a failure of *our prior*, not of the observers.
- Strength wording: *preliminary correspondence* (n = 3 matched events, descriptive rank check). Never "confirmation."

## 3. Three-layer decomposition (fixed by these results)

```
mode      — the FORM of impact (PASSIVE / ACTIVE / REFRAME).
            Gender-splits only where the forced-decision or reference-rewrite
            structure itself differs (guns/safety, breadwinner-crisis).
emphasis  — WHAT the event landed as (meaning components; effect_emphasis tags).
            Gender-splits along care, parenting, breadwinner, safety-perception
            channels. Already implemented and measured (Jaccard distance).
salience  — HOW HEAVILY it landed (weight in the exposure computation).
            The home of the MeToo / Instagram / body-norm / unwanted-attention
            class. NOT yet premise-resolved — this spec.
```

Empirical placement from the two rounds: Dobbs (no mode split, low emphasisΔ, low external gap — *correctly* undifferentiated) / Sandy Hook (all three layers split, externally concordant) / MeToo-class (form coincides, meaning and weight split — invisible to the current engine).

## 4. Why salience must never be an LLM-emitted number

Producing `female_salience = 0.87` from a language model would violate Honest Structuralism at its core (Non-overwrite / Provenance): the number would have **no observational anchor**, yet would flow into LOD 0 — the layer whose authority comes precisely from being computed, not interpreted. The division of labor is fixed:

```
LLM observer (interpretation layer):
  - resolved_mode, effect_emphasis, rationale          … as today
  - salience_channels[]: ENUMERATED candidate channels  … NEW (names, not numbers)
    e.g. ["unwanted_attention", "body_norm_pressure", "caregiving_load"]

External grounding (data layer):
  - survey gaps (GSS/ESS), attitude intensity, behavioral/usage indicators,
    domain-specific empirical findings
  - each mapped to a premise-resolved multiplier WITH source + status

SCEM engine (mathematics):
  - applies the grounded multiplier as part of LOD 0:
      w = s · g(a) · λ · m_salience(premise)
  - default m_salience = 1.0 whenever ungrounded (the engine never guesses)
```

The LLM proposes **where** weight differences may live; **how much** is answered only by external observation. An axiom check: the multiplier enters the mathematical layer *from data*, so LOD 0 remains non-interpretive; the LLM's `salience_channels` live at LOD 1 as provenance-traceable flags feeding a data-collection queue.

## 5. Grounding design

**Storage** — `data/salience_grounding_{country}.jsonl`:

```json
{"event_id": "us_sandy_hook_2012", "premise_pattern": "*_female",
 "channel": "child_safety_reference", "multiplier_tier": "elevated",
 "status": "grounded", "source": "GSS gunlaw gender gap +13.1pp (year-FE, 1972-2024)",
 "computed_by": "src/adapters/gss/gss_gender_gap.py"}
```

**Status vocabulary** (mandatory on every record and every UI surface):

| status | meaning |
|---|---|
| `grounded` | multiplier tier backed by a named external observation |
| `estimated` | interpolated from an adjacent grounded case; source of the analogy named |
| `ungrounded` | channel proposed by observers; **no weight applied** (m = 1.0); queued for evidence |

**Calibration protocol (pre-fixed before use):** external gaps map to **ordinal tiers** (baseline / elevated / strong), not free continuous values; the tier→multiplier table is fixed in advance and subjected to sensitivity analysis. Attitude gaps are *evidence about* differential landing, not the weight itself — the mapping is a declared calibration decision, revisable only by version bump.

## 6. Cases

| Case | mode | emphasis | salience (this spec) |
|---|---|---|---|
| **Dobbs** | same form both genders (GFR 0) | Δ0.03 — same axes | no gendered multiplier expected; status `grounded` as a **null** (GSS gap 1.5pp) — the engine's silence is correct |
| **Sandy Hook** | flips (6/8; F REFRAME) | Δ0.30 — child-safety / care | F-side `elevated`, grounded by gunlaw gap 13.1pp |
| **UK 2008 crisis** | flips in working-class only (F PAS / M ACT) | breadwinner, household risk | M-side candidate in industrial communities; grounding source: unemployment-by-sex×class series (ONS) — `ungrounded` until wired |
| **MeToo** | likely same form (REFRAME both) | splits: bodily autonomy / safety vs. norm recalibration | **the motivating case**: F-side multiplier from harassment-prevalence surveys and participation data; until wired, `ungrounded`, m = 1.0, channel visible in UI |
| **Instagram** | REFRAME both | visual self-presentation, peer validation, body-norm pressure, social comparison, unwanted attention | gendered usage-intensity and body-image findings as grounding; until then `ungrounded / requires usage and survey evidence` |

## 7. UI card format (Track B reflection)

Persona cards stop presenting mode alone. Three layers, with salience honesty surfaced to the end user:

```
Event: Sandy Hook / gun violence          (age 27 at impact)
  form      : ACTIVE
  landed as : child-safety reference point / care responsibility / household-risk perception
  weight    : elevated — grounded (GSS gender gap, large)

Event: Instagram diffusion                (age 24 at impact)
  form      : REFRAME
  landed as : visual self-presentation / body-norm pressure / social comparison
  weight    : not yet grounded — shown without weighting
```

Rules: (1) `landed as` comes from effect_emphasis of the person's own premise — never generic; (2) the weight line always carries the status word; `ungrounded` is displayed, never hidden and never silently weighted; (3) provenance links each line back to the LOD 0 event, as today.

---

**Sequencing:** this spec (now) → UI three-layer card (next) → additional external checks (UK employment/family-role instruments for the breadwinner channel; ESS `gndr` × freehms as the LGBT-side null) → engine wiring of `m_salience` behind a version bump.
