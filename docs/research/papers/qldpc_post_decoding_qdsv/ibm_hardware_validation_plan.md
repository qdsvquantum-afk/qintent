# IBM Hardware-Oriented Validation Plan

Working plan for the QDSV/QIntent LDPC/qLDPC-style post-decoding paper.

## Purpose

The current evidence supports QDSV/QIntent as a risk-aware post-decoding decision layer over LDPC/qLDPC-style correction candidates. The next validation step is to add a small hardware-oriented experiment where syndrome-like evidence is obtained from an IBM Quantum backend and then passed into the same QDSV/QIntent ranking workflow.

This is not intended to prove production qLDPC decoding or quantum advantage. The narrower goal is to show that the post-decoding decision layer can consume hardware-derived syndrome evidence and produce the same kind of auditable correction ranking already demonstrated in local benchmarks.

## Validation Scope

The IBM hardware-oriented validation should test:

- syndrome extraction from a small parity-check circuit;
- candidate correction generation from observed syndrome labels;
- baseline selection using confidence-only or minimum-weight logic;
- QDSV/QIntent reranking using structured evidence blocks;
- reproducible evidence export as JSON/CSV;
- comparison between Aer simulation and IBM hardware-derived counts.

## What This Closes

| Gap | Current state | Hardware-oriented contribution |
|---|---|---|
| Hardware noise and measurement faults | Not yet evaluated with real hardware-derived syndrome evidence. | Adds first IBM-derived syndrome/count evidence. |
| Practical workflow handoff | Demonstrated offline with synthetic and external decoder outputs. | Demonstrates hardware counts -> syndrome evidence -> QDSV ranking. |
| Reproducibility | JSON/CSV evidence already produced locally. | Adds hardware job metadata and backend name to evidence. |
| Industrial credibility | Current results are local/offline. | Shows the workflow can touch IBM hardware without changing the QDSV decision layer. |

## What Remains Open

| Gap | Why it remains open |
|---|---|
| Full production qLDPC decoding | The first hardware notebook uses a small parity-check syndrome circuit, not a full production qLDPC construction. |
| Real-time latency | Colab + IBM queue execution does not measure real-time decoder latency. |
| Full logical-operator preservation | The first hardware test still uses logical-risk proxies. |
| Large-scale qLDPC code families | The hardware test is intentionally small to keep cost and queue time manageable. |

## Readiness Criteria

We are ready to run the IBM hardware validation when:

1. The Colab notebook runs end-to-end on Aer.
2. QIntent scoring works without a QDSV API key.
3. The IBM token is supplied only through Colab Secrets, `getpass`, or a temporary environment variable.
4. The selected IBM backend is operational and has manageable queue depth.
5. The notebook saves:
   - `qdsv_qldpc_ibm_hardware_syndrome_summary.csv`
   - `qdsv_qldpc_ibm_hardware_syndrome_evidence.json`

## Recommended Claim After Success

If the hardware-oriented notebook runs successfully, the paper can add a cautious statement:

> As a preliminary hardware-oriented validation, we executed a small parity-check syndrome extraction workflow on IBM Quantum hardware and passed the resulting syndrome-count evidence into the same QDSV/QIntent post-decoding decision layer. This validates the handoff from hardware-derived evidence to auditable QDSV candidate ranking, while leaving production qLDPC code families, real-time latency and full logical-operator analysis as future work.

