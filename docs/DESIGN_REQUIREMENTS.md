# Clinical Review Questions and Design Requirements

The system must derive a persistent, auditable account of delivered care from
clinical and administrative records. Questions should reuse that account, and
numerical answers should be calculated in code. The central design challenge is
preserving the difference between a documented claim, a reconciled fact, and a
conclusion that the evidence does not settle.

All authored project artifacts must be in English, as specified in
[AGENTS.md](../AGENTS.md).

The proposed modules, data flows, and scaling path are described in
[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md).

## Scope and requirement sources

[Problem Statement.docx](../Problem%20Statement.docx) defines the submission and
evaluation requirements. [questions.json](../questions.json) supplies five
development questions about Rowan. The statement also describes collection-wide
analysis, consecutive weeks below plan requirements, and comparisons across plan
changes. These are stated capabilities and likely follow-up topics, although
they are not separate questions in the current development file.

The following question mapping distinguishes supplied questions, stated broader
capabilities, and anticipated engineering questions. The detailed design
requirements are derived from these behaviors; the proposed data model is an
implementation option rather than a mandated architecture.

## Questions and the behavior needed to answer them

| Basis | Example question | Design requirement |
| --- | --- | --- |
| DEV-01 | How many sessions did the patient attend, by service type and in total, and on how many distinct days? | Identify patients and encounters; reconcile multiple descriptions of one encounter; determine actual attendance and therapy eligibility; count encounters and distinct service dates separately. |
| DEV-02 | How many therapy minutes and hours were delivered overall and in each Monday-Sunday week? | Represent patient contact and therapy intervals; exclude breaks and non-contact gaps; aggregate eligible time in code; propagate unresolved duration evidence. |
| DEV-03 | Did each week's care meet the treatment plan? | Retrieve the applicable plan and its definitions; evaluate both day and minute requirements; return met, not met, or cannot be determined with supporting calculations. |
| DEV-04 | What happened on January 19 and January 21, and how do later records change the interpretation? | Join attendance, clinical content, corrections, and connection records; distinguish service time from document receipt time; explain encounter counts and patient-contact minutes separately. |
| DEV-05 | How did symptoms and functioning change, and why was an additional contact provided? | Identify distinct assessments; preserve observation dates and attribution; connect symptoms, functioning, and documented reasons for care without inventing causal conclusions. |
| Stated broader capability | Which patients had two consecutive weeks below their requirements, and whose inclusion remains uncertain? | Evaluate adjacent calendar weeks per patient and applicable plan; distinguish established cohort members from possible members; retain drill-down evidence and uncertainty dependencies. |
| Stated broader capability | What changed before and after a treatment-plan change? | Version plans by effective period; compare service mix and delivered time in explicit windows; explain partial weeks and unequal exposure periods. |
| Required reuse behavior | Can a new question be answered after restarting? | Persist the abstraction and its provenance; query saved facts without re-extracting the collection; load relevant source passages only when needed. |
| Daily arrivals and anticipated follow-up | What changes when a new note or correction arrives? | Link new claims to affected patients, encounters, assessments, and plans; reconcile those dependencies and invalidate affected derived results. |
| Required duplicate behavior | What happens if a document or an old roster is supplied again? | Duplicate inputs and repeated copies of the same evidence must not alter clinical results; keep relevant source relationships inspectable. |
| Required audit behavior | Which source passages and inclusion decisions support this total? | Show contributing records, exclusions, reconciliation decisions, arithmetic, and precise source references in reviewable calculation detail. |
| Anticipated evidence question | Does an absent record prove that treatment did not happen? | Distinguish documented absence from missing evidence; represent coverage limitations instead of assigning zero by default. |
| Required performance discussion | What becomes expensive at 500,000 documents, and what fails first at one million? | Measure ingestion, patient and collection queries, model usage, cost, and storage; identify code responsible for expected bottlenecks and distinguish measurements from estimates. |

## Cross-document evidence reconciliation

### Keep claims separate from resolved values

Each source assertion should retain its value, the entity and field it describes,
its source passage, and relevant dates. Resolving a field should produce a
separate decision with a reason and supporting or conflicting claim references.
Replacing a value must not erase the evidence that previously supported it.

Resolution applies at field level. A correction to patient departure time does
not automatically change the group's scheduled closing time, service type,
breaks, or encounter identity. Likewise, uncertainty about duration does not
automatically make the session count uncertain.

### Match entities before aggregating

The proposed abstraction distinguishes patient, episode, appointment, encounter,
document, connection segment, and symptom assessment identities. These
distinctions do not require separate database tables. Prefer explicit identifiers
when present. Matching without identifiers needs an explainable basis; unresolved
matches must not silently merge records or invent additional encounters.

There are two distinct duplicate problems. Identical files are duplicate inputs.
Different documents can describe the same clinical event or reproduce an old
claim. Content hashing addresses the first problem; encounter and assessment
reconciliation address the second.

### Use the source's scope and meaning

Evidence should be evaluated for the particular field being resolved. Attendance
records establish patient presence; clinical content can establish service
activities and breaks; a treatment plan defines eligibility and goals. A charge,
authorization, or appointment alone does not establish delivered therapy.

Do not implement a universal rule that the newest document, a signed note, or one
document type always wins. An explicit correction may supersede its named field;
two final clinical records can still disagree without a documented resolution.

### Preserve several kinds of time

Keep service dates and contact intervals separate from signature, correction,
receipt, import, and assessment-completion timestamps. Plan effective periods
must be represented explicitly. Clinical chronology follows the event being
described, rather than the order in which files reached the system.

## Deterministic calculations and plan evaluation

Therapy eligibility must follow the applicable documented definition. Rowan's
supplied plan requires patient-present individual, group, or family psychotherapy
and excludes medication management, collateral-only contacts, and care
coordination. This is a patient plan rule, not a universal medical definition.

Delivered minutes come from actual therapeutic patient contact. For group
services, intersect patient attendance with therapeutic activity intervals. For
interrupted telehealth, combine supported contact segments without counting the
gap or treating a reconnection as a second encounter. Intervals describing the
same contact must not be summed twice. Apparent overlap between different
encounters needs reconciliation rather than an automatic subtraction rule.

Count eligible encounters, distinct eligible service dates, and minutes as
different measures. Use Monday-Sunday week boundaries for the development
questions and keep calculations in integer minutes before converting to hours.
Expose the inclusion decision and contribution of each encounter.

Evaluate plans by their effective periods and documented definitions. A plan
change during a week, a partial review week, or an unequal before-and-after
window requires an explicit treatment of the boundary. Do not silently prorate
goals or assume a midweek transition policy that the record does not provide.

## Established conclusions and uncertainty

### Represent uncertainty at the affected field

An unresolved field should retain the competing supported claims, the type of
problem, and what evidence would resolve it. Missing information, conflicting
claims, ambiguous entity matches, and an unspecified calculation policy are
different problems. Model confidence alone does not resolve any of them.

For encounter HG-E115, BH-D110 supports 50 minutes and BH-D111 supports 40 minutes.
Both describe the full patient contact of the same encounter and both are final.
The record therefore supports one encounter with disputed duration. Preserve
the two alternatives rather than summing them, averaging them, or selecting the
later signature without a reason.

### Propagate uncertainty through calculations

Totals should expose established contributions and the alternatives that affect
them. Bounds are appropriate only when the evidence supports them. A missing
duration is not automatically zero and may not have a justified finite upper
bound. A 40-or-50-minute dispute identifies two supported alternatives; an
interval presentation should not imply evidence for every intermediate value.

Keep scenario dependencies when uncertain inputs are related. Independently
combining per-field minima and maxima can create a total that no consistent
interpretation of the records supports. Missing documents also limit what a
total over the available records establishes about all care received.

### Separate uncertain inputs from uncertain decisions

For a weekly goal, consider the feasible interpretations supported by the record
and the applicable rules:

- **Met:** every feasible interpretation satisfies all required thresholds.
- **Not met:** every feasible interpretation fails at least one required threshold.
- **Cannot be determined:** interpretations produce different decisions, or the
  evidence or policy does not support a definitive decision.

A disputed duration need not make the weekly decision uncertain if every
supported alternative leads to the same result. Conversely, an unsupported
assumption must not turn a threshold-crossing dispute into a definitive answer.
Incomplete coverage should remain explicit; established lower bounds can still
prove that a minimum goal was met.

For the two-consecutive-week query, preserve consistent interpretations across
both weeks and report established members separately from patients whose
inclusion is possible but unresolved. Consecutive means adjacent calendar weeks,
not simply neighboring rows in a result table.

## Symptom course and assessment identity

Represent a symptom assessment separately from documents that review, import,
or quote it. Keep instrument, score, source form identity, completion date, and
review or import dates distinct. Repeated mentions of the same questionnaire
must not create additional measurement events.

An account of progress should connect distinct measurements with attributed
patient reports, clinician observations, and functioning. Improvement in one
score does not by itself establish recovery, resolution of functional problems,
or a causal effect of treatment. Reasons for an additional contact should be
supported by the relevant clinical narrative.

## Concrete evidence cases for implementation review

| Records | Evidence relationship | Required behavior |
| --- | --- | --- |
| BH-D004 and BH-D005 | The clinical note records a group break; the roster records the patient's later arrival and earlier departure. | Combine activity and attendance evidence to determine eligible contact time. |
| BH-D102, BH-D103, and BH-D104 | BH-D103 corrects the January 19 departure field; BH-D104 later retransmits the original roster. | Retain the explicit correction and identify the later copy without reversing the correction or adding a visit. |
| BH-D110 and BH-D111 | Two final records describe encounter HG-E115 but disagree on full contact duration. | Count the encounter once and retain the unresolved 40-versus-50-minute alternatives. |
| BH-D106 | Two video calls continue one appointment with an explicit interval of no therapeutic contact. | Represent one encounter, two contact segments, and an excluded gap. |
| BH-D013 and BH-D014 | A January 26 import repeats the January 16 PHQ-9 submission HG-Q116. | Preserve one assessment at its completion date and retain both document references. |
| BH-D108 and BH-D112 | A final attendance record documents a no-show; a draft template and charge entry can suggest scheduled service. | Determine delivery from patient contact evidence and explain why administrative artifacts do not establish attendance. |
| BH-D003 | The signed plan defines therapy days, eligible services, and weekly thresholds. | Treat the plan as a source-backed rule applicable to its patient and effective period. |

These cases are small, meaningful checks of reconciliation and calculation
behavior. They should complement end-to-end review of the five development
answers. Additional useful checks include duplicate-input invariance, consistent
answers after restart, and targeted updates when a new correction is ingested.

## Proposed abstraction structure

A compact implementation can separate the following concepts without committing
to a specific database:

| Concept | Information to retain |
| --- | --- |
| Documents | Content identity, document ID, filename, raw content, ingestion history, extraction configuration and version. |
| Patients and episodes | Stable patient identity, record identifiers, episode boundaries, and identity evidence. |
| Source claims | Entity, field, asserted value, event date, source passage locator and text, and document relationships. |
| Encounters | Patient, episode, encounter and appointment identifiers, service date, service type, attendance, patient presence, contact segments, and exclusions. |
| Reconciliation decisions | Resolved field or unresolved alternatives, supporting and conflicting claim IDs, decision reason, and rule version. |
| Treatment plans | Effective periods, eligible service definitions, day and minute thresholds, and supporting source claims. |
| Assessments and observations | Measurement identity, instrument and value, completion date, attribution, clinical observations, and evidence references. |
| Derived results | Contributions, formulas, applicable rules, uncertainty dependencies, and abstraction version. |

A source locator should include the document identity and a stable passage
location, such as line ranges or character offsets in the retained text, with the
relevant excerpt. A filename alone is insufficient for a reviewable calculation.

## Reuse and performance requirements

Extraction can use a model, but arithmetic and aggregation must execute in code.
Persist extracted claims, reconciled entities, applicable rules, and provenance
so a question does not require rereading and re-extracting all documents. Cache
validity must account for source content and changes to extraction configuration
or schema.

Incremental processing should reuse unchanged work while updating affected
entities and derived results. A new question should query the saved abstraction;
targeted source inspection or narrowly scoped enrichment can address missing
information without rebuilding the collection.

Benchmark initial processing, individual-patient and collection-wide queries,
model usage and available cost, and abstraction size. Separate cold processing
from repeated queries and duplicate or incremental ingestion where useful.
Explain the expected first bottleneck at one million documents with reference
to the implementation code. Keep measured values separate from extrapolations.

## Likely system design discussion questions

- Why does this abstraction support related questions without starting over?
- Which facts come from a model, and which results are determined by code?
- Why did one correction resolve a field while two signed notes remained disputed?
- How can a reviewer trace a collection-level finding to source passages?
- How does a new document change existing answers, and how are stale results avoided?
- What happens when encounter identifiers are missing or patient identities are ambiguous?
- Which design decision was tested, what did the result show, and what limitation
  was actually observed?
- Which operations dominate processing cost and query latency at larger scales?

## Prototype boundaries

The submission needs runnable code and setup instructions, the saved clinical
abstraction, five development answers with evidence, execution logs, benchmarks,
and a short README. The README must disclose models and settings, coding
assistance, a tested design decision, an observed limitation and investigation
plan, and the expected first bottleneck at one million documents.

The scope is a two-to-five-hour prototype. A CLI or notebook is sufficient; a UI
and a universal clinical review system are not required. Related unseen questions
and additional records must work without hard-coding patient facts or answers.
