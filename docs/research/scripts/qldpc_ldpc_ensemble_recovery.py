"""Real-ldpc decoder ensemble recovery benchmark.

This experiment uses the external `ldpc` package to generate real decoder
outputs from BP, BP+OSD and BP+LSD. QDSV/QIntent is then evaluated as a
post-decoding decision layer over those candidate corrections.

The benchmark intentionally focuses on BP-failure / BP-ambiguity scenarios.
It does not claim to outperform BP+OSD as a decoder. Instead, it tests whether
the QDSV decision layer can recover useful corrections when BP alone fails by
selecting across a decoder ensemble and risk-aware candidate evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import numpy as np
import pandas as pd


def _find_platform_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "qdsv" / "qpython" / "compiler.py").exists():
            return parent
    raise RuntimeError("Could not locate qdsv_platform root from script path")


PLATFORM_ROOT = _find_platform_root(Path(__file__).resolve())
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

try:
    from ldpc import BpDecoder, BpLsdDecoder, BpOsdDecoder
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("Install the external decoder package first: python -m pip install ldpc==2.4.1") from exc

from qdsv.problems.process_data import compile_process_data_spec  # noqa: E402
from qdsv.qpython.compiler import compile_qpython_source  # noqa: E402


QINTENT_SOURCE = """
find_rows("candidate_index")
  .using_structured_semantic_score([
      block("syndrome", [
          signal("syndrome_support", influence=30, priority=2),
          signal("check_consistency", influence=25, priority=2),
          signal("decoder_agreement", influence=20, priority=2),
      ], influence=30, priority=2, risk_adjustment="syndrome_risk"),
      block("logical_safety", [
          signal("logical_preservation", influence=30, priority=2),
          signal("distance_safety", influence=20, priority=2),
      ], influence=30, priority=2, risk_adjustment="logical_risk"),
      block("decoder", [
          signal("decoder_confidence", influence=70, priority=5),
          signal("method_reliability", influence=35, priority=4),
          signal("propagation_safety", influence=15, priority=2),
      ], influence=55, priority=5),
  ], global_risk=0, profile="real_ldpc_bp_failure_recovery")
  .accept_if(threshold=600)
  .rank()
  .top_k(1)
"""


@dataclass(frozen=True)
class BenchmarkConfig:
    seed_start: int = 410001
    seed_count: int = 8
    samples_per_seed: int = 40
    n_qubits: int = 48
    m_checks: int = 24
    column_weight: int = 3
    max_attempts_multiplier: int = 25
    max_extra_candidate_weight: int = 2


class RealLdpcEnsembleBenchmark:
    def __init__(self, config: BenchmarkConfig, seed: int) -> None:
        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)
        self.h = self._make_sparse_pcm()
        self.logical_sensitive_qubits = set(
            self.rng.sample(
                range(config.n_qubits),
                max(8, config.n_qubits // 4),
            )
        )
        self.method_reliability = {
            "bp": 760,
            "bposd": 960,
            "bplsd": 920,
            "low_weight_alt": 650,
        }

    def _make_sparse_pcm(self) -> np.ndarray:
        columns: list[tuple[int, ...]] = []
        used: set[tuple[int, ...]] = set()
        for _q in range(self.config.n_qubits):
            for _attempt in range(1000):
                weight = self.config.column_weight if self.rng.random() < 0.8 else 2
                positions = tuple(sorted(self.rng.sample(range(self.config.m_checks), weight)))
                column = tuple(1 if i in positions else 0 for i in range(self.config.m_checks))
                if column not in used and any(column):
                    used.add(column)
                    columns.append(column)
                    break
            else:
                fallback = self.rng.sample(range(self.config.m_checks), self.config.column_weight)
                columns.append(tuple(1 if i in fallback else 0 for i in range(self.config.m_checks)))
        return np.array(
            [[columns[j][i] for j in range(self.config.n_qubits)] for i in range(self.config.m_checks)],
            dtype=np.uint8,
        )

    def syndrome(self, error: np.ndarray) -> np.ndarray:
        return (self.h @ error % 2).astype(np.uint8)

    @staticmethod
    def array_to_qubits(error: np.ndarray) -> str:
        return " ".join(str(i) for i, value in enumerate(error) if int(value))

    @staticmethod
    def residual(candidate: np.ndarray, true_error: np.ndarray) -> set[int]:
        return set(np.nonzero(candidate.astype(np.uint8) ^ true_error.astype(np.uint8))[0])

    def logical_failure_proxy(self, residual: set[int]) -> bool:
        return bool(residual & self.logical_sensitive_qubits) and len(residual) <= 5

    @staticmethod
    def log_probability(candidate: np.ndarray, probabilities: list[float]) -> float:
        total = 0.0
        for i, value in enumerate(candidate):
            p_error = max(1e-9, min(1 - 1e-9, probabilities[i]))
            total += math.log(p_error if int(value) else 1 - p_error)
        return total

    def sample_true_error(self) -> np.ndarray:
        weight = 1 if self.rng.random() < 0.35 else (2 if self.rng.random() < 0.75 else 3)
        qubits = self.rng.sample(range(self.config.n_qubits), weight)
        error = np.zeros(self.config.n_qubits, dtype=np.uint8)
        error[qubits] = 1
        return error

    def sample_channel_probabilities(self, true_error: np.ndarray) -> list[float]:
        probabilities: list[float] = []
        true_qubits = set(np.nonzero(true_error)[0])
        for q in range(self.config.n_qubits):
            value = self.rng.uniform(0.10, 0.40) if q in true_qubits else self.rng.uniform(0.02, 0.24)
            if q in self.logical_sensitive_qubits and self.rng.random() < 0.12:
                value = self.rng.uniform(0.18, 0.40)
            probabilities.append(value)
        return probabilities

    def decoder_candidates(self, syndrome: np.ndarray, probabilities: list[float]) -> list[tuple[str, np.ndarray, float]]:
        decoder_builders = {
            "bp": lambda: BpDecoder(
                self.h,
                error_channel=probabilities,
                max_iter=10,
                bp_method="minimum_sum",
                input_vector_type="syndrome",
            ),
            "bposd": lambda: BpOsdDecoder(
                self.h,
                error_channel=probabilities,
                max_iter=10,
                bp_method="minimum_sum",
                osd_method="OSD_CS",
                osd_order=2,
                input_vector_type="syndrome",
            ),
            "bplsd": lambda: BpLsdDecoder(
                self.h,
                error_channel=probabilities,
                max_iter=10,
                bp_method="minimum_sum",
                lsd_method="LSD_CS",
                lsd_order=2,
                input_vector_type="syndrome",
            ),
        }
        candidates: list[tuple[str, np.ndarray, float]] = []
        for method, builder in decoder_builders.items():
            try:
                correction = builder().decode(syndrome).astype(np.uint8)
            except Exception:
                continue
            candidates.append((method, correction, self.log_probability(correction, probabilities)))
        return candidates

    def compatible_low_weight_candidates(self, syndrome: np.ndarray, probabilities: list[float]) -> list[tuple[str, np.ndarray, float]]:
        candidates: list[tuple[str, np.ndarray, float]] = []
        for weight in range(1, self.config.max_extra_candidate_weight + 1):
            count = 0
            for qubits in combinations(range(self.config.n_qubits), weight):
                correction = np.zeros(self.config.n_qubits, dtype=np.uint8)
                correction[list(qubits)] = 1
                if np.array_equal(self.syndrome(correction), syndrome):
                    candidates.append(("low_weight_alt", correction, self.log_probability(correction, probabilities)))
                    count += 1
                if count >= 4:
                    break
        return candidates

    def build_rows(
        self,
        candidates: list[tuple[str, np.ndarray, float]],
        syndrome: np.ndarray,
        true_error: np.ndarray,
    ) -> list[dict[str, Any]]:
        unique: dict[tuple[int, ...], tuple[str, np.ndarray, float]] = {}
        for method, correction, log_prob in candidates:
            key = tuple(correction.tolist())
            if key not in unique or self.method_reliability[method] > self.method_reliability[unique[key][0]]:
                unique[key] = (method, correction, log_prob)

        candidate_items = list(unique.values())
        if len(candidate_items) < 2:
            return []

        logs = [item[2] for item in candidate_items]
        low, high = min(logs), max(logs)

        rows: list[dict[str, Any]] = []
        for index, (method, correction, log_prob) in enumerate(candidate_items):
            nonzero = set(np.nonzero(correction)[0])
            overlap = sum(q in self.logical_sensitive_qubits for q in nonzero)
            candidate_weight = int(correction.sum())
            valid_syndrome = np.array_equal(self.syndrome(correction), syndrome)
            residual = self.residual(correction, true_error)
            decoder_confidence = 1000 if high == low else int(round(500 + 500 * (log_prob - low) / (high - low)))
            rows.append(
                {
                    "candidate_index": index,
                    "decoder_method": method,
                    "correction_qubits": self.array_to_qubits(correction),
                    "candidate_weight": candidate_weight,
                    "syndrome_support": 1000 if valid_syndrome else 0,
                    "check_consistency": 1000 if valid_syndrome else 0,
                    "decoder_agreement": 940 if method in {"bposd", "bplsd"} else (760 if method == "bp" else 680),
                    "logical_preservation": max(0, 950 - 140 * overlap - 10 * max(0, candidate_weight - 1)),
                    "distance_safety": max(0, 930 - 120 * overlap - 10 * candidate_weight),
                    "decoder_confidence": decoder_confidence,
                    "method_reliability": self.method_reliability[method],
                    "propagation_safety": max(0, 930 - 30 * candidate_weight - 35 * overlap),
                    "syndrome_risk": 40 + 10 * candidate_weight,
                    "logical_risk": min(1000, 25 + 135 * overlap + 12 * candidate_weight),
                    "exact_correction": bool(np.array_equal(correction, true_error)),
                    "logical_failure_proxy": self.logical_failure_proxy(residual),
                }
            )
        return rows

    def run(self, compiled_process_data: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        rows_out: list[dict[str, Any]] = []
        attempts = 0
        scenario_id = 0
        max_attempts = self.config.samples_per_seed * self.config.max_attempts_multiplier

        while scenario_id < self.config.samples_per_seed and attempts < max_attempts:
            attempts += 1
            true_error = self.sample_true_error()
            syndrome = self.syndrome(true_error)
            probabilities = self.sample_channel_probabilities(true_error)
            candidates = self.decoder_candidates(syndrome, probabilities)
            candidates.extend(self.compatible_low_weight_candidates(syndrome, probabilities))
            rows = self.build_rows(candidates, syndrome, true_error)
            if len(rows) < 2 or not any(row["decoder_method"] == "bp" for row in rows):
                continue

            frame = pd.DataFrame(rows)
            bp_rows = frame[frame["decoder_method"] == "bp"]
            if bp_rows.empty:
                continue
            baseline = bp_rows.sort_values(["decoder_confidence", "candidate_weight"], ascending=[False, True]).iloc[0]

            # This benchmark focuses on BP-failure/ambiguity cases.
            if bool(baseline["exact_correction"]):
                continue

            payload = dict(compiled_process_data)
            payload["rows"] = rows
            result = compile_process_data_spec(payload)
            selected = result["selected_rows"][0]

            rows_out.append(
                {
                    "seed": self.seed,
                    "scenario_id": scenario_id,
                    "true_error": self.array_to_qubits(true_error),
                    "baseline_method": baseline["decoder_method"],
                    "baseline_qubits": baseline["correction_qubits"],
                    "baseline_exact": bool(baseline["exact_correction"]),
                    "baseline_failure": bool(baseline["logical_failure_proxy"]),
                    "baseline_logical_risk": int(baseline["logical_risk"]),
                    "qdsv_method": selected["decoder_method"],
                    "qdsv_qubits": selected["correction_qubits"],
                    "qdsv_exact": bool(selected["exact_correction"]),
                    "qdsv_failure": bool(selected["logical_failure_proxy"]),
                    "qdsv_logical_risk": int(selected["logical_risk"]),
                    "risk_delta": int(baseline["logical_risk"]) - int(selected["logical_risk"]),
                    "exact_delta": int(bool(selected["exact_correction"])) - int(bool(baseline["exact_correction"])),
                    "failure_delta": int(bool(baseline["logical_failure_proxy"])) - int(bool(selected["logical_failure_proxy"])),
                }
            )
            scenario_id += 1

        return rows_out, attempts


def _rate(values: pd.Series) -> float:
    return float(values.mean()) if len(values) else 0.0


def _seed_metrics(seed: int, attempts: int, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "seed": seed,
        "samples": int(len(frame)),
        "attempts": int(attempts),
        "bp_exact_rate": _rate(frame["baseline_exact"]),
        "qdsv_exact_rate": _rate(frame["qdsv_exact"]),
        "bp_failure_proxy_rate": _rate(frame["baseline_failure"]),
        "qdsv_failure_proxy_rate": _rate(frame["qdsv_failure"]),
        "bp_avg_logical_risk": float(frame["baseline_logical_risk"].mean()),
        "qdsv_avg_logical_risk": float(frame["qdsv_logical_risk"].mean()),
        "avg_risk_delta": float(frame["risk_delta"].mean()),
        "improved_risk_count": int((frame["risk_delta"] > 0).sum()),
        "worse_risk_count": int((frame["risk_delta"] < 0).sum()),
        "avg_exact_delta": float(frame["exact_delta"].mean()),
        "avg_failure_delta": float(frame["failure_delta"].mean()),
    }


def _aggregate(seed_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "bp_exact_rate",
        "qdsv_exact_rate",
        "bp_failure_proxy_rate",
        "qdsv_failure_proxy_rate",
        "bp_avg_logical_risk",
        "qdsv_avg_logical_risk",
        "avg_risk_delta",
        "avg_exact_delta",
        "avg_failure_delta",
    ]
    out: dict[str, Any] = {
        "seed_count": len(seed_metrics),
        "total_samples": int(sum(item["samples"] for item in seed_metrics)),
        "total_improved_risk_count": int(sum(item["improved_risk_count"] for item in seed_metrics)),
        "total_worse_risk_count": int(sum(item["worse_risk_count"] for item in seed_metrics)),
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
        benchmark = RealLdpcEnsembleBenchmark(config, seed)
        rows, attempts = benchmark.run(compiled)
        frame = pd.DataFrame(rows)
        if frame.empty:
            continue
        metrics = _seed_metrics(seed, attempts, frame)
        all_rows.extend(rows)
        per_seed.append(metrics)
        print(f"seed={seed} samples={metrics['samples']} qdsv_exact={metrics['qdsv_exact_rate']:.3f} avg_risk_delta={metrics['avg_risk_delta']:.2f}")

    return {
        "config": asdict(config),
        "qintent_source": QINTENT_SOURCE,
        "internal_formula_exposed": False,
        "per_seed_metrics": per_seed,
        "aggregate_metrics": _aggregate(per_seed),
        "summary_rows": all_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=410001)
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
    evidence_path = output_dir / "qdsv_qldpc_real_ldpc_ensemble_recovery_evidence.json"
    summary_path = output_dir / "qdsv_qldpc_real_ldpc_ensemble_recovery_summary.csv"
    metrics_path = output_dir / "qdsv_qldpc_real_ldpc_ensemble_recovery_metrics.csv"

    pd.DataFrame(result["summary_rows"]).to_csv(summary_path, index=False)
    pd.DataFrame(result["per_seed_metrics"]).to_csv(metrics_path, index=False)
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

    print("\nAggregate metrics:")
    print(json.dumps(result["aggregate_metrics"], indent=2))
    print("\nSaved:")
    print(evidence_path)
    print(summary_path)
    print(metrics_path)


if __name__ == "__main__":
    main()
