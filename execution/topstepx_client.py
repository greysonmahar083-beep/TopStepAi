"""
TopstepX API Client

Handles authentication and REST API calls. SignalR for real-time to be added later.
"""

import os
import json
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

class TopstepXClient:
    def __init__(self):
        self.base_url = os.getenv('TOPSTEPX_BASE_URL')
        self.user_hub_url = os.getenv('TOPSTEPX_USER_HUB')
        self.market_hub_url = os.getenv('TOPSTEPX_MARKET_HUB')
        self.username = os.getenv('TOPSTEPX_USERNAME')
        self.api_key = os.getenv('TOPSTEPX_API_KEY')
        self.token = None
        self.session = requests.Session()

    def authenticate(self):
        """Authenticate and get JWT token."""
        url = f"{self.base_url}/api/Auth/loginKey"
        payload = {"username": self.username, "apiKey": self.api_key}
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data['token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                return True
            else:
                print(f"Auth failed: {data.get('message')}")
        else:
            print(f"Auth request failed: {response.status_code}")
        return False

    def get_accounts(self):
        """Retrieve trading accounts."""
        url = f"{self.base_url}/api/Account/search"
        response = self.session.post(url, json={"onlyActiveAccounts": True})
        if response.status_code == 200:
            return response.json()
        return None

    def retrieve_bars(
        self,
        contract_id,
        start_time,
        end_time,
        unit,
        unit_number=1,
        limit=2000,
        include_partial_bar=False,
        live=False,
    ):
        """Retrieve historical bars via /api/History/retrieveBars."""

        def _to_iso8601(value):
            if isinstance(value, str):
                return value
            if not isinstance(value, datetime):
                raise TypeError("start_time/end_time must be datetime or ISO string")
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
            return value.isoformat(timespec="seconds").replace("+00:00", "Z")

        unit_map = {
            "second": 1,
            "seconds": 1,
            "sec": 1,
            "s": 1,
            "minute": 2,
            "minutes": 2,
            "min": 2,
            "m": 2,
            "hour": 3,
            "hours": 3,
            "h": 3,
            "day": 4,
            "days": 4,
            "d": 4,
            "week": 5,
            "weeks": 5,
            "w": 5,
            "month": 6,
            "months": 6,
            "mo": 6,
        }

        resolved_unit = unit
        if isinstance(unit, str):
            key = unit.lower().strip()
            if key not in unit_map:
                raise ValueError(f"Unsupported time unit '{unit}'")
            resolved_unit = unit_map[key]

        payload = {
            "contractId": contract_id,
            "live": bool(live),
            "startTime": _to_iso8601(start_time),
            "endTime": _to_iso8601(end_time),
            "unit": resolved_unit,
            "unitNumber": int(unit_number),
            "limit": int(limit),
            "includePartialBar": bool(include_partial_bar),
        }

        url = f"{self.base_url}/api/History/retrieveBars"
        response = self.session.post(url, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            print(f"Retrieve bars request failed: {exc} | Payload: {payload}")
            try:
                print(response.text)
            except Exception:  # pragma: no cover - best effort logging
                pass
            return None

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Retrieve bars: response was not valid JSON")
            return None

        if not data.get("success", False):
            print(f"Retrieve bars unsuccessful: {data}")
        return data

    def search_contracts(self, symbol, live=True):
        """Search for contracts by symbol."""
        url = f"{self.base_url}/api/Contract/search"
        payload = {"searchText": symbol, "live": live}
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        return None

    def get_contract_by_id(self, contract_id):
        """Retrieve a specific contract definition."""
        url = f"{self.base_url}/api/Contract/searchById"
        response = self.session.post(url, json={"contractId": contract_id}, timeout=15)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            print(f"Contract lookup failed for {contract_id}: {exc}")
            return None

        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Contract lookup for {contract_id} returned non-JSON response")
            return None

        if not data.get("success"):
            return None
        return data.get("contract")

    def place_order(self, account_id, contract_id, side, size, order_type='Market', **kwargs):
        """Place an order."""
        url = f"{self.base_url}/api/Order/place"
        payload = {
            "accountId": account_id,
            "contractId": contract_id,
            "type": order_type,
            "side": side,  # 0: buy, 1: sell
            "size": size,
            **kwargs
        }
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        return None

    def cancel_order(self, order_id):
        """Cancel an order."""
        url = f"{self.base_url}/api/Order/cancel"
        response = self.session.post(url, json={"orderId": order_id})
        return response.status_code == 200

    def get_positions(self, account_id):
        """Get open positions."""
        url = f"{self.base_url}/api/Position/search"
        payload = {"accountId": account_id}
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        return None

    def get_quotes(self, contract_id):
        """Get current quote for contract (if available via REST). Placeholder."""
        # TopstepX may not have REST quotes; use SignalR
        return None

    def get_trades(self, contract_id):
        """Get recent trades for contract (if available). Placeholder."""
        # Similar to quotes
        return None

if __name__ == "__main__":
    client = TopstepXClient()
    if client.authenticate():
        print("Authenticated")
        accounts = client.get_accounts()
        print(f"Accounts: {accounts}")
    else:
        print("Auth failed")