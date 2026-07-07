# QDSV/QIntent as a Risk-Aware Post-Decoding Layer for qLDPC-Style Correction Candidates

Technical note, public preview.

## Abstract

This note describes a controlled qLDPC-style benchmark evaluating QDSV/QIntent as a risk-aware post-decoding decision layer. The experiment does not propose a new qLDPC decoder and does not claim quantum advantage. Instead, it tests a narrower question: given a set of syndrome-compatible correction candidates, can a structured semantic decision layer select a lower-risk correction than a confidence-only or minimum-weight decoder policy?

In the controlled benchmark, a sparse CSS/qLDPC-style syndrome map is constructed so that a correlated two-qubit correction and a logical-sensitive single-qubit correction produce the same syndrome. A likelihood/minimum-weight baseline selects the high-confidence singleton, while QDSV structured semantic scoring selects the lower-risk correlated correction. Across six controlled scenarios, the baseline selected the exact correction in 0/6 cases and triggered the logical-failure proxy in 6/6 cases. QDSV selected the exact correction in 6/6 cases and avoided the logical-failure proxy in 6/6 cases, reducing the logical-risk score from 263 to 56 in each scenario.

## Motivation

qLDPC codes are a leading direction for scalable quantum error correction because they promise better asymptotic overhead than many conventional surface-code-style constructions. However, the value of a qLDPC code depends not only on the code family, but also on the ability to decode noisy, ambiguous syndrome information quickly and reliably.

In practical decoding workflows, a syndrome can be compatible with multiple correction hypotheses. A decoder policy that prioritizes likelihood or minimum weight may choose a high-confidence correction that is locally plausible but structurally risky. This motivates a complementary decision layer that can evaluate decoder-generated candidates against additional structure:

- syndrome consistency;
- logical-subspace preservation;
- distance safety;
- propagation safety;
- candidate risk;
- auditability of the final decision.

QDSV/QIntent is evaluated here in that complementary role. The objective is not to replace BP, OSD, MWPM, neural decoders, or qLDPC-specific decoders. The objective is to test whether a semantic decision layer can re-rank candidate corrections when decoder confidence alone is not sufficient.

## QDSV Role

The benchmark separates two roles:

1. Candidate generation remains a decoding task.
2. Candidate selection is evaluated through QDSV/QIntent as a structured semantic scoring workflow.

The QDSV/QIntent post-decoding representation treats each candidate correction as a decision state. Each state carries prepared evidence signals:

- `syndrome_support`;
- `check_consistency`;
- `logical_preservation`;
- `distance_safety`;
- `decoder_confidence`;
- `propagation_safety`;
- `syndrome_risk`;
- `logical_risk`;
- `syndrome_entropy_adjustment`.

These signals are grouped into public evidence blocks:

```text
syndrome
logical_safety
decoder
```

The internal QDSV scoring formula is not exposed. The public layer exposes the declared blocks, signals, risk fields, selected candidate, rank, score, and audit trace.

## Controlled Benchmark Design

The controlled benchmark builds a sparse CSS/qLDPC-style syndrome map with six repeated blocks. Each block contains two safer qubits and one logical-sensitive qubit:

```text
safe_a
safe_b
sensitive
```

The check columns are constructed so that:

```text
H[sensitive] = H[safe_a] xor H[safe_b]
```

Therefore, the same observed syndrome can be explained by:

```text
correction A: sensitive
correction B: safe_a + safe_b
```

The simulated true error is the correlated pair:

```text
true_error = safe_a + safe_b
```

The baseline decoder policy uses a likelihood/minimum-weight orientation. Since the singleton has lower weight, it receives higher decoder confidence:

```text
baseline correction = sensitive
baseline confidence = 1000
```

QDSV receives the same candidate set, but the structured scoring workflow also considers logical risk, logical preservation, distance safety, propagation safety, and block-level evidence.

## QIntent Declaration

The benchmark uses the public-preview operation:

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
  ], global_risk="logical_risk", profile="qldpc_formal_benchmark")
  .accept_if(threshold=600)
  .rank()
  .top_k(1)
```

The public explain output confirms:

```text
kind: structured_semantic_score
blocks_count: 3
signals_count: 6
internal_formula_exposed: false
```

## Results

The controlled benchmark produced six scenarios.

Summary:

| Metric | Baseline | QDSV/QIntent |
|---|---:|---:|
| Exact correction rate | 0/6 | 6/6 |
| Logical-failure proxy rate | 6/6 | 0/6 |
| Average logical risk | 263 | 56 |
| Average risk reduction | - | 207 |

Representative scenario:

| Field | Baseline | QDSV/QIntent |
|---|---:|---:|
| True error | `0 1` | `0 1` |
| Selected correction | `2` | `0 1` |
| Decoder confidence | 1000 | 600 |
| Logical risk | 263 | 56 |
| Exact correction | false | true |
| Logical-failure proxy | true | false |

Interpretation:

The baseline selects the high-confidence singleton because it is the minimum-weight hypothesis. QDSV/QIntent selects the lower-confidence correlated correction because it has stronger logical safety and lower risk. This is the intended behavior of a post-decoding decision layer: it does not replace the decoder, but it can re-rank decoder-generated candidates when confidence alone is structurally unsafe.

## Audit Trace

For the selected QDSV correction, the public audit trace includes block-level evidence:

```text
syndrome block
logical_safety block
decoder block
global_risk
selected
rank
profile
```

The selected candidate trace includes:

```text
profile: qldpc_formal_benchmark
public_operation: structured_semantic_score
internal_formula_exposed: false
```

This gives reviewers a reproducible decision trace without exposing the private QDSV scoring formula.

## Limitations

This benchmark is controlled and intentionally constructed. It should not be interpreted as a full qLDPC decoding benchmark.

Important limitations:

- The sparse check structure is synthetic.
- The candidate generator is exhaustive over low-weight hypotheses, not a production qLDPC decoder.
- The logical-failure proxy is a controlled structural proxy, not a full logical operator analysis over a production code.
- The benchmark tests a post-decoding decision layer, not a real-time hardware decoder.
- The public API executes the structured decision workflow over prepared evidence; it does not execute a quantum circuit for this benchmark.

## Next Experimental Step

The next step is to replace the controlled candidate generator with a real decoder pipeline:

```text
qLDPC / CSS code
-> noise model
-> syndrome samples
-> BP / OSD / LSD / other decoder candidates
-> QDSV structured semantic score
-> correction ranking
-> exact correction / logical failure / risk / audit metrics
```

The target comparison should be:

```text
decoder only
vs
decoder + QDSV post-decoding decision layer
```

Metrics should include:

- exact correction rate;
- logical failure rate or proxy;
- risk reduction;
- ambiguity resolution;
- ranking stability;
- added latency;
- audit trace completeness.

## Reproducibility

The controlled benchmark is available as a Colab notebook:

[qLDPC controlled formal benchmark Colab](https://colab.research.google.com/github/qdsvquantum-afk/qintent/blob/main/notebooks/qldpc_formal_benchmark_colab.ipynb)

The notebook generates:

```text
qdsv_qldpc_formal_benchmark_evidence.json
qdsv_qldpc_formal_benchmark_summary.csv
```

The QIntent public preview endpoint used in the notebook exposes:

```text
api_key_required_for: []
monthly_request_quota_scope: ip_or_optional_api_key
```

## Conclusion

The controlled benchmark supports the hypothesis that QDSV/QIntent can act as a risk-aware post-decoding decision layer for qLDPC-style correction candidates. In a constructed ambiguity where a high-confidence singleton competes against a lower-confidence correlated correction with the same syndrome, QDSV consistently selected the exact lower-risk correction and avoided the logical-failure proxy.

The result is not yet evidence of production qLDPC decoder superiority. It is evidence that the QDSV structured semantic decision layer is capable of using logical-risk and safety evidence to re-rank decoder-generated candidates in a reproducible and auditable way.
