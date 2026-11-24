# QIntent Roadmap

QIntent is a public SDK with bounded, client-only access to the QDSV semantic runtime. The public capability catalog expands through versioned releases while the private runtime remains protected.

## Current

- Public Python SDK on PyPI.
- Public QIntent API client.
- `validate`, `compile`, `explain` and `run`.
- QIntent Explain with Semantic Execution Passport.
- QuEST/statevector default route for public examples.
- Controlled QDSV operations for predicates, matching, similarity, safe math, null handling and row-level aggregation.
- Decision Model operation without exposing the internal QDSV formula.

## Next

- More reproducible Colab notebooks.
- Clearer example gallery by domain.
- More public grammar examples.
- Better error messages for invalid chains and unsupported syntax.
- Lightweight TypeScript client.
- Public examples that show semantic decision vs hardware evidence separation.

## Later

- Broader public operation families when stable.
- More backend-aware explain reports.
- Public community examples and GitHub Discussions.
- Deeper integrations with Qruba Cloud and QDSV Bridge.

## Boundaries

The public SDK will remain a client. It will not include QDSV Runtime internals, CAP, backend selector, private lowering, QuEST/Aer/IBM adapters, mitigation internals or private orchestration.
