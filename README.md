# qdsv-qintent

Lightweight Python client for **QIntent**, the native intent language powered by QDSV.

QIntent lets you write declarative computational intent over state spaces, rows, predicates, ranking, and sampling without installing the QDSV runtime locally.

```bash
pip install qdsv-qintent
```

> Developer Preview: the package is a client SDK. It does not include QDSV Runtime, CAP, QuEST, Aer, IBM adapters, lowering, noise mitigation internals, or crypto internals.

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
