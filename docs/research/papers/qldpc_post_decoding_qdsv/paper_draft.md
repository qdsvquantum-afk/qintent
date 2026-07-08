# QDSV/QIntent as a Guarded Semantic Decision Layer for LDPC/qLDPC-Style Post-Decoding Correction Governance

Mature research draft.

## Abstract

Quantum LDPC and qLDPC codes are promising candidates for scalable quantum error correction, but scalable codes and stronger decoders do not remove a practical downstream question: when several correction hypotheses are plausible, uncertain or conflicting, which correction should be trusted?

This paper evaluates QDSV/QIntent as a guarded semantic decision layer for post-decoding correction-hypothesis governance. QDSV/QIntent does not replace belief propagation, BP+OSD, LSD, neural or soft-information decoders. Instead, it receives decoder-generated candidates and prepared evidence signals, including syndrome consistency, decoder confidence, decoder agreement, logical-safety indicators, propagation safety and logical-risk indicators. It then performs structured candidate evaluation and returns an auditable decision trace without exposing the private QDSV scoring formula.

We report seven experimental stages. A controlled ambiguity benchmark demonstrates risk-aware selection under constructed syndrome ambiguity. A BP-soft multi-seed benchmark over 480 scenarios shows that raw QDSV improves exact rate from 0.7708 to 0.7896 and reduces average logical risk from 141.12 to 110.80, while guarded QDSV reduces bad overrides from 5.83% to 1.46%. An external `ldpc` decoder-ensemble recovery benchmark uses BP, BP+OSD and BP+LSD outputs. In 168 BP-failure scenarios, raw QDSV recovered exact corrections in 53.1% of cases, reduced the logical-failure proxy from 48.7% to 24.2%, and reduced average logical risk from 165.02 to 129.14. Guarded QDSV accepted fewer overrides but reduced bad overrides from 16.18% to 0.69% and eliminated worse-risk selections. A preliminary IBM Quantum hardware-oriented syndrome validation on `ibm_fez` validates the handoff from hardware counts to QDSV/QIntent evidence. Finally, two known stabilizer-code validations compute the formal residual `R = C E`: in 320 correctable single-error scenarios, the 5-qubit code baseline produced an 8.125% mean formal logical-failure rate while raw and guarded QDSV achieved 0%; in the Steane [[7,1,3]] CSS code, the baseline produced a 12.1875% mean formal logical-failure rate while raw and guarded QDSV again achieved 0%.

These results support the hypothesis that QDSV/QIntent can serve as a decoder-agnostic, guarded, auditable post-decoding decision layer validated across small stabilizer-code families. The results do not establish production decoder superiority, real-time suitability or quantum advantage. They identify a complementary role for semantic decision governance in decoder pipelines and motivate further evaluation with production qLDPC codes, larger stabilizer benchmarks and latency-aware implementations.

## 1. Introduction

Quantum error correction is a central requirement for scalable quantum computing. LDPC and qLDPC-style codes are attractive because they promise improved overhead properties compared with many conventional approaches. However, scalable code construction alone is not enough. The decoding workflow must interpret noisy syndromes, manage ambiguity, select corrections, avoid logical failures and do so under practical latency and reliability constraints.

Most decoding research focuses on producing better correction hypotheses: higher likelihood candidates, faster convergence, lower-weight corrections, ordered-statistics post-processing, localized inversion or learned neural inference. These are essential mechanisms. Yet a practical pipeline still faces a governance problem after candidate generation: if several hypotheses are plausible, if decoders disagree, or if confidence and logical risk point in different directions, the system must decide whether to accept, override, reject or defer a correction.

The final correction decision can involve several competing criteria:

- Does the candidate match the syndrome?
- How confident is the decoder?
- Do multiple decoders agree?
- Does the correction touch structurally sensitive qubits?
- Does it increase propagation risk?
- Is it likely to preserve the logical subspace?
- Can the decision be audited and reproduced?

This work explores QDSV/QIntent in that decision-governance gap. QDSV provides a semantic representation layer for structured evidence, building on the problem-first representation model introduced in [5] and its implementation/validation framework in [6]. QIntent provides a public declarative syntax for expressing correction-hypothesis decision workflows. In the experiments reported here, QDSV/QIntent is evaluated in the post-decoding phase: decoders generate candidates, and QDSV/QIntent governs whether a correction hypothesis should be accepted, rejected or overridden using structured evidence, risk-aware decision logic and guarded acceptance policies.

The paper makes four focused contributions:

1. It formulates post-decoding correction selection as a guarded semantic decision-governance problem rather than as a replacement decoder.
2. It evaluates QDSV/QIntent over synthetic ambiguity, BP-soft evidence and external `ldpc` decoder outputs including BP, BP+OSD and BP+LSD.
3. It introduces guarded override policies that reduce harmful overrides while preserving the ability to recover from baseline decoder failures.
4. It validates logical preservation in two known stabilizer-code settings by computing the residual `R = C E` and classifying it against `S` and `N(S)\S`.

The intended claim is deliberately narrow: QDSV/QIntent is a complementary post-decoding decision layer. It is not a new qLDPC code construction, not a replacement for BP/OSD/LSD/neural decoders, and not a claim of hardware fault tolerance.

## 2. Related Work and Positioning

Belief propagation is a natural baseline for sparse classical and quantum codes, but degeneracy, short cycles and ambiguous syndromes can limit standalone BP behavior in quantum LDPC settings. BP combined with ordered-statistics decoding has been studied as a general decoder for quantum LDPC codes and is implemented in the open `ldpc` ecosystem used by this work [1].

Localized statistics decoding (LSD) was proposed as a parallel decoding approach for quantum LDPC codes, addressing scalability and runtime limitations of global BP+OSD-style post-processing while retaining broad applicability [2]. Neural decoders and learned approaches provide another line of work, targeting accuracy-latency tradeoffs and hardware deployability under real-time constraints [3]. Soft-information and soft-output approaches incorporate richer measurement or confidence information into decoding pipelines, improving the evidence available to the decoder rather than treating each syndrome bit as a hard decision [4].

QDSV/QIntent is positioned differently. It does not attempt to replace BP, BP+OSD, LSD, neural or soft-information decoders. It operates after candidate generation, using decoder outputs and auxiliary evidence as inputs to a guarded decision layer. In this framing, decoders answer "what corrections are plausible?", while QDSV/QIntent addresses "which plausible correction should be trusted under the current evidence, risk and guard policy?".

This distinction matters because a post-decoding decision layer can be evaluated using metrics that are not identical to decoder accuracy alone: harmful override rate, successful override rate, evidence-insufficiency rate, risk delta, audit trace completeness and formal residual classification in known stabilizer codes.

## 3. Gap Analysis in LDPC/qLDPC Decoding

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
| Full logical-operator preservation | A real qLDPC system requires formal logical operator analysis, not proxies. | Adds two known stabilizer-code validations, 5-qubit and Steane CSS, using residual classification `R = C E`, with `R in S` as logical success and `R in N(S) \ S` as logical failure. | Extend from correctable single-error cases to larger stabilizer/CSS examples and production qLDPC-style codes. | ~65% | ~78% |
| Hardware noise and measurement faults | Real devices include correlated noise, readout errors and time dynamics. | Preliminary IBM `ibm_fez` syndrome-count evidence is archived for four small syndrome scenarios. | Repeat on additional backends and add noisy repeated runs. | ~40% | ~55% |
| Production qLDPC code families | Results should be tested on known production-relevant qLDPC constructions. | Adds named 5-qubit and Steane CSS stabilizer-code benchmarks with explicit stabilizer generators, normalizer and residual classification; qLDPC-scale families remain future work. | Add surface-code and production qLDPC-style benchmarks. | ~58% | ~70% |

Overall estimated coverage of the current work: approximately 72-80% of the broader qLDPC decoding workflow gap after the external `ldpc` ensemble benchmark, uncertainty instrumentation, timing instrumentation, guarded policy evaluation, preliminary IBM hardware-oriented syndrome validation and two known stabilizer-code logical validations.

Coverage of the post-decoding decision subproblem: approximately 78-85%.

The remaining gaps are no longer addressed by adding more synthetic benchmarks. They require a different validation tier: larger known code families, repeated hardware-derived syndrome evidence, latency-aware implementation and production qLDPC-scale comparisons.

## 4. QDSV/QIntent Post-Decoding Model

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

## 5. Methodology

Seven experiments were conducted.

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

### Experiment 6: Known Stabilizer-Code Logical Validation

Purpose: connect QDSV/QIntent correction-hypothesis decisions to formal logical behavior in a known stabilizer code rather than only proxy risk metrics.

Code:

```text
5-qubit perfect stabilizer code
generators: XZZXI, IXZZX, XIXZZ, ZXIXZ
```

For each physical error `E` and selected correction `C`, the experiment computes:

```text
R = C E
```

Classification:

```text
R in S        -> formal logical success
R in N(S)\S   -> formal logical failure
```

The benchmark evaluates a confidence-only baseline, raw QDSV/QIntent, guarded QDSV/QIntent and an `oracle_best` reference over the same candidate set. The oracle is used only as an experimental upper-bound reference; it is not part of the proposed method.

### Experiment 7: Steane CSS Logical Validation

Purpose: test whether the formal logical-preservation behavior observed in the 5-qubit code generalizes to a second known stabilizer-code family with CSS structure.

Code:

```text
Steane [[7,1,3]] CSS stabilizer code
generators: IIIXXXX, IXXIIXX, XIXIXIX, IIIZZZZ, IZZIIZZ, ZIZIZIZ
```

The same residual test is used:

```text
R = C E
R in S        -> formal logical success
R in N(S)\S   -> formal logical failure
```

This experiment adds CSS-sector evidence but keeps the same public QIntent pattern: syndrome evidence, logical-safety evidence, decoder evidence and guarded override policy.

## 6. Experimental Results

### 6.1 Controlled Ambiguity Benchmark

| Metric | Baseline | QDSV/QIntent |
|---|---:|---:|
| Exact correction rate | 0/6 | 6/6 |
| Logical-failure proxy rate | 6/6 | 0/6 |
| Average logical risk | 263 | 56 |
| Average risk reduction | - | 207 |

Interpretation: QDSV/QIntent successfully selected the lower-risk correlated correction in the constructed ambiguity.

### 6.2 Random Sparse Benchmark

The random sparse benchmark showed that aggressive risk-first scoring can reduce risk but may sacrifice exactness, while balanced policies preserve more decoder agreement. The ambiguity audit identified cases that cannot be resolved from the available synthetic evidence alone.

Interpretation: QDSV/QIntent should not be tuned only as a risk minimizer. It needs richer decoder evidence and policy calibration.

### 6.3 BP-Soft Multi-Seed Benchmark

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

### 6.4 External `ldpc` Decoder-Ensemble Recovery

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

### 6.5 IBM Hardware-Oriented Syndrome Validation

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

### 6.6 Known 5-Qubit Stabilizer-Code Logical Validation

Configuration:

```text
Code: 5-qubit perfect stabilizer code
Stabilizer generators: XZZXI, IXZZX, XIXZZ, ZXIXZ
Seeds: 8
Samples per seed: 40
Total scenarios: 320
Error model: correctable single-qubit Pauli errors
Formal residual: R = C E
```

| Metric | Confidence baseline | Oracle best | QDSV raw | QDSV guarded |
|---|---:|---:|---:|---:|
| Formal logical-failure rate, mean | 0.08125 | 0.00000 | 0.00000 | 0.00000 |
| Formal logical-failure rate, std | 0.02997 | 0.00000 | 0.00000 | 0.00000 |
| Formal logical-success rate, mean | 0.91875 | 1.00000 | 1.00000 | 1.00000 |
| Average logical risk, mean | 66.47 | 50.00 | 50.00 | 50.00 |
| Average risk delta vs baseline | - | 16.47 | 16.47 | 16.47 |
| Override rate, mean | - | - | 0.08125 | 0.08125 accepted |
| Bad override rate, mean | - | - | 0.00000 | 0.00000 |
| Successful override rate, mean | - | - | 0.08125 | 0.08125 |
| Recovery over baseline logical failures | - | 1.00000 | 1.00000 | 1.00000 |
| QDSV decision time, mean | - | - | 7.16 ms | 7.16 ms |
| Total local policy time, mean | - | - | 19.45 ms | 19.45 ms |

Interpretation: this experiment closes the main causal gap left by proxy-only logical-risk tests. In a known stabilizer-code setting, the selected correction can be evaluated by residual membership in the stabilizer group or normalizer. Under the correctable single-error benchmark, the confidence baseline occasionally selected a high-confidence but formally harmful correction. Raw and guarded QDSV/QIntent selected candidates whose residual was in the stabilizer group and matched the oracle-best candidate set over the available hypotheses.

This result should be interpreted narrowly. It does not prove production qLDPC decoder superiority, and it uses a small correctable-code setting. Its contribution is to demonstrate that QDSV/QIntent decision governance can be evaluated against formal logical-success and logical-failure conditions, not only heuristic risk proxies.

### 6.7 Steane [[7,1,3]] CSS Logical Validation

Configuration:

```text
Code: Steane [[7,1,3]] CSS stabilizer code
Stabilizer generators: IIIXXXX, IXXIIXX, XIXIXIX, IIIZZZZ, IZZIIZZ, ZIZIZIZ
Seeds: 8
Samples per seed: 40
Total scenarios: 320
Error model: correctable single-qubit Pauli errors
Formal residual: R = C E
```

| Metric | Confidence baseline | Oracle best | QDSV raw | QDSV guarded |
|---|---:|---:|---:|---:|
| Formal logical-failure rate, mean | 0.121875 | 0.00000 | 0.00000 | 0.00000 |
| Formal logical-failure rate, std | 0.04750 | 0.00000 | 0.00000 | 0.00000 |
| Formal logical-success rate, mean | 0.878125 | 1.00000 | 1.00000 | 1.00000 |
| Average logical risk, mean | 99.71 | 70.91 | 70.91 | 70.91 |
| Average risk delta vs baseline | - | 28.81 | 28.81 | 28.81 |
| Override rate, mean | - | - | 0.121875 | 0.121875 accepted |
| Bad override rate, mean | - | - | 0.00000 | 0.00000 |
| Successful override rate, mean | - | - | 0.121875 | 0.121875 |
| Recovery over baseline logical failures | - | 1.00000 | 1.00000 | 1.00000 |
| QDSV decision time, mean | - | - | 2.79 ms | 2.79 ms |
| Total local policy time, mean | - | - | 12.28 ms | 12.28 ms |

Interpretation: the Steane experiment reproduces the formal logical-preservation pattern in a CSS stabilizer code. The confidence baseline occasionally selected high-confidence multi-Pauli candidates whose residual was a non-trivial logical operator. Raw and guarded QDSV/QIntent selected candidates whose residual belonged to the stabilizer group and matched the oracle-best candidate set over the available hypotheses.

The scientific value is not that QDSV is perfect in this small setting. The value is cross-code consistency: the same decision-governance pattern that worked in the 5-qubit stabilizer code also worked in a CSS code with explicit X/Z stabilizer structure. This reduces the risk that the formal logical-preservation result is an artifact of a single code.

## 7. Discussion

The strongest contribution of QDSV/QIntent in these experiments is not replacing a decoder. The contribution is guarded semantic governance over decoder outputs.

The experiments show six important behaviors:

1. Raw QDSV/QIntent can use logical-risk and safety signals to override unsafe confidence-only selections.
2. Guarded QDSV/QIntent can reduce bad overrides and preserve reliable baseline decisions.
3. When evidence is insufficient, ambiguity audits reveal where more decoder information is required.
4. With real external LDPC decoder outputs, QDSV/QIntent can recover from BP failures by selecting across BP, BP+OSD, BP+LSD and compatible alternatives.
5. In known stabilizer-code settings, QDSV/QIntent decisions can be evaluated against formal residual membership conditions rather than only proxy risk metrics.
6. The formal logical-preservation behavior was reproduced across two small code families: a 5-qubit perfect stabilizer code and the Steane CSS code.

The results suggest that QDSV/QIntent is most useful as a policy and audit layer in the post-decoding workflow:

```text
decoder candidate generation
-> semantic evidence organization
-> raw risk-aware candidate selection
-> guarded override / rejection policy
-> reproducible decision trace
```

## 8. Limitations

This work remains preliminary.

Limitations:

- The LDPC/qLDPC-style check matrices are sparse synthetic structures; they are useful for controlled decision-governance tests but are not production qLDPC code families.
- Formal residual classification has so far been demonstrated only on small correctable single-error settings: the 5-qubit perfect stabilizer code and the Steane [[7,1,3]] CSS code.
- The experiments do not demonstrate scalability to large qLDPC codes, repeated syndrome extraction cycles or full fault-tolerant operation.
- The experiments are offline and do not establish real-time decoding suitability, even though local QDSV decision timing is instrumented.
- The external `ldpc` experiment focuses on BP-failure recovery and does not claim superiority over BP+OSD or BP+LSD as standalone decoders.
- Raw QDSV can still produce harmful overrides in some settings; guarded QDSV reduces but does not mathematically eliminate all bad override risk.
- The IBM hardware-oriented run is intentionally small and validates handoff from hardware syndrome counts, not hardware fault tolerance or production qLDPC decoding.
- The `oracle_best` rows are upper-bound references over available candidate sets. They are not deployable baselines and are not part of the proposed method.

## 9. Future Work

Before submission to a stronger venue, the most important next steps are:

1. Extend formal logical analysis from the 5-qubit and Steane stabilizer benchmarks to surface-code and qLDPC-style code families.
2. Test known LDPC/qLDPC code constructions rather than only synthetic sparse matrices.
3. Tune guarded decision policies against larger decoder ensembles and policy-ablation baselines.
4. Measure latency and identify which parts could run in real-time versus offline audit.
5. Evaluate noisy syndrome/readout conditions using `SoftInfoBpDecoder` or related workflows.
6. Compare against BP+OSD/BP+LSD as baselines, while keeping the claim focused on post-decoding policy rather than decoder replacement.

### 9.1 Hardware-Oriented Validation Status

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

## 10. Reproducibility

Evidence and scripts are archived in the QIntent repository.

Scripts:

```text
docs/research/scripts/qldpc_bp_soft_multiseed.py
docs/research/scripts/qldpc_ldpc_ensemble_recovery.py
docs/research/scripts/qldpc_ibm_guarded_reprocess.py
docs/research/scripts/qldpc_stabilizer_logical_validation.py
docs/research/scripts/qldpc_steane_css_logical_validation.py
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
docs/research/evidence/qdsv_qldpc_five_qubit_stabilizer_logical_evidence.json
docs/research/evidence/qdsv_qldpc_five_qubit_stabilizer_logical_summary.csv
docs/research/evidence/qdsv_qldpc_five_qubit_stabilizer_logical_metrics.csv
docs/research/evidence/qdsv_qldpc_steane_css_logical_evidence.json
docs/research/evidence/qdsv_qldpc_steane_css_logical_summary.csv
docs/research/evidence/qdsv_qldpc_steane_css_logical_metrics.csv
```

## 11. Conclusion

This paper evaluates QDSV/QIntent as a risk-aware post-decoding semantic decision layer for LDPC/qLDPC-style quantum error correction workflows.

The results support a focused conclusion: QDSV/QIntent can organize decoder-generated correction candidates into structured evidence blocks and apply guarded decision logic that governs correction-hypothesis selection under uncertainty.

The strongest decoder-ensemble result is the external `ldpc` recovery benchmark: in 168 BP-failure scenarios, raw QDSV/QIntent recovered exact corrections in 53.1% of cases and reduced the logical-failure proxy from 48.7% to 24.2%. Guarded QDSV/QIntent accepted fewer overrides, but reduced bad overrides from 16.18% to 0.69% and eliminated worse-risk selections in this benchmark.

The strongest logical-preservation result is now cross-code consistency across two stabilizer families. In the 5-qubit stabilizer-code benchmark, over 320 correctable single-error scenarios, the confidence baseline produced an 8.125% mean formal logical-failure rate, while raw and guarded QDSV/QIntent selected corrections with 0% formal logical-failure rate. In the Steane [[7,1,3]] CSS benchmark, the confidence baseline produced a 12.1875% mean formal logical-failure rate, while raw and guarded QDSV/QIntent again selected corrections with 0% formal logical-failure rate. In both cases, QDSV matched the oracle-best candidate set under residual classification `R = C E`.

The work does not claim a new qLDPC decoder, production readiness or quantum advantage. It contributes evidence for a complementary semantic decision-governance layer that can sit after existing decoders and support risk-aware, auditable and conservative correction-hypothesis selection.

## 12. References

[1] J. Roffe, D. R. White, S. Burton, and E. Campbell, "Decoding Across the Quantum LDPC Code Landscape", arXiv:2005.07016. https://arxiv.org/abs/2005.07016

[2] T. Hillmann, L. Berent, A. O. Quintavalle, J. Eisert, R. Wille, and J. Roffe, "Localized statistics decoding: A parallel decoding algorithm for quantum low-density parity-check codes", arXiv:2406.18655. https://arxiv.org/abs/2406.18655

[3] G. Yan, S. Li, and Y. Du, "Rethink the Role of Neural Decoders in Quantum Error Correction", arXiv:2605.12046. https://arxiv.org/abs/2605.12046

[4] J. Majaniemi and E. S. Matekole, "Reducing quantum error correction overhead using soft information", arXiv:2504.03504. https://arxiv.org/abs/2504.03504

[5] J. A. Jimenez Lozano, "QDSV: A Problem-First Semantic Representation Model for Quantum-Oriented Computation", arXiv:2606.15027. https://arxiv.org/abs/2606.15027

[6] J. A. Jimenez Lozano, "QDSV Implementation and Validation Framework", arXiv:2606.19312. https://arxiv.org/abs/2606.19312
