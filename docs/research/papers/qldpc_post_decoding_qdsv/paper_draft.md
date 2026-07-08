# QDSV/QIntent as a Guarded Semantic Decision Layer for LDPC/qLDPC-Style Post-Decoding Correction Governance

Working draft.

## Abstract

Quantum LDPC and qLDPC codes are promising candidates for scalable quantum error correction, but their practical value depends not only on code construction and decoder design. As correction pipelines scale, a second problem appears after decoding: when several correction hypotheses are plausible, uncertain or conflicting, which hypothesis should be trusted?

This paper evaluates QDSV/QIntent as a guarded semantic decision layer for post-decoding correction-hypothesis governance. QDSV/QIntent does not replace existing decoders. Instead, it receives decoder-generated candidates and prepared evidence signals, including syndrome consistency, decoder confidence, decoder agreement, logical-safety indicators, propagation safety and logical-risk proxies. It then performs structured candidate evaluation and returns an auditable decision trace without exposing the private QDSV scoring formula.

We report five experimental stages. A controlled ambiguity benchmark demonstrates that QDSV/QIntent can select lower-risk correlated corrections when a minimum-weight baseline selects a risky singleton. A random sparse benchmark exposes cases where available evidence is insufficient and motivates richer decoder outputs. A BP-soft multi-seed benchmark over 480 scenarios shows that raw QDSV improves exact rate from 0.7708 to 0.7896 and reduces average logical risk from 141.12 to 110.80, while guarded QDSV reduces bad overrides from 5.83% to 1.46%. An external `ldpc` decoder-ensemble recovery benchmark uses real BP, BP+OSD and BP+LSD outputs. In 168 BP-failure scenarios, raw QDSV recovered exact corrections in 53.1% of cases, reduced the logical-failure proxy from 48.7% to 24.2%, and reduced average logical risk from 165.02 to 129.14. The guarded policy accepted fewer overrides but reduced bad overrides from 16.18% to 0.69% and eliminated worse-risk selections. Finally, a preliminary IBM Quantum hardware-oriented syndrome validation on `ibm_fez` shows that syndrome-count evidence from real hardware can be handed into the same QDSV/QIntent decision workflow; guarded QDSV rejected the raw override that sacrificed exactness in the `x1` scenario.

These results support the hypothesis that QDSV/QIntent can serve as a decoder-agnostic, guarded, auditable post-decoding decision layer for LDPC/qLDPC-style workflows. The results do not establish production decoder superiority, real-time suitability or quantum advantage. They identify a complementary role for semantic decision governance in decoder pipelines and motivate further evaluation with production qLDPC codes, full logical-operator analysis and latency-aware implementations.

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

This work explores QDSV/QIntent in that decision-governance gap. QDSV provides a semantic representation layer for structured evidence. QIntent provides a public declarative syntax for expressing correction-hypothesis decision workflows. In the experiments reported here, QDSV/QIntent is evaluated primarily in the post-decoding phase: decoders generate candidates, and QDSV/QIntent governs whether a correction hypothesis should be accepted, rejected or overridden using structured evidence, risk-aware decision logic and guarded acceptance policies.

## 2. Gap Analysis in LDPC/qLDPC Decoding

This paper focuses on practical gaps in the decoding workflow rather than proposing a new code family.

| Gap | Meaning in decoding workflow | Current QDSV/QIntent contribution | Next validation step | Current coverage | Target after next step |
|---|---|---|---|---:|---:|
| Syndrome ambiguity | Multiple correction hypotheses can satisfy the same syndrome. | Represents candidates as decision states and evaluates syndrome, decoder and logical-safety evidence together. | Add hardware-derived syndrome-count evidence and compare Aer vs IBM observed syndromes. | ~60% | ~70% |
| Candidate selection under competing criteria | The highest-confidence or minimum-weight correction may not be the safest correction. | Compares baseline, raw QDSV and guarded QDSV using structured evidence, confidence, risk and safety signals. | Add oracle-best and policy-ablation baselines. | ~78% | ~85% |
| Risk-aware correction choice | A locally plausible correction can be structurally risky or logical-sensitive. | Adds logical-risk, propagation-safety, distance-safety and logical-preservation proxies; guarded QDSV prevents unsafe overrides. | Replace part of the proxy logic with explicit logical-observable or stabilizer-derived sensitivity features. | ~72% | ~80% |
| Decoder disagreement | BP, BP+OSD, BP+LSD or alternative methods may produce different corrections. | Treats decoder outputs as an ensemble and selects across them using method reliability, risk and guarded override evidence. | Compare against BP+OSD-preferred, BP+LSD-preferred and oracle-best ensemble baselines. | ~65% | ~78% |
| Auditability and reproducibility | Decoder decisions often lack a structured, human-readable decision trace. | Produces public block-level evidence, reproducible JSON/CSV traces and IBM job/backend metadata. | Add repeated hardware runs and cross-backend comparison. | ~86% | ~90% |
| Evidence insufficiency detection | Some cases cannot be resolved with the available signals. | Ambiguity audit now includes low-margin, decoder-disagreement, evidence-insufficient flags, IBM syndrome-count dispersion and guarded rejection reasons. | Add repeated hardware runs and uncertainty calibration. | ~70% | ~78% |
| Real-time latency | Decoding must eventually run under strict timing constraints. | Offline timing instrumentation now reports decode, candidate generation, QDSV scoring and total policy time. | Compare local timing against Colab/IBM-derived workflow timings and identify real-time-compatible substeps. | ~25% | ~35% |
| Full logical-operator preservation | A real qLDPC system requires formal logical operator analysis, not proxies. | Uses logical-risk/failure proxies only. | Introduce explicit logical-observable checks for small CSS/stabilizer examples before scaling. | ~25% | ~45% |
| Hardware noise and measurement faults | Real devices include correlated noise, readout errors and time dynamics. | Preliminary IBM `ibm_fez` syndrome-count evidence is archived for four small syndrome scenarios. | Repeat on additional backends and add noisy repeated runs. | ~40% | ~55% |
| Production qLDPC code families | Results should be tested on known production-relevant qLDPC constructions. | Current matrices are sparse synthetic LDPC/qLDPC-style structures plus external `ldpc` decoder ensemble tests. | Add one named small code/stabilizer benchmark and document its parity-check/logical structure. | ~30% | ~50% |

Overall estimated coverage of the current work: approximately 62-72% of the broader qLDPC decoding workflow gap after the external `ldpc` ensemble benchmark, uncertainty instrumentation, timing instrumentation, guarded policy evaluation and preliminary IBM hardware-oriented syndrome validation.

Coverage of the post-decoding decision subproblem: approximately 78-85%.

The next execution target is not only to improve one row. The target is to raise every weak row at least one level: hardware evidence, latency instrumentation, explicit logical checks, richer uncertainty flags and one better-defined code structure.

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

The POST contribution is not limited to candidate re-ranking. It provides a structured semantic decision layer for correction-hypothesis selection under uncertainty.

| POST capability | Scientific value |
|---|---|
| Heterogeneous evidence integration | Combines signals that are usually evaluated independently: syndrome evidence, decoder confidence, method agreement, logical risk and propagation safety. |
| Logical-risk management | Extends the decision beyond local criteria such as minimum weight or error probability by incorporating indicators related to potential logical failure. |
| Decoder-disagreement resolution | Selects among hypotheses produced by different decoding strategies under a common decision framework. |
| Uncertainty handling | Identifies situations with insufficient evidence, low decision margin or conflict between methods. |
| Guarded decision policy | Prevents the decision layer from degrading a reliable baseline decoder through controlled acceptance and override rules. |
| Traceability | Produces auditable evidence about the reasons and signals associated with the final correction selection. |

## 4. Methodology

Five experiments were conducted.

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
-> raw QDSV decision
-> guarded QDSV decision
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

This experiment focuses on BP-failure scenarios. BP is the baseline. Raw QDSV/QIntent selects across the decoder ensemble. Guarded QDSV/QIntent accepts the override only when the risk reduction and uncertainty evidence justify changing the baseline.

### Experiment 5: IBM Hardware-Oriented Syndrome Validation

Purpose: validate the handoff from real IBM hardware syndrome-count evidence into the same QDSV/QIntent post-decoding ranking layer.

Backend:

```text
ibm_fez
```

Job:

```text
d977en52su3c739horng
```

The experiment uses a small two-check syndrome extraction circuit. The goal is not production qLDPC decoding, but hardware-derived evidence integration:

```text
IBM counts
-> observed syndrome
-> candidate correction evidence
-> QDSV/QIntent ranking
-> auditable JSON/CSV artifacts
```

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

| Metric | BP-confidence baseline | QDSV raw | QDSV guarded |
|---|---:|---:|---:|
| Exact correction rate, mean | 0.7708 | 0.7896 | 0.7792 |
| Exact correction rate, std | 0.0668 | 0.0657 | 0.0628 |
| Logical-failure proxy rate, mean | 0.0542 | 0.0479 | 0.0542 |
| Logical-failure proxy rate, std | 0.0431 | 0.0438 | 0.0477 |
| Average logical risk, mean | 141.12 | 110.80 | 132.89 |
| Average logical risk, std | 13.03 | 11.38 | 13.51 |
| Improved-risk scenarios | - | 74/480 | 18/480 |
| Worse-risk scenarios | - | 0/480 | 0/480 |
| Override rate, mean | - | 0.1542 | 0.0375 accepted |
| Bad override rate, mean | - | 0.0583 | 0.0146 |
| Successful override rate, mean | - | 0.0958 | 0.0229 |
| Evidence-insufficient flag rate, mean | - | 0.1979 | 0.1979 |
| QDSV score margin, mean | - | 103.32 | 103.32 |
| QDSV decision time, mean | - | 2.22 ms | 2.22 ms |
| Total local policy time, mean | - | 50.76 ms | 50.76 ms |

Interpretation: raw QDSV/QIntent provided stable risk reduction across seeds with no worse-risk selections under this configuration. Guarded QDSV/QIntent accepted fewer overrides, preserved a modest exact-rate improvement over baseline and reduced the bad override rate from 5.83% to 1.46%.

The added timing and uncertainty instrumentation shows that this configuration is not yet a real-time decoder implementation, but the QDSV scoring step itself is small relative to candidate generation. The evidence-insufficient flag rate also provides a reproducible way to identify cases where the available signals may be too weak for a confident correction decision.

### 5.4 External `ldpc` Decoder-Ensemble Recovery

Configuration:

```text
External package: ldpc==2.4.1
Decoders: BP, BP+OSD, BP+LSD
Collected scenarios: BP-failure cases
Seeds: 8
Total BP-failure scenarios: 168
```

| Metric | BP-only baseline | QDSV raw ensemble | QDSV guarded ensemble |
|---|---:|---:|---:|
| Exact correction rate, mean | 0.0000 | 0.5307 | 0.1915 |
| Logical-failure proxy rate, mean | 0.4866 | 0.2420 | 0.3565 |
| Average logical risk, mean | 165.02 | 129.14 | 124.81 |
| Average risk delta, mean | - | 35.88 | 40.21 |
| Improved-risk scenarios | - | 61/168 | 34/168 |
| Worse-risk scenarios | - | 28/168 | 0/168 |
| Override rate, mean | - | 0.5482 | 0.1985 accepted |
| Bad override rate, mean | - | 0.1618 | 0.0069 |
| Successful override rate, mean | - | 0.3553 | 0.1915 |
| Evidence-insufficient flag rate, mean | - | 0.0551 | 0.0551 |
| QDSV score margin, mean | - | 216.78 | 216.78 |
| QDSV decision time, mean | - | 0.79 ms | 0.79 ms |
| Total local policy time, mean | - | 10.88 ms | 10.88 ms |

Interpretation: when BP fails, raw QDSV/QIntent can recover exact corrections in a substantial fraction of cases by selecting over a decoder ensemble. Guarded QDSV/QIntent accepts fewer overrides, but reduces bad overrides from 16.18% to 0.69% and eliminates worse-risk selections in this benchmark. This supports the interpretation of QDSV as a conservative governance layer rather than an aggressive decoder replacement.

This experiment also provides the strongest latency-oriented evidence so far. The local QDSV decision step is sub-millisecond on average in this configuration, while the total local policy path remains around 10.89 ms per accepted BP-failure scenario. This is not a real-time hardware decoder claim, but it narrows the latency gap from "untested" to "instrumented offline baseline".

### 5.5 IBM Hardware-Oriented Syndrome Validation

Configuration:

```text
Backend: ibm_fez
Job ID: d977en52su3c739horng
Shots: 1024
Scenarios: no_error, x0, x1, x2
```

| Metric | Baseline | QDSV raw | QDSV guarded |
|---|---:|---:|---:|
| Observed syndrome match rate | 1.0000 | 1.0000 | 1.0000 |
| Average expected-syndrome probability | 0.9573 | 0.9573 | 0.9573 |
| Average off-expected probability | 0.0427 | 0.0427 | 0.0427 |
| Exact rate | 1.0000 | 0.7500 | 1.0000 |
| Failure-proxy rate | 0.0000 | 0.0000 | 0.0000 |
| Average logical risk | 123.75 | 70.00 | 123.75 |
| Average risk delta | - | 53.75 | 0.00 |
| Override rate | - | 0.2500 | 0.0000 accepted |
| Bad override rate | - | 0.2500 | 0.0000 |

The hardware run produced the expected dominant syndrome in all four scenarios. The average expected-syndrome probability was 95.73%, with an average off-expected probability of 4.27%, reflecting real hardware noise/readout dispersion in the measured syndrome counts.

Raw QDSV/QIntent reduced average logical-risk proxy from 123.75 to 70.00. However, in the `x1` scenario, raw QDSV selected the lower-risk candidate `0 2` instead of the exact singleton `1`. The guarded policy rejected that override and preserved the baseline exact correction. This is an important result: it shows the central risk/exactness tradeoff and demonstrates why guarded governance is needed for high-confidence baseline cases.

Interpretation: the IBM run validates the hardware-evidence handoff and improves the hardware/readout gap. It does not yet validate production qLDPC decoding or full logical-operator preservation.

## 6. Discussion

The strongest contribution of QDSV/QIntent in these experiments is not replacing a decoder. The contribution is guarded semantic governance over decoder outputs.

The experiments show three important behaviors:

1. Raw QDSV/QIntent can use logical-risk and safety signals to override unsafe confidence-only selections.
2. Guarded QDSV/QIntent can reduce bad overrides and preserve reliable baseline decisions.
3. When evidence is insufficient, ambiguity audits reveal where more decoder information is required.
4. With real external LDPC decoder outputs, QDSV/QIntent can recover from BP failures by selecting across BP, BP+OSD, BP+LSD and compatible alternatives.

The results suggest that QDSV/QIntent is most useful as a policy and audit layer in the post-decoding workflow:

```text
decoder candidate generation
-> semantic evidence organization
-> raw risk-aware candidate selection
-> guarded override / rejection policy
-> reproducible decision trace
```

## 7. Limitations

This work remains preliminary.

Limitations:

- The check matrices are sparse synthetic LDPC/qLDPC-style structures.
- The logical-failure metric is a proxy, not a full logical-operator analysis.
- The experiments are offline and do not evaluate real-time latency.
- The external `ldpc` experiment focuses on BP-failure recovery and does not claim superiority over BP+OSD itself.
- Raw QDSV can still produce bad overrides; guarded QDSV reduces but does not mathematically eliminate all bad override risk.
- The IBM hardware-oriented run is intentionally small and validates handoff from hardware syndrome counts, not production qLDPC decoding.

## 8. Future Work

Before submission to a stronger venue, the most important next steps are:

1. Add full logical operator analysis rather than a proxy.
2. Test known LDPC/qLDPC code constructions rather than only synthetic sparse matrices.
3. Tune guarded decision policies against larger decoder ensembles and policy-ablation baselines.
4. Measure latency and identify which parts could run in real-time versus offline audit.
5. Evaluate noisy syndrome/readout conditions using `SoftInfoBpDecoder` or related workflows.
6. Compare against BP+OSD/BP+LSD as baselines, while keeping the claim focused on post-decoding policy rather than decoder replacement.

### 8.1 Hardware-Oriented Validation Status

The first IBM hardware-oriented syndrome experiment has been executed. The goal was not to claim production qLDPC decoding, but to validate the handoff:

```text
IBM hardware counts
-> syndrome evidence
-> candidate correction hypotheses
-> QDSV/QIntent post-decoding ranking
-> reproducible audit evidence
```

A Colab-ready notebook remains available to repeat this step:

```text
notebooks/qldpc_ibm_hardware_syndrome_validation_colab.ipynb
```

The notebook runs first on Aer, then optionally on IBM Quantum hardware using a user-supplied IBM token. The QDSV/QIntent side does not require a QDSV API key for this public workflow.

The executed `ibm_fez` job supports a cautious paper statement: QDSV/QIntent can consume hardware-derived syndrome-count evidence and produce the same kind of auditable post-decoding candidate ranking already demonstrated in local and external-decoder benchmarks. The next hardware step is repetition across more scenarios or another backend.

## 9. Reproducibility

Evidence and scripts are archived in the QIntent repository.

Scripts:

```text
docs/research/scripts/qldpc_bp_soft_multiseed.py
docs/research/scripts/qldpc_ldpc_ensemble_recovery.py
docs/research/scripts/qldpc_ibm_guarded_reprocess.py
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
docs/research/evidence/qdsv_qldpc_ibm_hardware_syndrome_evidence.json
docs/research/evidence/qdsv_qldpc_ibm_hardware_syndrome_summary.csv
docs/research/evidence/qdsv_qldpc_ibm_hardware_syndrome_counts.csv
docs/research/evidence/qdsv_qldpc_ibm_hardware_syndrome_metrics.json
```

## 10. Conclusion

This paper evaluates QDSV/QIntent as a risk-aware post-decoding semantic decision layer for LDPC/qLDPC-style quantum error correction workflows.

The results support a focused conclusion: QDSV/QIntent can organize decoder-generated correction candidates into structured evidence blocks and apply guarded decision logic that governs correction-hypothesis selection under uncertainty.

The most important result is the external `ldpc` ensemble recovery benchmark: in 168 BP-failure scenarios, raw QDSV/QIntent recovered exact corrections in 53.1% of cases and reduced the logical-failure proxy from 48.7% to 24.2%. Guarded QDSV/QIntent accepted fewer overrides, but reduced bad overrides from 16.18% to 0.69% and eliminated worse-risk selections in this benchmark.

The work does not claim a new qLDPC decoder, production readiness or quantum advantage. It contributes evidence for a complementary semantic decision-governance layer that can sit after existing decoders and support risk-aware, auditable and conservative correction-hypothesis selection.
