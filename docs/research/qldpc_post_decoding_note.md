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

## Random Sparse and BP-Soft Follow-Up

After the controlled benchmark, two follow-up notebooks were added to test less constructed settings.

The random sparse benchmark generates a sparse check matrix, random error samples, low-weight syndrome-compatible candidates, and compares three public policies:

```text
baseline
risk_first
balanced
guarded_balanced
```

This benchmark showed an important limitation: some scenarios are observationally ambiguous under the available candidate evidence. In particular, two scenarios can have the same observable candidate structure while the correct decision differs. This is not a failure of QDSV/QIntent; it indicates that a post-decoding policy needs richer decoder evidence than synthetic confidence and risk fields alone.

The next notebook therefore adds a lightweight BP-style soft decoder. BP produces posterior error probabilities and a decoder margin, which are used as additional prepared evidence. QDSV/QIntent then re-ranks the BP-generated candidate set.

### BP-Soft Benchmark Results

The BP-soft benchmark used:

```text
N_QUBITS = 24
M_CHECKS = 8
N_SAMPLES = 40
MAX_CANDIDATE_WEIGHT = 3
PHYSICAL_ERROR_RATE = 0.14
```

Summary:

| Metric | BP-confidence baseline | BP + QDSV/QIntent |
|---|---:|---:|
| Exact correction rate | 0.725 | 0.875 |
| Logical-failure proxy rate | 0.000 | 0.000 |
| Average logical risk | 153.05 | 109.80 |
| Average risk delta | - | 43.25 |
| Improved-risk scenarios | - | 10/40 |
| Worse-risk scenarios | - | 0/40 |
| Average exact-delta | - | +0.15 |

Representative changed scenarios include cases where the BP-confidence baseline selected a high-confidence but non-exact correction, while QDSV/QIntent selected the exact lower-risk correction using structured evidence from decoder confidence, decoder margin, logical preservation, distance safety and propagation safety.

This result is stronger than the controlled benchmark because QDSV/QIntent is no longer operating only over a hand-shaped ambiguity. It is receiving soft evidence from a decoder-style message-passing process. The result still remains a toy sparse-check benchmark, but it supports the narrower claim that QDSV/QIntent can act as a structured decision layer over decoder outputs.

### Multi-Seed BP-Soft Results

To test whether the BP-soft result was seed-specific, the experiment was repeated locally across 12 seeds with 40 samples per seed, for a total of 480 scenarios.

Aggregate summary:

| Metric | BP-confidence baseline | BP + QDSV/QIntent |
|---|---:|---:|
| Exact correction rate, mean | 0.7708 | 0.7896 |
| Exact correction rate, std | 0.0668 | 0.0657 |
| Logical-failure proxy rate, mean | 0.0542 | 0.0479 |
| Logical-failure proxy rate, std | 0.0431 | 0.0438 |
| Average logical risk, mean | 141.12 | 110.80 |
| Average logical risk, std | 13.03 | 11.38 |
| Average risk delta, mean | - | 30.32 |
| Average risk delta, std | - | 10.29 |
| Improved-risk scenarios | - | 74/480 |
| Worse-risk scenarios | - | 0/480 |

The multi-seed run is more conservative than the single-seed example. It does not show uniform exact-correction improvement across every seed. However, it does show a stable reduction in average logical-risk score, no worse-risk selections across the 480 scenarios, a small positive mean exact-correction delta, and a small positive mean failure-proxy delta.

This supports a more careful claim: QDSV/QIntent appears useful as a risk-aware post-decoding decision layer over BP-soft candidates, especially when the objective includes risk reduction and auditability rather than exact correction alone.

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

These benchmarks should not be interpreted as full production qLDPC decoding benchmarks.

Important limitations:

- The sparse check structures are synthetic.
- The candidate generator is exhaustive over low-weight hypotheses.
- The BP-soft decoder is a lightweight notebook implementation, not an optimized production decoder.
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

The BP-soft follow-up benchmark is available here:

[qLDPC BP-soft decoder reranking Colab](https://colab.research.google.com/github/qdsvquantum-afk/qintent/blob/main/notebooks/qldpc_bp_soft_decoder_reranking_colab.ipynb)

The multi-seed local benchmark script is available here:

[scripts/qldpc_bp_soft_multiseed.py](scripts/qldpc_bp_soft_multiseed.py)

The notebooks generate:

```text
qdsv_qldpc_formal_benchmark_evidence.json
qdsv_qldpc_formal_benchmark_summary.csv
qdsv_qldpc_bp_soft_decoder_evidence.json
qdsv_qldpc_bp_soft_decoder_summary.csv
qdsv_qldpc_bp_soft_multiseed_evidence.json
qdsv_qldpc_bp_soft_multiseed_summary.csv
qdsv_qldpc_bp_soft_multiseed_metrics.csv
```

The generated evidence used for this note is archived in this repository:

- [evidence/qdsv_qldpc_formal_benchmark_evidence.json](evidence/qdsv_qldpc_formal_benchmark_evidence.json)
- [evidence/qdsv_qldpc_formal_benchmark_summary.csv](evidence/qdsv_qldpc_formal_benchmark_summary.csv)
- [evidence/qdsv_qldpc_bp_soft_decoder_evidence.json](evidence/qdsv_qldpc_bp_soft_decoder_evidence.json)
- [evidence/qdsv_qldpc_bp_soft_decoder_summary.csv](evidence/qdsv_qldpc_bp_soft_decoder_summary.csv)
- [evidence/qdsv_qldpc_bp_soft_multiseed_evidence.json](evidence/qdsv_qldpc_bp_soft_multiseed_evidence.json)
- [evidence/qdsv_qldpc_bp_soft_multiseed_summary.csv](evidence/qdsv_qldpc_bp_soft_multiseed_summary.csv)
- [evidence/qdsv_qldpc_bp_soft_multiseed_metrics.csv](evidence/qdsv_qldpc_bp_soft_multiseed_metrics.csv)

The QIntent public preview endpoint used in the notebook exposes:

```text
api_key_required_for: []
monthly_request_quota_scope: ip_or_optional_api_key
```

## Conclusion

The controlled benchmark supports the hypothesis that QDSV/QIntent can act as a risk-aware post-decoding decision layer for qLDPC-style correction candidates. In a constructed ambiguity where a high-confidence singleton competes against a lower-confidence correlated correction with the same syndrome, QDSV consistently selected the exact lower-risk correction and avoided the logical-failure proxy.

The BP-soft follow-up adds a more realistic signal source: posterior evidence from a message-passing decoder. In that toy benchmark, QDSV/QIntent improved exact correction rate from 0.725 to 0.875, reduced average logical risk from 153.05 to 109.80, and did not increase the logical-failure proxy.

The multi-seed run gives a more stable view: across 480 scenarios, QDSV/QIntent reduced average logical risk from 141.12 to 110.80, produced 74 improved-risk selections, and produced no worse-risk selections under this benchmark configuration. Exact correction and failure proxy showed smaller average improvements and varied by seed.

The result is not yet evidence of production qLDPC decoder superiority. It is evidence that the QDSV structured semantic decision layer is capable of using decoder confidence, decoder margin, logical-risk and safety evidence to re-rank decoder-generated candidates in a reproducible and auditable way.
