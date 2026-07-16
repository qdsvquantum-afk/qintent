# QIntent Public Preview Grammar

QIntent is a declarative language for producing canonical QDSV problem intent. It does not execute arbitrary Python and does not own a separate compiler.

## Canonical route

```text
QIntent -> ProblemSpec -> Operation Compiler v2 -> QuantumCanonicalProgram
```

The same program can be realized through QuEST, a reversible circuit for Aer/IBM, or an export surface such as Bridge.

## State spaces and queries

```python
x = domain(0, 15)
find(x).where(and_(gte(x, 3), eq(mod(x, 2), 0)))

find_rows("candidate_index").where("score", ">=", 850)
find_rows("candidate_index").where_between("amount", 1000, 5000)
find_rows("candidate_index").where_all(["risk_ok", "income_ok"])
```

## ScoreModel v2

Flat:

```python
find_rows("candidate_index")
  .using_score_model([
      score_term("quality", importance=30, priority=2, adjustments=[
          score_adjustment("context", coefficient=0.10),
      ]),
      score_term("benefit", importance=40, priority=3),
  ], penalty=0.05)
  .accept_if(threshold=780, decision="gte")
```

Hierarchical:

```python
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
```

A score term may be a prepared similarity or any bounded numeric value/expression. ScoreModel supports contextual adjustments, term composition, flat or hierarchical aggregation, penalties, normalization and threshold decisions. Ranking is a later workflow/query concern, not part of the formula.

## Canonical operations

The public contract contains 43 operation identities:

```text
abs, abs_diff, add, and, between, ceil, clip, coalesce,
default_if_invalid, div, eq, field, floor, gt, gte, in_set,
is_null, lt, lte, max, mean_fields, min, mod, mul, ne, not,
not_null, or, outside, percent, ratio, round, safe_div, sign,
similarity, squared_diff, sub, sum_fields, vector,
vector_similarity, weighted_sum, within_tolerance, xor
```

Use `and_(...)`, `or_(...)` and `not_(...)` when a Python reserved word cannot be used as a function name. Operator syntax such as `+`, `-`, `*`, `/`, `%`, comparisons, `and`, `or` and `not` is also normalized into these operation identities.

## Field access

```python
field(x, "score")
row["score"]
```

Rows are attached through a bounded QDSV data binding. They are not scanned to precompute winning candidates before quantum materialization.

## Unsupported syntax

- imports, classes, function definitions or arbitrary Python
- file/network access
- unbounded loops
- direct calls to private runtime, lowering or hardware adapters

## IBM execution

The SDK can compile and submit through licensed deployments. Submission is allowed only after the public operation program reports `circuit_ready=true` and `answer_precomputed=false`.
