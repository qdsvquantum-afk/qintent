# Public Scope

This repository contains the MIT-licensed QIntent Developer Preview SDK, CLI, examples, notebooks, tests and public grammar.

## Included

- Validation, compilation, explanation and execution through QDSV APIs.
- A public capability contract for all 43 canonical operations.
- Flat and hierarchical ScoreModel v2 declarations.
- Canonical hardware preflight and licensed IBM job submission/status helpers.
- Public evidence and stable operation-program summaries.

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

ScoreModel is a canonical operation composition inside ProblemSpec. The public terms are value, importance, priority, contextual adjustments and penalties. Ranking and presentation remain workflow-level behavior.

## Availability and data

Public APIs are intended for bounded examples and may enforce payload, row, execution and backend limits. IBM execution requires a licensed deployment, a user token saved by that deployment and provider capacity. Do not send sensitive data to a public preview endpoint.

QDSV, QIntent and Qruba are project marks. The MIT license does not grant trademark rights.
