
+
"""Validate data inventory captured in status.json against targets.

This module can be scheduled (e.g., nightly) to ensure historical pulls
continue to meet expectations and to detect new contract additions.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

import yaml


DEFAULT_STATUS_PATH = Path("config/status.json")
DEFAULT_CONFIG_PATH = Path("config/config.yaml")
HISTORY_PATH = Path("monitoring/data_inventory_history.json")


def load_status(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"status file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _as_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_inventory(status: Dict, stitch_config: Dict, baseline: Dict | None = None) -> Iterable[str]:
    issues = []

    data_inventory = status.get("data_inventory") or {}
    timeframe_data = data_inventory.get("timeframes") or {}
    contract_data = data_inventory.get("contracts") or {}

    target_bars = stitch_config.get("target_bars") or {}
    warn_threshold = _as_float(stitch_config.get("warn_threshold"), 0.9)

    for timeframe, target in target_bars.items():
        target_int = int(target)
        actual = int(timeframe_data.get(timeframe, {}).get("rows", 0))
        threshold = int(target_int * warn_threshold)
        if actual < threshold:
            issues.append(
                f"Timeframe {timeframe}: {actual} bars below threshold {threshold} (target {target_int})"
            )

        if baseline:
            baseline_rows = int(baseline.get("timeframes", {}).get(timeframe, 0))
            if baseline_rows and actual < baseline_rows:
                issues.append(
                    f"Timeframe {timeframe}: bar count {actual} dropped below previous {baseline_rows}"
                )

    # Detect new contracts vs baseline
    current_contracts = {
        (tf, cid)
        for tf, mapping in contract_data.items()
        for cid in mapping.keys()
    }
    if baseline:
        baseline_contracts = {tuple(entry) for entry in baseline.get("contracts", [])}
        new_contracts = current_contracts - baseline_contracts
        retired_contracts = baseline_contracts - current_contracts
        if new_contracts:
            issues.append(
                "New contracts detected: " + ", ".join(f"{tf}:{cid}" for tf, cid in sorted(new_contracts))
            )
        if retired_contracts:
            issues.append(
                "Contracts missing: " + ", ".join(f"{tf}:{cid}" for tf, cid in sorted(retired_contracts))
            )

    return issues


def update_history(status: Dict) -> None:
    data_inventory = status.get("data_inventory") or {}
    timeframe_data = data_inventory.get("timeframes") or {}
    contract_data = data_inventory.get("contracts") or {}

    history_snapshot = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "timeframes": {tf: meta.get("rows", 0) for tf, meta in timeframe_data.items()},
        "contracts": [
            (tf, cid)
            for tf, mapping in sorted(contract_data.items())
            for cid in sorted(mapping.keys())
        ],
    }

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(history_snapshot, handle, indent=2)


def load_history() -> Dict | None:
    if not HISTORY_PATH.exists():
        return None
    with HISTORY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate data inventory health")
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS_PATH, help="Path to status.json")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config.yaml")
    args = parser.parse_args()

    status = load_status(args.status)
    config = load_config(args.config)
    stitch_config = (config.get("data") or {}).get("stitch", {})

    baseline = load_history()
    issues = list(validate_inventory(status, stitch_config, baseline))

    if issues:
        print("Data inventory validation failed:")
        for issue in issues:
            print(f" - {issue}")
        result = 1
    else:
        print("Data inventory validation passed")
        result = 0

    update_history(status)
    return result


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
