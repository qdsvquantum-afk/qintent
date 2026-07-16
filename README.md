# QIntent Developer Preview

[![PyPI](https://img.shields.io/pypi/v/qdsv-qintent.svg)](https://pypi.org/project/qdsv-qintent/)
[![Python](https://img.shields.io/pypi/pyversions/qdsv-qintent.svg)](https://pypi.org/project/qdsv-qintent/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-developer%20preview-0ea5e9.svg)](#public-preview-limits)

Documentation site: https://qdsvquantum-afk.github.io/qintent/

QIntent is the native intent-first language for **QDSV - Quantum Declarative Semantic Value**.

It lets users declare computational intent over state spaces, operations, predicates, relations, rankings, distributions, rows and evidence. QDSV then decides how to represent and execute that intent.

```text
problem intent
-> semantic representation
-> state space / operation / predicate / relation
-> QDSV Operation Compiler v2
-> execution route
-> evidence
```

QIntent does not start from manually written circuits and does not own a separate compiler. It produces canonical problem intent for QDSV Operation Compiler v2. QuEST, Aer, IBM-oriented materialization and Bridge exports must consume the same operation program and digest; circuit materialization appears only when an enabled backend requires it.

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

## QIntent -> Bridge -> Qiskit

QIntent can also act as an upstream intent layer for QDSV Bridge when a workflow needs to end in a Qiskit-oriented artifact:

- [QIntent to QDSV Bridge to Qiskit](docs/integrations/qintent_bridge_qiskit.md)

This route keeps QIntent positioned as the problem-intent language and uses QDSV Bridge, a Qiskit Ecosystem project, for the OpenQASM/Qiskit artifact handoff.

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
client.capabilities()
client.examples()
client.validate(source, rows=None, backend="quest")
client.compile(source, rows=None, backend="quest")
client.explain(source, rows=None, backend="quest")
client.run(source, rows=None, backend="quest")
client.compile_hardware(source, rows=None)
client.submit_hardware(source, rows=None, backend_name="least_busy")
client.hardware_job(job_id)
```

`compile()` responses include a safe `operation_program` passport with compiler version, digest, required capabilities, resource status and verification status. Private lowering operands and formulas are not exposed.

## Supported Preview Patterns

- `find_rows(...).where(...)`
- `find_rows(...).where_between(...)`
- `find_rows(...).where_all(...)`
- `find_rows(...).where_any(...)`
- `find_rows(...).rank_by(...).top_k(...)`
- `find_rows(...).using_score_model([...]).accept_if(...)`
- `find_rows(...).using_hierarchical_score_model([...]).accept_if(...)`
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

The capability contract reports exactly 43 canonical operations:

```text
abs, abs_diff, add, and, between, ceil, clip, coalesce,
default_if_invalid, div, eq, field, floor, gt, gte, in_set,
is_null, lt, lte, max, mean_fields, min, mod, mul, ne, not,
not_null, or, outside, percent, ratio, round, safe_div, sign,
similarity, squared_diff, sub, sum_fields, vector,
vector_similarity, weighted_sum, within_tolerance, xor
```

See [grammar/QINTENT_PREVIEW.md](grammar/QINTENT_PREVIEW.md) for public preview grammar notes.

## ScoreModel v2

ScoreModel v2 is the canonical QDSV composition for bounded multi-criteria decisions. A term can read a prepared similarity value or any bounded numeric value produced by another canonical operation. The public names are `importance` and `priority`.

Flat model:

```python
source = """
find_rows("candidate_index")
  .using_score_model([
      score_term("quality", importance=30, priority=2, adjustments=[
          score_adjustment("context", coefficient=0.10),
      ]),
      score_term("benefit", importance=40, priority=3),
      score_term("risk_fit", importance=30, priority=2),
  ], penalty=0.05)
  .accept_if(threshold=780, decision="gte")
"""
result = client.run(source, rows=rows)
```

Hierarchical model:

```python
source = """
find_rows("candidate_index")
  .using_hierarchical_score_model([
      score_block("value", [
          score_term("quality", importance=30, priority=2),
          score_term("benefit", importance=40, priority=3),
      ], importance=60, priority=2, penalty=0.02),
      score_block("risk", [
          score_term("risk_fit", importance=30, priority=3),
      ], importance=40, priority=3, penalty=0.05),
  ], penalty=0.03)
  .accept_if(threshold=780, decision="gte")
"""
result = client.run(source, rows=rows)
```

Both forms compile through the same QDSV Operation Compiler v2 route. They support bounded contextual adjustments, term/block/global penalties, normalization, threshold decisions and exact fixed-point contracts. QIntent does not calculate winning candidates before quantum materialization. Ranking and presentation remain workflow-level concerns and are not part of the ScoreModel formula.

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
- IBM execution is available only on licensed deployments with a saved user token. The SDK always performs canonical compilation preflight before submission.

```python
client = QIntentClient(license_key="your_qdsv_license")
preflight = client.compile_hardware(source, rows=rows)
job = client.submit_hardware(source, rows=rows, backend_name="least_busy", shots=1024)
status = client.hardware_job(job["job_id"])
```

The SDK refuses submission when the operation program is not circuit-ready or reports a precomputed answer. Credentials, provider availability, queue time, shots and hardware cost remain the user's responsibility.

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
qintent capabilities
qintent examples
qintent compile 'x = domain(0, 15); find(x).where(x in [3, 6, 9])'
qintent explain 'find_rows("candidate_index").where("score", ">=", 850)' --rows candidates.csv
qintent run 'find_rows("candidate_index").where("score", ">=", 850)' --rows candidates.csv
qintent submit-hardware score_model.qi --rows candidates.csv --license-key YOUR_LICENSE --backend-name least_busy
qintent hardware-job JOB_ID --license-key YOUR_LICENSE
```

## Examples And Notebooks

- [Quickstart](QUICKSTART.md)
- [Examples](examples/)
- [Notebooks](notebooks/)
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
