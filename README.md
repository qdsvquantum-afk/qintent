# QIntent Developer Preview

Lightweight Python SDK for **QIntent**, the native quantum-intent language powered by **QDSV**.

QIntent lets you write declarative computational intent over state spaces, predicates, rows, ranking, and sampling without writing circuits first or installing the QDSV Runtime locally.

QIntent is designed for quantum-oriented semantic computation: users describe what states, candidates, constraints, and evidence matter; QDSV decides how that intent is compiled, routed, and executed by logical, statevector, simulator, or quantum-capable backends.

QIntent does not require circuits as the starting point. QDSV may execute a problem directly through semantic/logical routes when possible, and only materializes circuits when a selected backend requires that representation. This is one of the core differences from circuit-first quantum SDKs.

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

QIntent uses Python-inspired syntax for ergonomics, but its semantics are QDSV-native: state spaces, predicates, ranking, sampling, evidence, and backend-independent execution intent.

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
client.validate(source, rows=None, backend="logical")
client.compile(source, rows=None, backend="logical")
client.run(source, rows=None, backend="logical")
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

The SDK can request a backend:

```python
client.run(source, backend="logical")
client.run(source, backend="quest")
client.run(source, backend="aer")
```

Backend availability depends on the public API or Qruba deployment you are using.

- `logical`: deterministic semantic execution, useful for fast validation and examples.
- `quest`: QDSV statevector route. This path can inspect and execute the semantic problem directly over the state space without requiring the user to write circuits.
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
