"""Entry point for the TopStepAi Streamlit GUI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import yaml

from gui import compliance_panel, dashboard

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = REPO_ROOT / "config" / "status.json"
CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"


@st.cache_data(show_spinner=False)
def _load_status() -> Dict[str, Any]:
    if not STATUS_PATH.exists():
        return {}
    try:
        with STATUS_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        st.error("`config/status.json` is not valid JSON.")
        return {}


@st.cache_data(show_spinner=False)
def _load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        st.error(f"Failed to parse `config/config.yaml`: {exc}")
        return {}


def _sidebar(status: Dict[str, Any]) -> str:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Views", ["Overview", "Compliance"], index=0)

    inventory = (status or {}).get("data_inventory") or {}
    as_of = inventory.get("as_of")
    if as_of:
        st.sidebar.caption(f"Status as of {as_of}")

    st.sidebar.write(
        "Run `python src/main.py` to refresh data and update `config/status.json` before launching the dashboard."
    )

    return page


def main() -> None:
    st.set_page_config(page_title="TopStepAi", layout="wide")

    status = _load_status()
    config = _load_config()
    page = _sidebar(status)

    if page == "Overview":
        dashboard.render(status, config)
    elif page == "Compliance":
        compliance_panel.render(status)


if __name__ == "__main__":  # pragma: no cover - Streamlit entry point
    main()
