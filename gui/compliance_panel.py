"""Streamlit components for the Combine compliance panel."""

from __future__ import annotations

from typing import Dict, Any

import streamlit as st


def _ratio(numerator: float | int | None, denominator: float | int | None) -> float:
    if not numerator or not denominator:
        return 0.0
    if denominator == 0:
        return 0.0
    return max(0.0, min(1.0, float(numerator) / float(denominator)))


def render(status: Dict[str, Any]) -> None:
    """Render detailed risk and rule compliance information."""

    st.title("Compliance Panel")

    if not status:
        st.error("Status data not available. Run `python src/main.py` to refresh.")
        return

    st.subheader("Risk Guardrails")
    cols = st.columns(2)
    daily_used = status.get("daily_loss_used")
    daily_cap = status.get("daily_loss_cap")
    trailing_dd = status.get("trailing_dd")
    kill_switch = status.get("killswitch_threshold")

    with cols[0]:
        st.metric(
            "Daily Loss Usage",
            f"{daily_used or 0:.0f}/{daily_cap or 0:.0f}",
            help="Tracks progress towards the daily loss cap",
        )
        st.progress(_ratio(daily_used, daily_cap))

    with cols[1]:
        st.metric(
            "Trailing Drawdown",
            f"{trailing_dd or 0:.0f}/{kill_switch or 0:.0f}",
            help="Trailing drawdown relative to kill-switch threshold",
        )
        st.progress(_ratio(trailing_dd, kill_switch))

    st.subheader("Rule Status")
    rules_status = status.get("rules_status", {}) or {}
    if not rules_status:
        st.info("No rule status entries recorded yet.")
    else:
        for rule, state in sorted(rules_status.items()):
            badge = "✅" if state == "pass" else "⚠️"
            st.write(f"{badge} **{rule.capitalize()}** — {state}")

    breaches = status.get("recent_breaches", []) or []
    st.subheader("Recent Breaches")
    if breaches:
        for breach in breaches:
            st.write("- ", breach)
    else:
        st.success("No recent breaches recorded.")

    auto_actions = status.get("auto_actions", []) or []
    st.subheader("Automated Actions")
    if auto_actions:
        for action in auto_actions:
            st.write("- ", action)
    else:
        st.caption("No automated actions triggered.")