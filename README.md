# TopStepAi

AI-first algorithmic futures trading focused on passing the Topstep Combine and operating a Topstep-funded account. The system is designed to be fully AI-driven while producing clear, visual outputs for humans (dashboards, compliance panels, annotated charts, and daily reports).

## Visual overview

## Project Structure

```
TopStepAi/
├── src/                    # Core source code
│   └── main.py            # Entry point
├── tests/                 # Unit and integration tests
├── config/                # Configuration files
│   ├── config.yaml       # Main config with env vars
│   └── status.json       # Compliance panel status
├── data/                  # Historical and live data
├── models/                # Trained ML models
├── strategies/            # Trading strategies
├── execution/             # TopstepX API integration
├── monitoring/            # Dashboards and alerts
├── gui/                   # GUI components (Streamlit)
│   ├── dashboard.py      # Main dashboard
│   └── compliance_panel.py # Compliance details
├── backtesting/           # Backtesting engine
├── docs/                  # Documentation
│   └── topstepx-gateway-api.md
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Getting Started

1. Clone the repo and open in dev container (Ubuntu 24.04).
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your TopstepX credentials and risk limits.
4. Run the entry point: `python src/main.py` (will authenticate and show status).
5. For development, use `pytest` in tests/ and `streamlit run gui/app.py` for the dashboard. (Charting views are intentionally left blank so you can implement your own.)

## Objective (Topstep Combine)

- Starting balance: $50,000
- Profit target: +$3,000
- Max loss limit (MLL): -$2,000

The project ships with risk guardrails and a compliance panel so the AI can trade autonomously without violating Combine rules, while a human can see status at a glance.

## Risk budgets and guardrails (defaults)

- Daily loss cap: $400 (20% of MLL)
- Trailing drawdown kill-switch: $1,600 (80% of MLL) from high-water mark
- Session loss cap: $200 (50% of daily cap)
- Open risk cap per account: ≤ 30% of daily cap
- Per-trade risk: 0.10–0.30% of equity, position size constrained by stop distance and tick value
- Hard rules: trading session calendars, news filters, scaling limits, and auto-flat at session end

Pass/Fail checks (automated):

- Profit target achieved (equity − start ≥ $3,000)
- Drawdown within MLL at all times (both daily and trailing)
- No rule violations (hours, scaling, news filter, order types)

## Compliance panel (human-visible)

The dashboard includes a combine “compliance panel” with live status indicators:

- Equity vs. target (+$3,000) with progress bar and ETA at current expectancy
- Remaining MLL and daily cap usage (gauges with color zones)
- Trailing drawdown vs. kill-switch threshold
- Exposure by symbol and total open risk vs. cap
- Trade limits (count, consecutive losses) and session timer
- Rule status checklist (green/amber/red): risk, hours, news filter, scaling, connectivity
- Recent breaches and automatic actions (auto-flat, disable, cooldown) with timestamps

## Broker integration (TopstepX Gateway API)

TopstepX provides REST + SignalR for authentication, accounts, orders, positions, and real-time market data. This project uses it autonomously and surfaces human-friendly visuals.

Connections:

- REST: https://api.topstepx.com
- User Hub (SignalR): https://rtc.topstepx.com/hubs/user
- Market Hub (SignalR): https://rtc.topstepx.com/hubs/market

Auth flow (session token):

1. Authenticate via `/api/Auth/loginKey` with username + API key → JWT token
2. REST calls include `Authorization: Bearer <token>`
3. SignalR connections append `?access_token=<token>`
4. Revalidate with `/api/Auth/validate` (tokens are typically ~24h)

Core endpoints used:

- Accounts: `/api/Account/search`
- Markets: `/api/Contract/search`, `/api/Contract/get`
- Orders: `/api/Order/place`, `/api/Order/modify`, `/api/Order/cancel`, `/api/Order/search`
- Positions/Trades: `/api/Position/search`, `/api/Position/get`, `/api/Trade/search`

For a full text-only reference, see `docs/topstepx-gateway-api.md`.

## Configuration

Configure via environment variables. Start from the template and never commit real secrets.

1. Copy `.env.example` to `.env` and fill in values
2. Store secrets securely (local vault, secret manager). Do not use version control.

Key variables:

- TopstepX endpoints, username, API key, and session TTL
- Combine targets and risk limits (MLL, daily cap, per-trade risk bounds)
- Alert channels (Slack webhook, email)

## AI control loop

1. Ingest/refresh historical and live data
2. Generate/curate features and regimes
3. Propose strategies and hyperparameters under risk constraints
4. Backtest with realistic slippage/fees; produce metrics and reports
5. Paper trade with live market data; monitor compliance and stability
6. Promote/demote to live based on guardrails and performance persistence
7. Monitor, alert, and auto-recover (kill-switch, cooldown, restart)

## Roadmap

- Data loaders for CME futures with rolls and session calendars
- Event-driven backtester + vectorized fast path for research
- Execution adapters for TopstepX (paper/live) with resilience and replay
- Compliance panel and annotated charting in the dashboard
- Experiment tracking and model registry; reproducible backtests

## Legal & risk

This repository is for research and educational purposes. Trading futures involves substantial risk of loss and is not suitable for every investor. Follow all Topstep program rules and broker terms. Nothing herein is financial advice.
