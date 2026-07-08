# Exposure Adapters — Implementation Spec: the layer that supplies SCEM's exposure structure

**Status:** specification (future implementation; today only curated_event_db + the DeepResearch grid are live).
**Scope:** the design of the **exposure-supply layer (Exposure Adapters)** placed *below* SCEM Core / the CMR Layer, and the specification of one such adapter, the **GDELT Adapter**.
**Design principle:** do not put GDELT at the core of the main design. To avoid dragging the core around by a free API and its operational constraints, GDELT is confined to the **Information Exposure Adapter spec**. The core stays a design that "separates material exposure structure, informational exposure structure, Community/Code, age-synchrony, and the 3 action modes — and integrates them last."

---

## 0. Overall architecture

SCEM consists of three layers + an exposure-supply layer. Exposure Adapters are **swappable data sources**; the core (Core/CMR) does not depend on their provenance.

```text
SCEM Core                                            [Paper 1, implemented]
  age-synchrony / 3 action modes (PASSIVE, ACTIVE, REFRAME)
  effect_vector / interference / REFRAME fire
────────────────────────────────────────────────────────────────────
CMR Layer                                            [Paper 2, implemented]
  Community / Code / premise
  resolved_mode (agree / disagree / operational)
  rationale / effect_emphasis / source_model
────────────────────────────────────────────────────────────────────
Exposure Adapters (swappable data sources)                ← THIS SPEC
  ├ curated_event_db      implemented (JP, 156 events)
  ├ DeepResearch grid     implemented (US/UK grid)
  ├ official_statistics   future (material exposure)
  ├ policy_datasets       future (material exposure)
  └ gdelt_adapter         future (informational exposure, spec only)
```

What the core (Core/CMR) receives is, regardless of provenance, a normalized **Event record** (`name / year / effective_year / effect_vector / salience / domain (display tag) / sensitivity_peak_age` …). An adapter's responsibility is limited to the conversion "each data source → this normalized record."

---

## 1. Separate the two kinds of exposure structure

The heart of SCEM's future extension is to **observe material exposure structure and informational exposure structure as separate lines, and integrate them last.** Mixing the two collapses into the false equation "lots of coverage = life changed."

| | Material Exposure Structure | Informational Exposure Structure |
|---|---|---|
| Definition | direct impact of institutions, economy, physical world, infrastructure | exposure mediated by coverage, media, social discourse, symbolic attention |
| Examples | employment, schooling, housing, disaster damage, legal status, public-health regulation | volume of news coverage, tone, social-media discourse, concentration of attention |
| Data sources | official_statistics / policy_datasets / disaster, housing, labor records | gdelt_adapter / media archives |
| Role in SCEM | the material component of effect_vector, grounding of effective_year | salience, tone, burst, diffusion, candidate REFRAME periods |
| Prohibited misuse | do not proxy it by coverage volume | do not treat it as the life impact itself |

Integration happens **on Core's effect_vector**: informational exposure supplies salience and effective_attention_year; material exposure supplies the material component of effect_vector and reference_value. Neither alone completes an Event.

---

## 2. GDELT Adapter Specification

GDELT measures not "society itself" but the **wave of informational exposure that appears in the coverage space.** Rather than building it into the core, it is defined as an adapter spec satisfying the following input/output contract.

```text
GDELT Adapter Specification

Purpose:
  automatic observation of the Informational Exposure Structure

Inputs:
  event_keyword     keyword/query representing the target event
  actor             involved actor (optional)
  location          geographic scope (country/region)
  time_range        observation period
  language          language
  region            aggregation region unit

Outputs:
  media_observed_salience    salience observed in the coverage space
  tone_trajectory            time series of tone (positive/negative)
  burstiness                 concentration of coverage (burstiness)
  geographic_spread          geographic diffusion
  language_spread            linguistic diffusion
  effective_attention_year   effective attention year (attention peak for impact-age computation)
  candidate_reframe_periods  candidate periods where reference-point rewriting occurred

NOT measured:
  the material exposure structure itself
  individual psychological state
  a complete measurement of actual institutional / life impact
```

### 2.1 Connection points to the core

- `effective_attention_year` → Core's impact-age computation (the informational-exposure version of `year`/`effective_year`). Useful for events whose coverage peak diverges from the actual event year (e.g. slow-burn scandals).
- `media_observed_salience` → the Event's `salience` (informational-exposure component). Held on a separate line from material-exposure salience and combined at integration.
- `candidate_reframe_periods` → only *proposes* candidates for REFRAME fire. The firing decision is made by Core's reference_value difference formula (the adapter does not decide).
- `tone_trajectory` / `burstiness` → auxiliary to the CMR rationale and to the context of observer-dependence (the "difference in observation stance on informational exposure" in §2.3).

### 2.2 Operational boundaries

- GDELT is **one implementation of an information-exposure adapter**, with gaps and biases. Its output is the quantity "only as it appears in the coverage space," not a population.
- Operational constraints (free API, rate limits, GKG schema changes, etc.) are **confined inside the adapter** and do not propagate to Core/CMR.
- Do not proxy material exposure with GDELT. Always cross-check against official_statistics / policy_datasets.

---

## 3. Ethical boundary (invariant even in productization)

This engine **does not assert an individual's inner life.** Its output is meaningful only in this form:

> an estimate of **what exposure structure a person placed in a given birth year, community, cultural preference, and institutional environment is likely to hold.**

That is, SCEM is not a tool for classifying, overwriting, or ranking people, but a **translation map between different worlds of meaning** (consistent with the ethics statement of Paper 2 §6.4). No matter how many data sources the adapter layer adds, it does not cross this boundary:

- It does not measure individual psychological state (explicitly listed as NOT measured for GDELT).
- A community profile is "the exposure structure a person placed in that environment is likely to hold," not a verdict about the individual.
- The provenance of any difference (age, community, normative code, material exposure, informational exposure, embodied reference point) is always kept traceable (Provenance).

**Four lines against misuse (stated at the design stage):** this model is powerful, and misused it could become an operational model of "hit this community with this stimulus and it moves." To prevent that:

| Uphold | Reject |
|---|---|
| **understanding**, not classification | classifying people by attribute and stopping there |
| **translation**, not manipulation | designing stimuli to move a community |
| **provenance-tracing**, not assertion | asserting an individual's inner life |
| **mutual understanding**, not division | fixing and legitimizing conflict |

---

## 4. Three tiers of value (for reference)

1. **Research tool:** redefine generations as exposure structure rather than birth-year labels (Paper 1 + Paper 2).
2. **Marketing tool:** even at the same age and preferences, a different Community/Code changes "which options feel natural / which words feel fishy." Can sit behind copy generation.
3. **Social-analysis tool:** treat immigration, religion, class, region, education, housing, employment, public safety, disaster, war, and pandemic not as "events" but as **per-community action transformation.**

All are operated only under the ethical boundary of §3.

---

## 5. Implementation order

```text
Now:          full grid of fixed events × fixed communities (US/UK complete)
Future:       pick up coverage volume, tone, geographic diffusion, burst via GDELT (this spec)
Further out:  combine with statistical data; separate informational and material exposure
              and update dynamically (Dynamic SCEM)
```

GDELT stays a Future spec; the top priority is first to solidify the **full-grid US/UK CMR.**
