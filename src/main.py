#!/usr/bin/env python3
"""
TopStepAi Main Entry Point

Loads configuration, authenticates with TopstepX, and initializes the trading system.
"""

import os
import sys
import json

import yaml
from dotenv import load_dotenv

# Ensure project root (one level up from src/) is importable when running as a script
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from execution.topstepx_client import TopstepXClient
from data.gold_data import GoldDataPuller

# Load environment variables
load_dotenv()

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

def main():
    print("TopStepAi Starting...")

    # Initialize TopstepX client
    client = TopstepXClient()
    if not client.authenticate():
        sys.exit(1)

    print("Authenticated with TopstepX.")

    # Get accounts
    accounts_data = client.get_accounts()
    if accounts_data and accounts_data.get('success'):
        accounts = accounts_data['accounts']
        print(f"Available accounts: {len(accounts)}")
        # Assume first account for now
        account_id = accounts[0]['id']
        print(f"Using account: {account_id}")

        # Get positions
        positions = client.get_positions(account_id)
        open_positions = positions.get('positions', []) if positions else []
        open_risk = sum(abs(p.get('quantity', 0)) * p.get('entryPrice', 0) for p in open_positions)

        # Update status.json
        with open('config/status.json', 'r') as f:
            status = json.load(f)

        status['equity'] = accounts[0]['balance']
        status['open_risk'] = open_risk
        status['exposure_by_symbol'] = {p.get('contractId', 'unknown'): abs(p.get('quantity', 0)) for p in open_positions}

        with open('config/status.json', 'w') as f:
            json.dump(status, f, indent=2)

        print(f"Updated status: equity ${status['equity']}, open risk ${open_risk}")

        # Pull gold data
        gold_puller = GoldDataPuller(client)
        if gold_puller.find_gold_contract():
            timeframes = ["1min", "5min", "15min", "1hour", "1day"]
            bars_per_timeframe = {tf: 20000 for tf in timeframes}

            # Use live feed for official Topstep data; partial bar gives the current interval snapshot.
            gold_puller.collect_candles(
                timeframes=timeframes,
                bars=bars_per_timeframe,
                live=False,
                include_partial_bar=True,
                fallback_to_live=True,
            )
            for tf in timeframes:
                gold_puller.save_candles(timeframe=tf)

            stitched, contract_frames = gold_puller.collect_stitched_candles(
                timeframes=timeframes,
                bars_per_contract=20000,
                include_partial_bar=True,
                include_current=True,
                min_year=20,
                target_bars=bars_per_timeframe,
            )

            for tf in timeframes:
                gold_puller.save_candles(timeframe=f"{tf}_chain")

            if contract_frames:
                gold_puller.save_contract_candles(contract_frames)
        else:
            print("No MGC contract found")

    # Load status
    with open('config/status.json', 'r') as f:
        status = json.load(f)

    print(f"Current equity: ${status['equity']}")
    print(f"Profit target: ${status['profit_target']}")
    print("System ready for trading.")

if __name__ == "__main__":
    main()