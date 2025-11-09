"""Utilities for publishing status snapshots to external channels."""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Iterable

import requests

logger = logging.getLogger(__name__)


def _format_timeframe_summary(timeframes: Dict[str, Dict]) -> Iterable[str]:
    for timeframe, meta in sorted(timeframes.items()):
        rows = meta.get("rows")
        start = meta.get("start")
        end = meta.get("end")
        yield f"{timeframe}: {rows} rows ({start} → {end})"


def format_status_message(status: Dict) -> str:
    lines = ["TopStepAi Data Inventory"]
    data_inventory = status.get("data_inventory") or {}
    timeframes = data_inventory.get("timeframes") or {}
    shortfalls = (data_inventory.get("shortfalls") or {}).get("timeframes", {})

    for line in _format_timeframe_summary(timeframes):
        lines.append(f" • {line}")

    if shortfalls:
        lines.append("Shortfalls:")
        for timeframe, meta in sorted(shortfalls.items()):
            actual = meta.get("actual")
            target = meta.get("target")
            if target and actual is not None and actual < target:
                lines.append(f"    - {timeframe}: {actual}/{target}")

    return "\n".join(lines)


def post_to_slack(webhook_url: str, message: str) -> None:
    payload = {"text": message}
    response = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
    if response.status_code >= 400:
        raise RuntimeError(f"Slack webhook failed ({response.status_code}): {response.text}")


def publish_status_report(status: Dict, monitoring_config: Dict) -> None:
    message = format_status_message(status)
    logger.info("Status summary:\n%s", message)

    slack_webhook = monitoring_config.get("alerts_slack_webhook")
    if slack_webhook:
        webhook_value = os.environ.get(slack_webhook.strip("${}"), slack_webhook)
        if webhook_value.startswith("http"):
            try:
                post_to_slack(webhook_value, message)
                logger.info("Posted status summary to Slack")
            except Exception as exc:  # pragma: no cover - network failure only exercised in prod
                logger.warning("Failed to post status summary to Slack: %s", exc)
        else:
            logger.debug("Slack webhook placeholder detected; skipping post")