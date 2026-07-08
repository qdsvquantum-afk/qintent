"""Steane CSS stabilizer-code logical preservation benchmark for QDSV/QIntent.

This experiment generalizes the 5-qubit stabilizer validation to a CSS code.
It uses the Steane [[7,1,3]] code and evaluates correction decisions by the
formal residual R = C E:

- R in stabilizer group S     -> formal logical success
- R in normalizer N(S) \\ S    -> non-trivial logical residual

The goal is not to propose a new decoder. QDSV/QIntent is evaluated as a
guarded semantic decision layer over candidate correction hypotheses. The
private QDSV scoring formula is not exposed.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from itertools import combinations, product
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import pandas as pd


def _find_platform_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "qdsv" / "qpython" / "compiler.py").exists():
            return parent
    raise RuntimeError("Could not locate qdsv_platform root from script path")


PLATFORM_ROOT = _find_platform_root(Path(__file__).resolve())
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from qdsv.problems.process_data import compile_process_data_spec  # noqa: E402
from qdsv.qpython.compiler import compile_qpython_source  # noqa: E402


GUARD_MIN_RISK_REDUCTION = 80
GUARD_MAX_CONFIDENCE_DROP = 180
GUARD_MIN_QDSV_MARGIN = 20
GUARD_HIGH_CONFIDENCE = 850
GUARD_SINGLETON_EXTRA_RISK_REDUCTION = 180


QINTENT_SOURCE = """
find_rows("candidate_index")
  .using_structured_semantic_score([
      block("syndrome", [
          signal("syndrome_support", influence=30, priority=2),
          signal("check_consistency", influence=25, priority=2),
          signal("css_sector_consistency", influence=20, priority=2),
      ], influence=32, priority=2, risk_adjustment="syndrome_risk"),
      block("logical_safety", [
          signal("logical_preservation", influence=45, priority=4),
          signal("distance_safety", influence=25, priority=3),
          signal("stabilizer_consistency", influence=20, priority=3),
      ], influence=45, priority=4, risk_adjustment="logical_risk"),
      block("decoder", [
          signal("decoder_confidence", influence=45, priority=3),
          signal("method_reliability", influence=25, priority=3),
          signal("propagation_safety", influence=20, priority=2),
      ], influence=35, priority=3),
  ], global_risk="logical_risk", profile="steane_css_logical_validation")
  .accept_if(threshold=600)
  .rank()
  .top_k(1)
"""


PAULIS = ("I", "X", "Y", "Z")
NON_IDENTITY = ("X", "Y", "Z")
N_QUBITS = 7

# Standard Steane [[7,1,3]] CSS stabilizer generators.
STABILIZER_GENERATORS = (
    "IIIXXXX",
    "IXXIIXX",
    "XIXIXIX",
    "IIIZZZZ",
    "IZZIIZZ",
    "ZIZIZIZ",
)


@dataclass(frozen=True)
class BenchmarkConfig:
    seed_start: int = 710001
    seed_count: int = 8
    samples_per_seed: int = 40
    max_candidate_weight: int = 3
    max_candidates_per_scenario: int = 60
    ambiguity_boost_probability: float = 0.46


def pauli_mul(a: str, b: str) -> str:
    """Multiply Pauli strings modulo global phase."""

    table = {
        ("I", "I"): "I",
        ("I", "X"): "X",
        ("I", "Y"): "Y",
        ("I", "Z"): "Z",
        ("X", "I"): "X",
        ("Y", "I"): "Y",
        ("Z", "I"): "Z",
        ("X", "X"): "I",
        ("Y", "Y"): "I",
        ("Z", "Z"): "I",
        ("X", "Y"): "Z",
        ("Y", "X"): "Z",
        ("X", "Z"): "Y",
        ("Z", "X"): "Y",
        ("Y", "Z"): "X",
        ("Z", "Y"): "X",
    }
    return "".join(table[(left, right)] for left, right in zip(a, b))


def anticommutes(a: str, b: str) -> bool:
    count = 0
    for left, right in zip(a, b):
        if left != "I" and right != "I" and left != right:
            count += 1
    return count % 2 == 1


def syndrome(error: str) -> tuple[int, ...]:
    return tuple(1 if anticommutes(error, generator) else 0 for generator in STABILIZER_GENERATORS)


def weight(pauli: str) -> int:
    return sum(char != "I" for char in pauli)


def stabilizer_group() -> set[str]:
    group = {"I" * N_QUBITS}
    for mask in product((0, 1), repeat=len(STABILIZER_GENERATORS)):
        current = "I" * N_QUBITS
        for bit, generator in zip(mask, STABILIZER_GENERATORS):
            if bit:
                current = pauli_mul(current, generator)
        group.add(current)
    return group


STABILIZER_GROUP = stabilizer_group()
NORMALIZER = {
    "".join(chars)
    for chars in product(PAULIS, repeat=N_QUBITS)
    if syndrome("".join(chars)) == (0, 0, 0, 0, 0, 0)
}


def residual(correction: str, error: str) -> str:
    return pauli_mul(correction, error)


def logical_failure(correction: str, error: str) -> bool:
    r = residual(correction, error)
    return r in NORMALIZER and r not in STABILIZER_GROUP


def logical_success(correction: str, error: str) -> bool:
    return residual(correction, error) in STABILIZER_GROUP


def pauli_at(qubit: int, op: str) -> str:
    chars = ["I"] * N_QUBITS
    chars[qubit] = op
    return "".join(chars)


def all_candidate_corrections(target_syndrome: tuple[int, ...], max_weight: int) -> list[str]:
    candidates: list[str] = []
    for w in range(0, max_weight + 1):
        for qubits in combinations(range(N_QUBITS), w):
            if w == 0:
                candidate = "I" * N_QUBITS
                if syndrome(candidate) == target_syndrome:
                    candidates.append(candidate)
                continue
            for ops in product(NON_IDENTITY, repeat=w):
                chars = ["I"] * N_QUBITS
                for qubit, op in zip(qubits, ops):
                    chars[qubit] = op
                candidate = "".join(chars)
                if syndrome(candidate) == target_syndrome:
                    candidates.append(candidate)
    return sorted(set(candidates), key=lambda item: (weight(item), item))


def _score_margin(result: dict[str, Any]) -> float:
    enriched = result.get("rows_enriched") or result.get("rows") or []
    scores = sorted(
        [
            float(row["_qdsv_structured_semantic_score"])
            for row in enriched
            if row.get("_qdsv_structured_semantic_score") is not None
        ],
        reverse=True,
    )
    if len(scores) < 2:
        return 1000.0
    return scores[0] - scores[1]


def _guarded_selection(
    baseline: Any,
    selected: dict[str, Any],
    *,
    qdsv_margin: float,
    evidence_insufficient: bool,
) -> tuple[dict[str, Any], bool, str]:
    baseline_row = baseline.to_dict() if hasattr(baseline, "to_dict") else dict(baseline)
    selected_row = dict(selected)

    if baseline_row.get("candidate_index") == selected_row.get("candidate_index"):
        return selected_row, False, "same_as_baseline"

    baseline_risk = int(baseline_row["logical_risk"])
    selected_risk = int(selected_row["logical_risk"])
    risk_delta = baseline_risk - selected_risk
    confidence_drop = int(baseline_row["decoder_confidence"]) - int(selected_row["decoder_confidence"])

    if evidence_insufficient:
        return baseline_row, False, "reject_evidence_insufficient"
    if qdsv_margin < GUARD_MIN_QDSV_MARGIN:
        return baseline_row, False, "reject_low_qdsv_margin"
    if risk_delta < GUARD_MIN_RISK_REDUCTION:
        return baseline_row, False, "reject_insufficient_risk_reduction"
    if confidence_drop > GUARD_MAX_CONFIDENCE_DROP:
        return baseline_row, False, "reject_confidence_drop"

    baseline_weight = int(baseline_row.get("candidate_weight", 99))
    selected_weight = int(selected_row.get("candidate_weight", 99))
    baseline_confidence = int(baseline_row["decoder_confidence"])
    if (
        baseline_confidence >= GUARD_HIGH_CONFIDENCE
        and baseline_weight <= 1
        and selected_weight > baseline_weight
        and risk_delta < GUARD_SINGLETON_EXTRA_RISK_REDUCTION
    ):
        return baseline_row, False, "reject_high_confidence_singleton_guard"

    return selected_row, True, "accept_guarded_override"


def _css_sector_balance(pauli: str) -> int:
    x_like = sum(char in {"X", "Y"} for char in pauli)
    z_like = sum(char in {"Z", "Y"} for char in pauli)
    return abs(x_like - z_like)


class SteaneCssLogicalBenchmark:
    def __init__(self, config: BenchmarkConfig, seed: int) -> None:
        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)

    def sample_error(self) -> str:
        # Steane [[7,1,3]] corrects arbitrary single-qubit Pauli errors.
        return pauli_at(self.rng.randrange(N_QUBITS), self.rng.choice(NON_IDENTITY))

    def build_rows(self, true_error: str, scenario_id: int) -> list[dict[str, Any]]:
        target = syndrome(true_error)
        candidates = all_candidate_corrections(target, self.config.max_candidate_weight)
        if true_error not in candidates:
            candidates.append(true_error)

        risky_candidates = [item for item in candidates if logical_failure(item, true_error)]
        boosted: str | None = None
        if risky_candidates and self.rng.random() < self.config.ambiguity_boost_probability:
            boosted = self.rng.choice(risky_candidates)

        raw_rows: list[dict[str, Any]] = []
        for candidate in candidates:
            candidate_weight = weight(candidate)
            sector_balance = _css_sector_balance(candidate)
            y_count = candidate.count("Y")
            is_success = logical_success(candidate, true_error)
            is_failure = logical_failure(candidate, true_error)

            confidence = 972 - 125 * max(0, candidate_weight - 1) + self.rng.randint(-45, 45)
            if candidate == true_error:
                confidence += self.rng.randint(0, 45)
            if candidate == boosted:
                confidence += self.rng.randint(175, 265)
            confidence = max(100, min(1000, confidence))

            structural_weight_penalty = max(0, candidate_weight - 1)
            css_penalty = 18 * sector_balance + 28 * y_count
            raw_rows.append(
                {
                    "seed": self.seed,
                    "scenario_id": scenario_id,
                    "candidate_index": len(raw_rows),
                    "true_error": true_error,
                    "candidate_correction": candidate,
                    "candidate_weight": candidate_weight,
                    "syndrome": "".join(str(bit) for bit in target),
                    "syndrome_support": 1000,
                    "check_consistency": 1000,
                    "css_sector_consistency": max(0, 1000 - css_penalty),
                    "stabilizer_consistency": 1000 if syndrome(candidate) == target else 0,
                    "logical_preservation": max(0, 980 - 245 * structural_weight_penalty - css_penalty),
                    "distance_safety": max(0, 950 - 220 * structural_weight_penalty - 14 * sector_balance),
                    "decoder_confidence": confidence,
                    "method_reliability": 860,
                    "propagation_safety": max(0, 950 - 105 * candidate_weight - 14 * y_count),
                    "syndrome_risk": 35 + 10 * candidate_weight + 4 * sector_balance,
                    "logical_risk": min(
                        1000,
                        30 + 150 * structural_weight_penalty + 20 * candidate_weight + css_penalty,
                    ),
                    "formal_logical_success": is_success,
                    "formal_logical_failure": is_failure,
                    "residual": residual(candidate, true_error),
                    "residual_in_stabilizer": residual(candidate, true_error) in STABILIZER_GROUP,
                    "residual_in_normalizer": residual(candidate, true_error) in NORMALIZER,
                    "boosted_risky_candidate": candidate == boosted,
                    "css_sector_balance": sector_balance,
                    "y_count": y_count,
                }
            )

        frame = pd.DataFrame(raw_rows).sort_values(
            ["decoder_confidence", "candidate_weight"],
            ascending=[False, True],
        )
        selected = frame.head(self.config.max_candidates_per_scenario)
        if true_error not in set(selected["candidate_correction"]):
            true_row = pd.DataFrame([row for row in raw_rows if row["candidate_correction"] == true_error])
            selected = pd.concat([selected, true_row], ignore_index=True)
        selected = selected.drop_duplicates("candidate_correction").reset_index(drop=True)
        selected["candidate_index"] = range(len(selected))
        return selected.to_dict(orient="records")

    def run(self, compiled_process_data: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        rows_out: list[dict[str, Any]] = []
        attempts = 0
        scenario_id = 0

        while scenario_id < self.config.samples_per_seed:
            total_start = time.perf_counter()
            attempts += 1
            true_error = self.sample_error()
            candidate_start = time.perf_counter()
            rows = self.build_rows(true_error, scenario_id)
            candidate_ms = (time.perf_counter() - candidate_start) * 1000
            if len(rows) < 2:
                continue

            frame = pd.DataFrame(rows)
            baseline = frame.sort_values(["decoder_confidence", "candidate_weight"], ascending=[False, True]).iloc[0]
            oracle = frame.sort_values(
                ["formal_logical_failure", "formal_logical_success", "logical_risk", "candidate_weight"],
                ascending=[True, False, True, True],
            ).iloc[0]

            payload = dict(compiled_process_data)
            payload["rows"] = rows
            qdsv_start = time.perf_counter()
            result = compile_process_data_spec(payload)
            qdsv_ms = (time.perf_counter() - qdsv_start) * 1000
            selected = result["selected_rows"][0]
            qdsv_margin = _score_margin(result)
            low_qdsv_margin = qdsv_margin < GUARD_MIN_QDSV_MARGIN
            many_candidates = len(rows) >= 50
            decoder_conflict = bool(frame["boosted_risky_candidate"].any())
            evidence_insufficient = int(low_qdsv_margin) + int(many_candidates) + int(decoder_conflict) >= 2
            guarded, guarded_override_accepted, guarded_reason = _guarded_selection(
                baseline,
                selected,
                qdsv_margin=qdsv_margin,
                evidence_insufficient=evidence_insufficient,
            )

            raw_override_attempted = baseline["candidate_index"] != selected["candidate_index"]
            guarded_override_rejected = raw_override_attempted and not guarded_override_accepted
            raw_failure_delta = int(bool(baseline["formal_logical_failure"])) - int(bool(selected["formal_logical_failure"]))
            guarded_failure_delta = int(bool(baseline["formal_logical_failure"])) - int(bool(guarded["formal_logical_failure"]))
            raw_risk_delta = int(baseline["logical_risk"]) - int(selected["logical_risk"])
            guarded_risk_delta = int(baseline["logical_risk"]) - int(guarded["logical_risk"])

            rows_out.append(
                {
                    "seed": self.seed,
                    "scenario_id": scenario_id,
                    "true_error": true_error,
                    "syndrome": "".join(str(bit) for bit in syndrome(true_error)),
                    "candidate_count": len(rows),
                    "baseline_correction": baseline["candidate_correction"],
                    "baseline_confidence": int(baseline["decoder_confidence"]),
                    "baseline_logical_risk": int(baseline["logical_risk"]),
                    "baseline_formal_logical_success": bool(baseline["formal_logical_success"]),
                    "baseline_formal_logical_failure": bool(baseline["formal_logical_failure"]),
                    "baseline_residual": baseline["residual"],
                    "oracle_best_correction": oracle["candidate_correction"],
                    "oracle_best_logical_risk": int(oracle["logical_risk"]),
                    "oracle_best_formal_logical_success": bool(oracle["formal_logical_success"]),
                    "oracle_best_formal_logical_failure": bool(oracle["formal_logical_failure"]),
                    "oracle_best_residual": oracle["residual"],
                    "qdsv_raw_correction": selected["candidate_correction"],
                    "qdsv_raw_confidence": int(selected["decoder_confidence"]),
                    "qdsv_raw_logical_risk": int(selected["logical_risk"]),
                    "qdsv_raw_formal_logical_success": bool(selected["formal_logical_success"]),
                    "qdsv_raw_formal_logical_failure": bool(selected["formal_logical_failure"]),
                    "qdsv_raw_residual": selected["residual"],
                    "qdsv_guarded_correction": guarded["candidate_correction"],
                    "qdsv_guarded_confidence": int(guarded["decoder_confidence"]),
                    "qdsv_guarded_logical_risk": int(guarded["logical_risk"]),
                    "qdsv_guarded_formal_logical_success": bool(guarded["formal_logical_success"]),
                    "qdsv_guarded_formal_logical_failure": bool(guarded["formal_logical_failure"]),
                    "qdsv_guarded_residual": guarded["residual"],
                    "raw_risk_delta": raw_risk_delta,
                    "guarded_risk_delta": guarded_risk_delta,
                    "raw_logical_failure_delta": raw_failure_delta,
                    "guarded_logical_failure_delta": guarded_failure_delta,
                    "raw_override_attempted": bool(raw_override_attempted),
                    "guarded_override_accepted": bool(guarded_override_accepted),
                    "guarded_override_rejected": bool(guarded_override_rejected),
                    "guarded_reason": guarded_reason,
                    "raw_bad_override": bool(raw_override_attempted and raw_failure_delta < 0),
                    "guarded_bad_override": bool(guarded_override_accepted and guarded_failure_delta < 0),
                    "raw_successful_override": bool(raw_override_attempted and raw_failure_delta > 0),
                    "guarded_successful_override": bool(guarded_override_accepted and guarded_failure_delta > 0),
                    "evidence_insufficient_flag": bool(evidence_insufficient),
                    "qdsv_score_margin": float(qdsv_margin),
                    "timing_candidate_ms": float(candidate_ms),
                    "timing_qdsv_ms": float(qdsv_ms),
                    "timing_total_ms": float((time.perf_counter() - total_start) * 1000),
                }
            )
            scenario_id += 1

        return rows_out, attempts


def _rate(values: pd.Series) -> float:
    return float(values.mean()) if len(values) else 0.0


def _conditional_rate(mask: pd.Series, values: pd.Series) -> float:
    selected = values[mask]
    return float(selected.mean()) if len(selected) else 0.0


def _seed_metrics(seed: int, attempts: int, frame: pd.DataFrame) -> dict[str, Any]:
    baseline_failure = frame["baseline_formal_logical_failure"].astype(bool)
    return {
        "seed": seed,
        "samples": int(len(frame)),
        "attempts": int(attempts),
        "baseline_logical_failure_rate": _rate(frame["baseline_formal_logical_failure"]),
        "oracle_best_logical_failure_rate": _rate(frame["oracle_best_formal_logical_failure"]),
        "qdsv_raw_logical_failure_rate": _rate(frame["qdsv_raw_formal_logical_failure"]),
        "qdsv_guarded_logical_failure_rate": _rate(frame["qdsv_guarded_formal_logical_failure"]),
        "baseline_logical_success_rate": _rate(frame["baseline_formal_logical_success"]),
        "oracle_best_logical_success_rate": _rate(frame["oracle_best_formal_logical_success"]),
        "qdsv_raw_logical_success_rate": _rate(frame["qdsv_raw_formal_logical_success"]),
        "qdsv_guarded_logical_success_rate": _rate(frame["qdsv_guarded_formal_logical_success"]),
        "baseline_avg_logical_risk": float(frame["baseline_logical_risk"].mean()),
        "oracle_best_avg_logical_risk": float(frame["oracle_best_logical_risk"].mean()),
        "qdsv_raw_avg_logical_risk": float(frame["qdsv_raw_logical_risk"].mean()),
        "qdsv_guarded_avg_logical_risk": float(frame["qdsv_guarded_logical_risk"].mean()),
        "avg_raw_risk_delta": float(frame["raw_risk_delta"].mean()),
        "avg_guarded_risk_delta": float(frame["guarded_risk_delta"].mean()),
        "avg_raw_logical_failure_delta": float(frame["raw_logical_failure_delta"].mean()),
        "avg_guarded_logical_failure_delta": float(frame["guarded_logical_failure_delta"].mean()),
        "raw_override_rate": _rate(frame["raw_override_attempted"]),
        "guarded_override_accept_rate": _rate(frame["guarded_override_accepted"]),
        "guarded_override_reject_rate": _rate(frame["guarded_override_rejected"]),
        "raw_bad_override_rate": _rate(frame["raw_bad_override"]),
        "guarded_bad_override_rate": _rate(frame["guarded_bad_override"]),
        "raw_successful_override_rate": _rate(frame["raw_successful_override"]),
        "guarded_successful_override_rate": _rate(frame["guarded_successful_override"]),
        "raw_recovery_over_baseline_failure_rate": _conditional_rate(
            baseline_failure,
            baseline_failure & ~frame["qdsv_raw_formal_logical_failure"].astype(bool),
        ),
        "guarded_recovery_over_baseline_failure_rate": _conditional_rate(
            baseline_failure,
            baseline_failure & ~frame["qdsv_guarded_formal_logical_failure"].astype(bool),
        ),
        "evidence_insufficient_rate": _rate(frame["evidence_insufficient_flag"]),
        "avg_qdsv_score_margin": float(frame["qdsv_score_margin"].mean()),
        "avg_timing_candidate_ms": float(frame["timing_candidate_ms"].mean()),
        "avg_timing_qdsv_ms": float(frame["timing_qdsv_ms"].mean()),
        "avg_timing_total_ms": float(frame["timing_total_ms"].mean()),
    }


def _aggregate(seed_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "baseline_logical_failure_rate",
        "oracle_best_logical_failure_rate",
        "qdsv_raw_logical_failure_rate",
        "qdsv_guarded_logical_failure_rate",
        "baseline_logical_success_rate",
        "oracle_best_logical_success_rate",
        "qdsv_raw_logical_success_rate",
        "qdsv_guarded_logical_success_rate",
        "baseline_avg_logical_risk",
        "oracle_best_avg_logical_risk",
        "qdsv_raw_avg_logical_risk",
        "qdsv_guarded_avg_logical_risk",
        "avg_raw_risk_delta",
        "avg_guarded_risk_delta",
        "avg_raw_logical_failure_delta",
        "avg_guarded_logical_failure_delta",
        "raw_override_rate",
        "guarded_override_accept_rate",
        "guarded_override_reject_rate",
        "raw_bad_override_rate",
        "guarded_bad_override_rate",
        "raw_successful_override_rate",
        "guarded_successful_override_rate",
        "raw_recovery_over_baseline_failure_rate",
        "guarded_recovery_over_baseline_failure_rate",
        "evidence_insufficient_rate",
        "avg_qdsv_score_margin",
        "avg_timing_candidate_ms",
        "avg_timing_qdsv_ms",
        "avg_timing_total_ms",
    ]
    out: dict[str, Any] = {
        "seed_count": len(seed_metrics),
        "total_samples": int(sum(item["samples"] for item in seed_metrics)),
    }
    for key in keys:
        values = [float(item[key]) for item in seed_metrics]
        out[f"{key}_mean"] = mean(values)
        out[f"{key}_std"] = pstdev(values) if len(values) > 1 else 0.0
    return out


def run_experiment(config: BenchmarkConfig) -> dict[str, Any]:
    compiled = compile_qpython_source(QINTENT_SOURCE)["process_data"]
    all_rows: list[dict[str, Any]] = []
    per_seed: list[dict[str, Any]] = []

    for offset in range(config.seed_count):
        seed = config.seed_start + offset
        benchmark = SteaneCssLogicalBenchmark(config, seed)
        rows, attempts = benchmark.run(compiled)
        frame = pd.DataFrame(rows)
        metrics = _seed_metrics(seed, attempts, frame)
        per_seed.append(metrics)
        all_rows.extend(rows)
        print(
            f"seed={seed} samples={metrics['samples']} "
            f"baseline_lfr={metrics['baseline_logical_failure_rate']:.3f} "
            f"raw_lfr={metrics['qdsv_raw_logical_failure_rate']:.3f} "
            f"guarded_lfr={metrics['qdsv_guarded_logical_failure_rate']:.3f}"
        )

    return {
        "config": asdict(config),
        "code": {
            "name": "Steane [[7,1,3]] CSS stabilizer code",
            "stabilizer_generators": STABILIZER_GENERATORS,
            "stabilizer_group_size": len(STABILIZER_GROUP),
            "normalizer_size": len(NORMALIZER),
            "logical_failure_condition": "R = C E in N(S) \\ S",
            "logical_success_condition": "R = C E in S",
        },
        "qintent_source": QINTENT_SOURCE,
        "internal_formula_exposed": False,
        "aggregate_metrics": _aggregate(per_seed),
        "per_seed_metrics": per_seed,
        "summary_rows": all_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=710001)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--samples-per-seed", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "evidence")
    args = parser.parse_args()

    config = BenchmarkConfig(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        samples_per_seed=args.samples_per_seed,
    )
    result = run_experiment(config)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "qdsv_qldpc_steane_css_logical_evidence.json"
    summary_path = output_dir / "qdsv_qldpc_steane_css_logical_summary.csv"
    metrics_path = output_dir / "qdsv_qldpc_steane_css_logical_metrics.csv"

    pd.DataFrame(result["summary_rows"]).to_csv(summary_path, index=False)
    pd.DataFrame(result["per_seed_metrics"]).to_csv(metrics_path, index=False)
    evidence_path.write_text(
        json.dumps(
            {
                "config": result["config"],
                "code": result["code"],
                "qintent_source": result["qintent_source"],
                "internal_formula_exposed": False,
                "aggregate_metrics": result["aggregate_metrics"],
                "per_seed_metrics": result["per_seed_metrics"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nAggregate metrics:")
    print(json.dumps(result["aggregate_metrics"], indent=2))
    print("\nSaved:")
    print(evidence_path)
    print(summary_path)
    print(metrics_path)


if __name__ == "__main__":
    main()
