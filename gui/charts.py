"""Streamlit components for interactive charting of gold timeframes."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


@st.cache_data(show_spinner=False)
def _load_candles(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, parse_dates=["timestamp"])
    except Exception as exc:  # pragma: no cover - defensive for malformed data files
        st.warning(f"Failed to load {path.name}: {exc}")
        return None


def _timeframe_options(status: Dict[str, Any]) -> list[str]:
    inventory = (status or {}).get("data_inventory") or {}
    timeframes = list((inventory.get("timeframes") or {}).keys())
    if timeframes:
        return sorted(timeframes)
    return ["1min", "5min", "15min", "1hour", "1day"]


def _dataset_modes() -> Dict[str, str]:
    return {
        "Front Contract": "{tf}.csv",
        "Stitched Chain": "{tf}_chain.csv",
    }


def _render_candlestick(df: pd.DataFrame, title: str) -> None:
    figure = go.Figure(
        data=[
            go.Candlestick(
                x=df["timestamp"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Price",
            )
        ]
    )
    figure.update_layout(xaxis_title="Timestamp", yaxis_title="Price", title=title)
    st.plotly_chart(figure, use_container_width=True)


def render(data_dir: Path, status: Dict[str, Any]) -> None:
    """Render interactive charts for available gold datasets."""

    st.title("Trading Charts")

    timeframes = _timeframe_options(status)
    default_timeframe = "1hour" if "1hour" in timeframes else timeframes[0]
    timeframe = st.selectbox("Timeframe", options=timeframes, index=timeframes.index(default_timeframe))
    dataset_labels = list(_dataset_modes().keys())
    dataset_label = st.radio("Dataset", options=dataset_labels, horizontal=True)

    filename_template = _dataset_modes()[dataset_label]
    csv_name = f"gold_candles_{filename_template.format(tf=timeframe)}"
    csv_path = data_dir / csv_name

    data = _load_candles(csv_path)
    if data is None or data.empty:
        st.warning(f"No candles available for {timeframe} ({dataset_label.lower()}).")
        return

    data = data.sort_values("timestamp")
    max_rows = min(len(data), 5000)
    if max_rows < 50:
        st.warning("Not enough rows to display a chart.")
        return

    min_rows = min(200, max_rows)
    default_rows = min(1000, max_rows)
    if default_rows < min_rows:
        default_rows = max_rows

    lookback = st.slider(
        "Rows to display",
        min_value=min_rows,
        max_value=max_rows,
        value=default_rows,
        step=50,
    )
    recent = data.tail(lookback)

    latest_row = recent.iloc[-1]
    st.metric(
        "Latest Close",
        f"{latest_row['close']:.2f}",
        delta=f"{latest_row['close'] - recent.iloc[0]['close']:.2f}",
    )

    _render_candlestick(recent, f"{timeframe} {dataset_label}")

    with st.expander("Summary Statistics"):
        st.dataframe(
            recent[["open", "high", "low", "close", "volume"]]
            .describe()
            .transpose()
            .round(2)
        )

    with st.expander("Raw Data Preview"):
        st.dataframe(recent.tail(200), use_container_width=True)