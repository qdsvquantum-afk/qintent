"""Multi-seed BP-soft qLDPC-style reranking benchmark.

This script runs the QDSV/QIntent post-decoding reranking experiment locally,
without Cloud Run, Colab, or public-preview API quota. It uses the local
QIntent compiler and process_data engine from qdsv_platform.

The benchmark is intentionally framed as a toy sparse-check experiment. It is
not a production qLDPC decoder benchmark and does not claim quantum advantage.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import asdict, dataclass
from itertools import combinations
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


GUARD_MIN_RISK_REDUCTION = 120
GUARD_MAX_CONFIDENCE_DROP = 100
GUARD_MIN_QDSV_MARGIN = 25
GUARD_HIGH_CONFIDENCE = 800
GUARD_SINGLETON_EXTRA_RISK_REDUCTION = 260
GUARD_SINGLETON_MAX_CONFIDENCE_DROP = 50


QINTENT_SOURCE = """
find_rows("candidate_index")
  .using_structured_semantic_score([
      block("syndrome", [
          signal("syndrome_support", influence=25, priority=2),
          signal("check_consistency", influence=20, priority=1),
          signal("decoder_margin", influence=20, priority=2),
      ], influence=28, priority=2, risk_adjustment="syndrome_risk", adjustments=[
          adjustment("syndrome_entropy_adjustment", influence=4),
      ]),
      block("logical_safety", [
          signal("logical_preservation", influence=32, priority=2),
          signal("distance_safety", influence=20, priority=2),
      ], influence=34, priority=2, risk_adjustment="logical_risk"),
      block("decoder", [
          signal("decoder_confidence", influence=60, priority=4),
          signal("propagation_safety", influence=15, priority=2),
      ], influence=45, priority=4),
  ], global_risk=0, profile="qldpc_bp_soft_decoder_rerank_multiseed")
  .accept_if(threshold=600)
  .rank()
  .top_k(1)
"""


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
    """Conservative override policy using only observable decision evidence."""

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
        and (risk_delta < GUARD_SINGLETON_EXTRA_RISK_REDUCTION or confidence_drop > GUARD_SINGLETON_MAX_CONFIDENCE_DROP)
    ):
        return baseline_row, False, "reject_high_confidence_singleton_guard"

    return selected_row, True, "accept_guarded_override"


@dataclass(frozen=True)
class BenchmarkConfig:
    seed_start: int = 260717
    seed_count: int = 12
    n_qubits: int = 24
    m_checks: int = 8
    samples_per_seed: int = 40
    max_candidate_weight: int = 3
    column_weight: int = 3
    physical_error_rate: float = 0.14
    true_error_weight2_probability: float = 0.55
    max_attempts_per_seed: int = 5000


class SparseBPBenchmark:
    def __init__(self, config: BenchmarkConfig, seed: int) -> None:
        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)
        self.check_columns: dict[int, tuple[int, ...]] = {}
        self.h: list[list[int]] = []
        self.logical_sensitive_qubits: set[int] = set()
        self._build_sparse_check_structure()

    def _build_sparse_check_structure(self) -> None:
        used_columns: set[tuple[int, ...]] = set()
        for q in range(self.config.n_qubits):
            while True:
                weight = self.config.column_weight if self.rng.random() < 0.75 else 2
                positions = self.rng.sample(range(self.config.m_checks), weight)
                column = [0] * self.config.m_checks
                for pos in positions:
                    column[pos] = 1
                column_tuple = tuple(column)
                if column_tuple not in used_columns and any(column_tuple):
                    used_columns.add(column_tuple)
                    self.check_columns[q] = column_tuple
                    break

        self.h = [
            [self.check_columns[q][check] for q in range(self.config.n_qubits)]
            for check in range(self.config.m_checks)
        ]
        self.logical_sensitive_qubits = set(
            self.rng.sample(
                range(self.config.n_qubits),
                max(5, self.config.n_qubits // 3),
            )
        )

    def xor_syndrome(self, qubits: tuple[int, ...] | list[int] | set[int]) -> tuple[int, ...]:
        return tuple(
            sum((1 if q in qubits else 0) * self.h[check][q] for q in range(self.config.n_qubits)) % 2
            for check in range(self.config.m_checks)
        )

    @staticmethod
    def residual_error(true_error: tuple[int, ...], correction: tuple[int, ...]) -> frozenset[int]:
        return frozenset(set(true_error) ^ set(correction))

    def logical_failure_proxy(self, residual: frozenset[int]) -> bool:
        return bool(residual & self.logical_sensitive_qubits) and len(residual) <= 3

    def channel_priors(self, true_error: tuple[int, ...]) -> list[float]:
        priors: list[float] = []
        for q in range(self.config.n_qubits):
            if q in true_error:
                value = self.rng.uniform(0.08, 0.38)
            else:
                value = self.rng.uniform(0.03, 0.28)
            if q in self.logical_sensitive_qubits and self.rng.random() < 0.22:
                value = self.rng.uniform(0.18, 0.48)
            if q not in true_error and self.rng.random() < 0.08:
                value = self.rng.uniform(0.20, 0.45)
            priors.append(value)
        return priors

    def bp_soft_decode(self, syndrome: tuple[int, ...], priors: list[float], max_iter: int = 20) -> tuple[list[float], list[int], int]:
        eps = 1e-12
        checks_for_var = [
            [check for check in range(self.config.m_checks) if self.h[check][q]]
            for q in range(self.config.n_qubits)
        ]
        vars_for_check = [
            [q for q in range(self.config.n_qubits) if self.h[check][q]]
            for check in range(self.config.m_checks)
        ]
        prior_llr = [
            math.log((1 - priors[q] + eps) / (priors[q] + eps))
            for q in range(self.config.n_qubits)
        ]

        q_msg = {
            (check, q): prior_llr[q]
            for q in range(self.config.n_qubits)
            for check in checks_for_var[q]
        }
        r_msg = {
            (check, q): 0.0
            for q in range(self.config.n_qubits)
            for check in checks_for_var[q]
        }
        hard = [0] * self.config.n_qubits

        iteration = 0
        for iteration in range(max_iter):
            for check in range(self.config.m_checks):
                variables = vars_for_check[check]
                for q in variables:
                    product = 1.0
                    for other_q in variables:
                        if other_q == q:
                            continue
                        product *= math.tanh(max(-30, min(30, q_msg[(check, other_q)])) / 2)
                    product = max(-1 + eps, min(1 - eps, ((-1) ** syndrome[check]) * product))
                    r_msg[(check, q)] = 2 * math.atanh(product)

            for q in range(self.config.n_qubits):
                connected_checks = checks_for_var[q]
                total = prior_llr[q] + sum(r_msg[(check, q)] for check in connected_checks)
                hard[q] = 1 if total < 0 else 0
                for check in connected_checks:
                    q_msg[(check, q)] = prior_llr[q] + sum(
                        r_msg[(other_check, q)]
                        for other_check in connected_checks
                        if other_check != check
                    )

        posterior_llr = [
            prior_llr[q] + sum(r_msg[(check, q)] for check in checks_for_var[q])
            for q in range(self.config.n_qubits)
        ]
        posterior_error_prob = [
            1 / (1 + math.exp(max(-30, min(30, llr))))
            for llr in posterior_llr
        ]
        return posterior_error_prob, hard, iteration + 1

    def enumerate_candidates(
        self,
        syndrome: tuple[int, ...],
        true_error: tuple[int, ...],
        posterior_error_prob: list[float],
        scenario_id: int,
    ) -> list[dict[str, Any]]:
        raw: list[tuple[tuple[int, ...], int, int, float, bool, bool]] = []
        for weight in range(1, self.config.max_candidate_weight + 1):
            for qubits in combinations(range(self.config.n_qubits), weight):
                if self.xor_syndrome(qubits) != syndrome:
                    continue
                log_probability = 0.0
                for q in range(self.config.n_qubits):
                    p_error = max(1e-9, min(1 - 1e-9, posterior_error_prob[q]))
                    log_probability += math.log(p_error if q in qubits else 1 - p_error)
                overlap = sum(q in self.logical_sensitive_qubits for q in qubits)
                residual = self.residual_error(true_error, qubits)
                raw.append(
                    (
                        qubits,
                        weight,
                        overlap,
                        log_probability,
                        len(residual) == 0,
                        self.logical_failure_proxy(residual),
                    )
                )

        if len(raw) < 2:
            return []

        log_values = [item[3] for item in raw]
        low, high = min(log_values), max(log_values)
        sorted_logs = sorted(log_values, reverse=True)
        decoder_margin = 0 if len(sorted_logs) < 2 else int(round(min(1000, max(0, (sorted_logs[0] - sorted_logs[1]) * 180))))

        rows: list[dict[str, Any]] = []
        for candidate_index, (qubits, weight, overlap, log_probability, exact, logical_fail) in enumerate(raw):
            decoder_confidence = 1000 if high == low else int(round(450 + 550 * (log_probability - low) / (high - low)))
            rows.append(
                {
                    "seed": self.seed,
                    "scenario_id": scenario_id,
                    "candidate_index": candidate_index,
                    "correction_qubits": " ".join(str(q) for q in qubits),
                    "candidate_weight": weight,
                    "observed_syndrome": "".join(str(bit) for bit in syndrome),
                    "predicted_syndrome": "".join(str(bit) for bit in syndrome),
                    "syndrome_support": max(0, 1000 - 20 * max(0, weight - 1)),
                    "check_consistency": 1000,
                    "logical_preservation": max(0, 950 - 160 * overlap - 15 * max(0, weight - 1)),
                    "distance_safety": max(0, 930 - 140 * overlap - 15 * weight),
                    "decoder_confidence": decoder_confidence,
                    "decoder_margin": decoder_margin,
                    "propagation_safety": max(0, 930 - 45 * weight - 45 * overlap),
                    "syndrome_risk": min(1000, 30 + 10 * weight),
                    "logical_risk": min(1000, 25 + 150 * overlap + 16 * weight),
                    "syndrome_entropy_adjustment": 12 if weight == 2 and overlap == 0 else (-12 if overlap else 0),
                    "exact_correction": exact,
                    "logical_failure_proxy": logical_fail,
                }
            )
        return rows

    def run(self, compiled_process_data: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        summary_rows: list[dict[str, Any]] = []
        attempts = 0
        scenario_id = 0

        while scenario_id < self.config.samples_per_seed and attempts < self.config.max_attempts_per_seed:
            total_start = time.perf_counter()
            attempts += 1
            true_weight = 1 if self.rng.random() < (1 - self.config.true_error_weight2_probability) else 2
            true_error = tuple(sorted(self.rng.sample(range(self.config.n_qubits), true_weight)))
            syndrome = self.xor_syndrome(true_error)
            priors = self.channel_priors(true_error)
            decode_start = time.perf_counter()
            posterior_error_prob, _hard_decision, bp_iterations = self.bp_soft_decode(syndrome, priors)
            decode_ms = (time.perf_counter() - decode_start) * 1000
            candidate_start = time.perf_counter()
            rows = self.enumerate_candidates(syndrome, true_error, posterior_error_prob, scenario_id)
            candidate_ms = (time.perf_counter() - candidate_start) * 1000
            if len(rows) < 2:
                continue

            candidates = pd.DataFrame(rows)
            baseline = candidates.sort_values(
                ["decoder_confidence", "candidate_weight"],
                ascending=[False, True],
            ).iloc[0]

            payload = dict(compiled_process_data)
            payload["rows"] = rows
            qdsv_start = time.perf_counter()
            result = compile_process_data_spec(payload)
            qdsv_ms = (time.perf_counter() - qdsv_start) * 1000
            selected = result["selected_rows"][0]
            qdsv_margin = _score_margin(result)

            low_qdsv_margin = qdsv_margin < 25
            low_decoder_margin = int(baseline["decoder_margin"]) < 50
            many_candidates = len(rows) >= 8
            uncertainty_flag_count = int(low_qdsv_margin) + int(low_decoder_margin) + int(many_candidates)
            evidence_insufficient = uncertainty_flag_count >= 2
            guarded, guarded_override_accepted, guarded_reason = _guarded_selection(
                baseline,
                selected,
                qdsv_margin=qdsv_margin,
                evidence_insufficient=evidence_insufficient,
            )
            raw_override_attempted = baseline["candidate_index"] != selected["candidate_index"]
            guarded_override_rejected = raw_override_attempted and not guarded_override_accepted
            raw_risk_delta = int(baseline["logical_risk"]) - int(selected["logical_risk"])
            raw_exact_delta = int(bool(selected["exact_correction"])) - int(bool(baseline["exact_correction"]))
            raw_failure_delta = int(bool(baseline["logical_failure_proxy"])) - int(bool(selected["logical_failure_proxy"]))
            guarded_risk_delta = int(baseline["logical_risk"]) - int(guarded["logical_risk"])
            guarded_exact_delta = int(bool(guarded["exact_correction"])) - int(bool(baseline["exact_correction"]))
            guarded_failure_delta = int(bool(baseline["logical_failure_proxy"])) - int(bool(guarded["logical_failure_proxy"]))

            summary_rows.append(
                {
                    "seed": self.seed,
                    "scenario_id": scenario_id,
                    "true_error": " ".join(str(q) for q in true_error),
                    "true_weight": true_weight,
                    "bp_iterations": bp_iterations,
                    "candidate_count": len(rows),
                    "baseline_qubits": baseline["correction_qubits"],
                    "baseline_confidence": int(baseline["decoder_confidence"]),
                    "baseline_logical_risk": int(baseline["logical_risk"]),
                    "baseline_exact": bool(baseline["exact_correction"]),
                    "baseline_failure": bool(baseline["logical_failure_proxy"]),
                    "qdsv_raw_qubits": selected["correction_qubits"],
                    "qdsv_raw_confidence": int(selected["decoder_confidence"]),
                    "qdsv_raw_logical_risk": int(selected["logical_risk"]),
                    "qdsv_raw_exact": bool(selected["exact_correction"]),
                    "qdsv_raw_failure": bool(selected["logical_failure_proxy"]),
                    "qdsv_qubits": selected["correction_qubits"],
                    "qdsv_confidence": int(selected["decoder_confidence"]),
                    "qdsv_logical_risk": int(selected["logical_risk"]),
                    "qdsv_exact": bool(selected["exact_correction"]),
                    "qdsv_failure": bool(selected["logical_failure_proxy"]),
                    "risk_delta": raw_risk_delta,
                    "exact_delta": raw_exact_delta,
                    "failure_delta": raw_failure_delta,
                    "qdsv_guarded_qubits": guarded["correction_qubits"],
                    "qdsv_guarded_confidence": int(guarded["decoder_confidence"]),
                    "qdsv_guarded_logical_risk": int(guarded["logical_risk"]),
                    "qdsv_guarded_exact": bool(guarded["exact_correction"]),
                    "qdsv_guarded_failure": bool(guarded["logical_failure_proxy"]),
                    "guarded_risk_delta": guarded_risk_delta,
                    "guarded_exact_delta": guarded_exact_delta,
                    "guarded_failure_delta": guarded_failure_delta,
                    "raw_override_attempted": bool(raw_override_attempted),
                    "guarded_override_accepted": bool(guarded_override_accepted),
                    "guarded_override_rejected": bool(guarded_override_rejected),
                    "guarded_reason": guarded_reason,
                    "raw_bad_override": bool(raw_risk_delta < 0 or raw_exact_delta < 0 or raw_failure_delta < 0),
                    "guarded_bad_override": bool(guarded_risk_delta < 0 or guarded_exact_delta < 0 or guarded_failure_delta < 0),
                    "raw_successful_override": bool(raw_override_attempted and raw_risk_delta > 0 and raw_exact_delta >= 0 and raw_failure_delta >= 0),
                    "guarded_successful_override": bool(guarded_override_accepted and guarded_risk_delta > 0 and guarded_exact_delta >= 0 and guarded_failure_delta >= 0),
                    "qdsv_score_margin": float(qdsv_margin),
                    "uncertainty_low_qdsv_margin": low_qdsv_margin,
                    "uncertainty_low_decoder_margin": low_decoder_margin,
                    "uncertainty_many_candidates": many_candidates,
                    "uncertainty_flag_count": uncertainty_flag_count,
                    "evidence_insufficient_flag": evidence_insufficient,
                    "timing_decode_ms": float(decode_ms),
                    "timing_candidate_ms": float(candidate_ms),
                    "timing_qdsv_ms": float(qdsv_ms),
                    "timing_total_ms": float((time.perf_counter() - total_start) * 1000),
                }
            )
            scenario_id += 1

        return summary_rows, attempts


def _rate(values: pd.Series) -> float:
    return float(values.mean()) if len(values) else 0.0


def _seed_metrics(seed: int, attempts: int, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "seed": seed,
        "samples": int(len(frame)),
        "attempts": int(attempts),
        "baseline_exact_rate": _rate(frame["baseline_exact"]),
        "qdsv_exact_rate": _rate(frame["qdsv_exact"]),
        "qdsv_guarded_exact_rate": _rate(frame["qdsv_guarded_exact"]),
        "baseline_failure_proxy_rate": _rate(frame["baseline_failure"]),
        "qdsv_failure_proxy_rate": _rate(frame["qdsv_failure"]),
        "qdsv_guarded_failure_proxy_rate": _rate(frame["qdsv_guarded_failure"]),
        "baseline_avg_logical_risk": float(frame["baseline_logical_risk"].mean()),
        "qdsv_avg_logical_risk": float(frame["qdsv_logical_risk"].mean()),
        "qdsv_guarded_avg_logical_risk": float(frame["qdsv_guarded_logical_risk"].mean()),
        "avg_risk_delta": float(frame["risk_delta"].mean()),
        "avg_guarded_risk_delta": float(frame["guarded_risk_delta"].mean()),
        "improved_risk_count": int((frame["risk_delta"] > 0).sum()),
        "worse_risk_count": int((frame["risk_delta"] < 0).sum()),
        "guarded_improved_risk_count": int((frame["guarded_risk_delta"] > 0).sum()),
        "guarded_worse_risk_count": int((frame["guarded_risk_delta"] < 0).sum()),
        "avg_exact_delta": float(frame["exact_delta"].mean()),
        "avg_guarded_exact_delta": float(frame["guarded_exact_delta"].mean()),
        "avg_failure_delta": float(frame["failure_delta"].mean()),
        "avg_guarded_failure_delta": float(frame["guarded_failure_delta"].mean()),
        "raw_override_rate": _rate(frame["raw_override_attempted"]),
        "guarded_override_accept_rate": _rate(frame["guarded_override_accepted"]),
        "guarded_override_reject_rate": _rate(frame["guarded_override_rejected"]),
        "raw_bad_override_rate": _rate(frame["raw_bad_override"]),
        "guarded_bad_override_rate": _rate(frame["guarded_bad_override"]),
        "raw_successful_override_rate": _rate(frame["raw_successful_override"]),
        "guarded_successful_override_rate": _rate(frame["guarded_successful_override"]),
        "evidence_insufficient_rate": _rate(frame["evidence_insufficient_flag"]),
        "avg_qdsv_score_margin": float(frame["qdsv_score_margin"].mean()),
        "avg_timing_decode_ms": float(frame["timing_decode_ms"].mean()),
        "avg_timing_candidate_ms": float(frame["timing_candidate_ms"].mean()),
        "avg_timing_qdsv_ms": float(frame["timing_qdsv_ms"].mean()),
        "avg_timing_total_ms": float(frame["timing_total_ms"].mean()),
    }


def _aggregate_metrics(seed_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "baseline_exact_rate",
        "qdsv_exact_rate",
        "qdsv_guarded_exact_rate",
        "baseline_failure_proxy_rate",
        "qdsv_failure_proxy_rate",
        "qdsv_guarded_failure_proxy_rate",
        "baseline_avg_logical_risk",
        "qdsv_avg_logical_risk",
        "qdsv_guarded_avg_logical_risk",
        "avg_risk_delta",
        "avg_guarded_risk_delta",
        "avg_exact_delta",
        "avg_guarded_exact_delta",
        "avg_failure_delta",
        "avg_guarded_failure_delta",
        "raw_override_rate",
        "guarded_override_accept_rate",
        "guarded_override_reject_rate",
        "raw_bad_override_rate",
        "guarded_bad_override_rate",
        "raw_successful_override_rate",
        "guarded_successful_override_rate",
        "evidence_insufficient_rate",
        "avg_qdsv_score_margin",
        "avg_timing_decode_ms",
        "avg_timing_candidate_ms",
        "avg_timing_qdsv_ms",
        "avg_timing_total_ms",
    ]
    out: dict[str, Any] = {
        "seed_count": len(seed_metrics),
        "total_samples": int(sum(item["samples"] for item in seed_metrics)),
        "total_improved_risk_count": int(sum(item["improved_risk_count"] for item in seed_metrics)),
        "total_worse_risk_count": int(sum(item["worse_risk_count"] for item in seed_metrics)),
        "total_guarded_improved_risk_count": int(sum(item["guarded_improved_risk_count"] for item in seed_metrics)),
        "total_guarded_worse_risk_count": int(sum(item["guarded_worse_risk_count"] for item in seed_metrics)),
    }
    for key in keys:
        values = [float(item[key]) for item in seed_metrics]
        out[f"{key}_mean"] = mean(values)
        out[f"{key}_std"] = pstdev(values) if len(values) > 1 else 0.0
    return out


def run_multiseed(config: BenchmarkConfig) -> dict[str, Any]:
    compiled = compile_qpython_source(QINTENT_SOURCE)
    compiled_process_data = compiled["process_data"]

    all_rows: list[dict[str, Any]] = []
    per_seed_metrics: list[dict[str, Any]] = []

    for offset in range(config.seed_count):
        seed = config.seed_start + offset
        benchmark = SparseBPBenchmark(config, seed)
        rows, attempts = benchmark.run(compiled_process_data)
        frame = pd.DataFrame(rows)
        if frame.empty:
            continue
        all_rows.extend(rows)
        per_seed_metrics.append(_seed_metrics(seed, attempts, frame))
        print(f"seed={seed} samples={len(frame)} qdsv_exact={per_seed_metrics[-1]['qdsv_exact_rate']:.3f} avg_risk_delta={per_seed_metrics[-1]['avg_risk_delta']:.2f}")

    aggregate = _aggregate_metrics(per_seed_metrics)
    return {
        "config": asdict(config),
        "qintent_source": QINTENT_SOURCE,
        "internal_formula_exposed": False,
        "per_seed_metrics": per_seed_metrics,
        "aggregate_metrics": aggregate,
        "summary_rows": all_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=260717)
    parser.add_argument("--seed-count", type=int, default=12)
    parser.add_argument("--samples-per-seed", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "evidence")
    args = parser.parse_args()

    config = BenchmarkConfig(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        samples_per_seed=args.samples_per_seed,
    )

    result = run_multiseed(config)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.DataFrame(result["summary_rows"])
    per_seed = pd.DataFrame(result["per_seed_metrics"])

    evidence_path = output_dir / "qdsv_qldpc_bp_soft_multiseed_evidence.json"
    summary_path = output_dir / "qdsv_qldpc_bp_soft_multiseed_summary.csv"
    metrics_path = output_dir / "qdsv_qldpc_bp_soft_multiseed_metrics.csv"

    evidence_path.write_text(
        json.dumps(
            {
                "config": result["config"],
                "qintent_source": result["qintent_source"],
                "internal_formula_exposed": False,
                "aggregate_metrics": result["aggregate_metrics"],
                "per_seed_metrics": result["per_seed_metrics"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    summary.to_csv(summary_path, index=False)
    per_seed.to_csv(metrics_path, index=False)

    print("\nAggregate metrics:")
    print(json.dumps(result["aggregate_metrics"], indent=2))
    print("\nSaved:")
    print(evidence_path)
    print(summary_path)
    print(metrics_path)


if __name__ == "__main__":
    main()
