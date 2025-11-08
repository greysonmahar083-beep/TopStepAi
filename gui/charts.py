"""
Charts Outline

Annotated charts for trades, entries/exits, regimes.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.title("Trading Charts")

# Placeholder data
data = pd.DataFrame({
    'time': pd.date_range('2023-01-01', periods=100, freq='H'),
    'price': [100 + i*0.1 for i in range(100)]
})

fig = go.Figure()
fig.add_trace(go.Scatter(x=data['time'], y=data['price'], mode='lines', name='Price'))

# Add annotations (placeholder)
fig.add_annotation(x=data['time'][50], y=data['price'][50], text="Entry", showarrow=True)

st.plotly_chart(fig)