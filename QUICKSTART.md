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

Use Docker/private local API:

```python
client = QIntentClient.local()
```

Private Docker/local execution is available only when a private QDSV node is online. If it is unavailable, it may be offline, reserved for private processing, or temporarily busy. Use `QIntentClient()` for public cloud examples.

QIntent is a declarative intent language powered by QDSV. The SDK is a client only; it does not install QDSV Runtime locally.
