from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .client import QIntentClient
from .exceptions import QIntentError


def _read_source(value: str) -> str:
    path = Path(value)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")
    return value


def _load_rows(path: str | None) -> list[dict[str, Any]] | None:
    if not path:
        return None
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON rows file must contain a list of objects")
        return [dict(item) for item in data]
    return QIntentClient.read_csv(file_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qintent",
        description="Run QIntent source through a QDSV API.",
    )
    parser.add_argument(
        "command",
        choices=[
            "spec", "capabilities", "examples", "validate", "compile", "explain", "run",
            "submit-hardware", "hardware-job", "cancel-hardware",
        ],
    )
    parser.add_argument("source", nargs="?", help="QIntent source string or path to a .qi file")
    parser.add_argument("--api-url", default=None, help="Base API URL, for example https://api.qdsv.cloud/api")
    parser.add_argument("--api-key", default=None, help="Optional API bearer token")
    parser.add_argument("--license-key", default=None, help="Optional QDSV/Qruba license key")
    parser.add_argument("--rows", default=None, help="CSV or JSON file with rows for find_rows/field queries")
    parser.add_argument("--backend", default="quest", help="Execution backend. Public preview default: quest")
    parser.add_argument("--backend-name", default="least_busy", help="IBM backend name for submit-hardware")
    parser.add_argument("--backend-mode", default=None)
    parser.add_argument("--shots", type=int, default=256)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    client = QIntentClient(api_url=args.api_url, api_key=args.api_key, license_key=args.license_key)

    try:
        if args.command == "spec":
            result = client.spec()
        elif args.command == "capabilities":
            result = client.capabilities()
        elif args.command == "examples":
            result = {"examples": client.examples()}
        elif args.command == "hardware-job":
            if not args.source:
                parser.error("hardware-job requires a job id")
            result = client.hardware_job(args.source)
        elif args.command == "cancel-hardware":
            if not args.source:
                parser.error("cancel-hardware requires a job id")
            result = client.cancel_hardware_job(args.source)
        elif args.command == "submit-hardware":
            if not args.source:
                parser.error("submit-hardware requires source")
            result = client.submit_hardware(
                _read_source(args.source),
                rows=_load_rows(args.rows),
                backend_name=args.backend_name,
                shots=args.shots,
            )
        else:
            if not args.source:
                parser.error(f"{args.command} requires source")
            source = _read_source(args.source)
            rows = _load_rows(args.rows)
            call = getattr(client, "run" if args.command == "run" else args.command)
            result = call(
                source,
                rows=rows,
                backend=args.backend,
                backend_mode=args.backend_mode,
                shots=args.shots,
            )
    except (QIntentError, OSError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
