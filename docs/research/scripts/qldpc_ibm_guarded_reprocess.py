"""Reprocess IBM hardware syndrome evidence with QDSV guarded policy.

This script does not submit a new IBM job. It takes the archived IBM syndrome
evidence and adds a conservative guarded decision layer:

baseline -> qdsv_raw -> qdsv_guarded

The policy uses only observable evidence already present in the public artifact:
confidence, logical-risk proxy, candidate weight and syndrome-count dispersion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


GUARD_MIN_RISK_REDUCTION = 120
GUARD_MAX_CONFIDENCE_DROP = 100
GUARD_HIGH_CONFIDENCE = 800
GUARD_SINGLETON_EXTRA_RISK_REDUCTION = 260
GUARD_SINGLETON_MAX_CONFIDENCE_DROP = 50
GUARD_MAX_OFF_EXPECTED_PROBABILITY = 0.10


def _candidate_weight(value: Any) -> int:
    clean = str(value or "").strip()
    if not clean or clean.lower() == "none":
        return 0
    return len(clean.split())


def _guarded_row(row: dict[str, Any], off_expected_probability: float) -> tuple[dict[str, Any], bool, str]:
    baseline = {
        "qubits": row["baseline_qubits"],
        "confidence": int(row["baseline_confidence"]),
        "logical_risk": int(row["baseline_logical_risk"]),
        "exact": bool(row["baseline_exact"]),
        "failure": bool(row["baseline_failure_proxy"]),
        "weight": _candidate_weight(row["baseline_qubits"]),
    }
    raw = {
        "qubits": row["qdsv_qubits"],
        "confidence": int(row["qdsv_confidence"]),
        "logical_risk": int(row["qdsv_logical_risk"]),
        "exact": bool(row["qdsv_exact"]),
        "failure": bool(row["qdsv_failure_proxy"]),
        "weight": _candidate_weight(row["qdsv_qubits"]),
    }

    if baseline["qubits"] == raw["qubits"]:
        return raw, False, "same_as_baseline"

    risk_delta = baseline["logical_risk"] - raw["logical_risk"]
    confidence_drop = baseline["confidence"] - raw["confidence"]

    if off_expected_probability > GUARD_MAX_OFF_EXPECTED_PROBABILITY:
        return baseline, False, "reject_noisy_syndrome_dispersion"
    if risk_delta < GUARD_MIN_RISK_REDUCTION:
        return baseline, False, "reject_insufficient_risk_reduction"
    if confidence_drop > GUARD_MAX_CONFIDENCE_DROP:
        return baseline, False, "reject_confidence_drop"
    if (
        baseline["confidence"] >= GUARD_HIGH_CONFIDENCE
        and baseline["weight"] <= 1
        and raw["weight"] > baseline["weight"]
        and (risk_delta < GUARD_SINGLETON_EXTRA_RISK_REDUCTION or confidence_drop > GUARD_SINGLETON_MAX_CONFIDENCE_DROP)
    ):
        return baseline, False, "reject_high_confidence_singleton_guard"

    return raw, True, "accept_guarded_override"


def reprocess(input_path: Path, output_dir: Path) -> dict[str, Any]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    summary = pd.DataFrame(data["summary"])

    count_rows: list[dict[str, Any]] = []
    off_expected_by_scenario: dict[int, float] = {}
    for scenario in data["scenarios"]:
        counts = scenario.get("ibm_counts", {})
        total = sum(int(v) for v in counts.values()) or 1
        expected = scenario["expected_syndrome"]
        observed = scenario["ibm_observed_syndrome"]
        expected_probability = int(counts.get(expected, 0)) / total
        off_expected_probability = 1 - expected_probability
        off_expected_by_scenario[int(scenario["scenario_id"])] = off_expected_probability
        count_rows.append(
            {
                "scenario_id": int(scenario["scenario_id"]),
                "label": scenario["label"],
                "expected_syndrome": expected,
                "observed_syndrome": observed,
                "expected_probability": expected_probability,
                "observed_probability": int(counts.get(observed, 0)) / total,
                "off_expected_probability": off_expected_probability,
                "counts": json.dumps(counts, sort_keys=True),
            }
        )

    guarded_rows: list[dict[str, Any]] = []
    for row in summary.to_dict(orient="records"):
        off_expected = off_expected_by_scenario[int(row["scenario_id"])]
        guarded, accepted, reason = _guarded_row(row, off_expected)
        baseline_risk = int(row["baseline_logical_risk"])
        baseline_exact = bool(row["baseline_exact"])
        baseline_failure = bool(row["baseline_failure_proxy"])
        raw_risk = int(row["qdsv_logical_risk"])
        raw_exact = bool(row["qdsv_exact"])
        raw_failure = bool(row["qdsv_failure_proxy"])

        enriched = dict(row)
        enriched.update(
            {
                "qdsv_raw_qubits": row["qdsv_qubits"],
                "qdsv_raw_confidence": int(row["qdsv_confidence"]),
                "qdsv_raw_logical_risk": raw_risk,
                "qdsv_raw_exact": raw_exact,
                "qdsv_raw_failure_proxy": raw_failure,
                "qdsv_guarded_qubits": guarded["qubits"],
                "qdsv_guarded_confidence": guarded["confidence"],
                "qdsv_guarded_logical_risk": guarded["logical_risk"],
                "qdsv_guarded_exact": guarded["exact"],
                "qdsv_guarded_failure_proxy": guarded["failure"],
                "guarded_risk_delta": baseline_risk - guarded["logical_risk"],
                "guarded_exact_delta": int(guarded["exact"]) - int(baseline_exact),
                "guarded_failure_delta": int(baseline_failure) - int(guarded["failure"]),
                "raw_override_attempted": row["baseline_qubits"] != row["qdsv_qubits"],
                "guarded_override_accepted": accepted,
                "guarded_override_rejected": row["baseline_qubits"] != row["qdsv_qubits"] and not accepted,
                "guarded_reason": reason,
                "raw_bad_override": bool((baseline_risk - raw_risk) < 0 or int(raw_exact) - int(baseline_exact) < 0 or int(baseline_failure) - int(raw_failure) < 0),
                "guarded_bad_override": bool((baseline_risk - guarded["logical_risk"]) < 0 or int(guarded["exact"]) - int(baseline_exact) < 0 or int(baseline_failure) - int(guarded["failure"]) < 0),
                "off_expected_probability": off_expected,
            }
        )
        guarded_rows.append(enriched)

    guarded_summary = pd.DataFrame(guarded_rows)
    counts_frame = pd.DataFrame(count_rows)
    metrics = {
        "experiment": data["experiment"],
        "source": data["source"],
        "shots": data["shots"],
        "run_ibm_hardware": data["run_ibm_hardware"],
        "ibm_backend_name": data["ibm_backend_name"],
        "ibm_job_id": data["ibm_job_id"],
        "scenario_count": int(len(guarded_summary)),
        "observed_syndrome_match_rate": float((counts_frame["expected_syndrome"] == counts_frame["observed_syndrome"]).mean()),
        "avg_expected_probability": float(counts_frame["expected_probability"].mean()),
        "avg_off_expected_probability": float(counts_frame["off_expected_probability"].mean()),
        "baseline_exact_rate": float(guarded_summary["baseline_exact"].mean()),
        "qdsv_raw_exact_rate": float(guarded_summary["qdsv_raw_exact"].mean()),
        "qdsv_guarded_exact_rate": float(guarded_summary["qdsv_guarded_exact"].mean()),
        "baseline_failure_proxy_rate": float(guarded_summary["baseline_failure_proxy"].mean()),
        "qdsv_raw_failure_proxy_rate": float(guarded_summary["qdsv_raw_failure_proxy"].mean()),
        "qdsv_guarded_failure_proxy_rate": float(guarded_summary["qdsv_guarded_failure_proxy"].mean()),
        "baseline_avg_logical_risk": float(guarded_summary["baseline_logical_risk"].mean()),
        "qdsv_raw_avg_logical_risk": float(guarded_summary["qdsv_raw_logical_risk"].mean()),
        "qdsv_guarded_avg_logical_risk": float(guarded_summary["qdsv_guarded_logical_risk"].mean()),
        "avg_raw_risk_delta": float(guarded_summary["risk_delta"].mean()),
        "avg_guarded_risk_delta": float(guarded_summary["guarded_risk_delta"].mean()),
        "raw_override_rate": float(guarded_summary["raw_override_attempted"].mean()),
        "guarded_override_accept_rate": float(guarded_summary["guarded_override_accepted"].mean()),
        "guarded_override_reject_rate": float(guarded_summary["guarded_override_rejected"].mean()),
        "raw_bad_override_rate": float(guarded_summary["raw_bad_override"].mean()),
        "guarded_bad_override_rate": float(guarded_summary["guarded_bad_override"].mean()),
    }

    data["summary"] = guarded_rows
    data["guarded_policy"] = {
        "name": "qldpc_ibm_hardware_guarded_policy.v1",
        "min_risk_reduction": GUARD_MIN_RISK_REDUCTION,
        "max_confidence_drop": GUARD_MAX_CONFIDENCE_DROP,
        "high_confidence": GUARD_HIGH_CONFIDENCE,
        "singleton_extra_risk_reduction": GUARD_SINGLETON_EXTRA_RISK_REDUCTION,
        "singleton_max_confidence_drop": GUARD_SINGLETON_MAX_CONFIDENCE_DROP,
        "max_off_expected_probability": GUARD_MAX_OFF_EXPECTED_PROBABILITY,
    }
    data["metrics"] = metrics

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "qdsv_qldpc_ibm_hardware_syndrome_evidence.json").write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    guarded_summary.to_csv(output_dir / "qdsv_qldpc_ibm_hardware_syndrome_summary.csv", index=False)
    counts_frame.to_csv(output_dir / "qdsv_qldpc_ibm_hardware_syndrome_counts.csv", index=False)
    (output_dir / "qdsv_qldpc_ibm_hardware_syndrome_metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "evidence" / "qdsv_qldpc_ibm_hardware_syndrome_evidence.json",
    )
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "evidence")
    args = parser.parse_args()
    metrics = reprocess(args.input, args.output_dir)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
