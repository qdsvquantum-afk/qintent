# QIntent Developer Preview

Lightweight Python SDK for **QIntent**, the native intent-first quantum language powered by **QDSV**.

QIntent lets users declare what they want to find, evaluate, rank, sample, or verify over state spaces, predicates, rows, and evidence. QDSV then decides how to represent and execute that intent.

QIntent is designed for quantum-oriented semantic computation: users describe the problem intent and the meaningful states, candidates, constraints, and evidence; QDSV decides how that intent is compiled, routed, and executed by statevector, simulator, or quantum-capable backends.

Not starting from circuits is a consequence of the model, not the main idea. QIntent starts from computational intent. QDSV may execute that intent directly through semantic/statevector routes when possible, and only materializes circuits when a selected backend requires that representation. The public SDK defaults to the QDSV QuEST route because it is designed to execute QIntent over state spaces from the declared intent.

```bash
pip install qdsv-qintent
```

> Developer Preview: this package is a client SDK. It does not include QDSV Runtime, CAP, backend selection, QuEST/Aer/IBM adapters, lowering, noise mitigation internals, crypto internals, private endpoints, credentials, or advanced orchestration logic.

## Open SDK, Private Runtime

This repository is intentionally open-core:

- **Open under MIT:** Python SDK, CLI, examples, notebooks, public preview docs, and public grammar notes.
- **Not included:** QDSV Runtime, CAP, backend selector, lowering, QuEST/Aer/IBM adapters, optimization layers, noise mitigation internals, crypto internals, private endpoints, keys, secrets, or production platform configuration.

QIntent SDKs and examples are released under the MIT License. QDSV Runtime, backend execution, optimization layers, quantum adapters, and internal orchestration components are not included in this repository and remain proprietary/private unless explicitly released under a separate license.

QDSV, QIntent, and Qruba names and marks are project marks of their respective owners. The MIT License for this repository does not grant trademark rights.

## Quick Start

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

## QIntent Syntax

```python
source = """
x = domain(0, 15)
score = clip(round(max(x["score"], 0)), 0, 1000)
find(x).where(all([700 <= score <= 950, x not in [0, 1]])).rank_by(score).top_k(3)
"""

compiled = client.compile(source)
print(compiled["compiled_summary"])
```

QIntent uses Python-inspired syntax for ergonomics, but its semantics are QDSV-native: computational intent, state spaces, predicates, ranking, sampling, evidence, and backend-independent execution.

## How QIntent Differs

QIntent works from the intention and formulation of the problem: users declare the search, condition, ranking, decision, verification, or state-space relationship they need, and QDSV decides how to represent and execute it. Circuits are not the starting point; they are only a possible materialization when a backend requires them.

Traditional quantum frameworks often ask users to translate the problem into an algorithm or circuit first. QIntent takes a different path: users declare the problem intent, and QDSV determines the representation and execution route.

This aligns naturally with the way quantum systems are reasoned about:

- Quantum physics works with states, superposition, amplitudes, probability, observation, distributions, and measurement.
- QIntent/QDSV starts from state spaces, conditions over states, solution mass, ranking, probability, and evidence.
- Circuits remain valid, but they are an operational way to materialize execution, not necessarily the natural language of the problem.

| Language / layer | What it tries to be | How QIntent is different | User benefit |
|---|---|---|---|
| Classiq Qmod | A high-level model for designing quantum algorithms and synthesizing circuits. | Qmod abstracts circuit creation. QIntent starts from the problem intent and only materializes circuits if the backend requires them. | Users can formulate search, ranking, or decision problems without starting by designing circuits. |
| Q# | A formal language for programming quantum and hybrid quantum-classical algorithms. | Q# is still quantum programming. QIntent is intent declaration over state spaces. | Reduces the need to know detailed quantum programming in order to express executable problems. |
| QIR | An intermediate representation for connecting languages and backends. | QIR is not designed for end users. QIntent is a declarative interface usable by people and SDKs. | Users write readable intent and QDSV decides the execution route. |
| OpenQASM 3 | A language for describing circuits, operations, and hardware-near control. | OpenQASM describes how to execute quantum operations. QIntent describes what condition, search, or decision should be resolved. | Avoids forcing users to write gates, measurements, and low-level control from the start. |
| Qiskit / Cirq / QPanda | Frameworks for building, simulating, and executing quantum circuits or algorithms. | They are powerful tools, but circuit/program-first. QIntent is intent/state-space-first. | Brings data, decision, or search problems to QDSV, QuEST, Aer, or hardware execution without manually redesigning them as circuits. |
| PennyLane | A framework for QML, differentiation, and hybrid optimization. | PennyLane is strong for trainable models and QML. QIntent is more general for predicates, scoring, ranking, search, and selection. | Useful when users do not want to train a QML model, but evaluate candidates or conditions with evidence. |
| Silq / Qrisp | High-level languages to make quantum programming more comfortable. | They simplify quantum programming. QIntent tries to avoid programming when the problem can be expressed semantically. | Lowers the entry barrier: users declare the problem and QDSV decides how to execute it. |

Supported preview patterns include:

- `find_rows(...).where(...)`
- `find_rows(...).where_between(...)`
- `find_rows(...).where_all(...)`
- `find_rows(...).where_any(...)`
- `find_rows(...).rank_by(...).top_k(...)`
- `domain(...), range(...), find(...).where(...)`
- `field(variable, column)` and `row["column"]`
- `not`, `in`, `not in`, chained comparisons
- `all([...])`, `any([...])`
- `abs(...)`, `round(...)`, `min(...)`, `max(...)`, `clip(...)`

See [grammar/QINTENT_PREVIEW.md](grammar/QINTENT_PREVIEW.md) for the public preview grammar notes.

## Methods

```python
client.spec()
client.examples()
client.validate(source, rows=None, backend="quest")
client.compile(source, rows=None, backend="quest")
client.run(source, rows=None, backend="quest")
```

## Authentication and access

The public preview can be used without a user key for small examples and public QIntent endpoints:

```python
client = QIntentClient()
```

The SDK can also send credentials when your Qruba/QDSV deployment or license requires them:

```python
client = QIntentClient(
    api_key="...",
    license_key="...",
)
```

Environment variables are also supported:

```bash
QINTENT_API_URL=https://api.qdsv.cloud/api
QINTENT_API_KEY=...
QDSV_LICENSE_KEY=...
```

The SDK is a client. It does not grant access to private backends by itself; available capabilities depend on the API endpoint, account, license, deployment, and backend policy.

## Data and workload policy

The public QIntent API is intended for lightweight evaluation:

- quickstarts
- notebooks
- examples
- small datasets
- public preview experiments

It should not be used for large datasets, private business data, long-running jobs, or heavy backend usage. Public endpoints may enforce row limits, payload limits, backend limits, and execution time limits to protect the shared free/preview infrastructure.

For larger datasets, sensitive data, or heavier workloads, use Qruba Cloud with an appropriate license or a private Docker/local QDSV node.

## Backends

The SDK defaults to the QDSV QuEST route:

```python
client.run(source)
client.run(source, backend="quest")
client.run(source, backend="aer")
```

Backend availability depends on the public API or Qruba deployment you are using.

- `quest`: default QDSV statevector route. This path can inspect and execute the semantic problem directly over the state space without requiring the user to write circuits.
- `aer`: circuit/simulator materialization when the deployment supports it.
- IBM/hardware routes are not part of the default public SDK preview; they are available through Qruba/full platform configurations when enabled.

For large datasets or production workloads, use a licensed Qruba/QDSV deployment. Public preview endpoints may enforce row, payload, backend, and execution limits.

For a local Docker/private demo API:

```python
client = QIntentClient.local()
```

Private Docker/local execution is available only when a private QDSV node is online:

```python
client = QIntentClient(api_url="https://qintent-local.qdsv.cloud/api")
```

If the private node is unavailable, it may be offline, reserved for private processing, or temporarily busy. Try again later or use the public cloud endpoint for lightweight examples:

```python
client = QIntentClient()
```

## CLI

```bash
qintent spec
qintent examples
qintent compile 'x = domain(0, 15); find(x).where(x in [3, 6, 9])'
qintent run 'find_rows("candidate_index").where("score", ">=", 850)' --rows candidates.csv
```

## Public Preview Limits

The public preview intentionally exposes a stable subset. Advanced QDSV families such as crypto, sensing, AI semantic operations, hardware routing, large-data execution, and mitigation internals may compile or run only through Qruba full platform endpoints depending on your license.

Write QIntent locally. Execute on QDSV.

## Links

- QDSV landing: https://qdsv.cloud
- QIntent site: https://qintent.qdsv.cloud
- Public API spec: https://api.qdsv.cloud/api/qintent/spec
- PyPI: https://pypi.org/project/qdsv-qintent/
