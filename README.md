# QIntent Developer Preview

Lightweight Python SDK for **QIntent**, the native quantum-intent language powered by **QDSV**.

QIntent lets you write declarative computational intent over state spaces, predicates, rows, ranking, and sampling without writing circuits first or installing the QDSV Runtime locally.

QIntent is designed for quantum-oriented semantic computation: users describe what states, candidates, constraints, and evidence matter; QDSV decides how that intent is compiled, routed, and executed by logical, simulated, or quantum-capable backends.

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

## Python-like QIntent

```python
source = """
x = domain(0, 15)
score = clip(round(max(x["score"], 0)), 0, 1000)
find(x).where(all([700 <= score <= 950, x not in [0, 1]])).rank_by(score).top_k(3)
"""

compiled = client.compile(source)
print(compiled["compiled_summary"])
```

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

For a local Docker/private demo API:

```python
client = QIntentClient.local()
```

## CLI

```bash
qintent spec
qintent examples
qintent compile 'x = domain(0, 15); find(x).where(x in [3, 6, 9])'
qintent run 'find_rows("candidate_index").where("score", ">=", 850)' --rows candidates.csv
```

Environment variables:

```bash
QINTENT_API_URL=https://api.qdsv.cloud/api
QINTENT_API_KEY=...
QDSV_LICENSE_KEY=...
```

## Public Preview Limits

The public preview intentionally exposes a stable subset. Advanced QDSV families such as crypto, sensing, AI semantic operations, hardware routing, and mitigation internals may compile or run only through Qruba full platform endpoints depending on your license.

Write QIntent locally. Execute on QDSV.

## Links

- QDSV landing: https://qdsv.cloud
- QIntent site: https://qintent.qdsv.cloud
- Public API spec: https://api.qdsv.cloud/api/qintent/spec
- PyPI: https://pypi.org/project/qdsv-qintent/
