# SCEM — Architecture (v7)

**Status: FIXED (2026-07-01).** The single source of truth. All subsequent code and papers follow this spec. Any change to the spec must bump the version.
v7 is the integration of v6 (2026-06-24, structural layer only) + the LOD Architecture (2026-06-25, persona generation) into **Track A / Track B**.

**Scope:** the collective exposure structure. **Individual inner life and individual lag are out of scope** (→ [Out of scope](#out-of-scope-deliberate-boundaries)).
Abbreviation: **SCEM**. Paper 1's Japanese title, "Age-synchronized media generation theory," is the generational presentation of this model.

---

## 0. Positioning — two faces, one engine

SCEM has two faces standing on a **shared engine (Core = LOD 0 = the mathematics of exposure structure):**

- **Track A (structural / academic)** — uses LOD 0 as **generation theory**. It computes generational fingerprints from a tensor of event × impact age × action mode, and resolves the mode by community premise (CMR). → [Part A](#part-a--architecture-of-the-structural--academic-track-track-a)
- **Track B (persona generation)** — uses LOD 0 as a **generative anchor**. It generates a persona (LOD 3) from the exposure structure (LOD 0), provenance-traceable, within a CSP whose constraints are the 4 axioms. → [Part B](#part-b--architecture-of-persona-generation-track-b)

**Central principle (shared by both tracks):**
> **Mathematics (Python) = event = fixed = exposure structure / interpretation (LLM) = response = branchable = persona expression.**

Mathematics handles what can be stably quantified (age, sensitivity curves, cos, `effective_year`); interpretation handles what thins out when quantified (texture, norms, context). The two are **mutually irreplaceable** and combine at the junctions of cos and Projection. This division of labor is the foundation of both tracks.

---

# Part A — Architecture of the Structural / Academic Track (Track A)

## A1. Structural layer (Core) — event × impact age × action mode  〔implemented: `src/core/media_generation_v4.py` / `v5.py` / `event_loader.py`〕

- **Three action modes** PASSIVE / ACTIVE / REFRAME. Not equated by raw sum but held on **3 axes** (`mode_density`, `report_3axis`):
  - PASSIVE (passive impact): $w = s\cdot\lambda$
  - ACTIVE (active branching = forced decision): $w = s\cdot(0.30+0.70\alpha)\cdot\lambda$
  - REFRAME (reference-point rewriting): $w = s\cdot(0.50+0.50\alpha)\cdot\lambda$
- **Sensitivity curve** an asymmetric Gaussian, an **individual-peak-preferring hybrid** (use the per-item `sensitivity_peak_age` if present, otherwise fall back to the 33 domain×mode curves):
  $g(a)=\max(\phi,\ \exp[-(a-\mu)^2/2\sigma(a)^2])$, $\sigma=\sigma_L\,(a\le\mu)\ /\ \sigma_R\,(a>\mu)$.
- **REFRAME firing** anchor→trigger within the same `reframe_group`, firing on the **log ratio** of `reference_value`:
  $\delta=\min(1,\ \log(\max/\min)/\log 2)$, $\text{fire}=w_a(0.35+0.65\,w_t)\,\delta$.
- **Interference** only for simultaneous impacts on the same cognitive band. Amplified by **action orthogonality** $D=1.6-1.05\min(\cos,1)$ (cos=0→1.6 / cos=1→0.55):
  $\text{score}=\frac{w_a+w_b}{2}\cdot D\cdot(0.5+0.5\,p)$, $p=1-\min(\delta a/W,1)$.
- **Overlap judgment** uses **only the cosine** of the `effect_vector`, in 4 grades (duplicate/sibling/interference/independent). **Domain does not enter the computation.**
- **Do not collapse an event into a single category** = a continuous action vector $\mathbf{v}_e$. Domain is merely a **human-facing display tag** and does not enter the computation (design rationale in §C3).

## A2. Community layer — modulation by the Situated (environment)  〔prototype: `src/culture/community_experiment.py`〕

- **Degree of closure** = **discrete archetype** (open / intermediate / closed). It **forms clusters**. It contains the Code (normative code = permitted / forbidden / tolerated / recommended).
  - Empirical basis: with closure fixed (speed varying), mean cos = 0.90 > with speed fixed = 0.86. A closed type converges to a single point regardless of speed (internal cos = 0.93) → discrete treatment is justified.
- **Propagation speed** = **continuous offset**. It modulates `effective_year` by region (fast 0 / medium +1 / slow +2 years). It **does not form clusters** (it smoothly shifts points within the same degree of closure).
- Closure produces individual embodiment delay, but **individual lag itself is not measured** (it is treated as collective exposure structure).

## A3. Culture layer — preference divergence (hypothesis generator)  〔implemented: `src/culture/culture_axis.py` / `generate_picks.py` / `compare_picks.py`〕

- LLM-generated 4-axis pick lists (music / sports / literature / film) per generation. A structural profile + preferences generate cultural subclusters.
- Its status is a **hypothesis generator**, not a measurement of a real distribution.

## A4. CMR Layer — contextual mode resolution (added in Paper 2)  〔implemented: `src/cmr/`〕

- Lifts `Event.mode` from a fixed value into the **operator `Event × Premise → ResolvedImpact`**. Even for the same event, the community premise changes PASSIVE/ACTIVE/REFRAME.
- Resolves the mode with multiple LLM observers (ChatGPT × Gemini × Claude), and rather than erasing disagreement, **measures it as observer-dependence** (`cmr_matrix.py` / `cmr_compare.py` / `merge_paper2_data.py`).
- Measures mode transformation, MFR, and CDI over designed comparison grids (US 8×12 / UK 9×13). Details in the Paper 2 manuscript (Contextual Mode Resolver).

## A5. Exposure Adapters — the supply layer for exposure structure  〔`src/adapters/{gss,ess}/`〕

- **Swappable data sources** for exposure structure: curated DB (`events_patched.jsonl`) / external surveys (GSS = US, ESS = UK/Europe) / future GDELT, etc.
- The design of observing material exposure (statistics, policy) and informational exposure (news coverage) as separate lines and integrating them in Core is in `docs/exposure_adapters_spec.md`.

## A6. Grounding — prompt tuning (architecture-independent)

- Sharpening the LLM's resolution of regional characteristics = the **only remaining adjustment**. The architecture does not change; this is a matter of prompt quality.

## Out of scope (deliberate boundaries)

Boundaries we chose **not** to cross, to keep "the object = the collective exposure structure":
- **The individual layer** (self-efficacy, individual ability and will). * However, Track B treats "individual persona expression" as LOD 3 — this is **not an assertion about the individual** but interpretive generation of "the exposure structure a person in that position is likely to hold" (→ Part B ethical boundary).
- **The individual information-embodiment lag** (sampled in `test_lag.py` → collective diffusion lag runs opposite to the hypothesis and is contaminated by right-censoring. The individual "know vs. become" gap cannot be measured with this proxy and is out of bounds).
- **A dynamic model of cross-regional embodiment spillover** (chasm / diffusion dynamics between regions).

## Validation architecture (the place of external cross-checking)

- The validity of Core/CMR is examined by **cross-checking against external surveys (GSS/ESS)**. **The validation question is not predictive accuracy but "the existence of an intermediate tendency bundle that clears the personalization ↔ statistical-aggregate trade-off."** The strength is "prediction-consistent, suggestive, modest"; never write "confirmation."
- The main result = the **two-tier structure**: premise drives the level, `effective_year` drives slope visibility (transition stage). Numbers in `SI/results_tables.md`; reproduction via `SI/reproduce_all.sh`.

---

# Part B — Architecture of Persona Generation (Track B)

This formalizes **what lies beyond** the boundary at which Paper 1 declared "the individual layer is out of scope," as a **resolution hierarchy** from LOD 0 (exposure structure) → LOD 3 (individual persona). **No change whatsoever** is made to the Core engine (`v4/v5`).

## B1. The LOD hierarchy (Level of Detail)

Isomorphic to LOD in 3D graphics. The use case (camera distance) determines the LOD, and the LOD determines the scope.

| LOD | Name | Content | Math : interpretation | Owner |
|-----|------|---------|-----------------------|-------|
| 0 | ExposureStructure | exposure profile (3-axis fingerprint, key events, interference, REFRAME firing) | 100:0 | Python (Core) |
| 1 | ResponseOrientation | response direction (Fight / Flight, etc.) | 50:50 | LLM |
| 2 | StrategyBranch | strategy branch (attack via technology / defend via a large firm, etc.) | 25:75 | LLM |
| 3 | PersonalContext | personal context (occupation, family, region, assets, education, relational capital) | 5:95 | LLM |

**Transitions:** `refine: LOD_n → LOD_{n+1}` (adding interpretation = branching) / `project: LOD_{n+1} → LOD_n` (summarizing = projection).
```
LOD₀ = ExposureStructure
LOD₁ = refine(LOD₀, response_orientation)
LOD₂ = refine(LOD₁, strategy_branch)
LOD₃ = refine(LOD₂, personal_context)
```
**Use-case mapping:** sociology = LOD 0 is enough / marketing = LOD 1–2 (the true identity of Paper 1 Appendix D) / counseling = LOD 3. **An LOD beyond the use case is redundant.**
**Continuity:** LOD is not a discrete switch but seamless (LOD 1.5 is allowed). It is structurally isomorphic to "treating a generation as a continuous profile."

## B2. The 4 axioms (Honest Structuralism / SCEM Axioms)

The correctness conditions LOD operations must satisfy — and simultaneously the validation criteria for LLM generation.

- **Axiom 1: Anchor Preservation** — the events, ages, modes, and weights of a lower LOD are preserved (the mathematics is an immovable skeleton). Violation example: LOD 3 generates "was not affected by the employment ice age," contradicting LOD 0.
- **Axiom 2: Non-overwrite** — a higher LOD's interpretation does not rewrite the mathematical result. **Adding** information is fine; **rewriting** is not. Violation example: interpreting "because this is a Fight type, the sensitivity peak shifts younger" to change the mathematics.
- **Axiom 3: Projection Consistency** — `project(LOD₃→LOD₀)=LOD₀`. Summarizing the generated persona restores the original exposure structure (the operational definition that LOD 3 contains LOD 0). Violation example: LOD 3 says "no college" while LOD 0 has a high-weight "college enrollment at 19, ACTIVE."
- **Axiom 4: Provenance Traceability** — every interpretive branch can be traced to which event, interference, or REFRAME it derived from. Violation example: it is unclear what in LOD 0 "carries anxiety" corresponds to.

**Two-axis organization (symmetric, retraction structure):**

| | Static constraint (structure) | Dynamic constraint (process) |
|---|---|---|
| **On refine (down→up)** | Axiom 2: Non-overwrite | Axiom 4: Provenance |
| **On project (up→down)** | Axiom 1: Anchor Preservation | Axiom 3: Projection Consistency |

Two constraints each in both the up and down directions → the interpretation added on refine drops away on project, but the original LOD 0 is preserved (= a round trip with no information loss).

## B3. Formulation as a CSP (Constraint Satisfaction Problem)

```
variables = the interpretive content of each LOD / domain = all patterns the LLM can generate / constraints = the 4 axioms + user specification
```
As the LOD rises, constraints **increase** and the solution space narrows (at LOD 3 it is pinned to "this person"). At every LOD the LOD 0 constraints are preserved (= Anchor Preservation).

**SAT / UNSAT detection** (a diagnostic signal, not mere error handling):
- **SAT**: all constraints satisfied → output as a valid persona.
- **UNSAT**: contradiction → reject and regenerate. Uses:
  - **LLM hallucination detection** (plausible but contradicts LOD 0 → caught by a Projection Consistency violation).
  - **Making self-perception mismatch visible** ("thinks they are Flight but structurally they are Fight" — a design feature for counseling applications).
  - **Discovering contradictions in constraint combinations.**

The constraint (the mathematical anchor that is LOD 0) narrows the LLM's degrees of freedom and brings generation closer to **observation** ("this person will respond like this" rather than "what should you do next?").

## B4. Implementation prototype spec (`src/cmr/lod_persona.py`)

The Core engine is untouched.
```
input LODConstraints: lod0_exposure / lod1_response (Fight|Flight|None) / lod2_strategy / lod3_context
output dict: status (SAT|UNSAT) / persona{summary, narrative, provenance} / attempts
```
**Validation flow:** (1) build a prompt that states the 4 axioms explicitly → (2) call the LLM → (3) project the generated persona via `project(LOD0)` → (4) compare with the original lod0_exposure (match = SAT / mismatch = UNSAT, retry) → (5) UNSAT with a reason once max_retries is exceeded.
**MVP of Projection Consistency:** extract LOD 0 elements from the persona's `provenance` and judge whether **most of the core events (top weights, REFRAME-firing pairs, key interferences)** appear (MVP threshold 70%). Exact match is not required.
**Out of MVP scope (deliberate):** a complete CSP solver / mathematical rigor of bidirectional LOD0↔3 conversion / persona database / WebUI · API.

## Ethical boundary (Track B's first principle, invariant even in productization)

SCEM **does not assert an individual's inner life.** LOD 3 output is an estimate of "what exposure structure a person placed in a given birth year, community, and institutional environment is *likely to hold*," not a verdict about the individual. The four lines: **understanding not classification / translation not manipulation / provenance-tracing not assertion / mutual understanding not division.** It is not a tool for classifying people but a **translation map between different worlds of meaning** (consistent with Paper 2 §6.4).

---

# Common

## Implementation status at a glance

| Layer | Track | Status | Implementation |
|---|---|---|---|
| Structural layer (Core) | A | **implemented & purified** (domain-independent, D-term integrated) | `src/core/` |
| Community layer | A | prototype | `src/culture/community_experiment.py` |
| Culture layer | A | implemented | `src/culture/` |
| CMR Layer | A | implemented (grids, multiple observers) | `src/cmr/` |
| Exposure Adapters | A | implemented (GSS, ESS) | `src/adapters/{gss,ess}/` |
| LOD / persona generation | B | implemented (CSP, SAT/UNSAT) | `src/cmr/lod_persona.py` |

**FIX stamp (born 1981):** fingerprint PASSIVE 0.81 / ACTIVE 0.56 / REFRAME 0.55. Top interference = Windows 95 launch × spread of Purikura (score 1.60). Overlap judgment domain-independent = True, interference D-term integrated = True.

## Validation artifacts (reproducibility)

- `src/core/test_domainless.py` — empirical test of domain redundancy (fingerprint & batch invariant, interference matches 9/10 → justifies abolishing domain)
- `src/culture/community_experiment.py` — empirical test of the closure=discrete / speed=continuous asymmetry
- `src/core/test_lag.py` — sampling of the information-embodiment lag (grounds for placing individual lag out of scope)
- `src/core/make_figures.py` / `src/cmr/make_paper2_figures.py` — figures
- `SI/reproduce_all.sh` / `SI/results_tables.md` — full reproduction and results compendium of the GSS/ESS external cross-check

## Design rationale (why it is designed this way; philosophy kept minimal)

- **Do not let domain enter the computation:** collapsing an event into a single category would be exactly the defect the central claim rejects ("refuse the discrete bucket of birth year"), now **self-applied to the event side**. Overlap is judged by the cos of the action vector alone, and domain is demoted to a display tag (invariance measured in `test_domainless.py`).
- **Separate mathematics from interpretation:** mixing them produces category violations (applying N and significance tests to interpretation / mixing interpretation into mathematics). The two are irreplaceable.
- **Impose the 4 axioms:** an LLM output without LOD 0 breaks Projection Consistency and becomes "skillful but empty." Binding to the mathematical anchor brings generation closer to observation and structurally rejects fabrication.
- **LOD (isomorphic to 3D graphics):** resolution beyond the use case is redundant. Sociology is LOD 0, marketing LOD 1–2, the individual LOD 3.
- (The broader theory of existence design and the cross-domain isomorphism are kept as philosophy unnecessary to the implementation, and are not part of the public repository.)

## Appendix: glossary crosswalk

| Term | Equivalent expressions |
|---|---|
| LOD 0 | exposure profile / 3-axis fingerprint / exposure structure / mathematical anchor |
| LOD 1–3 | refined interpretation layers / persona expression |
| refine / project | interpretive branching (adding constraints) / interpretive projection (summarizing) |
| 4 axioms | SCEM Axioms / Honest Structuralism |
| CMR | Contextual Mode Resolver (`Event × Premise → ResolvedImpact`) |
| premise | community premise (religion × race × region × education / class × EU distance × religiosity, etc.) |
| SAT / UNSAT | constraints satisfied / unsatisfied |
