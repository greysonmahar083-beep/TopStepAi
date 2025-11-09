"""Streamlit components for the TopStepAi overview dashboard."""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd
import streamlit as st

DEFAULT_START_BALANCE = 50_000


def _safe_get(mapping: Dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if not mapping:
        return default
    return mapping.get(key, default)


def _format_currency(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"${value:,.2f}"


def _render_equity_section(status: Dict[str, Any], config: Dict[str, Any]) -> None:
    combine_config = _safe_get(config, "combine", {}) or {}
    start_balance = combine_config.get("start_balance", DEFAULT_START_BALANCE)
    target = combine_config.get("profit_target", _safe_get(status, "profit_target", 0))
    equity = _safe_get(status, "equity")
    open_risk = _safe_get(status, "open_risk", 0)

    st.subheader("Equity Progress")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Equity", _format_currency(equity))
    with col2:
        st.metric("Profit Target", _format_currency(target))
    with col3:
        st.metric("Open Risk", _format_currency(open_risk))

    if equity is not None and target:
        progress = max(0.0, min(1.0, (equity - start_balance) / target))
        st.progress(progress, text=f"{progress * 100:.1f}% towards target")
    else:
        st.info("Equity or profit target not available in status.json")

    exposures = _safe_get(status, "exposure_by_symbol", {}) or {}
    if exposures:
        exposure_df = (
            pd.DataFrame(
                {"contract": list(exposures.keys()), "exposure": list(exposures.values())}
            )
            .set_index("contract")
            .sort_values("exposure", ascending=False)
        )
        st.caption("Open exposure by contract")
        st.bar_chart(exposure_df)
    else:
        st.caption("No open exposure recorded.")


def _render_data_inventory(status: Dict[str, Any]) -> None:
    inventory = _safe_get(status, "data_inventory", {}) or {}
    timeframes = inventory.get("timeframes", {})
    shortfalls = (inventory.get("shortfalls") or {}).get("timeframes", {})

    st.subheader("Data Inventory")
    if timeframes:
        inventory_df = (
            pd.DataFrame.from_dict(timeframes, orient="index")
            .rename(columns={"rows": "Rows", "start": "Start", "end": "End"})
            .sort_index()
        )
        st.dataframe(inventory_df, use_container_width=True)
    else:
        st.info("No timeframe data captured yet. Run the data refresh pipeline.")

    if shortfalls:
        shortfall_rows = []
        for timeframe, meta in sorted(shortfalls.items()):
            actual = meta.get("actual")
            target = meta.get("target")
            if target and actual is not None and actual < target:
                shortfall_rows.append(
                    {
                        "timeframe": timeframe,
                        "actual": actual,
                        "target": target,
                        "coverage": f"{actual}/{target}",
                    }
                )
        if shortfall_rows:
            st.warning("Shortfalls detected in historical coverage")
            st.table(pd.DataFrame(shortfall_rows).set_index("timeframe"))
        else:
            st.success("All configured timeframes meet historical coverage targets.")

    cached_contracts = (inventory.get("shortfalls") or {}).get("emptyContractCache")
    if cached_contracts:
        with st.expander("Contracts with no data returned"):
            st.write(", ".join(sorted(cached_contracts)))


def _render_status_snapshot(status: Dict[str, Any]) -> None:
    st.subheader("Session Status")
    status_cols = st.columns(4)
    status_cols[0].metric("Daily Loss Used", _format_currency(status.get("daily_loss_used")))
    status_cols[1].metric("Daily Loss Cap", _format_currency(status.get("daily_loss_cap")))
    status_cols[2].metric("Trailing DD", _format_currency(status.get("trailing_dd")))
    status_cols[3].metric("Kill Switch", _format_currency(status.get("killswitch_threshold")))

    rules_status = _safe_get(status, "rules_status", {}) or {}
    if rules_status:
        with st.expander("Rule Compliance Checks", expanded=True):
            for rule, state in sorted(rules_status.items()):
                badge = "✅" if state == "pass" else "⚠️"
                st.write(f"{badge} **{rule.capitalize()}** — {state}")

    breaches = _safe_get(status, "recent_breaches", []) or []
    if breaches:
        with st.expander("Recent Breaches"):
            for breach in breaches:
                st.write("- ", breach)

    auto_actions = _safe_get(status, "auto_actions", []) or []
    if auto_actions:
        with st.expander("Automated Actions"):
            for action in auto_actions:
                st.write("- ", action)


def render(status: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Render the main dashboard view."""

    st.title("TopStepAi Overview")

    if not status:
        st.error("`config/status.json` could not be loaded. Run `python src/main.py` first.")
        return

    _render_equity_section(status, config)
    _render_status_snapshot(status)
    _render_data_inventory(status)

    combine_config = _safe_get(config, "combine", {})
    if combine_config:
        with st.expander("Combine Configuration"):
            st.json(combine_config)