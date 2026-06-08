# QIntent Roadmap

QIntent is in Developer Preview. The public SDK is intentionally small, bounded and client-only while QDSV Runtime remains private.

## Current

- Public Python SDK on PyPI.
- Public QIntent API client.
- `validate`, `compile`, `explain` and `run`.
- QIntent Explain with Semantic Execution Passport.
- QuEST/statevector default route for public preview examples.
- Controlled QDSV operations for predicates, matching, similarity, safe math, null handling and row-level aggregation.
- Decision Model operation without exposing the internal QDSV formula.

## Next

- More reproducible Colab notebooks.
- Clearer example gallery by domain.
- More public grammar examples.
- Better error messages for invalid chains and unsupported preview syntax.
- Lightweight TypeScript client preview.
- Public examples that show semantic decision vs hardware evidence separation.

## Later

- Broader public operation families when stable.
- More backend-aware explain reports.
- Public community examples and GitHub Discussions.
- Deeper integrations with Qruba Cloud and QDSV Bridge.

## Boundaries

The public SDK will remain a client. It will not include QDSV Runtime internals, CAP, backend selector, private lowering, QuEST/Aer/IBM adapters, mitigation internals or private orchestration.
