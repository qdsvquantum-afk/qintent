# QIntent Public Preview Grammar

This document describes the stable public preview subset exposed by the `qdsv-qintent` SDK.

QIntent is a declarative quantum-intent language for expressing computational intent over state spaces, predicates, rows, ranking, and sampling.

The syntax is Python-inspired for developer ergonomics. The semantics are QDSV-native: state spaces, predicates, ranking, sampling, evidence, and backend-independent execution intent.

## Row selection

```python
find_rows("candidate_index").where("score", ">=", 850)
find_rows("candidate_index").where_between("amount", 1000, 5000)
find_rows("candidate_index").where_all(["risk_ok", "income_ok"])
find_rows("candidate_index").where_any(["risk_ok", "manual_review_ok"])
find_rows("candidate_index").rank_by("score").top_k(10)
find_rows("candidate_index").using_decision_model([...]).accept_if(threshold=850).rank().top_k(10)
```

### Decision model

`using_decision_model(...)` declares a prebuilt QDSV decision operation over prepared criteria without exposing the internal formula.

```python
find_rows("candidate_index")
  .using_decision_model([
      criterion("credit_score_norm", importance=25, priority=1),
      criterion("default_score", importance=25, priority=1),
      criterion("debt_burden_score", importance=20, priority=1),
  ])
  .accept_if(threshold=850)
  .rank()
  .top_k(10)
```

Each `criterion(...)` uses:

- `field`: prepared signal column.
- `importance`: semantic influence of the criterion.
- `priority`: optional priority modifier, defaulting to `1`.

QDSV maps the criteria internally into a state-space representation for selection, ranking, confidence, and evidence. The internal formula is not part of the public QIntent grammar.

## Domain search

```python
x = domain(0, 15)
find(x).where(x in [3, 6, 9])
```

`range(...)` is accepted as a familiar alias in the public preview.

## Expression ergonomics

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

QDSV may execute QIntent directly through semantic/statevector routes when possible. Circuit materialization is optional and is used only when a selected backend requires it.
