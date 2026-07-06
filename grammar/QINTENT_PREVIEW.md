# QIntent Public Preview Grammar

This document describes the stable public preview subset exposed by the `qdsv-qintent` SDK.

QIntent is a declarative quantum-intent language for expressing computational intent over state spaces, operations, predicates, relations, transformations, rows, ranking, sampling, and evidence.

The syntax is Python-inspired for developer ergonomics. The semantics are QDSV-native: state spaces, operations, predicates, relations, transformations, ranking, sampling, evidence, and backend-independent execution intent.

## Semantic scope

The public preview exposes a safe subset first. Row selection, ranking, `using_decision_model(...)` and `using_semantic_score(...)` are supported operations, not the full ceiling of the QDSV model.

At the model level, QDSV is designed to represent computable semantics as operations, predicates, relations, transformations, observations, distributions, constraints, and evidence over state spaces. Circuit materialization is a backend-dependent representation, not the starting point of the language.

## Row selection

```python
find_rows("candidate_index").where("score", ">=", 850)
find_rows("candidate_index").where_between("amount", 1000, 5000)
find_rows("candidate_index").where_all(["risk_ok", "income_ok"])
find_rows("candidate_index").where_any(["risk_ok", "manual_review_ok"])
find_rows("candidate_index").rank_by("score").top_k(10)
find_rows("candidate_index").using_decision_model([...]).accept_if(threshold=850).rank().top_k(10)
find_rows("candidate_index").using_semantic_score([...], risk_adjustment="risk").accept_if(threshold=850).rank().top_k(10)
find_rows("candidate_index").using_structured_semantic_score([...], global_risk="risk", profile="qldpc_post_decoding").accept_if(threshold=850).rank().top_k(10)
```

### Decision model

`using_decision_model(...)` declares a prebuilt QDSV decision operation over prepared criteria without exposing the internal formula.

Each criterion is a prepared value: a comparable, oriented value that represents something meaningful about the process. This lets the prebuilt decision operation work across different domains without hard-coding those domains into the language.

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

Typical mappings start from raw data and convert it into comparable prepared values before QIntent evaluates or ranks candidates.

### Semantic score

`using_semantic_score(...)` declares an advanced QDSV semantic scoring operation over prepared signals without exposing the internal formula.

Use it when each candidate already has comparable evidence fields, operational influence, priority, and an optional prepared risk adjustment.

```python
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
```

Each `signal(...)` uses:

- `field`: prepared signal column.
- `influence`: operational influence of the signal.
- `priority`: optional priority modifier, defaulting to `1`.

`risk_adjustment` may be a prepared field name or a numeric constant. QDSV uses it internally as a controlled risk adjustment while keeping the private scoring representation inside the runtime.

### Structured semantic score

`using_structured_semantic_score(...)` declares an advanced QDSV structured scoring operation over prepared signal blocks without exposing the internal hierarchical or nonlinear formula.

Use it when candidates are naturally evaluated through groups of evidence, local risk, global risk and prepared adjustment fields.

```python
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
```

Each `block(...)` uses:

- `name`: public operational block name.
- `signals`: list of `signal(...)` prepared fields.
- `influence`: operational influence of the block.
- `priority`: optional priority modifier, defaulting to `1`.
- `risk_adjustment`: optional prepared field name or numeric constant.
- `adjustments`: optional list of prepared `adjustment(...)` fields.

Each `adjustment(...)` uses:

- `field`: prepared adjustment column.
- `influence`: operational influence of the adjustment.

The public API exposes declared blocks, signals, risk fields and evidence outputs. The private QDSV hierarchical/nonlinear scoring representation remains inside the runtime.

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
- `floor(...)`
- `ceil(...)`
- `sign(...)`
- `min(...)`
- `max(...)`
- `clip(value, minimum, maximum)`
- `clamp(value, minimum, maximum)`
- `between(value, minimum, maximum)`
- `outside(value, minimum, maximum)`
- `abs_diff(left, right)`
- `squared_diff(left, right)`
- `similarity(left, right)`
- `vector_similarity(left_vector, right_vector)`
- `within_similarity(left, right, threshold)`
- `within_vector_similarity(left_vector, right_vector, threshold)`
- `within_tolerance(left, right, tolerance)`
- `safe_div(numerator, denominator[, default])`
- `ratio(numerator, denominator)`
- `percent(part, total)`
- `is_null(value)`
- `not_null(value)`
- `coalesce(value, fallback, ...)`
- `default_if_invalid(value, fallback)`
- `sum_fields([value_a, value_b, ...])`
- `mean_fields([value_a, value_b, ...])`
- `weighted_sum([value_a, value_b, ...], [weight_a, weight_b, ...])`

These are QDSV primitives, not arbitrary Python built-ins. They are intended for bounded predicates, safe numeric handling, tolerance checks, semantic relations, null handling, and row-level signal aggregation.

Example:

```python
i = domain(0, 9)
gap = abs_diff(field(i, "amount_a"), field(i, "amount_b"))
quality = coalesce(field(i, "quality"), 0)
score = weighted_sum([quality, max(0, 1000 - gap)], [0.6, 0.4])
find(i).where(within_tolerance(field(i, "amount_a"), field(i, "amount_b"), 5) and between(score, 700, 1000))
```

Semantic similarity example:

```python
i = domain(0, 9)
sim = similarity(field(i, "reference_a"), field(i, "reference_b"))
find(i).where(sim >= 850).rank_by(sim).top_k(10)
```

`similarity(...)` returns a prepared 0..1000 relation signal. It can become part of the intent, predicate, ranking objective, or decision-model input. On QuEST, QDSV can represent it through the semantic/statevector route without user-written circuits; circuit materialization is only used when a selected backend requires and supports it.

Quantum vector similarity example:

```python
i = domain(0, 9)
left_state = [field(i, "a1"), field(i, "a2"), field(i, "a3")]
right_state = [field(i, "b1"), field(i, "b2"), field(i, "b3")]
overlap = vector_similarity(left_state, right_state)
find(i).where(overlap >= 850).rank_by(overlap).top_k(10)
```

`vector_similarity(...)` returns a 0..1000 normalized-overlap / fidelity score over equal-length numeric vectors. It is intended for prepared features, embeddings, amplitudes or state-like signals with comparable meaning.

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

## Explain model

The public preview exposes `client.explain(...)` and `POST /api/qintent/explain`.

`explain` returns a Semantic Execution Passport instead of executing the problem. The passport describes:

- intent type
- state-space source and size
- predicate or decision-model shape
- selected backend path
- whether user-written circuits are required
- whether backend circuit materialization is required
- backend availability roles
- source, predicate, IR, or process-data digests

Default public narrative:

```text
QIntent -> QDSV -> QuEST/statevector -> no user-written circuits
```

`logical` may appear as an internal/dev/reference semantic validation role. IBM hardware execution is part of Qruba/full platform configurations and is not enabled by the public SDK preview.
