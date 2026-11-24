# Hardware Optimization Profiles

QIntent and Qruba use the same server-side hardware pipeline. The
optimization_profile selects how much physical-candidate search the worker
performs before submitting the circuit to IBM Quantum.

The profile is a per-job setting. It does not change the semantic operation,
the measurement contract, or the public endpoint used by the request.

## Profiles

| Profile | Physical selection | Recommended use |
| --- | --- | --- |
| baseline | Validates one eligible logical candidate, materializes one target candidate, and selects it directly. | Normal user runs, smoke tests, and the shortest path to a QPU submission. |
| balanced | Evaluates a bounded set of candidates and applies Pareto/resource selection. | Regular hardware experiments where target quality matters. |
| advanced | Uses the largest configured candidate and replay budgets with Pareto selection. | Deliberate optimization campaigns with extra CPU time available. |

baseline is the default for the QIntent SDK and Qruba's QIntent node. It does
not mean that validation is skipped: the selected circuit still must pass the
canonical compilation, target compatibility, and hardware readiness checks.
The one-candidate limit is intentional for constrained workers.

## SDK

    from qintent import QIntentClient

    client = QIntentClient(license_key="...")

    job = client.submit_hardware(
        "x = domain(0, 31); find(x).where(eq(x, 17))",
        backend_name="least_busy",
        shots=1024,
        optimization_profile="baseline",
    )

    # The GET is storage-backed by default. It does not ask the API to
    # perform an extra live provider poll.
    status = client.hardware_job(job["job_id"])

To request the more expensive path explicitly:

    job = client.submit_hardware(
        source,
        backend_name="least_busy",
        optimization_profile="advanced",
    )

Use live_poll=True only when an immediate provider refresh is explicitly
needed:

    status = client.hardware_job(job["job_id"], live_poll=True)

## Qruba

Open the QIntent node, expand Execution settings, and choose:

- Baseline for the normal end-user flow.
- Balanced for a bounded physical optimization experiment.
- Advanced for a longer optimization campaign.

The selected value is sent as optimization_profile to
POST /api/product/qpython/quantum/sample, the same API used by the SDK.

## What this does not change

- The existing v2 manual-operation workflow remains available.
- Simulator execution and local QIntent execution keep their current paths.
- The QIntent and ScoreModel public endpoints remain separate for compatibility.
- The worker and evidence model remain shared.
- A profile never authorizes automatic promotion or hides a failed hardware
  readiness check.

## Public job evidence

Hardware job responses expose the normalized profile and effective limits,
including the selection mode and candidate budget. The complete physical
report records the selected profile and the effective limits used by the
worker.
