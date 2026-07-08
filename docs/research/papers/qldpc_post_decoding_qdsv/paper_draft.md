# QDSV/QIntent as a Risk-Aware Post-Decoding Decision Layer for LDPC/qLDPC-Style Quantum Error Correction Workflows

Working draft.

## Abstract

Quantum LDPC and qLDPC codes are promising candidates for scalable quantum error correction, but their practical value depends not only on code construction, but also on the ability to decode ambiguous syndrome information and select corrections that avoid logical failure. Current decoder families such as belief propagation (BP), BP+OSD, BP+LSD and related methods provide powerful correction mechanisms, yet practical workflows still face uncertainty in candidate selection, risk interpretation, reproducibility and auditability.

This paper evaluates QDSV/QIntent as a post-decoding semantic decision layer over LDPC/qLDPC-style correction candidates. QDSV/QIntent does not replace existing decoders. Instead, it receives decoder-generated candidates and prepared evidence signals, including syndrome consistency, decoder confidence, decoder agreement, logical-safety indicators, propagation safety and logical-risk proxies. It then performs structured candidate ranking and returns an auditable decision trace without exposing the private QDSV scoring formula.

We report four experimental stages. A controlled ambiguity benchmark demonstrates that QDSV/QIntent can select lower-risk correlated corrections when a minimum-weight baseline selects a risky singleton. A random sparse benchmark exposes cases where available evidence is insufficient and motivates richer decoder outputs. A BP-soft multi-seed benchmark over 480 scenarios shows stable logical-risk reduction, reducing average logical risk from 141.12 to 110.80 with 74 improved-risk selections and no worse-risk selections under that configuration. Finally, an external `ldpc` decoder-ensemble recovery benchmark uses real BP, BP+OSD and BP+LSD outputs. In 168 BP-failure scenarios, QDSV/QIntent recovered exact corrections in 53.1% of cases, reduced the logical-failure proxy from 48.7% to 24.2%, and reduced average logical risk from 165.02 to 129.14.

These results support the hypothesis that QDSV/QIntent can serve as a risk-aware, auditable post-decoding decision layer for LDPC/qLDPC-style workflows. The results do not establish production decoder superiority, real-time suitability or quantum advantage. They identify a complementary role for semantic decision logic in decoder pipelines and motivate further evaluation with production qLDPC codes, full logical-operator analysis and latency-aware implementations.

## 1. Introduction

Quantum error correction is a central requirement for scalable quantum computing. LDPC and qLDPC-style codes are attractive because they promise improved overhead properties compared with many conventional approaches. However, scalable code construction alone is not enough. The decoding workflow must interpret noisy syndromes, manage ambiguity, select corrections, avoid logical failures and do so under practical latency and reliability constraints.

Many decoders are optimized for likelihood, convergence, minimum weight, ordered-statistics search or localized statistics. These are essential mechanisms, but the final correction decision can still involve several competing criteria:

- Does the candidate match the syndrome?
- How confident is the decoder?
- Do multiple decoders agree?
- Does the correction touch structurally sensitive qubits?
- Does it increase propagation risk?
- Is it likely to preserve the logical subspace?
- Can the decision be audited and reproduced?

This work explores QDSV/QIntent in that decision gap. QDSV provides a semantic representation layer for structured evidence. QIntent provides a public declarative syntax for expressing candidate-ranking workflows. In the experiments reported here, QDSV/QIntent is evaluated primarily in the post-decoding phase: decoders generate candidates, and QDSV/QIntent ranks them using structured evidence and risk-aware decision logic.

## 2. Gap Analysis in LDPC/qLDPC Decoding

This paper focuses on practical gaps in the decoding workflow rather than proposing a new code family.

| Gap | Meaning in decoding workflow | QDSV/QIntent contribution in this work | Coverage estimate |
|---|---|---:|---:|
| Syndrome ambiguity | Multiple correction hypotheses can satisfy the same syndrome. | Represents candidates as decision states and evaluates syndrome, decoder and logical-safety evidence together. | ~60% |
| Candidate selection under competing criteria | The highest-confidence or minimum-weight correction may not be the safest correction. | Re-ranks candidates using structured evidence, confidence, agreement, risk and safety signals. | ~70% |
| Risk-aware correction choice | A locally plausible correction can be structurally risky or logical-sensitive. | Adds logical-risk, propagation-safety, distance-safety and logical-preservation proxies. | ~65% |
| Decoder disagreement | BP, BP+OSD, BP+LSD or alternative methods may produce different corrections. | Treats decoder outputs as an ensemble and selects across them using method reliability and evidence. | ~55% |
| Auditability and reproducibility | Decoder decisions often lack a structured, human-readable decision trace. | Produces public block-level evidence and reproducible JSON/CSV traces. | ~80% |
| Evidence insufficiency detection | Some cases cannot be resolved with the available signals. | Ambiguity audit detects observationally indistinguishable scenarios. | ~50% |
| Real-time latency | Decoding must eventually run under strict timing constraints. | Not solved. Current experiments are offline/local scripts. | ~10% |
| Full logical-operator preservation | A real qLDPC system requires formal logical operator analysis, not proxies. | Uses logical-risk/failure proxies only. | ~25% |
| Hardware noise and measurement faults | Real devices include correlated noise, readout errors and time dynamics. | Not yet evaluated with real hardware syndromes. | ~15% |
| Production qLDPC code families | Results should be tested on known production-relevant qLDPC constructions. | Current matrices are sparse synthetic LDPC/qLDPC-style structures. | ~25% |

Overall estimated coverage of the current work: approximately 45-55% of the broader qLDPC decoding workflow gap.

Coverage of the post-decoding decision subproblem: approximately 65-75%.

## 3. QDSV/QIntent Post-Decoding Model

The proposed workflow is:

```text
LDPC/qLDPC check structure
-> syndrome extraction
-> decoder outputs / candidate generation
-> prepared evidence signals
-> QDSV/QIntent structured semantic score
-> ranked correction
-> audit trace
```

The active contribution in this paper is the post-decoding decision layer. QDSV/QIntent does not replace BP, BP+OSD, BP+LSD or other decoder families. It consumes their outputs and organizes candidate evidence into structured blocks.

Public evidence blocks:

```text
syndrome
logical_safety
decoder
```

Representative signals:

```text
syndrome_support
check_consistency
decoder_confidence
decoder_margin
decoder_agreement
method_reliability
logical_preservation
distance_safety
propagation_safety
syndrome_risk
logical_risk
```

The internal QDSV decision formula is not exposed. The public QIntent layer exposes the declaration of blocks, signals, priorities, risk fields, selected candidate, rank, score and audit trace.

## 4. Methodology

Four experiments were conducted.

### Experiment 1: Controlled Ambiguity Benchmark

Purpose: verify whether QDSV/QIntent can select a lower-risk correlated correction when a minimum-weight baseline selects a risky singleton.

Design:

```text
H[sensitive] = H[safe_a] xor H[safe_b]
true_error = safe_a + safe_b
baseline selects sensitive
QDSV evaluates logical safety and risk
```

### Experiment 2: Random Sparse Benchmark with Ambiguity Audit

Purpose: move away from a fully constructed win case and test random sparse structures.

The experiment showed that some scenarios are observationally ambiguous: two scenarios can have the same visible candidate evidence but opposite ground truth. This motivates adding richer decoder evidence rather than only tuning weights.

### Experiment 3: BP-Soft Multi-Seed Benchmark

Purpose: test QDSV/QIntent over soft evidence produced by a lightweight BP message-passing process.

Design:

```text
sparse check matrix
-> sampled errors
-> BP posterior evidence
-> syndrome-compatible candidate enumeration
-> QDSV reranking
```

### Experiment 4: External `ldpc` Decoder-Ensemble Recovery

Purpose: evaluate QDSV/QIntent over real external decoder outputs.

Decoders:

```text
BpDecoder
BpOsdDecoder
BpLsdDecoder
low_weight_alt candidates
```

This experiment focuses on BP-failure scenarios. BP is the baseline. QDSV/QIntent selects across the decoder ensemble.

## 5. Experimental Results

### 5.1 Controlled Ambiguity Benchmark

| Metric | Baseline | QDSV/QIntent |
|---|---:|---:|
| Exact correction rate | 0/6 | 6/6 |
| Logical-failure proxy rate | 6/6 | 0/6 |
| Average logical risk | 263 | 56 |
| Average risk reduction | - | 207 |

Interpretation: QDSV/QIntent successfully selected the lower-risk correlated correction in the constructed ambiguity.

### 5.2 Random Sparse Benchmark

The random sparse benchmark showed that aggressive risk-first scoring can reduce risk but may sacrifice exactness, while balanced policies preserve more decoder agreement. The ambiguity audit identified cases that cannot be resolved from the available synthetic evidence alone.

Interpretation: QDSV/QIntent should not be tuned only as a risk minimizer. It needs richer decoder evidence and policy calibration.

### 5.3 BP-Soft Multi-Seed Benchmark

Configuration:

```text
12 seeds
40 samples per seed
480 total scenarios
```

| Metric | BP-confidence baseline | BP + QDSV/QIntent |
|---|---:|---:|
| Exact correction rate, mean | 0.7708 | 0.7896 |
| Exact correction rate, std | 0.0668 | 0.0657 |
| Logical-failure proxy rate, mean | 0.0542 | 0.0479 |
| Logical-failure proxy rate, std | 0.0431 | 0.0438 |
| Average logical risk, mean | 141.12 | 110.80 |
| Average logical risk, std | 13.03 | 11.38 |
| Improved-risk scenarios | - | 74/480 |
| Worse-risk scenarios | - | 0/480 |

Interpretation: QDSV/QIntent provided stable risk reduction across seeds with no worse-risk selections under this configuration. Exact correction improved modestly on average.

### 5.4 External `ldpc` Decoder-Ensemble Recovery

Configuration:

```text
External package: ldpc==2.4.1
Decoders: BP, BP+OSD, BP+LSD
Collected scenarios: BP-failure cases
Seeds: 8
Total BP-failure scenarios: 168
```

| Metric | BP-only baseline | QDSV over decoder ensemble |
|---|---:|---:|
| Exact correction rate, mean | 0.0000 | 0.5307 |
| Logical-failure proxy rate, mean | 0.4866 | 0.2420 |
| Average logical risk, mean | 165.02 | 129.14 |
| Average risk delta, mean | - | 35.88 |
| Improved-risk scenarios | - | 61/168 |
| Worse-risk scenarios | - | 28/168 |

Interpretation: when BP fails, QDSV/QIntent can recover exact corrections in a substantial fraction of cases by selecting over a decoder ensemble. It also reduces the logical-failure proxy and average logical risk. However, the existence of 28 worse-risk cases shows that policy calibration remains necessary.

## 6. Discussion

The strongest contribution of QDSV/QIntent in these experiments is not replacing a decoder. The contribution is structured decision-making over decoder outputs.

The experiments show three important behaviors:

1. QDSV/QIntent can use logical-risk and safety signals to override unsafe confidence-only selections.
2. When evidence is insufficient, ambiguity audits reveal where more decoder information is required.
3. With real external LDPC decoder outputs, QDSV/QIntent can recover from BP failures by selecting across BP, BP+OSD, BP+LSD and compatible alternatives.

The results suggest that QDSV/QIntent is most useful as a policy and audit layer in the post-decoding workflow:

```text
decoder candidate generation
-> semantic evidence organization
-> risk-aware candidate selection
-> reproducible decision trace
```

## 7. Limitations

This work remains preliminary.

Limitations:

- The check matrices are sparse synthetic LDPC/qLDPC-style structures.
- The logical-failure metric is a proxy, not a full logical-operator analysis.
- The experiments are offline and do not evaluate real-time latency.
- The external `ldpc` experiment focuses on BP-failure recovery and does not claim superiority over BP+OSD itself.
- The QDSV policy still produces worse-risk selections in some ensemble cases.
- No real hardware syndrome stream is used.

## 8. Future Work

Before submission to a stronger venue, the most important next steps are:

1. Add full logical operator analysis rather than a proxy.
2. Test known LDPC/qLDPC code constructions rather than only synthetic sparse matrices.
3. Tune guarded decision policies to reduce worse-risk cases in ensemble recovery.
4. Measure latency and identify which parts could run in real-time versus offline audit.
5. Evaluate noisy syndrome/readout conditions using `SoftInfoBpDecoder` or related workflows.
6. Compare against BP+OSD/BP+LSD as baselines, while keeping the claim focused on post-decoding policy rather than decoder replacement.

### 8.1 Hardware-Oriented Validation Readiness

The next immediate validation step is a small IBM hardware-oriented syndrome experiment. The goal is not to claim production qLDPC decoding, but to validate the handoff:

```text
IBM hardware counts
-> syndrome evidence
-> candidate correction hypotheses
-> QDSV/QIntent post-decoding ranking
-> reproducible audit evidence
```

A Colab-ready notebook has been prepared for this step:

```text
notebooks/qldpc_ibm_hardware_syndrome_validation_colab.ipynb
```

The notebook runs first on Aer, then optionally on IBM Quantum hardware using a user-supplied IBM token. The QDSV/QIntent side does not require a QDSV API key for this public workflow.

If successful, this validation can support a cautious paper statement: QDSV/QIntent can consume hardware-derived syndrome-count evidence and produce the same kind of auditable post-decoding candidate ranking already demonstrated in local and external-decoder benchmarks.

## 9. Reproducibility

Evidence and scripts are archived in the QIntent repository.

Scripts:

```text
docs/research/scripts/qldpc_bp_soft_multiseed.py
docs/research/scripts/qldpc_ldpc_ensemble_recovery.py
```

Hardware-oriented validation plan:

```text
docs/research/papers/qldpc_post_decoding_qdsv/ibm_hardware_validation_plan.md
notebooks/qldpc_ibm_hardware_syndrome_validation_colab.ipynb
```

Evidence:

```text
docs/research/evidence/qdsv_qldpc_formal_benchmark_evidence.json
docs/research/evidence/qdsv_qldpc_formal_benchmark_summary.csv
docs/research/evidence/qdsv_qldpc_bp_soft_decoder_evidence.json
docs/research/evidence/qdsv_qldpc_bp_soft_decoder_summary.csv
docs/research/evidence/qdsv_qldpc_bp_soft_multiseed_evidence.json
docs/research/evidence/qdsv_qldpc_bp_soft_multiseed_summary.csv
docs/research/evidence/qdsv_qldpc_bp_soft_multiseed_metrics.csv
docs/research/evidence/qdsv_qldpc_real_ldpc_ensemble_recovery_evidence.json
docs/research/evidence/qdsv_qldpc_real_ldpc_ensemble_recovery_summary.csv
docs/research/evidence/qdsv_qldpc_real_ldpc_ensemble_recovery_metrics.csv
```

## 10. Conclusion

This paper evaluates QDSV/QIntent as a risk-aware post-decoding semantic decision layer for LDPC/qLDPC-style quantum error correction workflows.

The results support a focused conclusion: QDSV/QIntent can organize decoder-generated correction candidates into structured evidence blocks and apply decision logic that reduces logical-risk proxies and recovers corrections in selected BP-failure regimes.

The most important result is the external `ldpc` ensemble recovery benchmark: in 168 BP-failure scenarios, QDSV/QIntent recovered exact corrections in 53.1% of cases and reduced the logical-failure proxy from 48.7% to 24.2%.

The work does not claim a new qLDPC decoder, production readiness or quantum advantage. It contributes evidence for a complementary semantic decision layer that can sit after existing decoders and support risk-aware, auditable correction selection.
