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

The intended product architecture is:

```text
Open SDK
Closed Runtime
Public API
Private Core
```

## Trademark note

QDSV, QIntent, and Qruba names and marks are project marks of their respective owners. The MIT License for this repository does not grant trademark rights.
