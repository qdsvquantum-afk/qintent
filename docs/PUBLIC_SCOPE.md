# Public Scope

This repository is the public Developer Preview for QIntent.

## Included under MIT

- Python SDK package: `qdsv-qintent`
- CLI command: `qintent`
- Public examples
- VS Code/Jupyter and Colab notebooks
- Tests for the public SDK surface
- Public preview grammar notes
- Documentation for using QIntent through the QDSV public API
- QIntent Explain / Semantic Execution Passport
- Controlled QDSV helpers for comparison, logic, ranges, tolerance, safe division, null handling, numeric bounds, and row-level signal aggregation

## Not included

The following components are not part of this repository:

- QDSV Runtime
- CAP
- Backend selector
- Lowering and materialization layers
- QuEST, Aer, IBM, or hardware adapters
- Noise mitigation internals
- Crypto internals
- Advanced orchestration logic
- Private endpoints
- Secrets, keys, tokens, or production deployment configuration

## Positioning

QIntent is the public language and SDK layer. QDSV is the underlying semantic computation model and runtime. Qruba is the commercial platform built on top of QDSV.

QIntent is not a circuit-authoring language. It is a quantum-intent language. QDSV can execute a problem without circuits through semantic/statevector routes when available, and can materialize circuits only when the selected backend requires them.

The intended product architecture is:

```text
Open SDK
Closed Runtime
Public API
Private Core
```

## Data and availability policy

The public API is for lightweight examples, notebooks, and evaluation. It may enforce row, payload, backend, and execution limits.

For larger datasets, sensitive data, or heavier workloads, use Qruba Cloud with an appropriate license or a private Docker/local QDSV node.

Private Docker/local nodes are availability-limited. If a private node is not reachable, it may be offline, reserved for private processing, or temporarily busy. This should be treated as limited availability, not as a public cloud outage.

## Trademark note

QDSV, QIntent, and Qruba names and marks are project marks of their respective owners. The MIT License for this repository does not grant trademark rights.
