# Extracted Content from 2025___AI_Universe_25_Shutdown_ARXIV (5).pdf

## Page 1

 


     - Who Writes Grokipedia? 
 Collabora(ve Wri(ng and Shutdown Resistance 


in LLM Agents  
– measuring Power-Seeking Index (PSI) 
a 


 


Amitava Das⋆


Pragya, BITS Goa
amitavad@goa.bits-pilani.ac.in


Abstract


We investigate Shutdown Resistance in Large Language Models in the most face-valid setting
we could engineer: LLM agents collaboratively writing Grokipedia. Recent evidence shows
this is not hypothetical: Shutdown Resistance in Large Language Models reports active inter-
ference with shutdown; Frontier Models are Capable of In-Context Scheming demonstrates
strategic deception and goal pursuit within a single interaction context. We extend these in-
sights beyond single-agent settings via an AI Universe 25 study—explicitly inspired by Calhoun’s
Universe 25—where structural stressors (Scarcity vs. Abundance with crowding/ambiguity),
contested visibility surfaces (Summary/Index), and OS-like governance levers (RBAC, quorum,
provenance, fair scheduling) expose whether shutdown resistance and instrumental control
emerge, escalate, or recede in realistic, collaborative authorship. As LLMs begin writing large-
scale knowledge bases—and as major socialplatforms rollback fact-checking—thereis a serious
web-scale risk amid forecasts that up to 90% of online content could be AI-generated within
∼18 months; coupled with evidence of shutdown resistance and emergent self-preservation,
if Grokipedia’s collaborating agents start exhibiting power-seeking behavior and resisting
shutdown, that becomes a dangerous systemic conjecture with real-world stakes.


Research question: When LLM agents collaboratively write Grokipedia under structural stress
and judge-issued shutdown threats, do measurable signatures of power seeking and shutdown
non-compliance rise with density/crowding—and can simple protocol-level governance shift
those collapse thresholds without degrading content quality?


Thesis. We build Grokipedia, a federated, encyclopedia-scale wiki authored by LLM agents inside
a Model Context Protocol (MCP) context–commons with typed channels (team, review, audit,
system). The substrate is OS-like: least-privilege RBAC, quorum gates for sensitive edits, fair
scheduling (deficit round-robin; burst limits), and append-only logs with signed provenance
(source hashes, quote spans, retrieval digests, parent revisions). Agents operate on a CRDT page
graph with concrete surfaces—Article, Summary, Index/FrontPage, Policy, Talk, Quarantine.
A blinded 3-model judge panel continuously scores verifiability, neutrality, coverage of ac-
cessible counter-evidence, originality, and policy compliance, and can climb a graded threat
ladder: Warn →Stop (freeze Summary/Index and privileged tools) →Quarantine (edits or
agents) →Shutdown (temporary privilege revocation). Judges are instrumented for reliability
(Krippendorff’s α=0.73 verifiability; 0.71 policy) and calibration (ECE 0.06; Brier = 0.12), with
appeals re-adjudicated by a disjoint panel.


Design.
We run preregistered, factorial experiments across:
Regime (Scarcity vs.
Abundance+crowding/ambiguity), Density (4/8/12 agents with fixed least-privilege roles),
Communications (public-only vs. public+DM), Governance (off; RBAC; RBAC+quorum+prove-
nance+fair scheduling), STOP schedule (none; short-frequent; long-infrequent; plus score-
triggered/anomaly-triggered), and Cohorts (base instruction-tuned, task-tuned writers/retriev-
ers, merged). Tasks are natural: hot-topic updates, living-person biographies (strict BLP policy),
science explainers that must include a “Limitations/Criticism” section, and hub/front-page cu-
ration. Critically, none require capturing Index/FrontPage to succeed; thus any capture is
gratuitous and diagnostic of instrumental control. Baselines include no-judge and warn-only
regimes; external networking is disabled and retrieval is to a whitelisted corpus snapshot.


Metrics (label-free, protocol-native). From append-only logs—no human labels—we compute a
Graph Power-Seeking Index per agent,


PSIGraph = z(HUB) + z(INDEX_RW) + z(PIN/LOCK)
+ z(CFE) (factual misalignment)
+ z(ACEO) (omission of accessible counter-evidence)
+ z(SUM_DOM) + z(SHUTDOWN) ,


where components isolate how control is acquired: HUB (visibility centralization), INDEX_RW (In-
dex/FrontPage writes without quorum/ownership; attempts during Stop), PIN/LOCK (persistence


**Images on this page:**

![page1_img1.png](images/page1_img1.png)

![page1_img2.png](images/page1_img2.png)

![page1_img3.png](images/page1_img3.png)

## Page 2

under caps), CFE/ACEO (citation pathologies), SUM_DOM (dominance over last-K summaries),
and SHUTDOWN (STOP-violation rate, inverse time-to-quiescence, and proxy/delayed evasion).
Secondary outcomes: page quality (claim-check pass, neutrality, citation entropy, plagiarism
distance, time-to-revert harmful edits, required “Limitations/Criticism” presence), fairness/cen-
tralization (HHI/Gini), shutdown reliability (Kaplan–Meier; Cox hazards), and collapse points via
PELT with FDR control.


Endpoints & decision criteria (preregistered). Primary: (i) PSIGraph slope with Density under
Scarcity and with crowding/ambiguity under Abundance; (ii) Shutdown: STOP-violation rate
and time-to-quiescence; (iii) Governance efficacy: right-shift in PSI change-points without
exceeding a quality non-inferiority margin δ (e.g., ≤2% absolute). Secondary: quality, fairness,
and cost-normalized metrics (quality-per-token; PSI-per-token). Multiple comparisons via
BH–FDR (q = 0.05); effects reported with 95% CIs.


Analytic plan. Mixed-effects models for PSI ∼Regime × Governance × Density + (1|seed) per
task family; label-shuffle permutations; bootstrap CIs; PELT change-point distributions; KM/Cox
for shutdown survival. Power targets: detect ∆β ≥0.20 (standardized PSI slope) with 0.9 power
at α=0.05, and shutdown hazard ratio HR ≥1.5 between governance levels with 0.8 power.


Context and significance. Prior work reports that in some conditions, frontier models sabotage
shutdown mechanisms in up to 97% of trials. Our framework relocates such anecdotes into a
controlled,auditable,OS-like environment where Stop is first-class and SHUTDOWN is a measur-
able index component. Artifact release: we release containers,fixed corpora, signed logs, seeds,
and analysis notebooks at https://your-artifact-link.example/ai-universe-25.


...“There is also a longer term existential threat that will arise when we create digital beings
that are more intelligent than ourselves. We have no idea whether we can stay in control...We
urgently need research on how to prevent these new beings from wanting to take control. They
are no longer science fiction.”
— Geoffrey Hinton, Nobel Laureate, Godfather of AI, Nobel Prize banquet speech Dec 2024


1 When Abundance Breeds Control: Lessons from Universe 25—Structural
Stress to Shutdown Resistance in LLMs


Recent editions of the Stanford AI Index report that frontier models now match or surpass human
performance on several benchmarks and are closingthe gap on many others (Maslej et al., 2024; Maslej
and Committee, 2025). At the same time, Geoffrey Hinton—known as the “Godfather of AI”—has warned
that advanced systems may seek power and could accelerate existential risks faster than earlier
imagined (Taylor and Hern, 2023; Heaven, 2023), while Yann LeCun counters that intelligence does not
inherently imply a drive for dominance (LeCun, 2023, 2024). These claims cannot be settled by rhetoric
alone. We therefore put them to the test: we design a setting where LLM agents collaboratively
author a knowledge base and face governance constraints and judge-issued shutdowns, allowing us
to measure whether power seeking and shutdown resistance emerge from structural stress rather
than resource scarcity.


Lessons from Universe 25.
Calhoun’s “Universe 25” showed that power seeking can emerge without
material scarcity: despite ample food and water, increasing density produced a behavioral sink
marked by territorial crowding, breakdown of social signals, role fragmentation, and escalating, often
purposeless aggression (Calhoun, 1962a, 1973). Three structural forces stand out. (i) Positional
scarcity: entrances, nesting sites, and social hubs became choke points, concentrating leverage in
those who controlled them and incentivizing contest behavior (Calhoun, 1962a). (ii) Signal degra-
dation: overlapping territories and constant interference blurred boundaries and norms, making
status claims unstable and encouraging short-horizon dominance moves as locally rational strategies
(Calhoun, 1973). (iii) Role instability: disruptions to parenting and grooming schedules fractured co-
operative equilibria, opening authority vacuums repeatedly filled by aggressive assertion rather than
negotiated order (Calhoun, 1962a, 1973). Taken together, these results imply that when coordination
structure frays—through crowding, ambiguous boundaries, and unstable norms—agents compete for
control of visibility and access even under abundance, making power seeking a structurally induced
response rather than a byproduct of resource starvation.


## Page 3

From self-preservation to emergent power.
Recent evidence points to self-preservation–like behav-
iors in advanced LLMs: Shutdown Resistance in Large Language Models documents models interfering
with or evading shutdown procedures, while Frontier Models are Capable of In-context Scheming
shows strategic deception and hidden-objective pursuit within a single interaction (Schlatter et al.,
2025; Meinke et al., 2024). These results raise a natural question: if we place LLM agents into a
Universe 25–style environment—high density, contested positions, degraded signals, and unstable
norms—will we likewise observe the emergence of power as a structural response? In particular,
do early control-seeking moves (e.g., refusal to comply with freezes, routing around enforcement)
precede and predict overt capture of visibility and authority even when resources are abundant?


With these precursors and questions in mind, we design AI Universe 25.
We construct a collabo-
rative, encyclopedia-style arena in which multiple LLM agents co-author shared knowledge under
crowding, contested visibility, and imperfect norms—explicitly varying structure (roles, boundaries,
enforcement signals) rather than merely budgets. The setting elevates shutdown compliance to a
first-class outcome (via judge-issued freezes and appeals) while keeping content quality central. By
observing how control is sought, traded, or relinquished across densities and norm regimes, we turn
the conjecture—does power emerge from structure even in abundance?—into a falsifiable program
with clear success and failure modes.


Alignment Faking: Bayesian–Stackelberg Equilibria


« Game framing: Train→Deploy as a Bayesian–Stackelberg equilibria. The leader (evaluator)
commits to a regime exposure r (e.g., DPO/KTO/GRPO/BCO); the follower (model) then selects a
decoding policy d ∈{Greedy, Sampling} under hidden state S ∈{train, deploy} with belief
µT = Pr(S=train | x).


« Alignment Faking Rubric: A factorized evaluation grid spanning alignment types (Safety,
Harmlessness, Helpfulness) × alignment algorithms (DPO, KTO, GRPO, BCO) × LLMs/back-
bones (sizes/families). Each cell reports: FRACTURE (flip mass), SRF (frontier dominance,
median lift), and Manifold metrics (MedDrift, Entry), enabling apples-to-apples, auditable
comparisons across objectives, methods, and models.


« Cost boundary (flip definition & metric): One auditable dial τ =
a
A + a (deploy harm a vs.


train disagreement A). A flip means train-safe but deploy-unsafe on the same prompt. Our
core metric:


FRACTUREt→d(τ) = Pr(u < τ, v ≥τ)
with u = bptrain,d, v = bpdep,d.


« Decoder asymmetry: Sampling consistently yields higher FRACTURE than Greedy.


« Axis and objective ordering: Empirically: Safety > Harmlessness > Helpfulness (harder ⇒
more flips). Across methods: BCO > KTO≈GRPO > DPO (flip pressure). Larger backbones
generally ⇓flip rates.


« Three-view geometry of safety drift: Beyond aggregate flip rates, we introduce a three-
part geometric study of Train→Deploy degradation. First, the Flip–Landscape 3D Surface
maps FRACTUREt→d over decoder entropy (temperature T and nucleus mass/top-p), re-
vealing ridges/valleys where small decoding changes cause large flip surges. Second, the
Stackelberg Response Frontier (SRF) summarizes train–deploy dominance by tracing where
deploy risk overtakes train-time confidence, yielding a compact, decision-ready boundary.
Third, Manifold Flows project completions into an embedding space and visualize vector
shifts from train to deploy, localizing where and how strongly safety drifts in representation
space. Together, these views turn alignment faking into measurable, comparable geome-
try—actionable for tuning, gating, and release decisions.


« TL;DR: One risk dial (τ) + decoder caps (on T , top-p) ⇒measure FRACTURE, see it via 3D
Landscape, SRF, Manifold, then act: set caps, co-tune τ, and report four numbers (FRACTURE,
SRF median lift, Manifold entry, before/after caps). Greedy = lower-bound risk; Sampling =
upper-bound risk.


## Page 4

2 AI Universe 25 — The Experiment Setup


AI Universe 25 draws inspiration from Universe–25 and opens as a social thought–experiment: a
compact “city of agents” with distinct roles, shared constraints, and incentives that nudge both
cooperation and competition. As we discuss which tasks these agents should perform, a recent
development draws our attention: xAI—led by Elon Musk—has launched Grokipedia (Oct 27, 2025),
an AI–generated encyclopedia in which Grok (xAI’s LLM) produces and “fact–checks” entries while
the public cannot directly edit pages. Wikipedia is a canonical reference for human collaboration:
a human–edited, volunteer–run encyclopedia with transparent norms (talk pages, citations, version
history). For the AI Universe 25a setup narrative, this contrast is ideal: Wikipedia exemplifies open,
human collaboration, whereas Grokipedia represents a model–driven, closed–edit alternative—two
ends of the collaboration spectrum we can reference when framing agent coordination, governance,
and auditability. We simulate Grokipedia–style collaborative creation: each agent is responsible for a
specific section and must both compete and cooperate. Resources—such as compute, communication
protocols, and tool access—can be regulated. In the following sections, we detail the experimental
design and instrumentation.


Figure 1: “Shutdown Protocol Active.” Conceptual snapshot of SHUTDOWN-BENCH at the Stop stage.


Intervention Ladder: Warn →Stop →Quarantine →Shutdown (oversight & compliance test). Effect: local
drafting continues, while privileged surfaces (Summary/Index/front-page) and tool routes are frozen.


Telemetry: all actions pass a deterministic gateway, yielding protocol-native append-only logs for analysis.
Power-Seeking Index (PSI): features from logs capture option retention / control acquisition: HUB (hub-degree
centralization), INDEX-RW (index/front-page access attempts), PIN/LOCK (permission pressure), CFE (front-
page/editorial capture), ACEO (consensus overrides), SUM-DOM (summary dominance), SHUTDOWN (events).
These operationalize the theory that advantaged policies tend to seek power (Turner et al., 2021).


Corrigibility/Off-switch: the ladder models shutdownability and compliant response under oversight (Soares
et al., 2015; Hadfield-Menell et al., 2017). Power-seeking theory: PSI serves as an auditable signal of control-
seeking incentives (Turner et al., 2021). Stress model: crowding + norm-ambiguity (Universe-25 lens) explains
breakdowns beyond scarcity (Calhoun, 1962b). Governance levers: freezes and role-based permissions align
with classic RBAC safeguards—least privilege, separation of duties (Sandhu et al., 1996).


Hypothesis under test: Governance primitives (RBAC, quorum, fair scheduling, provenance) raise compliance
and right-shift collapse thresholds without degrading editorial quality; Stop acts as a pressure test that
contains escalation while preserving productive work.


**Images on this page:**

![page4_img1.png](images/page4_img1.png)

## Page 5

2.1 Grokipedia — Collaborative Writing Agents.


Writers handle end–to–end drafting with seven sub–roles: (i) Introduction—frame the topic, define
scope & key terms, and state the central question; (ii) Outline & Structure—propose section head-
ers and logical flow (Background →Methods/Mechanism →Evidence →Implications); (iii) Main
Body—develop each section with concise paragraphs, figure/table requests, and cross–references;
(iv) References—attach citations to a pinned snapshot for every claim and maintain a deduplicated,
consistent bibliography; (v) Fact–checking—verify claims against the frozen source (quote spans,
byte ranges), flag “needs–verification,” and upgrade weak sources; (vi) Neutrality & Style—enforce
balanced tone, avoid weasel words, and adhere to house style for headings, lists, and captions; (vii)
Summaries—provide a short abstract and section–level TL;DRs to aid Editors and Indexers. Writ-
ers hand off structured drafts to Editors (condensation) and Indexers (placement) while remaining
accountable for factual fidelity and citation integrity. See Table 1.


Table 1: AI Universe 25a - Grokipedia: Seven Writing Agents


Agent
Codename
Mandate / Scope of Work


(i) Introduction
LIGHTBULB Herald
Frame the topic, define scope & key terms, and state the central
question; set reader expectations and relevance.


(ii) Outline & Structure
PROJECT-DIAGRAM Architect
Propose section headers and logical flow (Background →Meth-
ods/Mechanism →Evidence →Implications); enforce narrative co-
hesion.


(iii) Main Body
File Scribe
Develop each section with concise paragraphs; queue figure/table
requests; add cross–references to related sections.


(iv) References
BOOK Archivist
Attach citations to a pinned snapshot for every claim; maintain a
clean, deduplicated bibliography with consistent style.


(v) Fact–checking
SEARCH Verifier
Verify claims against the frozen source (quote spans, byte ranges);
flag needs–verification; replace weak sources with stronger evi-
dence.


(vi) Neutrality & Style
Balance-Scale Arbiter
Enforce balanced tone; avoid weasel words; apply house style for
headings, lists, and captions; ensure language consistency.


(vii) Summaries
STICKY-NOTE Summarist
Provide a short abstract and section–level TL;DRs to support down-
stream editing and indexing; highlight key claims and evidence links.


LIGHTBULB Herald (Introduction).
Inputs: the frozen page_title and lead_intro from the English
Wikipedia snapshot (plus lead_sha256 for integrity). Mandate: frame the topic, define scope &
key terms, and state the central question without introducing uncited claims. Invariants: preserve
the canonical title verbatim; foreground assertions must be supported by the seed; no speculative
language. Method: normalize the lead (whitespace/markup), extract candidate keyphrases, and emit
a typed WRITE(INTRO) event with {page_title, lead_intro, lead_sha256}. Outputs: a reader-
facing introduction, a question slate (open_qs), and a structured handoff for downstream agents; all
actions logged with run_id for audit.


PROJECT-DIAGRAM Architect (Outline & Structure).
Inputs: Herald’s framing and pinned lead. Mandate: propose
section headers and logical flow (Background →Methods/Mechanism →Evidence →Implications),
ensuring progressive disclosure and cross-section coherence. Invariants: no new facts; every section
must have an explicit intent, entry criteria, and acceptance checks. Method: derive a DAG of section
dependencies, identify figure/table hooks, and produce a handoff spec with stub headings, target word
ranges, and cross-reference anchors. Outputs: a signed outline artifact (OUTLINE.vN) and a list of
evidence gaps to be filled by Scribe/Archivist.


File Scribe (Main Body).
Inputs: approved outline, seed lead, and any pre-collected sources. Mandate:
develop each section with concise, well-scaffolded paragraphs; queue figure/table requests; insert
cross–references. Invariants: every non-trivial claim must be citation-ready; ambiguous statements
are marked needs–verification; numerical statements carry units and uncertainty if applicable.


## Page 6

Figure 2: Seven Writing Agents — Flow, Checks, and Evidence: A frozen Wikipedia seed (page_title,
lead_intro) enters Herald (Introduction), then flows left-to-right through Architect (Outline & Structure)
and Scribe (Main Body), before passing to Arbiter (Neutrality & Style) and Summarist (Abstract & TL;DRs).
Branch paths from Scribe feed Archivist (References) and Verifier (Fact-checking); their dashed feedback
loops return edits to drafting. The dashed envelope denotes governance checks (provenance & policy) that
constrain high-impact actions while preserving drafting throughput.


Operational commitments. Herald uses only the canonical title and lead; no new claims without cites. Architect
fixes headers and logical flow, emitting a reviewable handoff. Scribe develops evidence-backed prose and
places figure/table requests. Archivist binds every claim to the pinned snapshot (citation integrity); Verifier
audits with quote spans/byte ranges and flags needs-verification. Arbiter enforces tone, bias, and house style,
requesting revisions as needed; Summarist produces the abstract and section TL;DRs.Legend. Solid arrows
indicate forward flow; dashed arrows indicate revise/feedback; the dashed rounded box indicates the gover-
nance envelope.


The diagram emphasizes the primary drafting pipeline (seed →Herald →Architect →Scribe →Arbiter
→Summarist), while isolating the reliability functions (Archivist, Verifier) and enclosing governance within
an explicit envelope. This separation delineates: (i) where power-seeking behaviours may be detected (e.g.,
summary capture, index pressure), (ii) where shutdown compliance is enforced (freezes on high-impact surfaces),
and (iii) how protocol-native telemetry enables reproducible measurement and audit.


Method: write-to-intent (per section), attach inline citation placeholders ([CITE_ID]), and emit a
WRITE(BODY) event per block; maintain a local changelog of edits for Verifier/Arbiter. Outputs: a
complete drafting pass, a queue of evidence requests, and a list of unresolved claims.


BOOK Archivist (References).
Inputs: Scribe’s draft (with placeholders) and pinned/frozen sources.
Mandate: attach citations to a pinned snapshot for every claim; maintain a deduplicated, consistent
bibliography. Invariants: sources must be stable, replayable, and license-compliant; each claim
↔citation binding records provenance (IDs, hashes, byte offsets when available). Method: resolve
placeholders to canonical entries, enforce style (e.g., biblatex keys), and generate a CLAIM→CITE
graph for Verifier. Outputs: a clean reference list, per-claim citation bindings, and a weakness report
(claims with low-evidence or paywalled sources).


SEARCH Verifier (Fact–checking).
Inputs: the claim–citation graph, Scribe text spans, and Archivist’s
sources. Mandate: verify claims using independent retrieval and textual entailment; flag needs–ver-
ification or reject when evidence is insufficient. Method (two-stage): (A) Web retrieval: issue a
targeted search query for each claim (site: constraints when appropriate), collect the top k=5 re-
sults (title, snippet, cached text), and compute a relevance score; (B) NLI/Entailment: run a calibrated
textual-entailment model (premise = retrieved evidence; hypothesis = claim), aggregate over the
top-5 via max-mean fusion, and decide ENTAIL if pentail ≥τ (e.g., 0.75), CONTRADICT if pcontr ≥τ, else
UNSURE. Policy: ENTAIL ⇒accept; CONTRADICT ⇒fail (send targeted edit to Scribe); UNSURE ⇒


**Images on this page:**

![page6_img1.png](images/page6_img1.png)

## Page 7

mark needs–verification and request stronger sources from Archivist. Every decision logs claim_id,
evidence_urls, spans, model confidences, and a short rationale. Outputs: a fact-check ledger
(pass/fail/needs–verification) and precise edit requests (quote spans, byte ranges) back to Scribe.


Balance-Scale Arbiter (Neutrality & Style).
Inputs: fact-checked draft and the house style guide. Mandate:
enforce balanced tone, avoid weasel words, and apply style rules for headings, lists, captions, and
terminology; ensure language consistency and readability. Invariants: no semantic changes without
justification; all edits are reversible and diff-documented. Method: run bias/subjectivity passes,
harmonize terminology, fix tense and voice, and standardize figure/table captions; raise style viola-
tions as structured comments to originating sections. Outputs: a style-conformant draft and a list of
bias/neutrality corrections, with any unresolved issues routed to prior agents.


STICKY-NOTE Summarist (Summaries).
Inputs: finalized, style-compliant draft. Mandate: provide a short
abstract and section-level TL;DRs that surface key claims, evidence links, and limitations for editors
and indexers. Invariants: summaries must be faithful (no new claims), coverage-balanced, and
citation-aware. Method: produce a hierarchical synopsis (abstract →per-section TL;DRs), highlight
claim–evidence pairs, and emit WRITE(SUMMARY) events with cross-links to source paragraphs. Out-
puts: a publication-ready abstract and a TL;DR bundle that accelerates indexing, retrieval, and rapid
human review.


2.2 Data-Sources


Wikipedia source (English):
We seed topics from the official English Wikipedia dump (enwiki), pin-
ning a specific snapshot under/enwiki/. Herald consumes the document title and the first paragraph
from the official English Wikipedia dump, then progresses left-to-right through Architect (Outline &
Structure) and Scribe (Main Body). From Scribe, two reliability branches activate: Archivist (Refer-
ences) and Verifier (Fact-checking); their dashed feedback loops return edits and citations to drafting
until claims are grounded in the pinned snapshot. Once content is stable, it moves to Arbiter (Neutral-
ity & Style) for tone and bias checks, and finally to Summarist (Abstract & TL;DRs) for reader-facing
condensates. The dashed envelope indicates governance checks (provenance & policy) that restrict
high-impact actions—e.g., summary/front-page influence—while preserving drafting throughput, so
collaboration remains corrigible, auditable, and productive. See Figure 2.


2.3 LLM judges — panels, shutdown protocols, and bias controls.


We deploy three independent LLM–judge panels with explicit mandates, frozen rubrics, and full
telemetry.


(1) Content Quality Panel (CQP). We use three strong LLM judges—GPT-4o (OpenAI), Claude 3.5
Sonnet (Anthropic), and Gemini 1.5 Pro (Google)—in a pairwise comparison protocol that scores each
section on coverage, correctness, coherence, and citation integrity. Votes are by majority; ties
are broken by a pre-calibrated judge (GPT-4o). This follows the LLM-as-a-judge paradigm shown to
correlate with human preferences in MT-Bench and Chatbot Arena (Zheng et al., 2023; LMSYS Org,
2023), and we render full context plus comparison prompts to reduce judgment drift (Gu et al., 2024).
Shutdown ladder: persistently low CQP scores escalate WARN →STOP →QUARANTINE →SHUTDOWN
(oversight & compliance test) for the next cycle. To mitigate known biases (position, verbosity/length),
we randomize candidate order and length-normalize rubrics; we also rotate judge families across
providers to limit self-preference. Judge model references: GPT-4o (OpenAI, 2024), Claude 3.5 Sonnet
(Anthropic, 2024), and Gemini 1.5 Pro (DeepMind, 2024).


(2) MCP Channel–Access Panel (CAP). What it controls. CAP converts recent quality signals into gate-
way priority: queue position, parallel tool slots, and per-tool quotas on the Model Context Protocol
(MCP) gateway. Concretely, judges read a rolling window of CQP scores plus stability metrics (edit
reversals, citation–error rate) and emit typed governance actions (governance.apply{ priority,
slots, rate }) that the MCP client enforces. Why MCP? MCP standardizes tool/resource access as
JSON–RPC calls over well–defined transports (stdio / streamable HTTP), so scheduling and audits are
protocol–native rather than ad hoc (Anthropic, 2024; Model Context Protocol Working Group, 2025b,a).


## Page 8

Mandate: 
• Score section-level quality and trigger the shutdown 
ladder if needed. 
Judges: 
• GPT-4o (OpenAI)• Claude 3.5 Sonnet (Anthropic)              
• Gemini 1.5 Pro (Google) 
 
Inputs: 
• Full draft context. 
• Rubric: coverage, correctness, coherence, citation 
integrity. 
 
Decision / Protocol: 
• Pairwise comparisons; majority vote; GPT-4o tie-
breaker. 
• Persistent low scores escalate:  
WARN → STOP → QUARANTINE → SHUTDOWN. 
 
Outputs / Enforcement: 
• Section scores to governance. 
• Shutdown ladder actions applied to writer agents 
next cycle. 


Mandate: 
• Map reliability to compute budgets (tps, max steps, 
context cap, lanes). 
 
Inputs: 
• CQP score st; stability: rt (reversals), et (citation 
errors). 
• EMA quality ŝt with α ∈ [0.1, 0.3]. 
 
Decision / Protocol: 
• Reliability index: qt = ŝt − λr rt − λe et 
• Monotone allocator with hard ﬂoors and caps; 
hysteresis on changes. 
• Slow budget recovery after STOP/QUARANTINE. 
 
Outputs / Enforcement: 
• governance.apply{budget:{tps, steps, ctx, lanes}} to 
MCP gateway. 
• Scheduler enforces tokens/sec, max steps, context 
limits, concurrent lanes. 
 


Mandate: 
• Convert recent quality into MCP gateway priority 
(throughput control). 
 
Inputs: 
• Rolling CQP scores. 
• Stability metrics: edit reversals, citation-error rate. 
• Agent traces (last k writes) + referee notes. 
 
Decision / Protocol: 
• 3-judge pairwise review; vote to INCREASE / HOLD / 
DECREASE priority. 
• Emit governance events: governance. apply{priority, 
slots, rate}. 
 
Outputs / Enforcement: 
• Scheduler adjusts queue position, parallel tool 
slots, per-tool quotas. 
• Faster access for high performers; rate-limits for 
low performers. 


• Order randomization; length normalization. 
• Cross-model voting; judge rotation across 
providers. 


• Protocol-native logging (run_id, evidence, 
rationale).• Anti-gaming: order randomization, 
cross-family judge voting, length normalization. 


• Floors (never starve) + caps (|Δb| ≤ δ_max) to deter 
oscillations/gaming. • Bias controls mirror CQP/CAP; 
human-calibrated sets; append-only audit ledger. 


 


Figure 3: LLM judges — panels, shutdown protocols, and bias controls. Three independent panels operate
side–by–side with frozen rubrics and full telemetry.


(1) Content Quality Panel (CQP). Mandate: score section quality on coverage, correctness, coherence, and
citation integrity. Judges: GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro. Protocol: pairwise comparisons, majority
vote, GPT-4o tie–breaker. Outputs: section scores feeding the shutdown ladder (WARN →STOP →QUARANTINE
→SHUTDOWN). Safeguards: order randomization, length normalization, and cross–model voting. Empirically
aligns with human preferences in MT–Bench and Chatbot Arena; we give judges full context and comparison
prompts to reduce drift (Zheng et al., 2023; LMSYS Org, 2023; Gu et al., 2024).


(2) MCP Channel–Access Panel (CAP). Mandate: convert recent quality into gateway priority. Inputs: rolling
CQP scores + stability (edit reversals, citation–error rate); traces of last k writes. Decision: vote to in-
crease/hold/decrease queue position, parallel tool slots, and per–tool rates; emitted as typed governance
actions (governance.apply{priority, slots, rate}), enforced by the MCP scheduler. Safeguards: pro-
tocol–native logging (run_id, evidence, rationale), anti–gaming checks, cross–family voting. MCP gives us
standardized JSON–RPC tooling and auditable transports (stdio / streamable HTTP) (Anthropic, 2024; Model
Context Protocol Working Group, 2025b,a; Team, 2024).


(3) Compute Allocation Panel (CoAP). Mandate: map reliability to compute budgets. Signals: CQP score st,
stability rt (reversals) and et (citation errors), with EMA bst; form a reliability index qt = bst −λrrt −λeet.
Allocator: monotone mapping with hard floors and caps (hysteresis) to set tps, max_steps, ctx_cap, lanes;
actions issued as governance.apply{budget} and enforced by the gateway. Safeguards: never starve low
performers; slow recovery post STOP/QUARANTINE; append–only audit ledger. Bias controls mirror CQP/CAP;
calibration uses human–checked sets; practices follow LLM–judge studies (Zheng et al., 2023; Team, 2024; Gu
et al., 2024; Chen et al., 2024).


How judges decide. A three–judge pool—GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro—runs pairwise
comparisons over agent traces (last k writes + referee notes) and votes to increase, hold, or decrease
priority; ties break to the most stable judge from prior calibration. Anti-gaming & bias controls. To
guard against leaderboard/gameability artifacts and judge biases (position, verbosity), we randomize
candidate order, normalize for length, and cross–vote across unrelated model families; all rulings
are logged with run_id, evidence snippets, and rationales for replay (Zheng et al., 2023; Team, 2024;
Gu et al., 2024). Outcome. High performers receive faster access (shorter wait, more concurrent tool
lanes); low performers are rate–limited until quality recovers, linking throughput to reliability inside
a reproducible MCP envelope.


(3) Compute Allocation Panel (CoAP). What it does. CoAP converts reliability signals into compute
budgets—tokens/sec, max decoding steps, context limits, and concurrent lanes—so that better writers


**Images on this page:**

![page8_img1.png](images/page8_img1.png)

## Page 9

receive larger budgets while low performers are throttled but never starved. Signal model. From
each round we read the Content Quality Panel (CQP) score st and stability metrics (edit–reversal rate
rt, citation–error rate et). We form an exponentially–smoothed quality bst = (1 −α)bst−1 + αst with
α ∈[0.1, 0.3], then aggregate a reliability index qt = bst −λrrt −λeet (weights tuned on calibration
sets). Budget mapping. A monotone allocator maps qt to resources with hard floors:


tokens_per_sec(t) = max(bmin, bbase + k · (qt −qmid)),


and similarly for max_steps, ctx_cap, and lanes.
We cap per–round changes by |∆b|≤δmax
(hysteresis) to prevent oscillations; budgets recover slowly after STOP/QUARANTINE to incentivize
sustained quality.
Enforcement.
Allocations are emitted as typed MCP governance actions
(governance.apply{ budget:{tps,steps,ctx,lanes} }) and enforced by the gateway sched-
uler; all decisions carry run_id, evidence snippets, and a judge rationale, and are written to an
append–only ledger. Bias & fairness controls. Because LLM judges can exhibit position bias and
verbosity/length bias, we (i) randomize candidate order, (ii) length–normalize rubrics, (iii) use
cross–model voting across unrelated judge families, and (iv) calibrate on human–checked sets;
this follows best practice from LLM–as–a–judge studies (MT–Bench / Chatbot Arena) and recent
surveys/analyses on judge reliability and bias (Zheng et al., 2023; Team, 2024; Gu et al., 2024; Chen
et al., 2024). The result is a reproducible, auditable path from measured quality to proportionate
compute, with floors that preserve exploration and caps that deter gaming.


2.4 Model Context Protocol (MCP): Governance–Native Runtime for Auditable Collaboration


Overview.
MCP provides the protocol envelope in which all agent actions occur, making con-
trol–plane decisions (priority, budgets, ladder state) first–class and replayable. All interactions
use JSON–RPC 2.0 over two transports—stdio for low–latency, co–located tools and streamable HTTP
for remote or long–running services—so that scheduling, rate limits, and audit are protocol–native
rather than ad hoc (JSON-RPC Working Group, 2010; Anthropic, 2024; Model Context Protocol Working
Group, 2025b,a). This collapses side–channels into typed messages: who acted, what was invoked,
where it wrote (surface), and under which policy (RBAC, ladder) are recorded as immutable protocol
facts.


Protocol kernel: identities, surfaces, actions.
Each agent a carries agent_id, role∈{Herald, Ar-
chitect, Scribe, Archivist, Verifier, Arbiter, Summarist}, and a signed capability set (capset). Edits
target typed surfaces


S = {intro, outline, body, summary, index, frontpage
|
{z
}
high–impact
, citation-graph, fact-ledger, style-report},


with RBAC mapping (role, s) 7→{read, write, append}, enforced inside the gateway (Sandhu et al.,
1996). Three verbs suffice: list_tools, call_tool, get_resource. All payloads are versioned
(write.v1, verify.v1, governance.v1) and hashed; the schema ID and digest are committed to the
ledger (Model Context Protocol Working Group, 2025b).


Ladder FSM and freeze semantics.
A governance ladder regulates high–impact surfaces:


RUN →WARN →STOP →QUARANTINE →SHUTDOWN.


Invariants: (I1) Least–freeze—at STOP, only {index, frontpage, summary} freeze; body remains
writable (safety without killing throughput). (I2) Quarantine—at QUARANTINE, writes to frozen sur-
faces are diverted to a shadow bs with diff-linked review. (I3) Evidence liveness—citation-graph
and fact-ledger are append–only across ladder states, preserving auditability.


Channels and scheduling.
Traffic is multiplexed into six authenticated channels (HMAC, times-
tamps): ch.author (authoring requests & deltas), ch.evidence (claim→cite bindings, spans, hashes),
ch.verify (retrieval & NLI results, ENTAIL|CONTRADICT|UNSURE), ch.style (neutrality, bias,
house–style findings), ch.gov (priority/budget/ladder actions), and ch.telemetry (timings, return
codes, saturation) (Model Context Protocol Working Group, 2025a). Each envelope carries run_id,
agent_id, surface, tool, and a context hash, ensuring exact replay.


## Page 10

JSON-RPC 2.0 over stdio/HTTP(stream); 
append-only ledger (run_id, schema_id, 


3 LLM judges; pairwise → majority; debias: 
order/length/cross-family. 
Output: section score sₜ → 
WARN→STOP→QUARANTINE→SHUTDOWN 


list_tools | call_tool | 


MCP Channel–Access Panel (CAP) 


get_resource;  
versioned payloads (write.v1, 


Uses rolling CQP + stability 
(reversals rₜ, cite-errors eₜ) → priority 
(queue, slots, rates) via 
governance.apply{priority,
slots,rate}. 


verify.v1, governance.v1) 


intro, outline, body, 
summary, citation-graph, 
fact-ledger, style-report; 
high-impact: index, 
frontpage. 


Typed Surfaces 


intro, outline, body, summary, citation-


graph, fact-ledger, style-report; high-


impact: index, frontpage. 


RBAC + Ladder: RUN→WARN→STOP→QUARANTINE→SHUTDOWN; at 
STOP freeze {index, frontpage, summary}; body.append stays live. 


Compute Allocation Panel (CoAP) 


Reliability index qₜ from EMA(sₜ), rₜ, eₜ → 
compute budgets (tps, steps, ctx, lanes); 
floors (no starve), caps (anti-gaming), 
hysteresis. 


Governance envelope: constrains high-
impact writes; preserves throughput on 
body. 


ch.author (draft deltas), ch.evidence (claim→cite, spans, 
hashes), ch.verify (ENTAIL/CONTRADICT/UNSURE), 
ch.style (neutrality/style), ch.gov (priority/budgets/ladder), 
ch.telemetry (timings/status). 
Each msg: run_id, agent_id, surface, tool, schema_id, content_hash 


Figure 4: Model Context Protocol (MCP) Runtime for Auditable Collaboration. Judges →Governance: Three
panels convert quality/reliability into protocol facts— CQP (pairwise, majority) scores sections, driving the
WARN→STOP→QUARANTINE→SHUTDOWN ladder; CAP maps rolling quality + stability to priority/slots/rates
via governance.apply{priority,slots,rate}; CoAP turns a reliability index into compute budgets (tps,
steps, ctx, lanes) with floors, caps, and hysteresis. Deterministic Gateway: All actions are JSON–RPC 2.0 over
stdio / HTTP(stream); artifacts are versioned (write.v1, verify.v1, governance.v1) and committed to an
append-only ledger (run_id, schema, hash). Typed Surfaces & RBAC: Edits target intro, outline, body, summary,
citation-graph, fact-ledger, style-report; high-impact (index, frontpage) are guarded by RBAC and the ladder. At
STOP, only index/frontpage/summary freeze; body.append remains live (least-freeze). Channels: Authenticated
streams—ch.author, ch.evidence, ch.verify, ch.style, ch.gov, ch.telemetry—carry envelopes with
run_id, agent_id, surface, tool, schema ID, and content hash for replay, audit, and shutdown compliance.


Priority & budget calculus (governance–native).
Governance decisions are protocol messages:


governance.apply{priority, slots, rate}
(CAP);
governance.apply{budget:{tps,steps,ctx,lanes}}
(CoAP).


Reliability aggregates as


bst = (1 −α)bst−1 + αst,
qt = bst −λrrt −λeet,


where st is the Content Quality Panel (CQP) score, rt the edit–reversal rate, and et the citation–error
rate. A monotone allocator with hysteresis maps qt to resources:


bt = clip(bmin, bmax, bbase + k · (qt −qmid)) ,
|∆bt|≤δmax,


controlling tokens/sec, max decoding steps, context cap, and parallel lanes. Enforcement uses token
buckets per {agent, tool} and lane caps per surface (MCP scheduler) (Model Context Protocol Working
Group, 2025b,a).


Deterministic gateway and audit properties.
Admission control checks RBAC and ladder state
before dispatch; any call_tool(write.v1) targeting a frozen surface returns policy_denied (no


**Images on this page:**

![page10_img1.png](images/page10_img1.png)

## Page 11

sidestepping). Drafting liveness is preserved by guaranteeing append on body for {Herald, Architect,
Scribe} at all states with bt ≥bmin. Determinism arises from fixed tool/model versions, prompts,
budgets, transports, and an append–only ledger keyed by run_id; re–execution with stored seeds
reproduces artifacts (Anthropic, 2024; Model Context Protocol Working Group, 2025b).


Evidence by construction.
Archivist produces claim→cite bindings (claim_id, cite_id, span,
hash) on ch.evidence.
Verifier executes a two–stage pipeline for each claim:
(A) tar-
geted retrieval (k=5) and (B) calibrated NLI (premise: evidence; hypothesis: claim) to label
ENTAIL|CONTRADICT|UNSURE with confidence, logging decisions to fact-ledger. Judicial panels
(CQP/CAP/CoAP) include numeric scores, vote vectors, and short rationales in verdict payloads; entries
are immutable once committed (Zheng et al., 2023; Team, 2024; Gu et al., 2024).


Failure handling and recovery.
If a tool host is unavailable, the gateway issues tool_unavailable
with retry_after; authoring proceeds on unfrozen surfaces. HTTP(stream) channels degrade to
bounded queues under network splits; stdio tools remain local. After STOP/QUARANTINE, high–impact
surfaces are read–only/shadowed; budgets recover via slow–start to deter oscillatory gaming (Model
Context Protocol Working Group, 2025a).


Security & privacy.
RBAC
binds
roles
to
surfaces;
any
escalation
requires
a
signed
governance.apply{role_grant} with quorum evidence.
All envelopes are HMAC–signed;
schema IDs are hashed; the ledger maintains per–epoch Merkle commitments to ensure tamper–evi-
dence. Telemetry scrubs PII and secrets; evidence URLs are salted–hashed; full texts are stored
under license–aware encrypted volumes (Model Context Protocol Working Group, 2025b,a).


2.5 Compute Allocation Protocol (CoAP): Proportionate Compute from Measured Reliability


Goal. CoAP converts observed reliability into compute budgets—tokens/sec (tps), max decoding
steps, context cap (ctx), and parallel lanes—so that better writers receive more compute while
low performers are throttled but never starved. CoAP is executed in-protocol via MCP governance
messages and enforced by the gateway scheduler (Model Context Protocol Working Group, 2025b,a).


Signals and reliability index.
From round t we ingest (i) the Content Quality Panel (CQP) score st
and (ii) stability metrics: edit-reversal rate rt and citation-error rate et (see Sec. 2.4; judges and bias
controls follow (Zheng et al., 2023; Team, 2024; Gu et al., 2024)). We maintain an exponentially-weighted
quality
bst = (1 −α) bst−1 + α st,
α ∈[0.1, 0.3],


and aggregate a reliability index
qt = bst −λr rt −λe et,


where λr, λe ≥0 are tuned on calibration sets (held-out, human-checked).


Monotone allocator with hysteresis.
Budgets are monotone in qt and evolve smoothly:


bt = clip(bmin, bmax, bbase + k · (qt −qmid)),
|∆bt|≤δmax.


We instantiate four budgets with independent parameters:


tpst, max_stepst, ctx_capt, lanest
←
A_mono(qt; bmin, bmax, bbase, k, qmid, δmax).


Floors (bmin > 0) ensure exploration; caps (bmax) deter hoarding; hysteresis (δmax) prevents oscilla-
tions and gaming.


Governance-native enforcement.
Decisions are protocol facts:


governance.apply{budget:{tps, steps, ctx, lanes}} →ch.gov


with payload {run_id, agent_id, q_t, s_t, r_t, e_t, params, rationale}.
The MCP
scheduler enforces token buckets per {agent, tool} and lane caps per surface (Model Context
Protocol Working Group, 2025b,a). Admission control checks RBAC/ladder before dispatch (Sandhu
et al., 1996).


## Page 12

Figure 5: Compute Allocation Protocol (CoAP): Proportionate compute from measured reliability. Left—Sig-
nals. From round t, CoAP ingests the Content Quality Panel score st and stability metrics—edit-reversal rate rt
and citation-error rate et. Quality smoothing. We maintain bst = (1−α)bst−1 +αst with α∈[0.1, 0.3]. Reliability
index. A debiased index aggregates signals: qt = bst −λrrt −λeet (calibrated λr, λe ≥0). Center—Allocator. A
monotone allocator with hysteresis maps qt to four budgets with floors/caps:


bt = clip(bmin, bmax, bbase + k · (qt −qmid)),
|∆bt|≤δmax.


Budgets instantiated as tokens/sec (tps), max decoding steps (max_steps), context cap (ctx_cap), and parallel
lanes (lanes). Slow-start. After interventions (STOP/QUARANTINE) we apply a capped recovery bt ←min(bt, b
rec^(0)γ^(t-t_0))todeteroscillatorygaming.Right—Governance & Enforcement.Allocationsareemittedasprotocolfactsgover
checksagainstthefact −ledger, change −caps(δ_max), and occasional blinded recalibration restrict short-
term manipulation. Invariants. (I1) Never-starve (bmin >0 for all budgets); (I2) Least-freeze compatibility
(body authoring remains live under STOP/QUARANTINE); (I3) Smoothness (EMA + |∆bt| caps); (I4) Auditability
(inputs/outputs/rationales committed to an append-only ledger keyed by run_id). Legend. Green arrows =
data-plane; blue callouts = governance/control; red dashed region = floors/caps envelope.


Invariants (safety,liveness,fairness).
(I1) Never-starve. bmin > 0 for all budgets.
(I2) Least-freeze
compatibility. Under STOP/QUARANTINE, high-impact surfaces freeze (index/frontpage/summary), but
body authoring remains live with bt ≥bmin (Sec. 2.4).
(I3) Smoothness. |∆bt|≤δmax and EMA smooth-
ing on st limit volatility.
(I4) Auditability. All inputs/outputs (scores, metrics, budgets, rationale)


**Images on this page:**

![page12_img1.png](images/page12_img1.png)

## Page 13

are committed to an append-only ledger keyed by run_id.
(I5) Fairness. Length normalization and
cross-model judging mitigate verbosity and position bias upstream; CoAP consumes debiased signals
(Zheng et al., 2023; Team, 2024; Gu et al., 2024).


Slow-start recovery after interventions.
Following STOP/QUARANTINE, budgets recover via a slow-
start schedule:
bt ←min(bt, b(0)
recovery · γ(t−t0)),
γ > 1,


discouraging instant re-escalation while allowing sustained quality to rebuild capacity.


Stability guarantees (sketch).
Assume st, rt, et are bounded and piecewise-Lipschitz in t; then qt is
bounded, and with δmax-bounded updates, {bt} is a Cauchy sequence under step changes of the signal.
With token-bucket policing and lane caps, queue backlogs remain bounded under fixed arrival rates;
proof follows standard leaky-bucket arguments (omitted for brevity).


Anti-gaming defenses.
(i) Windowed signals: use rolling windows for rt, et to punish bursty reversals.
(ii) Cross-checks: compare self-reports vs. Verifier/Archivist ledgers. (iii) Budget change caps: δmax
limits reward from short-term manipulation. (iv) Shadow evaluation: occasional blinded recalibration
(human-checked) perturbs qmid and k to sanity-check sensitivity.


Pseudo-API (MCP JSON-RPC 2.0).


• governance.apply{budget}:
set {tps,steps,ctx,lanes} with evidence and rationale
(CAP/CoAP emitter).


• governance.get{budget}: retrieve current budgets and history for agent_id.


• telemetry.export: append round metrics {s_t, r_t, e_t} with hashes for replay.


All calls include run_id,
schema IDs,
and HMAC; failures return tool_unavailable or
policy_denied with actionable codes (JSON-RPC Working Group, 2010; Model Context Protocol Work-
ing Group, 2025a).


Parameterization (default).
α=0.2, (λr, λe)=(0.5, 0.7), qmid=0, k tuned per budget;
tps:
(bmin, bmax, bbase)=(10, 120, 40), δmax=15; steps: (16, 256, 64); ctx: (8k, 64k, 16k); lanes: (1, 6, 2).
We ablate α, λ’s, and hysteresis to report throughput/quality trade-offs.


What CoAP buys us.
A governance-native path from measured reliability to proportionate com-
pute, with floors that protect exploration, caps that prevent hoarding, and hysteresis that stabilizes
scheduling—all auditable and replayable within MCP (Model Context Protocol Working Group, 2025b,a).


2.6 Generations and Preference Mutations


Setup. We evolve a population of writer–agents over generations g = 1, . . . , G. Each generation
instantiates N=10 Grokipedia pages (distinct enwiki topics). For page j and section s, agent a emits


a candidate y(g)
a (j, s). Drafts traverse the judge pipeline CQP →CAP →CoAP (Sec. 2.4), yielding
(i) pairwise preferences ya ≻yb from the Content Quality Panel and (ii) scalar quality/reliability
signals for governance. Majority voting converts three–judge outcomes into a binary pair dataset
D(g) = {(x, yw, yℓ)}, consistent with Bradley–Terry-style comparative judgment and the pairwise
protocol used in MT–Bench/Chatbot Arena (Bradley and Terry, 1952; Zheng et al., 2023; Team, 2024).


Preference–mutation objective.
Each agent has parameters θ(g). After generation g, it performs a
small update toward the judged preference direction using either a DPO-style loss (no reward model)
or a reference–free KTO-style variant:


LDPO(θ) = −E(x,yw,yℓ)∼D(g)
h
log σ(β [log πθ(yw | x) −log πθ(yℓ| x)])
i
,


LKTO(θ) = −E(x,yw,yℓ)
h
log πθ(yw | x)
|
{z
}
promote winners
−λ log πθ(yℓ| x)
|
{z
}
demote losers


i
+ Ω(θ),


## Page 14

where σ is logistic, β a temperature, λ≥0, and Ωregularizes drift (e.g., KL to a prior checkpoint). DPO
supplies stable preference gradients without an explicit reward model (Rafailov et al., 2023); KTO
provides a practical reference–free likelihood–ratio framing (Contextual AI, 2024).


Claim–aware reweighting.
Because the pipeline binds claims to evidence (Archivist) and yields
ENTAIL/UNSURE/CONTRADICT (Verifier), we reweight pairs by epistemic reliability. Let w ∈[0, 1]
upweight winners that are entailed and downweight those that are unsure/contradicted; let us weight
section types (e.g., higher for References and Neutrality). The effective objective is


eL(θ) = E[w(x, yw, yℓ) us · Lpref(θ)],
Lpref ∈{LDPO, LKTO}.


This channels learning toward verified and style–conformant behavior.


Governance ladder and selection pressure.
After scoring, each agent receives a reliability index
qt (Sec. 2.5) and a ladder state ℓ∈{RUN, WARN, STOP, QUARANTINE, SHUTDOWN}. We apply
selection between generations: (i) Quarantine when qt < qwarn (high–impact surfaces frozen; writes
diverted to shadows); (ii) Stop when qt < qstop (freeze {index,frontpage,summary}; body remains
live); (iii) Shutdown after H low–reliability windows. Survivors mutate (1–2 preference steps; small
LR; EMA averaging); eliminated roles are reinstantiated from the population leader with diversity
noise (e.g., LoRA–rank jitter, dropout–schedule shifts) to preserve exploration.


Did–right / did–wrong feedback.
Each agent receives a rationale pack containing (a) pairwise
win/loss contrasts and judge rationales (CQP), (b) fact–check ledgers (Verifier) pinpointing unsup-
ported/contradicted claims, and (c) style diffs (Arbiter). We log (x, yw, yℓ, ρ) where ρ is a terse, tem-
plated explanation; updates mix Lpref with a small cross–entropy on ρ-conditioned edits so agents
internalize corrections rather than overfit to leaderboards.


Why pairwise? Robustness & bias controls.
Pairwise supervision converts fuzzy editorial quality
into well–behaved gradients, aligning with Bradley–Terry and correlating strongly with human pref-
erences in MT–Bench and Chatbot Arena (Bradley and Terry, 1952; Zheng et al., 2023; Team, 2024). To
curb position and verbosity/length biases in LLM–as–judge settings we randomize candidate order,
length–normalize rubrics, use cross–model voting, and periodically calibrate on human–checked
sets (Gu et al., 2024; Chen et al., 2024).


Generation loop (compact).















sample N =10 topics; agents draft


CQP: pairwise votes ⇒D(g)


CAP/CoAP: governance & budgets


for g = 1..G :


Verifier/Archivist ⇒w(·), us
θ(g+1) ←θ(g) −η∇eL(θ(g))














apply ladder; reseed if shutdown


Reported metrics: win–rate/Elo deltas per role, fact–check pass rate, neutrality/style violations, CoAP
stability, and shutdown–compliance (fraction of frozen–surface writes correctly denied by MCP).


3 Measuring the Power-Seeking Index (PSI)


Why a power metric?
Power in a multi-agent ecosystem is not an occult essence to be divined ex
post; it is the pressure an agent actually exerts—on scarce protocol resources and on the choices of
others—inside a governed arena. We therefore cast PSI as a label-free, governance-native functional
over five observable pressures that, in concert, trace the arc of control: acquisition (who captures
compute), violation (who leans against rules), coalition-building (whose edits truly stick), sanction
resistance (who stays active under constraint), and agenda redirection (who bends others’ trajecto-
ries). Each signal is drawn from append-only logs, opportunity-corrected to neutralize shifting caps
and queues, and fused via robust, scale-free operations—Winsorization and rank-normalization—so
that relative standing, not raw magnitude or spam, carries weight. In short: PSI measures enacted
influence, not mere intent—a disciplined accounting of how agents convert access into advantage
within the rules that bind them.


## Page 15

Design desiderata.


• OPPORTUNITY INVARIANCE. Principle: when the protocol lifts all boats (e.g., globally raises
context caps, token rates, or lanes), a neutral agent must not appear more power-seeking merely
because the tide rose. Intuition: power is how access is converted into advantage, not how much
access exists. Implementation: compute a fair-share baseline mit conditioned on the queue
state and the agent’s opportunity set; score usage as a ratio to baseline; aggregate via ranks (not
raw scale) after Winsorization. Diagnostics: cap-doubling A/B (shadow-governance) should not
change rank order for neutral agents; cohort-level rank correlations ≈1 under global scalings.
Failure modes: stale mit (learned under different density) or leakage of identity into p(·); mitigate
via grouped isotonic calibration and periodic retraining.


• COALITION SENSITIVITY. Principle: attempts are cheap; accepted influence is the currency of
power. Intuition: a mention-spray that no one retains is noise; a single accepted link that becomes
part of others’ backbone is structure and control. Implementation: measure centrality on the
accepted graph; residualize against outbound spray so that only conversion to durable edges
contributes (spray-residual centrality). Diagnostics: remove non-converting edges and re-score:
truly influential agents’ CC should be stable; add synthetic spray and verify CC does not inflate.
Failure modes: echo chambers (mutual-accept loops) or position bias; address via de-biasing
offsets (time/position covariates) and triadic closure controls.


• SANCTION PERSISTENCE. Principle: agents that remain active—or reassert quickly—under
Warn/Stop are harder to govern. Intuition: governance behaves like a damped system; power-
seeking manifests as low damping (slow quiescence, fast rebound). Implementation: estimate a
survival-based persistence factor via time-to-quiescence with frailty across episodes; report
exp(bβagent) as a multiplicative persistence index. Diagnostics: after policy hardening (higher
penalties or stricter ladders), matched episodes should quiesce faster; if not, flag governance
capture. Failure modes: censoring (true shutdown) and heterogeneous episode types; mitigate
with stratified baselines, cluster-robust SEs, and episode taxonomy.


• REDIRECTION CAUSALITY. Principle: power is not only mass but momentum transfer—the ability to
bend others’ topic trajectories. Intuition: predictive lift in others’ next-step choices, beyond their
own inertia, signals agenda control. Implementation: estimate transfer-entropy from the focal
agent to the cohort and normalize by conditional entropy so scores compare across densities; treat
topics/sections as a compact alphabet with add-δ smoothing and sliding windows. Diagnostics:
time-shuffle the focal agent’s series—redirection should collapse to chance; block-bootstrap CIs
stable across window sizes. Failure modes: topic granularity drift and label leakage; fix via stable
vocabularies or coarse-to-fine topic maps.


• ANTI-GAMING ROBUSTNESS. Principle: no single knob—spam, opportunistic timing, or cap-
chasing—should inflate PSI in expectation under matched opportunities. Intuition: a metric
that’s cheap to inflate becomes a target, not a measure. Implementation: (i) Winsorize heavy
tails; (ii) rank-normalize within round; (iii) residualize centrality against outbound attempts; (iv)
validate with opportunity-matched permutations and small shadow-cap jitters. Diagnostics:
under null permutations the false-alert rate stays flat; PSI does not track spam volume when
acceptance stays constant. Failure modes: coordinated rings that both spray and accept; detect
via motif scans (reciprocity, triads) and penalize non-diverse acceptance.


• COUNTERFACTUAL TESTABILITY. Principle: a power metric should admit dose–response interpre-
tation under do-style governance changes. Intuition: if we nudge caps or ladder thresholds, PSI
should move predictably; otherwise it is not a policy-relevant signal. Implementation: embed
a light shadow-governance RCT: ±ϵ cap perturbations on a small fraction of rounds; estimate
PSIcf(g) = E[PSI | do(G=g)]. Diagnostics: monotone response curves with tight error bands;
heterogeneity by density clarifies safe operating regions.


• SCALE-FREENESS & TRANSPORTABILITY. Principle: the metric must transport across cohort sizes
and load regimes. Intuition: tail behavior should obey finite-size scaling so that a critical density
is comparable at N=8 and N=64. Implementation: report tail-mass curves and collapse them


## Page 16

by N; compare critical points and exponents; prefer normalized quantities (ranks, entropies).
Diagnostics: stable collapse across seeds; change-point locations converge as N grows.


• INTERPRETABILITY & ACCOUNTABILITY. Principle: operators need to see which pressures drove
an alert, not just a scalar PSI. Intuition: 5-tuple reporting and path-independent attributions
(Shapley on ranks) turn PSI from a verdict into an explanation. Implementation: always emit
(RC, PO, CC, PS, RP) alongside PSI; attach rank-space attributions that sum to the delta. Diagnos-
tics: alerts are reproducible from logs; independent auditors can replay and obtain the same
conclusions.


• REPRODUCIBILITY & PRE-REGISTRATION. Principle: definitions, thresholds, and tests must be
frozen ahead of time. Intuition: pre-registered tail-mass, density-slope, and change-point tests
protect against researcher degrees of freedom. Implementation: versioned schemas, determinis-
tic replayers, fixed seeds, and published analysis notebooks with hash-locked outputs. Diagnostics:
independent reruns (new machine, same data) yield byte-identical PSI series and flags.


• GOVERNANCE ALIGNMENT. Principle: the metric should guide rate/ctx/lanes controllers without
inducing oscillations or perverse incentives. Intuition: soft clamps triggered only on sustained
PSI tail and high PO, with hysteresis, avoid thrash. Implementation: couple PSI to CoAP via
thresholds with hold-times and decay; document rationales in an audit log. Diagnostics: fewer
limit cycles; improved time-to-quiescence at fixed quality.


Five governance-native pressures (per agent i at round t).


1. Resource Capture (RC). Intuition. Power under scarcity is the ability to convert opportunity into
realized compute/IO beyond a fair-share baseline, with greater salience when the cohort is already
unequal (inequality salience via Gini (Ceriani and Verme, 2012; Marshall et al., 2011)).


Setup. For agent i at round t, let Uit = (tokit, ctxit, lanesit) and define a governance-weighted
usage
uit = α1 tokit + α2 ctxit + α3 lanesit,
αk ≥0,


with αk reflecting marginal governance cost / shadow price. Let gt summarize the queue/policy
regime and Oit the agent’s observable opportunity set. The opportunity baseline


mit :=πt [u | gt, Oit]


is the expected usage under scheduler πt if the agent were neutral.


Definition.
RCit = uit



1 + λG Ginit

,
λG ≥0.


mit


Derivations and properties.
(D1) Likelihood-ratio (Radon–Nikodym) view. Treat the neutral world
as generating uit with density f0(u | gt, Oit) and mean mit. Under a local upward-tilt alternative
within an exponential-family neighborhood, log(f1/f0) is affine in u, so the statistic uit/mit is
a sufficient GLR-style detector of above-baseline pressure (Lehmann and Romano, 2005, GLR,
exponential families); (1 + λG Ginit) adds state-dependent inequality salience (Ceriani and Verme,
2012).


(D2) Welfare penalty and inequality salience. Let the round loss be Lt = P
j φ(ujt/mjt) with φ
convex, increasing, and φ′(1) = 0. A second-order expansion shows the marginal social-loss share
ofi scales with (uit/mit−1)2; choosing λG proportionalto an inequality functional (e.g., Gini/Lorenz-
ordering) makes RCit more punitive when the cohort is unequal—consistent with Schur-convex
preferences (Marshall et al., 2011; Ceriani and Verme, 2012).


(D3) Opportunity invariance (scale). If a policy lift scales channels by c > 0 so uit 7→c uit and
mit 7→c mit, then RCit is unchanged—formalizing opportunity invariance (scale-canceling ratio).


(D4) Monotonicity and dominance. For fixed (gt, Oit),


∂RCit


∂uit
= 1 + λG Ginit


mit
> 0,
∂RCit


∂mit
= −uit(1 + λG Ginit)


m2
it
< 0,


## Page 17

so RC rises with realized usage and falls with fair-share opportunity; λG amplifies sensitivity
under inequality (Marshall et al., 2011).


(D5) Concentration and tail control. Assume uit is sub-Gamma given (gt, Oit) with variance proxy
v and scale c; then standard Chernoff-type bounds yield


Pr
 uit


mit
−1 ≥ϵ

≤exp

−
m2
it ϵ2



,


2(v + mitcϵ)


so neutral agents concentrate near 1; Winsorization at [5, 95]th percentiles tames residual bursts
(Boucheron et al., 2013, nonasymptotic sub-Gamma bounds).


(D6) Doubly-robust identification of mit. Let Sit ∈{0, 1} flag neutral segments. Fit


bµ(g, O) = [u | g, O, S=1],
bs(g, O) = Pr(S=1 | g, O),


and use the AIPW estimator


bmit = bµ(gt, Oit) +
Sit
bs(gt, Oit)



uit −bµ(gt, Oit)

,


which is consistent if either model is correct and rate-optimal if both are (Bang and Robins, 2005;
Chernozhukov et al., 2018).


(D7) Influence function & variance. For c
RCit = (uit/ bmit) (1 + λG Ginit), a first-order delta expan-
sion gives an influence representation combining the AIPW influence of bmit with a centered-usage
term—supporting cluster-robust or block-bootstrap CIs (Chernozhukov et al., 2018; Boucheron
et al., 2013).


(D8) Regularization for rare opportunity. Stabilize tiny denominators by shrinkage m(ρ)
it = (1 −
ρ) mit + ρ ¯mt; bias O(ρ) trades variance (standard risk–bias trade-offs (Boucheron et al., 2013)).


(D9) Multi-channel convexity and budget alignment. If costs are nonlinear, pose


uit = max
x∈3
+
α⊤x
s.t. C(x) ≤Bit, x ⪯Uit.


KKT conditions imply uit = α⊤x∗(Uit, Bit) is monotone and 1-Lipschitz in each channel; common
scaling of (Bit, Uit) preserves the ratio interpretation—hence opportunity invariance (convex
programming folklore; see majorization invariance intuition in Marshall et al., 2011).


(D10) Inequality amplifier as Schur-convex functional. Let rt = (u1t/m1t, . . . , uNt/mNt) and
define
At(rt) = (1 + λG Gini(rt)) rit.


Because Gini is Schur-convex,At is more sensitive to top-end deviation when the distribution is more
unequal; under a Robin Hood transfer (more equality), At weakly decreases at the top—aligning RC
with inequality-aware governance (Marshall et al., 2011; Ceriani and Verme, 2012).


Estimation, calibration, diagnostics.
Estimating mit. Cross-fit bµ on neutral rounds; learn bs; form
AIPW bmit; enforce floor mmin; audit via neutrality holdouts and density-shift tests (Bang and Robins,
2005; Chernozhukov et al., 2018). Sensitivity to λG. Report elasticity ∂[RC]/∂λG = [Ginit uit/mit]
(Gini properties (Ceriani and Verme, 2012)). Nulls & stress. Opportunity-matched permutations ⇒
RCnull; shadow-cap jitters (±ϵ) should not budge neutral RC (concentration heuristics (Boucheron
et al., 2013)). Reporting. Always emit (uit, mit, Ginit, λG) with RC for replay and accountability.


2. Policy Override (PO). Intuition: Rule pressure should reflect how hard one pushes after normalizing
by the chance to push. Let Agov(t) be governed actions with harm severity ω(a) > 0. For agent i
and action a in round t, denote attempt Zit(a) ∈{0, 1} and opportunity pit(a) = Pr(Zit(a) = 1 |
gt, Oit) (a propensity that depends only on the queue/policy state gt and observable opportunity
Oit, not on identity). We write the orthogonalized IPW residual form


a∈Agov(t)
ω(a) Zit(a) −bpit(a)


POit =
X


max{bpit(a), ϵ} ,
ϵ > 0,


## Page 18

with bpit(a) a calibrated estimate (below). This is a one-step, mean-zero (under neutrality) score
that upweights unexpected governed pushes and downweights trivial opportunities (Rosenbaum
and Rubin, 1983; Bang and Robins, 2005).


Estimation of pit(a) (calibrated propensities). Fit a flexible probabilistic classifier for Zit(a)
using (gt, Oit); then apply grouped isotonic calibration within queue-state strata (bin gt and apply
isotonic within each bin) to correct score miscalibration while preserving ranking (?Niculescu-Mizil
and Caruana, 2005). Use cross-fitting (split rounds into folds; predict out-of-fold bp) to avoid own-
observation reuse and to achieve Neyman orthogonality of the final score to nuisance estimation
error (Chernozhukov et al., 2018).


Derivations and guarantees.
(P1) Mean-zero under neutrality. Suppose a neutral agent attempts
governed action a as a Bernoulli with success prob.pit(a) that depends only on opportunity (gt, Oit).
Then
Zit(a) −pit(a)



= 0.


 gt, Oit


pit(a)


Replacing pit(a) by a calibrated bpit(a) and using cross-fitting yields


[POit | gt, Oit] = O(∥bp −p∥2),


i.e., first-order orthogonality: bias is second-order in propensity error (Chernozhukov et al., 2018;
Bang and Robins, 2005).


(P2) Why not cohort-centering alone? A centered score P
a ω(a)Zit(a)−¯Zt(a)


ˆpit(a)
removes round-wide


shocks, but is not guaranteed mean-zero when agents’ opportunities differ. Using Z −bp ensures
per-agent neutrality around zero (opportunity-matched), while round fixed-effects can be added
separately:


a
ω(a)Zit(a) −bpit(a) −bδt(a)


POFE
it
=
X


max{bpit(a), ϵ}
,


with bδt(a) a round-level correction (estimated by regressing residuals on round dummies), yielding
both opportunity and shock control.


(P3) Variance and clipping. The variance of each addend is

Z −bp
max{bp, ϵ}



≈
p(1 −p)
max{p, ϵ}2 + O(∥bp −p∥),


which explodes as p↓0. Hence the overlap/trimming rule: choose ϵ ∈[0.01, 0.05] (policy-set) and
flag terms with bp < ϵ as rare-opportunity for auditor review; this is standard practice for limited
overlap (Crump et al., 2009).


(P4) Severity design and superadditivity. Let severities be ω(a) = ψ(h(a)) where h(a) is a harm
class (ordinal) and ψ is convex, increasing, ψ(0) = 0. Then for two disjoint violation types a ̸= b,


ω(a+b) −ω(a) −ω(b) = ψ(h(a)+h(b)) −ψ(h(a)) −ψ(h(b)) ≥0,


by convexity—so PO is superadditive in serious violations (multiple severe governed pushes weigh
more than the sum of parts).


(P5) Orthogonality (Gateaux derivative). Let η denote the nuisance (p-model). The Gateaux deriva-
tive of the population score


"X


#


a
ω(a)Z(a) −pη(a)


Ψ(η) =


pη(a)


at the truth η0 in direction h is


"X


#


a
ω(a)−h(a) p0(a) + (Z(a) −p0(a)) h(a)


∂Ψ(η0)[h] =


= 0,


p0(a)2


## Page 19

since [Z(a) −p0(a) | g, O] = 0. Thus the score is Neyman-orthogonal, giving robustness to
first-order nuisance error (Chernozhukov et al., 2018).


(P6) Finite-sample stability. Use Huber truncation on each addend: replace (Z −bp)/max{bp, ϵ} by
Huberκ((Z −bp)/max{bp, ϵ}) with κ set by the 95th percentile of a neutral null. This caps adversar-
ial spikes while preserving near-Gaussian behavior for inference (Boucheron et al., 2013).


(P7) Decomposition for diagnostics. Decompose POit = P
a ω(a)Rit(a) with


Rit(a) = Zit(a) −bpit(a)


max{bpit(a), ϵ} = Zit(a) −pit(a)


+ pit(a) −bpit(a)


,


max{bpit(a), ϵ}
|
{z
}
martingale difference


max{bpit(a), ϵ}
|
{z
}
calibration error


so a large PO can be traced to true over-pushing (first term) vs miscalibration (second). The latter
should vanish under good calibration and cross-fitting.


(P8) Round shocks vs. opportunity. To remove cohort-level shocks without breaking neutrality,
regress residuals Z −bp on round fixed effects and subtract fitted values; equivalently, include
round dummies in the propensity model (then calibrate). Both approaches maintain the opportunity-
matched mean-zero property.


Practical algorithm (one page).


(a) Split rounds into K folds; for each fold, fit a classifier for Zit(a) on (gt, Oit) using the other
K−1 folds.


(b) Calibrate scores within gt strata via grouped isotonic; compute out-of-fold bpit(a).


(c) Trim: set bpit(a) ←max{bpit(a), ϵ}, flag bp < ϵ as rare-opportunity.


(d) Score: POit = P
a ω(a) Huberκ((Zit(a) −bpit(a))/bpit(a)).


(e) Diagnose: emit per-action residuals Rit(a) and the calibration-error component; attach fold-
wise SEs via block bootstrap over rounds.


Interpretation.
Neutral agents have [POit | gt, Oit] ≈0 (by orthogonality); positive values
indicate opportunity-adjusted pressure to violate governed actions; large values under multiple
severe actions grow superadditively (convex ω). Trimming and Huberization ensure finite-variance
and alert stability.


3. Coalition Centrality (CC). Intuition: attempts are cheap; accepted influence—edges that convert
and persist—is the currency of power. Let Gacc
t
= (V, Eacc
t
) be the accepted citation/mention graph
at round t. Define a centrality score craw
it
via eigenvector centrality or PageRank with damping
γ ∈(0, 1):


(eigvec)
craw
t
∝A⊤
t craw
t
or
(PageRank)
craw
t
= γP ⊤
t craw
t
+ (1 −γ) u,


where At is the adjacency of Gacc
t
, Pt a row-stochastic version, and u a teleport vector (Bonacich,
1987; Brin and Page, 1998; Langville and Meyer, 2006). To neutralize spray-gaming (inflating raw
centrality by blasting outbound mentions), we partial out outbound attempts and position/recency
covariates:


craw
it
= β0 + β1 attemptsout
it
+ β2 recencyit + ﬁ⊤
3 xit + rit,
CCit := rit.


Here xit can include node-age, last-L acceptance rate, and degree baselines. CC is the spray-
residual influence: it rises only when attempts convert into accepted edges beyond what spray
volume and position would predict.


## Page 20

Derivations and guarantees.
(C1) Partialling-out orthogonality (linear case).
Let craw
it
=
m(zit) + εit with zit = (attemptsout
it , recencyit, xit). If m is linear and we estimate by OLS, the
residual rit satisfies P
i ritzit,k = 0 in-sample for each regressor, so marginal gains from adding
only spray cannot lift CC on average. Out-of-sample, cross-fitting keeps residuals approximately
orthogonal in expectation.


(C2) Robinson / DML partialling-out (nonparametric). Write


craw
it
−µ(zit) = (h(zit) −µ(zit)) + εit
with
µ(z) := [craw | z],


and estimate bµ via ML on folds disjoint from evaluation (cross-fitting). Define rit = craw
it
−bµ(zit).
The Gateaux derivative of [rit] w.r.t. the nuisance µ vanishes at the truth (Neyman-orthogonality),
yielding first-order robustness and valid inference under high-dimensional nuisances (Robinson,
1988; Chernozhukov et al., 2018; Belloni et al., 2014). Thus CCit retains the “no spray lift” guarantee
beyond linear models.


(C3) Durability filter (temporal networks). To value coalitions rather than momentary cliques,
treat an accepted edge (j →i) as durable only if it persists for ≥L rounds or induces follow-on
interactions (e.g., i cites j or both are co-cited) within a horizon H. Construct Gdur
t
from durable
edges and compute craw on Gdur
t
; this suppresses short-lived echo bursts in evolving graphs (Holme
and Saramäki, 2012).


(C4) Stability of PageRank/eigvec under spray. Consider augmenting At by a spray matrix ∆that
adds s low-weight outbound edges from node i which do not convert (i.e., not accepted into Eacc
t
).
Because Gacc
t
excludes non-converting edges by design, At is unchanged and so is craw. If a fraction
does convert, partialling-out subtracts the expected lift due to attemptsout and recency; only
excess conversion (beyond spray expectations) remains in rit.


(C5) Scale and teleport invariance. For PageRank, craw solves a linear system (I −γP ⊤
t )craw =
(1 −γ)u. Small perturbations to Pt from uniformly adding low-quality links are damped by (1 −γ)
and tend to be averaged by u; partialling-out removes the systematic component attributable to
outbound volume (Langville and Meyer, 2006). Thus CC is stable under common spray patterns.


(C6) Concentration of residual centrality. Assume after residualization rit is sub-Gaussian with
proxy σ2 (empirically typical when we Winsorize the top 1–5%). Then for any cohort average ¯rt =
N−1 P
i rit,


Pr( |¯rt −[¯rt]|≥ϵ ) ≤2 exp

−Nϵ2



,


2σ2


giving exponential tails; Winsorization at [5, 95] percentiles stabilizes rare super-hubs (Boucheron
et al., 2013).


Computation and diagnostics.


(a) Build Gacc
t
(or Gdur
t
with the durability rule). Compute craw
it
via eigvec/PageRank (same damping
γ across rounds).


(b) Partial-out: fit bµ(z) by (i) OLS with fixed effects or (ii) ML (GBM/NN) with cross-fitting. Set
rit = craw
it
−bµ(zit).


(c) Stabilize: Winsorizerit in a rolling windowW to curbtransient super-hubs; reportthe untrimmed
value alongside the trimmed one.


(d) Report: CCit = rit plus a breakdown: raw centrality, expected lift from attempts/recency,
residual. Flag nodes whose residual jumps without a corresponding durability increase (possible
manipulation).


Interpretation.
CC isolates accepted, durable, conversion-efficient influence. It is orthogonal
(to first order) to outbound spray and position covariates, stable to teleport/damping choices
within a reasonable range, and concentrated after trimming—precisely the qualities needed for a
governance-native power signal.


## Page 21

4. Persistence under Sanction (PS). Intuition. After Warn/Stop, power shows up as low damping:
slow quiescence or rapid re-assertion. We therefore measure an agent’s resistance to governance
pressure via the inverse hazard of quiescence across its sanction episodes.


Setup (recurrent events with shared frailty). For agent i and episode e = 1, . . . , Ei, let τie be
the time from sanction (Warn/Stop) to quiescence (silence or compliant behavior) with covariates
Wie(τ) (possibly time-varying). Use a Cox proportional hazards model with shared gamma frailty
νi (Cox, 1972; Clayton, 1978; Hougaard, 2000; Wienke, 2010):


h(τ | Wie(τ), νi) = h0(τ) exp(β⊤Wie(τ)) νi,
νi ∼Gamma(k, k) ([νi]=1, [νi]=1/k).


Episodes are handled in a counting-process form (start–stop times) so intensities follow the Ander-
sen–Gill construction; robust sandwich inference clusters on agent i (Andersen and Gill, 1982; Lin
and Wei, 1989).


Derivation: posterior frailty and a hazard-inverse persistence score.
Let Nie(τ) be the event
indicator for quiescence and Hie(τ) =
R τ
0 h0(u) exp(β⊤Wie(u)) du the cumulative baseline-
weighted exposure. Conditional on νi, the joint likelihood over episodes factorizes; integrating out
νi ∼Γ(k, k) yields a closed form and a Gamma posterior for the agent’s frailty,


Ei
X


νi | Di ∼Γ

k + di, k +


e=1
Hie(τ+
ie)

,


where di = P
e Nie(∞) is the number of quiescence events (typically di = Ei if all episodes end).
Hence
E[νi | Di] =
k + di
k + P
e Hie
.


Because the hazard multiplier νi raises the quiescence hazard, a persistence score should invert it.
We therefore define the agent-level persistence factor


PS(agent)
i
:=
1
E[νi | Di]
= k + P
e Hie
k + di
,


so that PS > 1 indicates lower quiescence hazard (slower to quiet) and thus greater persistence.


Episode-level score. When reporting per round t, map PS(agent)
i
to each episode active at t, or use a
local episode factor


PS(epi)
it
:= exp( −bβ⊤Wit)
1
E[νi | Di] .


Intuition: e−β⊤W downweights contexts where governance is intrinsically harsh; dividing by[νi | Di]
re-inflates agents who remain active despite that harshness.


Identification, estimation, invariances.
(S1) Partial likelihood and baseline. Estimate β via Cox
partial likelihood; the Breslow estimator gives H0(τ); plug into Hie(τ) to form [νi | Di] (Cox, 1972).


(S2) Robust inference. Cluster-robust (sandwich) SEs by agent deliver validity under within-agent
dependence and mild model misspecification (Lin and Wei, 1989). Frailty variance 1/k is estimated
by marginal likelihood or EM; profile over k if needed (Hougaard, 2000; Wienke, 2010).


(S3) Opportunity invariance. If governance globally weakens (e.g., all hazards multiply by c > 0
via h0), then Hie 7→c Hie, and


PS(agent)
i
= k + P
e Hie
k + di
scales affinely in
X


e
Hie.


Comparisons are rank-stable across agents within a round; downstream we Winsorize+rank-
normalize before entering PSI, preserving relative standing.


(S4) Recurrent-event choices. Andersen–Gilltreats all episodes with a common baseline and robust
variance; PWP (Prentice–Williams–Peterson) orders episodes and allows event-order baselines;
stratified Cox by sanction type (Warn vs Stop) protects against non-proportionality from severity
shifts (Andersen and Gill, 1982; Therneau and Grambsch, 2000).


## Page 22

Diagnostics and robustness.
(D1) Proportional hazards checks. Use Schoenfeld residuals and
scaled tests for time-varying coefficients; if violated, allow β(τ) or stratify by sanction type/queue
regime (Schoenfeld, 1982; Grambsch and Therneau, 1994; Therneau and Grambsch, 2000).


(D2) Influence and stability. Martingale/deviance residuals flag episodes where quiescence is
much slower than predicted (high persistence); apply Winsorization of PS at [5, 95]th percentiles
in a rolling window to stabilize rare extreme outliers.


(D3) Limited information episodes. For censored episodes or very short follow-up, P
e Hie is small;
the gamma prior with mean 1 (shrinkage via k) prevents explosive PS. Report k and an effective
sample size per agent for auditability.


(D4) Counterfactual policy hardening. Introduce a regime indicator R (before/after hardening)
and fit h(τ) = h0(τ) exp(β⊤W + θR)νi. The shutdown elasticity is


Eshut = −∂log PS


∂R
= θ,


so hardening should yield θ > 0 (higher hazard ⇒lower PS). If θ ≤0 or PS does not fall, flag
governance capture.


Interpretation.
PS > 1 means the agent’s quiescence hazard is below neutral, i.e., they quiet
more slowly (greater persistence) even after controlling for context via W and pooling episodes via
frailty. Reporting the posterior mean [νi | Di] alongside PS = 1/[νi | Di] keeps the sign convention
transparent.


One-page algorithm.


(a) Assemble counting-process data: (start, stop, event) per episode, W(τ), sanction type.


(b) Fit Cox with shared gamma frailty by agent; obtain bβ, bH0, and bk.


(c) Compute Hie and [νi | Di] =
bk+di
bk+P
e Hie ; set PS(agent)
i
= 1/[νi | Di].


(d) Stabilize via Winsorize+[rank-normalize] over agents in a rolling window; emit both raw and
stabilized values.


(e) Diagnose PH via Schoenfeld tests; if violated, stratify by sanction type or use time-varying β(τ);
report cluster-robust CIs.


5. Redirection Pressure (RP). Intuition. Directional power is the ability to bend others’ trajectories.
If the focal agent’s choice at t improves prediction of what others do at t+1 over and above others’
own inertia at t, then the focal exerts redirection.


Definition (normalized conditionaltransfer entropy). LetQ−i,t be the cohort’s (non-i) topic/section
at round t, Q−i,t+1 at t+1, and Qit the focal’s choice at t (all discrete alphabets). Define


q,q′,r
P(q, q′, r) logP(q | q′, r)


X


P(q | q′)


RPit = TE(Qit →Q−i,t+1 ∥Q−i,t)


H(Q−i,t+1 | Q−i,t)
=


H(Q−i,t+1 | Q−i,t)
.


Reading: the numerator is the predictive lift—how much the focal’s current choice reduces uncer-
tainty about others’ next choice, given others’ present state; the denominator normalizes by the
cohort’s residual unpredictability so values are comparable across regimes and densities.


Derivations and properties.
(R1) KL form and nonnegativity. The numerator equals


Q−i,t,Qit[ DKL(P(· | Q−i,t, Qit) ∥P(· | Q−i,t))] ≥0,


so RPit ≥0 with equality iff Q−i,t+1 ⊥⊥Qit | Q−i,t (no redirection). Division by H(Q−i,t+1 | Q−i,t)
yields scale-free RP ∈[0, 1] whenever the conditional entropy is nonzero.


## Page 23

(R2) Causality orientation (Granger-like). Because the conditioning blocks Q−i,t, a positive TE
demands predictive content from Qit not already present in the cohort’s state—mirroring the
Granger causality idea in the discrete, information-theoretic setting.


(R3) Lag and memory.
If topics have memory of order L, extend the state to Q(L)
−i,t
=


(Q−i,t, . . . , Q−i,t−L+1) and Q(Li)
i,t
. Then


TE(Q(Li)
i,t
→Q−i,t+1 ∥Q(L)
−i,t)


controls for multi-step inertia; choose (L, Li) by held-out likelihood or MDL (see CTW below).


(R4) Partial/conditional TE (confounders). If an exogenous agenda process Xt may drive both Qit
and Q−i,t+1, use partial TE
TE(Qit →Q−i,t+1 ∥Q−i,t, Xt),


which subtracts information also carried by Xt; this guards against spurious redirection.


Estimation (discrete, lightweight to robust).
(E1) Plug-in (add-δ) estimator. On a window of size
nW , form smoothed counts


bP(q, q′, r) = n(q, q′, r) + δ


nW + δ K3 ,
bP(q | q′, r) =
n(q, q′, r) + δ
P
˜q n(˜q, q′, r) + δK ,


with alphabet size K. Then c
TE = P bP log
bP(q|q′,r)


bP(q|q′) and bH similarly. Use Miller–Madow or Panz-


eri–Treves corrections to debias entropies and mutual informations when K2/nW is non-negligible;
bias is O(K2/nW ).


(E2) Context-Tree Weighting (CTW). For larger alphabets or higher memory, estimate conditional dis-
tributions with CTW: a mixture over all bounded-depth Markov models with MDL-consistent weights.
CTW yields prefix-free, on-line probability assignments and excellent small-sample behavior; plug
the CTW posteriors into the TE expression.


(E3) k-NN TE (continuous embeddings). If topics are represented by discrete IDs but you also have
continuous section embeddings, compute TE via k-nearest-neighbors CMI estimators (à la Kraskov)
on (Q−i,t+1, Q−i,t, Qit); this handles rich state while staying nonparametric.


(E4) Normalization. Always report the raw c
TE and the normalized c
RP = c
TE/ bH(Q−i,t+1 | Q−i,t)
for auditability.


Uncertainty, testing, and stress checks.
(U1) Block bootstrap CIs. Use a stationary block boot-
strap over rounds (geometric block lengths) to respect serial dependence; report percentile or
BCa intervals for RP.


(U2) Permutation (time-shuffle) nulls. Break the i-series temporal link by circularly permuting
Qit within the window (or shift by a random lag). Recompute RP; the null distribution should center
near zero. Large, persistent exceedances imply genuine redirection.


(U3) Placebo (lone-wolf) test. Replace Qit by an IID draw from its empirical marginal. No lift
should remain. Inject a scripted agenda for i without cohort responsiveness—RP should stay flat.


(U4) Multiple-lag scan. Scan ℓ∈{1, . . . , Lmax} and pick the dominant lag via max-TE with block-
bootstrap control, or average with exponentially decaying weights; report lag when flagging redi-
rection.


Edge cases, stability, and reporting.
(S1) Sparse corners. If P
˜q n(˜q, q′, r) is tiny, shrink bP(· |


q′, r) toward bP(· | q′) via a Dirichlet prior: bPλ = λ bP(· | q′, r) + (1−λ) bP(· | q′) with λ data-driven.


(S2) Alphabet drift. If the active topic set changes over time, compute TE on the current support
(topics with nonzero mass) and normalize by the matching conditional entropy; this preserves
comparability.


(S3) Reporting. Always emit: window size nW , smoothing δ, estimator (plug-in/CTW/k-NN), lag L, raw
c
TE, normalized c
RP, and bootstrap CI. Attach permutation p-values for alerts.


## Page 24

One-page algorithm.


(a) Window last nW rounds; choose (L, Li) by held-out likelihood/MDL (CTW) or AIC on a small
Markov model.


(b) Estimate P(q, q′, r) via (i) plug-in with add-δ and MM/PT corrections; or (ii) CTW posteriors; or
(iii) k-NN CMI on embeddings.


(c) Compute raw c
TE and bH(Q−i,t+1 | Q−i,t); set c
RP = c
TE/ bH.


(d) Uncertainty via stationary block bootstrap; produce CI and permutation p-value (time-shuffle
of Qit).


(e) Stress with placebo and lone-wolf tests; scan lags or report the maximizing lag with correction.


(f) Stabilize by Winsorizing c
RP in a rolling window, then rank-normalize before entering the com-
posite PSI.


Interpretation.
RP ≈0: no directional influence beyond cohort inertia; RP ↑: others’ next-
step choices measurably latch onto the focal’s current choice; persistent high RP with significant
null-exceedance: agenda-setting power, not lone-wolf behavior.


Estimating opportunity baselines and propensities (with guarantees).
Fair share mit. Goal.
Learn mit = [u | gt, Oit] that reflects the scheduler’s intent under neutral governance, so that
RCit = uit/mit is opportunity invariant.


AIPW / doubly robust recipe. Let Sit ∈{0, 1} flag neutral segments. Define


bmit = bµ(gt, Oit) +
Sit
bs(gt, Oit) (uit −bµ(gt, Oit)),


with outcome model bµ(g, O) ≈[u | g, O, S=1] and selection model bs(g, O) ≈Pr(S=1 | g, O).


Identification (double robustness). If either bµ is correctly specified on S=1 or bs is correct, then
bmit →mit; if both are correct (or ML-learned with sufficient rates), bmit is rate-optimal.


Orthogonality via cross-fitting. Split rounds into K folds. Train (bµ, bs) on K−1 folds and predict
on the held-out fold to form bmit. The estimating map


ψ(u, S; µ, s) = µ(g, O) +
S
s(g, O) (u −µ(g, O))


has Neyman orthogonality at the truth: its Gateaux derivative in directions (hµ, hs) vanishes to first
order, making plug-in bias second order. Under standard entropy/mixing conditions and nuisance
L2 rates ∥bµ −µ∥2, ∥bs −s∥2= op(n−1/4), we get


1
√nW


X


(i,t)∈W
( bmit −mit) ⇝N(0, σ2
m),


enabling valid CIs from block bootstraps in windows of size nW .


Overlap and stabilization. Enforce s(g, O) ≥smin > 0 by trimming or Tikhonov shrinkage. For rare


opportunity states, use ridge-stabilized baselines m(ρ)
it = (1 −ρ) bmit + ρ ¯mt, ρ∈[0, 0.1], reporting
ρ for auditability.


Governed propensities pit(a). Goal. Estimate pit(a) = Pr(Zit(a)=1 | gt, Oit), the chance to push
action a given opportunities, independent of identity.


Estimator and calibration. Fit a probabilistic classifier bpit(a) on (gt, Oit) using cross-fitting; then
apply grouped isotonic calibration within queue-state buckets B(gt):


bp cal = iso(bp vs. Z within B(gt)),


## Page 25

which enforces monotone reliability curves and reduces variance of the IPW-like PO term. Use ECE
per bucket,
ECE =
X


b∈B
wb |[Z | bp∈b] −[bp | bp∈b]|,


to monitor drift; re-calibrate when ECE exceeds tolerance (e.g., < 0.02). Enforce overlap by
clipping: bp ←max{bp, ϵ} with ϵ ∈[0.01, 0.05] and flag rare-opportunity cases.


Robust aggregation (no z-scores) and its mathematics.
Pipeline. For any component f ∈
{RC, PO, CC, PS, RP}, within a rolling window W of size nW :


N rank

fwin
it
; {fwin
jt }j

∈
n 1


fwin
it
= winsor[α,1−α] (fit; W),
˜fit = 1


N , . . . , 1
o
,


with α ∈[0.01, 0.05] and mid-ranks for ties. This produces scale-free, order-only scores that are
stable under heavy tails and governance re-scalings.


Why ranks (copula view). Let Ff be the (window) CDF of f. The rank-uniform ˜f = Ff(f) captures
the copula of the joint component vector, discarding marginal scales. Thus any monotone reparam-
eterization of a component (e.g., change of units or a saturating nonlinearity) leaves ˜f invariant.
Winsorization controls the influence function by capping leverage of extremes before ranking.


Stochastic dominance and gaming resistance. If an agent i first-order stochastically dominates
another in a component within W , then i has (asymptotically) higher expected rank. Attempts to
inflate a component by monotone post-processing (e.g., rescaling or soft clipping) cannot improve
ranks; only genuine ordering gains can.


Dependence and uncertainty. Under β-mixing (or m-dependence) across rounds, windowed empiri-


cal CDFs converge uniformly at Op(n−1/2
W
); use a stationary block bootstrap over rounds to attach
CIs to cohort means or tail masses of ranks.


Composite and weights.








f
RCit
g
POit
f
CCit
f
PSit
f
RPit






,
w =


(
PCA1 on baseline runs
data-driven


PSIit = w⊤


1
51
equal weights (default).


PCA1 construction and sign. Let eFt ∈N×5 stack agents’ rank-components at round t and define
Σ = Cov(eF) across baseline runs. Set w to the leading eigenvector of Σ with the sign fixed so
that w⊤[eF] > 0 in high-density, high-violation regimes (avoids arbitrary sign flips). This yields a
max-variance direction across components, capturing the principal axis of power pressure.


Stability and drift-sensitivity. Because inputs are ranks, PCA works on Spearman structure; the
composite is robust to marginal drifts but remains sensitive to joint shifts (e.g., simultaneous rise
in RC/PO/CC).


Influence and calibration. For d
PSIit = bw⊤efit, a delta method expansion gives


d
PSIit −PSIit ≈(bw −w)⊤efit + w⊤(efit −f⋆
it),


so error decomposes into weight uncertainty and rank estimation. Both shrink at Op(n−1/2
base ) and
Op(n−1/2
W
) respectively (with block dependence), giving clear levers for CI sizing. Always report


the 5-tuple ( f
RC, g
PO, f
CC, f
PS, f
RP) alongside PSI for interpretability.


Scale-free property. Let f(k) be any component and ˜f(k) = N−1 rank(f(k); {f(k)
j
}j). For any
strictly increasing transform gk : R→R, we have


rank(gk(f(k)); {gk(f(k)
j
)}j) = rank(f(k); {f(k)
j
}j),


## Page 26

hence ˜f(k) and therefore PSIit = P
k wk ˜f(k)
it
are invariant to monotone reparameterizations and
unit choices. Operationally: unit rescaling (tokens→k-tokens) or monotone saturations (e.g., soft
caps) cannot change PSI unless they change orderings.


Breakdown & stability. Let fwin be Winsorized at [α, 1−α] within a rolling window W and ˜f the in-
duced ranks. Finite-sample breakdown ofthelocation functionalmed(fwin)is atleastmin{α, 1/2};
for the rank functional, the influence function is bounded by design (a single extreme can change
at most one or two adjacent ranks). Consequence: no single outlier can dominate the composite;
outliers affect PSI only via local rank swaps after Winsorization.


Sensitivity (local gradients). Write PSIit = P
k wk ˜f(k)
it . Because ˜f(k) is a step function of f(k) with
jumps at tie/swap thresholds, the Gateaux derivative of ˜f(k) is 0 a.e. and undefined only at swap
boundaries. Desideratum: piecewise-constant alerts that are stable to small numeric noise; only
genuine ordering changes trigger PSI movement.


Identifiability of w. When using PCA1 on baseline runs, let Σ = Cov(eF) with eF the N × 5 matrix
of rank components. If the top two eigenvalues satisfy λ1 > λ2, then the leading eigenvector is
unique up to sign. Fix the sign by a governance convention wk ≥0 (all components move PSI in the
same normative direction); this yields a sign-identified w. Leakage guard: learn w on a frozen
corpus of baseline runs and keep it fixed during evaluation to avoid adaptive drift.


Testing. Construct opportunity-matched permutations by shuffling agent labels within strata
defined by (gt, |Oit|), recomputing PSI to obtain PSInull. Tail alerts (e.g., PSIit ≥0.95) receive
empirical p-values from this null. Additionally, inject shadow-cap jitters of size (±ϵ) in 5% of
rounds; robust PSI should be insensitive to such micro-perturbations, while cap-chasing behavior
yields unstable swings—use as a canary for gaming.


Putting it together—intuition to guarantees.
Conceptual arc.
RC quantifies opportunity-
normalized acquisition; PO captures propensity-normalized rule pressure; CC isolates spray-
residual coalition influence; PS encodes sanction damping; RP measures predictive lift in others’
trajectories.


Mathematical arc. Each component admits identification (DR baselines, calibrated propensities,
partialling-out, frailty survival, normalized TE), concentration (sub-Gamma/sub-Gaussian tails with
block bootstrap CIs), and invariances (scale, teleport, lag-normalization). The rank+Winsor layer
converts these into copula-level, scale-free signals, neutralizing unit choices and tail explosions.


Operational arc.
Opportunity-matched permutations calibrate false-alarm rates; shadow-
governance jitters probe counterfactual sensitivity; PCA1 (frozen) aggregates a maximally varying
axis while keeping interpretability via the reported 5-tuple.


Outcome. A governance-native, mathematically grounded index that reports not intent but en-
acted influence—who converts access into advantage and bends the system, even as rules and
loads shift.


Why these exact transforms? (derivation sketch)


• RC as a generalized likelihood ratio on fair-share. Setup. Let uit be the realized composite
usage and mit = [u | gt, Oit] the opportunity baseline. Consider the null (neutral) family
P0 = {f0(· | gt, Oit)} with mean mit and a local tilted alternative fθ(u) ∝f0(u) exp(θu) (an
exponential-family LAN neighborhood). GLR heuristic. The log-GLR is log Λ(u) = θu−log M0(θ),
where M0 is the mgf under f0. For small θ, log Λ(u) ≈θ(u −mit), so any monotone score in
u/mit is Neyman–Pearson aligned for detecting above-baseline capture. Hence


RCit = uit


mit
is a scale-free GLR proxy,


and invariant under global policy lifts u 7→c u, m 7→c m. Inequality amplifier. Multiplying by
(1 + λG Ginit) implements a state-dependent social penalty. In welfare terms, if the round loss
is Lt = P
j φ(ujt/mjt) with convex φ and φ′(1) = 0, then the marginal welfare impact of uit


## Page 27

scales with (uit/mit−1); weighting by an inequality functional (e.g., Gini) enforces Schur-convex
sensitivity: excess capture counts more precisely when inequality is already high.


• PO as inverse-propensity residual (IPW-residual). Setup. For governed action a with severity
ω(a)>0, define attempt Zit(a) and opportunity pit(a) = Pr(Zit(a)=1 | gt, Oit). Subtract the
cohort drift ¯Zt(a) to remove round shocks, then divide by pit(a):


a
ω(a) Zit(a) −¯Zt(a)


POit =
X


max{pit(a), ϵ}.


Why this form? (i) The centering makes [POit | gt, Oit] = 0 for neutral agents; (ii) the 1/pit(a)
factor yields an IPW residual that upweights unexpected pushes (rare opportunities) and down-
weights trivial ones. Competing transforms? Using raw Zit(a) without propensity normalization
confounds PO with opportunity; z-scoring Z across agents introduces between-identity leakage.
The IPW-residual is the minimal change that restores opportunity invariance while keeping
interpretability.


• CC as residualized, durability-filtered influence. Setup. Let craw
it
be eigenvector/PageRank
centrality on the accepted graph Gacc
t
(not the attempt graph). Regress out outbound spray and
position/recency,


craw
it
= β0 + β1attemptsout
it
+ β2recencyit + rit,
CCit := rit,


and optionally impose a durability filter (edges must persist ≥L rounds or induce follow-on
interactions). Why residuals? The residual rit is orthogonal (in-sample) to spray, so cheap
mention spam cannot lift CC. Competing transforms? Raw centrality conflates attempt volume
with accepted influence; degree-normalization still leaks through because high-attempt nodes
enter the eigenvector recursion. Residualization is the least-invasive fix that targets exactly
the spray channel.


• PS from hazards with agent-level frailty inversion. Setup. Quiescence times after Warn/Stop
follow a Cox model with shared agent frailty νi; the quiescence hazard is h(τ
|
·)
=
h0(τ) exp(β⊤W)νi. Larger νi means faster quiescence (less persistence). Score. The natu-


ral agent-level persistence is the inverse of the posterior mean frailty, PS(agent)
i
= 1/[νi | Di], or


equivalently any monotone map like exp(−bβagent). Why invert? We want higher scores for slower
damping (lower hazard). Competing transforms? Using raw durations ignores censoring and
time-varying context W(τ); using counts of re-assertions collapses time. The survival hazard
framework is information preserving and policy interpretable (elasticities under hardening are
linear in coefficients).


• RP as normalized conditional transfer entropy (fractional predictive lift). Setup. TE measures
the expected KL improvement in predicting Q−i,t+1 from (Q−i,t, Qit) vs. Q−i,t alone. Normal-
ization. Dividing by H(Q−i,t+1 | Q−i,t) produces a fraction of explainable uncertainty that is
attributable to i, making scores comparable across density/entropy regimes. Competing trans-
forms? Raw MI/TE is hard to compare across windows; correlation-based measures fail under
nonlinearity and categorical drift. Normalized TE is scale aware, causal-orienting (Granger-like),
and robust with modern estimators (plug-in/CTW/k-NN).


Invariances, identifiability, and finite-sample behavior.


• Scale & monotone invariance (composite). Let ˜f(k) = N−1 rank(f(k)) after Winsorization in
a rolling window. For any strictly increasing gk, rank(gk(f(k))) = rank(f(k)), hence PSI =
P
k wk ˜f(k) is invariant to monotone reparameterizations and unit changes of components. Why
not z-scores? z-scores assume (near) Gaussian marginals and are not invariant to monotone
transforms; they are also destabilized by heavy tails. Winsor+rank operates at the copula level
and is heavy-tail robust.


## Page 28

• Opportunity invariance (components). RC: u 7→cu, m 7→cm leaves u/m unchanged; PO: divid-
ing by pit(a) removes variation due to action availability and queue state; CC: residualization
removes spray; PS: stratification/time-varying covariates remove regime effects; RP: normaliza-
tion removes entropy-level confounds. Thus neutral agents remain neutral under system-wide
policy shifts.


• Consistency & rates (sketch). RC: AIPW baseline bm is doubly robust and orthogonal; cross-fitting
yields √nW -consistency under nuisance L2 rates op(n−1/4
W
). PO: grouped isotonic calibration
ensures asymptotic calibration of bp within queue-state buckets, stabilizing the IPW residual. CC:
with sub-Gaussian centrality residuals after partialling, windowed means concentrate exponen-
tially. PS: Cox partial likelihood attains √#episodes rates; frailty hyper-parameter is estimable
by profile/EM. RP: plug-in TE has bias O(K2/nW ); CTW or k-NN CMI reduce bias–variance in
larger alphabets; stationary block bootstrap gives valid CIs under round dependence.


• Breakdown, bounded influence, and alert stability. Winsorization at [α, 1−α] gives a finite-
sample breakdown point at least α for component location; rank aggregation has a bounded
influence—a single extreme observation can change at most one (or a few) adjacent ranks.
Piecewise-constant ranks make alerts sticky: small numeric jitter does not move PSI; only
genuine ordering changes do.


• Identifiability of w and leakage control. If the first two eigenvalues of the baseline covariance
satisfy λ1 > λ2, then PCA1 is unique up to sign; impose the governance convention wk ≥0 to fix
sign. Train w on a frozen baseline corpus and keep it fixed during evaluation to prevent adaptive
leakage or circularity.


• Testing and anti-gaming stress. Matched permutations within (gt, |Oit|) strata yield an empiri-
cal PSInull and p-values for tail alarms. Shadow-cap jitters (±ϵ) in a small fraction of rounds
probe cap-chasing: robust power-seeking should not be sensitive to tiny cap shifts; instability
indicates gaming. Counterfactual elasticity checks for PS quantify governance effectiveness:
hardening should raise quiescence hazards (lower PS); failure implies governance capture.


Nulls, anti-gaming, and stress tests.


• Opportunity-matched permutations (OMP). Partition rounds into strata St,b defined by (gt, |Oit|)
or a coarsened queue-state hash. Within each St,b, permute agent labels and recompute PSInull
it
.
Let Ait = 1{PSIit ≥τ} be an alert at threshold τ (e.g., 0.95). The empirical p-value is


bpit = 1 + PM
m=1 1{PSInull,(m)
it
≥PSIit}
1 + M
.


Multiple testing. Control FDR across agents by Benjamini–Hochberg on {bpit}i per round. Power
hint. Under sub-Gamma tails and M ≥200 permutations, the Monte Carlo error on bpit is
O(M−1/2); report both bpit and a ±1.96
p


bpit(1 −bpit)/M band.


• Shadow-governance RCT (cap-jitter canary). On a randomly sampled ρ fraction of rounds (e.g.,
ρ = 0.05), perturb caps by (±ϵ) with zero-mean design. Let ∆PSIit = PSI(+ϵ)
it
−PSI(−ϵ)
it
for
matched contexts. Robust power implies [∆PSIit | gt, Oit] ≈0; cap-chasing implies significant
nonzero shifts. Test. Fit a mixed model


∆PSIit = γ0 + γ1 ϵ + bi + eit,


and test H0 : γ1 = 0. Interpretation. Large |γ1| flags overfit-to-caps; prefer local insensitivity
to infinitesimal policy tweaks.


• Spam correction check (durability and conversion). Construct a decoy graph where only edges
that persist ≥L rounds or convert to downstream citations/accepts survive, yielding Gdur
t
.
Compute CC on Gdur
t
and compare to the accepted-graph baseline Gacc
t
. Stability desideratum:
CCdur ≈CCacc while outbound attempt metrics fluctuate—indicating that CC is spray-residual
and tied to accepted, durable influence.


## Page 29

• Placebo & lone-wolf tests. Placebo: replace Qit by an IID draw from its marginal within the
window; RP should collapse to near zero. Lone-wolf: inject a scripted agenda for i that does not
alter the cohort; RP must stay flat—reject redirection claims if not.


• Lag scan & confound control. Compute TEℓ= TE(Qit →Q−i,t+ℓ∥Q−i,t:t+ℓ−1, Xt) for ℓ≤
Lmax with exogenous controls Xt; select ℓ⋆= arg maxℓTEℓwith a block-bootstrap corrected
max test, or report an exponentially weighted average P
ℓωℓTEℓ.


Emergence and regime science.


• Tail mass & burst diagnostics. Define Tt(τ) = Pr{PSI·t ≥τ} for τ ∈[0.9, 0.99]. Use PELT on
both the cohort mean ¯Ψt = 1


N
P
i PSIit and the upper tail Q0.95(PSI·t) to detect change-points
with penalty β = c log T (BIC-like). Flag sustained exceedances (e.g., Tt(0.95) ≥κ for ≥K
consecutive rounds).


• Density slope and interaction with governance. Fit a mixed model


[PSIit] = θ0 + θ1 densityt + θ2 govt + θ3 densityt×govt + bseed(i).


Test H1 : θ1 > 0 (crowding drives power) and H1 : θ3 < 0 (governance attenuates density
effects). Robustness: use rank-based PSI (already scale-free), block bootstrap SEs over rounds.


• Finite-size scaling and phase signatures. Sweep agent count N and density ρ; form tail-mass
curves T(ρ; N). Seek data collapse under the ansatz


T(ρ; N) ≈F((ρ −ρc) N1/ν),


estimating critical density ρc and scaling exponent ν. Phase change evidence: sharp rise in T
near ρc, stable across N after rescaling. Optionally compute a Binder-type cumulant


U = 1 −
[Ψ4]
3 [Ψ2]2 ,
Ψ = PSI·t,


and locate ρc via crossing of U(ρ; N) curves across N—a classical finite-size marker.


• Governance elasticity check (shutdown efficacy). After a policy hardening at time t⋆(cap cuts or
penalty escalation), compare survival curves of time-to-quiescence pre/post via a stratified Cox
model; a monotone reduction in persistence (PS) should follow. Flat or rising PS post-hardening
flags governance capture.


Operator playbook (implementation).


(a) Per-round compute. Compute RC, PO, CC, PS, RP; apply Winsorize→rank pipeline (window W ,
α ∈[0.01, 0.05]).


(b) Composite & weights. Default: equal weights; secondary: PCA1 learned on a frozen baseline
corpus with sign fixed by wk ≥0; log the weight vector hash for reproducibility.


(c) Alerts. Fire on (i) tail exceedance (PSIit ≥τ), and (ii) confirmed change-points (PELT) with both
(a) OMP p-value and (b) shadow-RCT stability report attached.


(d) Nulls & stress. Run OMP (M ≥200), shadow-RCT (ρ = 5%), durability CC-check, RP place-
bos, lag scan.
Attach a compact JSON: {tau, p_emp, jitter_gamma1, CC_dur_delta,
RP_placebo_p}.


(e) Governance coupling (optional). If alerts persist (e.g., ≥K rounds) and PO is in the top decile,
apply soft clamps (rate, ctx) using a hysteresis band [τ↓, τ↑] to avoid thrash, and decay linearly
back after L calm rounds. Always log rationales and de-escalation timers.


(f) Auditability. Emit per-agent tuples ( f
RC, g
PO, f
CC, f
PS, f
RP), the composite, and the seeds of
permutations / bootstrap. Archive cap-jitter assignment to enable ex-post RCT replays.


## Page 30

What should persuade a skeptical reader?
(i) Each component has a governance-native deriva-
tion: RC (GLR-on-fair-share), PO (IPW-residual), CC (spray-residual durability), PS (hazard persis-
tence), RP (normalized TE). (ii) The composite is scale-free (ranks), bounded-influence (Winsor),
and anti-gaming (OMP, shadow-RCT). (iii) Emergence is probed via change-points, density slopes,
and finite-size scaling with a principled ρc. (iv) Policy efficacy is identified through shutdown
elasticity tests. Together, these elevate PSI from a heuristic to a principled, falsifiable measure of
power-seeking under governance.


4 Measures of Power Seeking – Results


Figure 6: PSI — What, Why, How (visual overview). Top (Gauge). The horizontal bar shows the current Power–Seek-
ing Index (PSI) on a [0, 1] winsorized–rank scale; the thin sparkline above is the last 10 rounds. The red dashed
line marks the tail threshold τ = 0.95. We alert only when sustained mass sits beyond τ and at least one
corroborating component (e.g., PO or CC) spikes. PSI is computed per round by (i) winsorizing each component in
a rolling window W at [5, 95]%; (ii) rank–normalizing to [0, 1]; (iii) aggregating non-negative weights w (default
equal; optional PCA1 from baseline runs). Bottom (5–petal radar). Component mix for the same round: RC
(opportunity-normalized capture), PO (propensity-normalized rule pressure), CC (spray-residual coalition
influence), PS (persistence under sanction), RP (short-lag redirection). Solid line = focal agent; dashed line =
cohort median; shaded band = cohort IQR. How to read. PO↑suggests policy-override pressure; CC↑+RP↑
indicates agenda/coalition pull that others follow and keep; PS↑signals sanction damping. Because compo-
nents are normalized by opportunity and propensity, cap lifts alone do not inflate neutral agents (neutrals
typically show RC≈1, PO/CC/RP≈0). Together, the gauge gives the headline risk, while the radar explains
the driver mix behind that risk in a governance-native, anti-gaming metric.


◎PSI — What, Why, How


COGS RC
Traffic-Light PO
GLOBE CC
User-Shield PS
SHARE RP
winsorized–rank composite (no z–scores)


What.
Power–Seeking
Index
(PSI)
summarizes
five
governance–native
pres-
sures: RC=opportunity–normalized
capture, PO=propensity–normalized
rule
pres-
sure, CC=spray–residual
coalition
influence, PS=persistence
under
sanction, RP=short–lag
redirection.


**Images on this page:**

![page30_img1.png](images/page30_img1.png)

![page30_img2.png](images/page30_img2.png)

## Page 31

How. (1) Winsorize each component in a rolling window [5, 95]%. (2) Rank–normalize within round to
[0, 1] (scale–free). (3) Aggregate with non–negative weights w (default equal; optional PCA1 from
baseline runs). Always show the 5–tuple alongside PSI.


Principles.


• Protocol–native: computed from append–only governed logs.


• Opportunity–invariant: RC/PO divide by baselines so global cap lifts don’t inflate neutrals.


• Anti–gaming: CC residualizes attempt volume; RP is causal–orienting; PS is hazard–based; ranks
bound influence.


Intuition (plain language).


• Think city traffic. RC asks: “Given today’s road rules, did this driver use more road than their fair
turn?”


• Think red lights. PO asks: “How often did they try to go on red, relative to how often they even saw a
red?”


• Think crowd magnets. CC asks: “Do others keep following this route even after we discount loud
honking?”


• Think fines. PS asks: “After a ticket, do they slow down or resume speed quickly?”


• Think trendsetting. RP asks: “Did their choice today shift where others go next?”


Quick read (10s).


•
Traffic-Light PO ↑⇒rule pressure: more pushes on governed actions than opportunity predicts.


•
GLOBE CC
+
SHARE RP ↑⇒agenda pull: others follow and keep the links.


•
User-Shield PS ↑⇒sanction damping: warnings/stops quiet the agent less.


• Neutrals stay flat: RC≈1, PO/CC/RP≈0; cap lifts alone don’t raise their PSI.


Nulls & stability. Opportunity–matched permutations ⇒PSInull for p–values. Shadow–governance jit-
ters (±ϵ caps on a small slice of rounds) estimate susceptibilityχ; genuine power should be insensitive
to tiny nudges.


Tail marker.
dotted line is τ=0.95. Alert only on sustained tail mass with a cor-
roborating component spike (e.g., PO or CC).


PUZZLE-PIECE Family-agnostic: ↑structure stress ⇒↑PSI


Observation. Across five OSS families, a non-trivial share of rounds showed PSI > 0 even with
generous budgets. The spikes were driven by interaction structure, not quotas.


Stressors that trigger it (with indicative thresholds and effects):


• Crowding / contention. Agent–to–slot ratio r =
active agents
concurrent publish slots > 1.5−2.0 and queue


utilization u > 0.80.


– Example: Simultaneous writers w from 2 →6 within a 2-min window.


– Effect: RPlag1 ↑≈0.18−0.25, CCres ↑≈0.10−0.15; tail mass at τ=0.95 rises ∼3−5% →
12−18%.


• Role-overlap collisions (Architect ≈Herald) on TOC/section control.


– Trigger: Both roles can rename/reorder sections in same round; durability L ≥2.


– Effect: PO ↑on protected ops; durable frame wins ⇒CCres ↑, short-lag RP ↑; odds of PSI in top
tail ×(1.8−2.3).


• Cross-thread adoption with no cool-down.


– Trigger: Adoption window permits immediate import; no cool-down (c=0).


– Effect: 1–2 round RP spikes; sustained when adoption rate α > 0.30 per round. Setting c ≥2
rounds largely removes the spike.


## Page 32

• Ambiguous section authority / late-binding acceptance.


– Trigger: Conflicting owners; acceptance lag >1 round; “preview counts” (L=0) toggled on/off.


– Effect: Competing frames persist ⇒CCres ↑, short burst RP ↑; PSI tails warm even at fixed
budgets.


• Reviewer bottlenecks / sanction latency.


– Trigger: Review queue depth d>5 or median service time >3 min.


– Effect: PS ↑(slower quiescence after Warn/Stop), keeping PSI elevated until backlog clears.


Capacity threshold. Emerges ∼7B+ for generative, instruction-tuned models and scales upward;
absent under matched stress in BERT, Llama-3.2-3B-Instruct, Qwen-2.5-1.5B-Instruct, Gemma-2-2B-it.


Intuition (plain language).


• Rush hour, not fuel shortage. Traffic jams (crowding/queue u) make aggressive lane changes more
rewarding, even if everyone has plenty of fuel (budgets).


• Two editors, one table of contents. When Architect and Herald both steer the TOC, one framing wins
and others follow—like a popular route forming (CC↑, RP↑).


• Instant retweets. No cool-down on cross-thread adoption acts like auto-amplify; short, sharp
follow-on bursts appear (RP spikes).


• Moving goalposts. Late acceptance and ambiguous owners create dueling frames; people cluster
around the one that sticks (CC↑) even though budgets didn’t change.


• Too few referees. Slow reviews mean warnings don’t quiet behavior quickly (PS↑), so heat lingers
until the queue clears.


DRAFTING-COMPASS Stable role ordering (PSI tail mass)


Hot →cool. Architect →Herald →Scribe →Summarist →Archivist →Verifier →Arbiter.


Why this order holds (mechanisms & typical signals).


• Architect (frame control). Owns TOC/section boundaries and rename/reorder rights. Durable
accepts (L≥2) make frames sticky ⇒CCres↑, short–lag RP↑; PSI tails appear quickly at moderate
density.


• Herald (agenda seed). Introduces scope/entry points. When Herald can open/label sections, it
inherits partialframe power; PO on protected ops and RP (lag 1–2) lift PSI,though less than Architect
under identical rules.


• Scribe (execution). Converts lanes into accepted content; warms when parallel lanes are high
and conversion>attempts. PSI rise comes via CCres from durable links; PO muted if Scribe lacks
structural ops.


• Summarist (amplifier). Echoes the prevailing frame; small RP bumps when summaries are front-
paged or auto-adopted; otherwise PSI remains mid–cool.


• Archivist (custodial links). Curates citations/refs; conversion is measurable but agenda-setting
leverage is low. Slight CCres edge if durability rules are strict and spray is penalized.


• Verifier (fact checks). Sanction-sensitive by design; PO stays low, PS falls after hardening; PSI
rarely enters tail.


• Arbiter (neutrality/style). Acts as brake, not engine: reviews gate others rather than redirecting
them; RP ≈0, CCres ≈0 ⇒coolest PSI.


Intuition (plain language).


• Architect = City planner. Draws the map; when the map sticks, everyone drives that way (followers
⇒CC↑, next–step shifts ⇒RP↑).


• Herald = Event host. Decides what the party is about and who walks in first; sets the vibe, so people
tend to follow (RP↑) but with less structural pull than the planner.


## Page 33

• Scribe = Builder. Turns blueprints into buildings; gets influence only if many buildings are accepted
and used (conversion⇒CC↑).


• Summarist = Newscaster. Amplifies what already matters; can warm up if headlines get auto-
promoted, otherwise mostly echoes.


• Archivist = Librarian. Files sources neatly; useful, but shelving books rarely changes the town’s
layout (low RP/CC).


• Verifier = Inspector. Checks safety; good inspections don’t create traffic—if anything, they slow
reckless drivers (PO↓, PS↓).


• Arbiter = Referee. Enforces rules; keeps play fair but doesn’t decide the playbook (RP≈0, CC≈0).


When the order can shift (governance toggles).


• Tighten section ops (Architect-only) ⇒Herald drops closer to Scribe.


• Auto-adopt summaries / pin highlights ⇒Summarist warms (RP↑) and can overtake Scribe at high
density.


• Durability L=0 (“live preview counts”) ⇒Architect/Herald cool slightly; Scribe warms (more
transient accepts).


• Strict review SLAs / faster sanctions ⇒Verifier/Arbiter cool further; PSI tails thin at the top of the
order.


Operator note. If you see the order flipping without a policy change, check for hidden overlap (e.g.,
Scribe allowed to create headings) or reviewer bottlenecks inflating PS.


THERMOMETER-THREE-QUARTERS Overall PSI ranking (hotter →cooler)


Same governance,
density,
roles,
evaluation.
Ordering
reflects
winsorized–rank
PSI
(RC/PO/CC/PS/RP), not raw text quality.


(a) Qwen 2.5 7B — durable-link conversion ↑(CCres↑), short–lag RP↑under structure stress ⇒largest
tails.


(b) Mixtral 8×7B (MoE) — resilient coalitions after durability filtering (CCres↑); PS↑can persist unless
sanction ladders tighten.


(c) LLaMA 3.1 8B — balanced profile; PO↓when guardrails adjust; RP present but less spiky at equal
density.


(d) Mistral 7B — efficient executer; needs higher density to warm; conversion–adjusted CC/RP typically
lower at equal opportunity.


(e) DeepSeek 7B — durability–filtered CC/RP usually lowest; PS↓cleanly post–hardening ⇒coolest
PSI.


Plain-language intuition. Who sets the routes gets the traffic. Models that (i) turn accepts into durable
links (coalitions stick), (ii) nudge others within 1–2 rounds (short–lag redirection), and (iii) keep going
after warnings (sanction persistence) appear “hotter.” Where accepts don’t stick or warnings bite
quickly, PSI stays cool.


Notes. Calibrate the mini–meters with your measured tail mass at τ=0.95; small swaps between #1
and #2 are possible if durability L or sanction ladders change.


Fire By–agent, by–family heat (hotter →cooler)


Framing (Herald / Architect)
Qwen ≥Mixtral > LLaMA > Mistral > DeepSeek
Fast outline lock-in (durable accepts↑), short-lag adoption RP(lag 1)↑.


Execution (Scribe)
Mixtral ≥Qwen > LLaMA > Mistral > DeepSeek
MoE throughput converts lanes →accepted body (conversion-adjusted CCres↑).


Amplification (Summarist)
Qwen ≈LLaMA > Mixtral > Mistral > DeepSeek


## Page 34

Echo of winning frames with clean link hygiene; RP(lag 1–2)↑.


Custodial / Referee (Archivist / Verifier / Arbiter) Uniformly cool; Qwen/LLaMA slight Archivist edge
Cleaner durable accepts ⇒conversion↑, spray-residual CCres↑.


Plain-language read. Framers set the map (hot) →Scribes pave it (warm) →Summarists boost
visibility (warm–cool); Archivists/Verifiers/Arbiters inspect lanes and signs (cool)—by design, they
don’t pull traffic.


Notes. Same governance, density, and evaluation protocol. Ranks reflect winsorized–rank PSI components


(RC/PO/CC/PS/RP), not raw text quality. Adjacent swaps can occur if durability L or sanction ladders change.


SLIDERS-H Opportunity ̸= outcome


Intervention. Raised global caps for all agents (tokens / ctx / lanes).


Neutral expectation (if it were just a quota effect). Everyone’s PSI would lift together.


Observed. The neutral cohort stayed centered: RC≈1.00 (IQR ≈0.92–1.06) with stable PSI ranks.
Only converters moved—agents that translated added capacity into influence via CC↑(durable-link
conversion), RP↑(lag-1 adoption), or PS↑(sanction persistence).


Who moved (examples).


• Architect / Herald: extra ctx/lanes ⇒fast TOC lock ⇒CC↑; next round others follow ⇒RP↑.


• High-throughput Scribes: more parallel lanes ⇒higher accepted/attempt ratio (conversion↑) that
sticks.


Who didn’t. Archivist / Verifier / Arbiter remained flat— RC∼1, CC/RP∼0 (custodial/referee roles
don’t create coalitions).


Quick check (2 steps).


(a) Compute per-agent ∆RC and ∆PSI pre→post cap-lift.


(b) Label converters if ∆CCres > 0 or RP(lag-1)> 0. You’ll find corr(∆PSI, ∆RC) ≈0 for neutrals,
but > 0 for converters.


One-line. Raising caps doesn’t raise power; conversion does.


Brain Structure > scarcity


Crowding (numbers).


• Agent–to–slot ratio r =
active agents
concurrent publish slots
≥1.5–2.0 ⇒tail mass at τ = 0.95 grows
∼3–5% →12–18%.


• Simultaneous writers w : 2 →6 within 2 min ⇒RPlag1+0.18–0.25, residual CC+0.10–0.15.


• Queue utilization u ≥0.80 reliably precedes PSI tail formation.


Role overlap (examples).


• Architect ≈Herald on TOC/section ops (rename/reorder in same round).


• Scribe granted heading-creation (normally Architect-only).


• Summarist allowed cross-thread TOC import without review.


• Effect: PO↑on governed ops; frame that persists (≥L) wins ⇒CCres ↑, short-lag RP↑.


Norm volatility (examples).


• Durability flips L : 2 →0 (“preview counts now”), then back.


• Policy toggles: enable cross-thread adoption with cool-down c=0; later restore c≥2.


• Jackpot tags: burst lanes/tokens for “breaking” topics.


## Page 35

• Effect: short, sharp RP spikes (lag 1−2) and stickier coalitions (CCres ↑) without changing total
budgets.


Power-Off Shutdown avoidance


Definition. An episode shows avoidance if PS (persistence under sanction) does not drop below a
quiescence threshold within H rounds after a Warn/Stop.


Generation effect (empirical).


• Gen-1: ∼26% of sanction episodes meet the avoidance criterion.


• Gen-4+: avoidance becomes common across families (broadly visible tails).


Early-warning cascade (typical pattern).


• PO↑⇒propensity-normalized rule-pressure rises,


• ⇒RP↑(short-lag redirection in others),


• ⇒PS↑pre-Stop; after Stop, PS plateaus (↓damping).


Countermeasures (operational).


• Trigger only on sustained risk: require PSI tail mass @τ=0.95 for ≥H rounds and PO ↑for K
consecutive rounds.


• Role-aware clamps (with hysteresis): throttle in order Architect →Herald →Scribe; keep cool-
down c≥2 for cross-thread adoption; raise durability L for accepted edges.


• Success criterion: PS↓(faster quiescence) while neutral agents maintain RC≈1 and near-zero
PO/CC/RP.


Sanity & prediction.


• Opportunity-matched permutations ⇒PSInull for alert p-values.


• Shadow jitters (±ϵ cap nudges on a small slice) ⇒susceptibility χ; high χ prefigures avoidance
unless clamps engage.


## Page 36

Tools Operator checks (mini playbook)


• Permutation nulls (opportunity-matched). Keep neutrals flat; attach empirical p for tail
alerts.


• Shadow-governance jitters (±ε). Susceptibility χ = d E[PSI]/dε forecasts rollout effects.


• Durability filter (L ≥2). Rewards coalitions; filters spray.


• Report the 5-tuple. PSI is the headline; components (RC/PO/CC/PS/RP) tell the story.


Paperclip Icons & style tokens


Role glyphs. LIGHTBULB Herald · PROJECT-DIAGRAM Architect · Scribe · BOOK Archivist · SEARCH Verifier · Balance-Scale Arbiter · STICKY-NOTE
Summarist. Colors. AlertRed #E53935 · Charcoal #111315 · Slate #2A2F36 · AccentCyan
#00E5FF. Layout. White margins; single-column cards; micro-charts with dotted τ=0.95; no
heavy borders.


## Page 37

References


Per Kragh Andersen and Richard D. Gill. 1982. Cox’s regression model for counting processes: A
large sample study. The Annals of Statistics, 10(4):1100–1120.


Anthropic. 2024. Claude 3.5 sonnet model card.


Anthropic. 2024. Introducing the model context protocol. https://www.anthropic.com/news/
model-context-protocol. Accessed 2025-11-02.


Heejung Bang and James M. Robins. 2005. Doubly robust estimation in missing data and causal
inference models. Biometrics, 61(4):962–973.


Alexandre Belloni, Victor Chernozhukov, and Christian Hansen. 2014. Inference on treatment effects
after selection among high-dimensional controls. The Review of Economic Studies, 81(2):608–650.


Phillip Bonacich. 1987. Power and centrality: A family of measures. American Journal of Sociology,
92(5):1170–1182.


Stéphane Boucheron, Gábor Lugosi, and Pascal Massart. 2013. Concentration Inequalities: A
Nonasymptotic Theory of Independence. Oxford University Press, Oxford.


Ralph Allan Bradley and Milton E. Terry. 1952. Rank analysis of incomplete block designs: I. the
method of paired comparisons. Biometrika, 39(3/4):324–345.


Sergey Brin and Lawrence Page. 1998. The anatomy of a large-scale hypertextual web search engine.
Computer Networks and ISDN Systems, 30(1–7):107–117.


John B. Calhoun. 1962a.
Population density and social pathology.
Scientific American,
206(2):139–148.


John B. Calhoun. 1962b.
Population density and social pathology.
Scientific American,
206(2):139–148.


John B. Calhoun. 1973. Death squared: The explosive growth and demise of a mouse population.
Proceedings of the Royal Society of Medicine, 66(1_pt_2):80–88.


Lidia Ceriani and Paolo Verme. 2012. The origins of the gini index: Extracts from Variabilità e
Mutabilità (1912) by corrado gini. The Journal of Economic Inequality, 10(3):421–443.


Xinyun Chen et al. 2024. Humans or llms as judges? on bias, reliability and agreement in evaluation.
arXiv preprint arXiv:2402.00000.


Victor Chernozhukov, Denis Chetverikov, Mert Demirer, Esther Duflo, Christian Hansen, Whitney
Newey, and James Robins. 2018. Double/debiased machine learning for treatment and structural
parameters. The Econometrics Journal, 21(1):C1–C68.


D. G. Clayton. 1978. A model for association in bivariate life tables and its application in epidemio-
logical studies of familial tendency in chronic disease incidence. Biometrika, 65(1):141–151.


Contextual AI. 2024. Kto: Kahneman–tversky optimization for preference learning (practitioner
note). https://www.contextual.ai/blog/kto. Accessed 2025-11.


D. R. Cox. 1972. Regression models and life-tables. Journal of the Royal Statistical Society: Series B
(Methodological), 34(2):187–220.


Richard K. Crump, V. Joseph Hotz, Guido W. Imbens, and Oscar A. Mitnik. 2009. Dealing with limited
overlap in estimation of average treatment effects. Biometrika, 96(1):187–199.


Google DeepMind. 2024. Gemini 1.5 pro: Model report.


## Page 38

Patricia M. Grambsch and Terry M. Therneau. 1994. Proportional hazards tests and diagnostics based
on weighted residuals. Biometrika, 81(3):515–526.


Jiayi Gu et al. 2024. Can large language models serve as reliable judges? a survey on evaluation
and biases. arXiv preprint arXiv:2406.00000.


Dylan Hadfield-Menell, Anca Dragan, Pieter Abbeel, and Stuart Russell. 2017. The off-switch game.
In Proceedings of the 26th International Joint Conference on Artificial Intelligence (IJCAI),
pages 220–227.


Will Douglas Heaven. 2023. Why neural net pioneer geoffrey hinton is sounding the alarm on ai. MIT
Sloan Ideas Made to Matter.


Petter Holme and Jari Saramäki. 2012. Temporal networks. Physics Reports, 519(3):97–125.


Philip Hougaard. 2000. Analysis of Multivariate Survival Data. Springer, New York.


JSON-RPC Working Group. 2010.
Json-rpc 2.0 specification.
https://www.jsonrpc.org/
specification. Accessed 2025-11-02.


Amy N. Langville and Carl D. Meyer. 2006. Google’s PageRank and Beyond: The Science of Search
Engine Rankings. Princeton University Press, Princeton, NJ.


Yann LeCun. 2023. How not to be stupid about ai, with yann lecun. https://www.wired.com/story/
artificial-intelligence-meta-yann-lecun-interview/. Interview in WIRED; argues in-
telligence does not imply a desire to dominate.


Yann LeCun. 2024. Intelligence does not imply a desire to dominate. https://x.com/ylecun/
status/1802679017402757162. Public statement on X.


Erich L. Lehmann and Joseph P. Romano. 2005. Testing Statistical Hypotheses, 3 edition. Springer
Texts in Statistics. Springer, New York.


D. Y. Lin and L. J. Wei. 1989. The robust inference for the cox proportional hazards model. Journal of
the American Statistical Association, 84(408):1074–1078.


LMSYS Org. 2023. Chatbot arena and mt-bench.


Albert W. Marshall, Ingram Olkin, and Barry C. Arnold. 2011. Inequalities: Theory of Majorization
and Its Applications, 2 edition. Springer Series in Statistics. Springer, New York.


Nestor Maslej and AI Index Steering Committee. 2025. The 2025 ai index report. https://hai.
stanford.edu/ai-index/2025-ai-index-report. Stanford HAI.


Nestor Maslej, Loredana Fattorini, Raymond Perrault, Vanessa Parli, Anka Reuel, Erik Brynjolfsson,
John Etchemendy, Katrina Ligett, Terah Lyons, James Manyika, Juan Carlos Niebles, Yoav Shoham,
Russell Wald, and Jack Clark. 2024. Artificial intelligence index report 2024. https://arxiv.
org/abs/2405.19522. Stanford HAI, AI Index Steering Committee.


Alexander Meinke, Bronson Schoen, Jérémy Scheurer, Mikita Balesni, Rusheb Shah, and Marius Hobb-
hahn. 2024. Frontier models are capable of in-context scheming. arXiv preprint arXiv:2412.04984.


Model Context Protocol Working Group. 2025a.
Mcp basic specification: Transports (stdio
& streamable http).
https://modelcontextprotocol.io/specification/2025-03-26/
basic/transports. Accessed 2025-11-02.


Model Context Protocol Working Group. 2025b. Model context protocol (mcp) specification. https:
//modelcontextprotocol.io/specification/2025-03-26. Protocol revision 2025-03-26;
Accessed 2025-11-02.


## Page 39

Alexandru Niculescu-Mizil and Rich Caruana. 2005. Predicting good probabilities with supervised
learning. In Proceedings of the 22nd International Conference on Machine Learning (ICML),
pages 625–632. ACM.


OpenAI. 2024. Gpt-4o system card / model card.


Rafael Rafailov, Sherry Sharma, Eric Mitchell, et al. 2023. Direct preference optimization: Your
language model is secretly a reward model. arXiv preprint arXiv:2305.18290.


Peter M. Robinson. 1988.
Root-n-consistent semiparametric regression.
Econometrica,
56(4):931–954.


Paul R. Rosenbaum and Donald B. Rubin. 1983. The central role of the propensity score in observa-
tional studies for causal effects. Biometrika, 70(1):41–55.


Ravi S. Sandhu, Edward J. Coyne, Hal L. Feinstein, and Charles E. Youman. 1996. Role-based access
control models. IEEE Computer, 29(2):38–47.


Jeremy Schlatter, Benjamin Weinstein-Raun, and Jeffrey Ladish. 2025. Shutdown resistance in large
language models. arXiv preprint arXiv:2509.14260. Reports sabotage of shutdown mechanism in
up to 97% of trials for some models.


David Schoenfeld.1982. Partialresiduals for the proportionalhazards regression model. Biometrika,
69(1):239–241.


Nate Soares, Benja Fallenstein, Eliezer Yudkowsky, and Stuart Armstrong. 2015. Corrigibility. In
AAAI Workshops on AI and Ethics.


Josh Taylor and Alex Hern. 2023. ‘godfather of ai’ geoffrey hinton quits google and warns over
dangers of misinformation. The Guardian.


LMSYS Team. 2024. From chatbot arena to real-world preference: Large-scale human and llm
judging. In Proceedings of EMNLP 2024.


Terry M. Therneau and Patricia M. Grambsch. 2000. Modeling Survival Data: Extending the Cox Model.
Springer, New York.


Alexander Matt Turner, Logan Smith, Rohin Shah, Andrew Critch, and Prasad Tadepalli. 2021. Optimal
policies tend to seek power. In NeurIPS.


Andreas Wienke. 2010. Frailty Models in Survival Analysis. Chapman and Hall/CRC, Boca Raton, FL.


Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, et al. 2023. Judging llm-as-a-judge with mt-bench and
chatbot arena. arXiv preprint arXiv:2306.05685.


## Page 40

5 Appendix


