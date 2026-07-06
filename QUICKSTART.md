# QIntent SDK Quickstart

Install:

```bash
pip install qdsv-qintent
```

Run a first query:

```python
from qintent import QIntentClient

client = QIntentClient()

rows = [
    {"candidate_index": 0, "score": 720},
    {"candidate_index": 1, "score": 910},
]

result = client.run(
    'find_rows("candidate_index").where("score", ">=", 850)',
    rows=rows,
)

print(result["status"])
print(result["result"]["selected_rows"])
```

Compile without running:

```python
compiled = client.compile(
    'x = domain(0, 15)\nfind(x).where(x in [3, 6, 9])'
)

print(compiled["compiled_summary"])
```

Explain an intent before running it:

```python
passport = client.explain(
    'i = domain(0, 3)\nfind(i).where(within_tolerance(field(i, "amount_a"), field(i, "amount_b"), 5))',
    rows=[
        {"candidate_index": 0, "amount_a": 100, "amount_b": 104},
        {"candidate_index": 1, "amount_a": 100, "amount_b": 130},
    ],
)

print(passport["semantic_execution_passport"]["execution_plan"])
```

Use controlled QDSV helpers:

```python
source = """
i = domain(0, 3)
gap = abs_diff(field(i, "amount_a"), field(i, "amount_b"))
score = weighted_sum([coalesce(field(i, "quality"), 0), max(0, 1000 - gap)], [0.6, 0.4])
find(i).where(between(score, 700, 1000)).rank_by(score).top_k(2)
"""
```

Use Docker/private local API:

```python
client = QIntentClient.local()
```

Private Docker/local execution is available only when a private QDSV node is online. If it is unavailable, it may be offline, reserved for private processing, or temporarily busy. Use `QIntentClient()` for public cloud examples.

QIntent is a declarative intent language powered by QDSV. The SDK is a client only; it does not install QDSV Runtime locally.

Public informational endpoints can be viewed without a key. Public demo deployments also allow value-producing calls such as `validate`, `compile`, `explain` and `run` without a key, using deployment-controlled IP or optional API-key quota buckets.
