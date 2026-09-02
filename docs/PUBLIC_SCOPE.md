# Public Scope

This repository contains the MIT-licensed QIntent Developer Preview SDK, CLI, examples, notebooks, tests and public grammar.

## Included

- Validation, compilation, explanation and execution through QDSV APIs.
- A public capability contract for all 45 canonical operations, including
  bounded conditional selection through ``select_if``.
- Flat and hierarchical ScoreModel v2 declarations.
- Canonical hardware preflight and licensed IBM job submission/status helpers.
- Public evidence and stable operation-program summaries.
- Explicit family states: `compiler_v2_ready`, `compile_only`, `specialized_runtime` and `not_materialized`.

## Not included

- QDSV Runtime or private semantic programs.
- Reversible lowering implementation and optimization rules.
- QuEST, Aer or IBM adapter internals.
- Tokens, secrets, production configuration or private endpoints.
- Arbitrary Python execution.

## Architecture

```text
QIntent
-> ProblemSpec
-> QDSV Operation Compiler v2
-> QuantumCanonicalProgram
-> QuEST or reversible circuit realization

Bridge and Qruba consume this route; they do not define parallel semantics.
```

Physical-property semantics retain their specialized runtimes. QDSV wraps each
registered physical strategy and realizer in an OperationProgram v2 contract
with immutable digests and an explicit execution class. Scientific classical
materializers are never reported as quantum execution.

QIntent execution is fail-closed. A valid parse or compilation is not enough:
the selected family must also provide a verifiable program and compatible
realizer for the requested backend.

The shared `qdsv_semantic_execution_contract.v1` additionally requires
explicit execution profiles and separates semantic result, backend evidence
and reported result. Classical references remain available only as explicitly
labeled references and are never reclassified as quantum execution.

ScoreModel is a canonical operation composition inside ProblemSpec. The public terms are value, importance, priority, contextual adjustments and penalties. Ranking and presentation remain workflow-level behavior.

## Availability and data

Public APIs are intended for bounded examples and may enforce payload, row, execution and backend limits. IBM execution requires a licensed deployment, a user token saved by that deployment and provider capacity. Do not send sensitive data to a public preview endpoint.

QDSV, QIntent and Qruba are project marks. The MIT license does not grant trademark rights.
