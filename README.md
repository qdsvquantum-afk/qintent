# QIntent Developer Preview

[![PyPI](https://img.shields.io/pypi/v/qdsv-qintent.svg)](https://pypi.org/project/qdsv-qintent/)
[![Python](https://img.shields.io/pypi/pyversions/qdsv-qintent.svg)](https://pypi.org/project/qdsv-qintent/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-developer%20preview-0ea5e9.svg)](#public-preview-limits)

QIntent is the native intent-first language for **QDSV - Quantum Declarative Semantic Value**.

It lets users declare computational intent over state spaces, operations, predicates, relations, rankings, distributions, rows and evidence. QDSV then decides how to represent and execute that intent.

```text
problem intent
-> semantic representation
-> state space / operation / predicate / relation
-> execution route
-> evidence
```

QIntent does not start from manually written circuits. The public SDK defaults to the QDSV QuEST/statevector route, which is designed to execute declared state-space intent without user-written circuits. Circuit materialization appears only when an enabled backend requires it.

## 5 Minute Quickstart

Install the SDK:

```bash
pip install qdsv-qintent
```

Run a first intent:

```python
from qintent import QIntentClient

client = QIntentClient()

rows = [
    {"candidate_index": 0, "score": 720, "risk_ok": True},
    {"candidate_index": 1, "score": 910, "risk_ok": True},
    {"candidate_index": 2, "score": 840, "risk_ok": False},
]

result = client.run(
    'find_rows("candidate_index").where("score", ">=", 850).rank_by("score").top_k(5)',
    rows=rows,
)

print(result["status"])
print(result["result"]["selected_rows"])
```

Explain before running:

```python
passport = client.explain(
    'find_rows("candidate_index").where("score", ">=", 850).rank_by("score").top_k(5)',
    rows=rows,
)

plan = passport["semantic_execution_passport"]["execution_plan"]
print(plan["selected_backend"])
print(plan["uses_circuits"])
print(plan["reason"])
```

Default narrative:

```text
QIntent -> QDSV -> QuEST/statevector -> no user-written circuits
```

## What This Is

- A lightweight Python client SDK for QIntent.
- A public preview grammar and examples for QDSV-native intent expression.
- A way to validate, compile, explain and run small public-preview examples through QDSV APIs.
- A developer entry point into Qruba/QDSV.

## What This Is Not

- It is not the QDSV Runtime.
- It is not an unrestricted Python execution environment.
- It is not a local QuEST/Aer/IBM installation.
- It does not expose CAP, backend selection internals, lowering, noise mitigation internals, crypto internals, private endpoints or credentials.
- It is not intended for large private datasets on the public free preview API.

## Core Methods

```python
client.spec()
client.examples()
client.validate(source, rows=None, backend="quest")
client.compile(source, rows=None, backend="quest")
client.explain(source, rows=None, backend="quest")
client.run(source, rows=None, backend="quest")
```

## Supported Preview Patterns

- `find_rows(...).where(...)`
- `find_rows(...).where_between(...)`
- `find_rows(...).where_all(...)`
- `find_rows(...).where_any(...)`
- `find_rows(...).rank_by(...).top_k(...)`
- `find_rows(...).using_decision_model([...]).accept_if(...).rank().top_k(...)`
- `find_rows(...).using_semantic_score([...], risk_adjustment=...).accept_if(...).rank().top_k(...)`
- `find_rows(...).using_structured_semantic_score([...], global_risk=..., profile=...).accept_if(...).rank().top_k(...)`
- `domain(...), range(...), find(...).where(...)`
- `field(variable, column)` and `row["column"]`
- `not`, `in`, `not in`, chained comparisons
- `all([...])`, `any([...])`
- `abs(...)`, `round(...)`, `floor(...)`, `ceil(...)`, `sign(...)`, `min(...)`, `max(...)`, `clip(...)`
- `between(...)`, `outside(...)`, `abs_diff(...)`, `squared_diff(...)`, `within_tolerance(...)`
- `similarity(...)`, `within_similarity(...)`
- `vector_similarity(...)`
- `safe_div(...)`, `ratio(...)`, `percent(...)`
- `is_null(...)`, `not_null(...)`, `coalesce(...)`, `default_if_invalid(...)`
- `sum_fields([...])`, `mean_fields([...])`, `weighted_sum([...], [...])`

See [grammar/QINTENT_PREVIEW.md](grammar/QINTENT_PREVIEW.md) for public preview grammar notes.

## Decision Model Operation

QIntent can express a prebuilt QDSV decision model without exposing the internal formula.

Users declare criteria, importance, priority, an acceptance rule and ranking behavior. Each criterion is a prepared value: a comparable, oriented value that represents something meaningful about a process.

```python
from qintent import QIntentClient

client = QIntentClient()

rows = [
    {"candidate_index": 0, "credit_score_norm": 780, "default_score": 1000, "debt_burden_score": 900},
    {"candidate_index": 1, "credit_score_norm": 700, "default_score": 700, "debt_burden_score": 700},
    {"candidate_index": 2, "credit_score_norm": 950, "default_score": 1000, "debt_burden_score": 980},
]

source = """
find_rows("candidate_index")
  .using_decision_model([
      criterion("credit_score_norm", importance=25, priority=1),
      criterion("default_score", importance=25, priority=1),
      criterion("debt_burden_score", importance=20, priority=1),
  ])
  .accept_if(threshold=850)
  .rank()
  .top_k(10)
"""

result = client.run(source, rows=rows)
print(result["result"]["selected_rows"])
```

Use this operation when a problem is better represented as a multi-signal decision than as a single threshold. QIntent keeps the operation declarative: criteria are visible, while QDSV internal representation stays inside the private runtime.

## Semantic Score Operation

`using_semantic_score(...)` is the advanced public-preview scoring operation for prepared signals. It is useful when a workflow needs to rank candidates using evidence, influence, priority and a prepared risk adjustment without exposing the internal QDSV scoring formula.

Users declare:

- `signal(...)`: a prepared comparable value in the input rows.
- `influence`: how strongly that signal contributes to the evaluation.
- `priority`: an operational priority modifier for that signal.
- `risk_adjustment`: an optional prepared field or constant used by QDSV as a controlled risk adjustment.

```python
from qintent import QIntentClient

client = QIntentClient()

rows = [
    {
        "candidate_index": 0,
        "syndrome_support": 920,
        "logical_preservation": 860,
        "decoder_confidence": 810,
        "propagation_safety": 830,
        "distance_safety": 850,
        "logical_risk": 80,
    },
    {
        "candidate_index": 1,
        "syndrome_support": 910,
        "logical_preservation": 700,
        "decoder_confidence": 840,
        "propagation_safety": 730,
        "distance_safety": 720,
        "logical_risk": 220,
    },
]

source = """
find_rows("candidate_index")
  .using_semantic_score([
      signal("syndrome_support", influence=30, priority=2),
      signal("logical_preservation", influence=30, priority=3),
      signal("decoder_confidence", influence=20, priority=1),
      signal("propagation_safety", influence=10, priority=2),
      signal("distance_safety", influence=10, priority=3),
  ], risk_adjustment="logical_risk")
  .accept_if(threshold=780)
  .rank()
  .top_k(5)
"""

passport = client.explain(source, rows=rows)
result = client.run(source, rows=rows)

print(passport["semantic_execution_passport"]["predicate"]["internal_formula_exposed"])
print(result["result"]["selected_rows"])
```

This operation is intended for controlled evidence-ranking workflows, including classical triage, candidate prioritization, benchmarking, and qLDPC-style correction-candidate evaluation. The public API exposes the declared signals and evidence outputs, not the private QDSV scoring formula.

## Structured Semantic Score Operation

`using_structured_semantic_score(...)` is the advanced public-preview operation for hierarchical prepared-signal workflows. It is useful when candidates should be evaluated through blocks such as syndrome evidence, logical safety, decoder confidence, propagation safety, and global risk.

The public syntax exposes operational structure, not the private QDSV hierarchical or nonlinear scoring representation.

```python
from qintent import QIntentClient

client = QIntentClient()

rows = [
    {
        "candidate_index": 0,
        "syndrome_support": 930,
        "check_consistency": 900,
        "logical_preservation": 820,
        "distance_safety": 830,
        "decoder_confidence": 850,
        "propagation_safety": 820,
        "syndrome_risk": 50,
        "logical_risk": 120,
        "syndrome_entropy_adjustment": -10,
    }
]

source = """
find_rows("candidate_index")
  .using_structured_semantic_score([
      block("syndrome", [
          signal("syndrome_support", influence=30, priority=2),
          signal("check_consistency", influence=20, priority=1),
      ], influence=30, priority=2, risk_adjustment="syndrome_risk", adjustments=[
          adjustment("syndrome_entropy_adjustment", influence=5),
      ]),
      block("logical_safety", [
          signal("logical_preservation", influence=40, priority=3),
          signal("distance_safety", influence=20, priority=2),
      ], influence=40, priority=3, risk_adjustment="logical_risk"),
      block("decoder", [
          signal("decoder_confidence", influence=25, priority=1),
          signal("propagation_safety", influence=15, priority=2),
      ], influence=30, priority=1),
  ], global_risk="logical_risk", profile="qldpc_post_decoding")
  .accept_if(threshold=600)
  .rank()
  .top_k(5)
"""

passport = client.explain(source, rows=rows)
result = client.run(source, rows=rows)

print(passport["semantic_execution_passport"]["predicate"]["internal_formula_exposed"])
print(result["result"]["selected_rows"])
```

This operation is intended for structured evidence-ranking workflows, including qLDPC-style post-decoding analysis where a decoder produces candidate corrections and QDSV ranks them with block-level evidence, local/global risk and an auditable decision trace.

## Semantic Similarity

`similarity(...)` is exposed as a bounded QDSV semantic relation helper. It returns a prepared 0..1000 signal that can feed predicates, ranking objectives or the prebuilt Decision Model operation.

For prepared numeric vectors, QIntent also exposes `vector_similarity(...)`, which returns a 0..1000 normalized-overlap / fidelity score. This is the semantic bridge toward kernel, overlap or state-similarity style representations.

```python
source = """
i = domain(0, 9)
left_state = [field(i, "a1"), field(i, "a2"), field(i, "a3")]
right_state = [field(i, "b1"), field(i, "b2"), field(i, "b3")]
overlap = vector_similarity(left_state, right_state)
find(i).where(overlap >= 850).rank_by(overlap).top_k(10)
"""
```

This does not claim automatic production-grade record linkage. It is a bounded, auditable QDSV operation for representing similarity as part of the problem intent.

## Decision And Reliability Columns

QIntent/QDSV separates semantic decisions from backend evidence so results are not misread.

Tabular executions may include:

- `qdsv_selected_semantic`: decision produced by declared QIntent/QDSV semantics.
- `qdsv_selected_hardware`: hardware-reconstructed decision when per-candidate hardware evidence exists; otherwise `null`.
- `qruba_reliability_status`: `accepted`, `uncertain`, `rejected`, `reported` or `not_available`.
- `qruba_accepted_as_reliable`: `true`, `false` or `null`.
- `qruba_final_decision`: decision recommended by the platform.
- `qdsv_selected_decision_source`: whether the final decision came from semantic execution, hardware evidence or reliability policy.

This matters when comparing semantic results with real quantum hardware. A high semantic accuracy does not automatically mean that the hardware distribution reproduced the same decision with high reliability.

## Backends

```python
client.run(source)                  # defaults to quest
client.run(source, backend="quest") # QDSV statevector route
client.run(source, backend="aer")   # when supported by the deployment
```

- `quest`: default QDSV statevector route. It can inspect and execute semantic state-space intent without requiring user-written circuits.
- `aer`: circuit/simulator materialization when the deployment supports it.
- IBM/hardware routes are not part of the default public SDK preview. They are available through Qruba/full platform configurations when enabled.

## Public API And Access

Public informational endpoints such as `spec()` and `examples()` can be opened without a key. Public-preview value calls such as `validate`, `compile`, `explain` and `run` are also available without a key when the deployment is configured for public demo mode:

```python
client = QIntentClient()
```

In public demo mode, usage is limited by an IP-based access bucket. The SDK can still send optional API or license keys when a private deployment enables them:

```python
client = QIntentClient(api_key="optional_private_key", license_key="optional_license_key")
```

Environment variables:

```bash
QINTENT_API_URL=https://api.qdsv.cloud/api
QINTENT_API_KEY=optional_private_key
QDSV_LICENSE_KEY=optional_license_key
```

Initial public SDK quota:

- QIntent value requests: deployment-controlled, default 100/month per IP or optional API key bucket.
- QIntent rows: deployment-controlled, default 200 rows/request.
- Hardware execution: not available from public SDK preview.

Private Docker/local execution is available only when a private QDSV node is online:

```python
client = QIntentClient.local()
client = QIntentClient(api_url="https://qintent-local.qdsv.cloud/api")
```

If the private node is unavailable, it may be offline, reserved for private processing or temporarily busy. Use `QIntentClient()` for public cloud examples.

## CLI

```bash
qintent spec
qintent examples
qintent compile 'x = domain(0, 15); find(x).where(x in [3, 6, 9])'
qintent explain 'find_rows("candidate_index").where("score", ">=", 850)' --rows candidates.csv
qintent run 'find_rows("candidate_index").where("score", ">=", 850)' --rows candidates.csv
```

## Examples And Notebooks

- [Quickstart](QUICKSTART.md)
- [Examples](examples/)
- [Notebooks](notebooks/)
- [qLDPC-style structured semantic score Colab](https://colab.research.google.com/github/qdsvquantum-afk/qintent/blob/main/notebooks/qldpc_structured_semantic_score_colab.ipynb)
- [qLDPC batch decoder-generated candidates Colab](https://colab.research.google.com/github/qdsvquantum-afk/qintent/blob/main/notebooks/qldpc_batch_decoder_semantic_score_colab.ipynb)
- [qLDPC controlled formal benchmark Colab](https://colab.research.google.com/github/qdsvquantum-afk/qintent/blob/main/notebooks/qldpc_formal_benchmark_colab.ipynb)
- [qLDPC random sparse benchmark Colab](https://colab.research.google.com/github/qdsvquantum-afk/qintent/blob/main/notebooks/qldpc_random_sparse_benchmark_colab.ipynb)
- [Technical note: QDSV/QIntent as a risk-aware qLDPC-style post-decoding layer](docs/research/qldpc_post_decoding_note.md)
- [Public grammar](grammar/QINTENT_PREVIEW.md)
- [Roadmap](ROADMAP.md)

## How QIntent Differs

QIntent works from the intention and formulation of the problem. Users declare the operation, predicate, relation, search, observation, ranking, decision, verification or state-space relationship they need, and QDSV decides how to represent and execute it.

Traditional quantum frameworks often ask users to translate the problem into an algorithm or circuit first. QIntent takes a different path: users declare the problem intent, and QDSV determines the representation and execution route.

| Language / layer | What it tries to be | How QIntent is different | User benefit |
|---|---|---|---|
| Classiq Qmod | High-level model for designing quantum algorithms and synthesizing circuits. | QIntent starts from semantic problem intent and only materializes circuits if the backend requires them. | Users can formulate operations, predicates, relations, searches, rankings or decisions without starting by designing circuits. |
| Q# | Formal language for programming quantum and hybrid algorithms. | QIntent is semantic intent declaration over state spaces and operations. | Reduces the need to know detailed quantum programming to express executable problems. |
| QIR | Intermediate representation for connecting languages and backends. | QIntent is a declarative interface usable by people and SDKs. | Users write readable intent and QDSV decides the execution route. |
| OpenQASM 3 | Language for describing circuits and hardware-near control. | QIntent describes what semantic operation, condition, relation, search or decision should be resolved. | Avoids forcing users to write gates and measurements from the start. |
| Qiskit / Cirq / QPanda | Frameworks for building, simulating and executing quantum circuits or algorithms. | QIntent is intent/state-space-first. | Brings operations, data relationships, predicates, decisions or searches to QDSV, QuEST, Aer or hardware execution without manually redesigning them as circuits. |
| QiliSDK | Python framework for digital, analog and hybrid quantum algorithms. | QIntent starts from semantic problem intent over state spaces and lets QDSV decide whether semantic/statevector execution or circuit materialization is needed. | Users can express operations, predicates, relationships, searches, rankings or decisions without first translating them into a circuit or Hamiltonian. |
| PennyLane | Framework for QML, differentiation and hybrid optimization. | QIntent is broader for semantic operations, predicates, relations, scoring, ranking, search and evidence. | Useful when users do not want to train a QML model, but represent and execute a semantic problem with evidence. |
| Silq / Qrisp | Higher-level quantum programming languages. | QIntent tries to avoid programming when the problem can be expressed semantically. | Users declare the problem and QDSV decides how to execute it. |

## Public Preview Limits

The public preview intentionally exposes a stable subset.

Advanced QDSV families such as crypto, sensing, AI semantic operations, hardware routing, large-data execution and mitigation internals may compile or run only through Qruba full platform endpoints depending on license.

Public endpoints may enforce row limits, payload limits, backend limits and execution time limits to protect shared free/preview infrastructure. For larger datasets, sensitive data or heavier workloads, use Qruba Cloud with an appropriate license or a private Docker/local QDSV node.

## Open SDK, Private Runtime

This repository is intentionally open-core:

- Open under MIT: Python SDK, CLI, examples, notebooks, public preview docs and public grammar notes.
- Not included: QDSV Runtime, CAP, backend selector, lowering, QuEST/Aer/IBM adapters, optimization layers, noise mitigation internals, crypto internals, private endpoints, keys, secrets or production platform configuration.

QDSV, QIntent and Qruba names and marks are project marks of their respective owners. The MIT License for this repository does not grant trademark rights.

## Live Access

These web experiences are currently in Developer Preview. Interfaces, copy and visual design may evolve while QIntent and QDSV continue to stabilize.

- QDSV landing: https://qdsv.cloud
- QIntent site: https://qintent.qdsv.cloud
- Qruba Cloud Platform: https://cloud.qruba.site/
- Public API spec: https://api.qdsv.cloud/api/qintent/spec
- PyPI: https://pypi.org/project/qdsv-qintent/
