"""
TopStepAi Dashboard Outline

Main dashboard for human visuals: PnL, compliance, charts.
Uses Streamlit for web interface.
"""

import streamlit as st
import json
import plotly.graph_objects as go
from datetime import datetime

# Load status
with open('config/status.json', 'r') as f:
    status = json.load(f)

st.title("TopStepAi Dashboard")

# Equity and Target
st.header("Equity & Profit Target")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Equity", f"${status['equity']}")
with col2:
    st.metric("Profit Target", f"${status['profit_target']}")
with col3:
    progress = min(status['equity'] / (50000 + status['profit_target']), 1.0)
    st.progress(progress)

# Compliance Panel
st.header("Compliance Panel")
st.json(status['rules_status'])

# Charts Placeholder
st.header("PnL Chart")
fig = go.Figure()
fig.add_trace(go.Scatter(x=[datetime.now()], y=[status['equity']], mode='lines'))
st.plotly_chart(fig)

# Run: streamlit run gui/dashboard.py