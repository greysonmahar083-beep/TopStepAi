"""
Compliance Panel Outline

Detailed view of Combine rules, risk, and breaches.
"""

import streamlit as st
import json

with open('config/status.json', 'r') as f:
    status = json.load(f)

st.title("Compliance Panel")

st.subheader("Risk Gauges")
st.write(f"Daily Loss Used: {status['daily_loss_used']}/{status['daily_loss_cap']}")
st.progress(status['daily_loss_used'] / status['daily_loss_cap'])

st.write(f"Trailing DD: {status['trailing_dd']}/{status['killswitch_threshold']}")
st.progress(status['trailing_dd'] / status['killswitch_threshold'])

st.subheader("Rules Status")
for rule, stat in status['rules_status'].items():
    color = "green" if stat == "pass" else "red"
    st.markdown(f"**{rule}**: <span style='color:{color}'>{stat}</span>", unsafe_allow_html=True)

st.subheader("Recent Breaches")
for breach in status['recent_breaches']:
    st.write(breach)