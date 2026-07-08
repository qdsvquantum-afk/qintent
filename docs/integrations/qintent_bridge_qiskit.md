# QIntent to QDSV Bridge to Qiskit

Status: public developer-preview positioning note.

This guide shows how QIntent can be described as an upstream intent layer for QDSV Bridge without submitting QIntent as a separate Qiskit Ecosystem project yet.

The intended public message is:

```text
QIntent declares the problem intent.
QDSV Bridge turns controlled semantic specifications into inspectable OpenQASM/Qiskit-oriented artifacts.
Qiskit remains the circuit inspection, transpilation, simulation and execution environment.
```

## Why This Exists

QDSV Bridge is listed in the Qiskit Ecosystem as a semantic-to-circuit blueprint SDK for supported quantum problem families.

QIntent should not be positioned as a competing Qiskit integration at this stage. Instead, QIntent can benefit from the Bridge path by acting upstream:

```text
QIntent
-> QDSV semantic intent
-> Bridge-compatible problem specification
-> QDSV Bridge
-> OpenQASM/Qiskit-oriented artifact
-> Qiskit inspection/simulation/execution
```

This keeps the ecosystem story clean:

- QIntent is the declarative language for intent and structured evidence.
- Bridge is the Qiskit-facing SDK/artifact layer.
- Qiskit is the downstream circuit ecosystem.

## Recommended Wording

Use:

```text
QIntent can feed Bridge-compatible semantic specifications that are exported by QDSV Bridge as inspectable OpenQASM/Qiskit-oriented artifacts.
```

Avoid:

```text
QIntent is officially integrated with Qiskit.
QIntent is a Qiskit Ecosystem project.
QIntent replaces Qiskit circuit construction.
```

## Conceptual Flow

Install both public SDKs when testing this handoff:

```bash
pip install qdsv-qintent qdsv-bridge qiskit
```

QIntent is useful when the user wants to begin from intent, rows, predicates, ranking criteria or structured evidence:

```python
from qintent import QIntentClient

qintent = QIntentClient()

rows = [
    {"candidate_index": 0, "eligibility_score": 910, "risk_score": 80},
    {"candidate_index": 1, "eligibility_score": 760, "risk_score": 120},
]

source = """
find_rows("candidate_index")
  .where("eligibility_score", ">=", 800)
  .rank_by("eligibility_score")
  .top_k(1)
"""

passport = qintent.explain(source, rows=rows)
```

Bridge is useful when the workflow needs an artifact that circuit ecosystems can inspect:

```python
from qdsv_bridge import QDSVBridgeClient

bridge = QDSVBridgeClient()

spec = {
    "family": "bounded_semantic_marking",
    "bridge_mode": "build",
    "state_space": {
        "kind": "finite_candidates",
        "candidate_count": len(rows),
        "candidate_id": "candidate",
    },
    "signals": ["eligibility_score", "risk_score"],
    "goal": {
        "kind": "marking",
        "predicate": "eligible_candidate",
    },
    "target": {
        "format": "qasm3",
        "backend_family": "qiskit",
    },
    "limits": {
        "max_qubits": 5,
        "max_depth": 160,
    },
}

artifact_package = bridge.build(spec)
qasm3_source = artifact_package["artifact"]["content"]
```

Then Qiskit users keep control of the circuit artifact:

```python
from qiskit import qasm3

circuit = qasm3.loads(qasm3_source)
print(circuit)
```

## Public Scope

This guide is intentionally narrow. It does not claim that QIntent itself is a Qiskit Ecosystem submission.

Current public role:

```text
QIntent provides upstream intent expression.
QDSV Bridge provides the Qiskit-facing artifact handoff.
```

## When To Use This Route

Use this route when a workflow needs:

- intent-first problem declaration;
- structured evidence or ranking before artifact generation;
- a Bridge-compatible semantic specification;
- OpenQASM/Qiskit-oriented artifacts for downstream inspection;
- a reproducibility trail that connects problem intent to circuit artifacts.

Use Bridge directly when the user already has a controlled semantic problem specification and only needs the artifact/report handoff.

## Strategic Boundary

The recommended external positioning is:

```text
QIntent is upstream of Bridge.
Bridge is the current Qiskit Ecosystem entry point.
```

This allows QIntent to gain visibility through the accepted Bridge path without creating confusion or asking Qiskit maintainers to evaluate a second QDSV project before the ecosystem story is mature.
