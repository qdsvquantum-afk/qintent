# QIntent Public Preview Grammar

This document describes the stable public preview subset exposed by the `qdsv-qintent` SDK.

QIntent is a declarative, Python-like language for expressing computational intent over state spaces, predicates, rows, ranking, and sampling.

## Row selection

```python
find_rows("candidate_index").where("score", ">=", 850)
find_rows("candidate_index").where_between("amount", 1000, 5000)
find_rows("candidate_index").where_all(["risk_ok", "income_ok"])
find_rows("candidate_index").where_any(["risk_ok", "manual_review_ok"])
find_rows("candidate_index").rank_by("score").top_k(10)
```

## Domain search

```python
x = domain(0, 15)
find(x).where(x in [3, 6, 9])
```

`range(...)` is accepted as a familiar alias in the public preview.

## Python-like expressions

Supported preview syntax:

- `not`
- `in`
- `not in`
- chained comparisons such as `700 <= score <= 950`
- `all([...])`
- `any([...])`
- `abs(...)`
- `round(...)`
- `min(...)`
- `max(...)`
- `clip(value, minimum, maximum)`
- `clamp(value, minimum, maximum)`

## Field access

```python
field(x, "score")
row["score"]
```

## Not supported in the public preview

QIntent is intentionally not full Python. The following are not supported:

- arbitrary imports
- file or network access from QIntent source
- classes
- function definitions
- unbounded loops
- arbitrary Python execution
- direct QDSV Runtime internals
- direct hardware adapter internals

## Execution model

The public SDK is a client. It sends QIntent source and optional data to the public API:

```text
write QIntent locally
send to QDSV API
compile / validate / execute remotely
receive results and evidence
```

The SDK does not install QDSV Runtime locally.
