"""
TopstepX API Client

Handles authentication and REST API calls. SignalR for real-time to be added later.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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
        self.token_acquired_at: Optional[datetime] = None
        self.session_ttl = float(os.getenv('TOPSTEPX_SESSION_TTL_HOURS', '24'))

    def authenticate(self):
        """Authenticate and get JWT token."""
        url = f"{self.base_url}/api/Auth/loginKey"
        payload = {"username": self.username, "apiKey": self.api_key}
        response = self.session.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data['token']
                self.token_acquired_at = datetime.now(timezone.utc)
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                return True
            else:
                print(f"Auth failed: {data.get('message')}")
        else:
            print(f"Auth request failed: {response.status_code}")
        return False

    def token_valid(self) -> bool:
        if not self.token or not self.token_acquired_at:
            return False
        expires_at = self.token_acquired_at + timedelta(hours=self.session_ttl)
        # Refresh a few minutes early to avoid race conditions
        refresh_at = expires_at - timedelta(minutes=5)
        return datetime.now(timezone.utc) < refresh_at

    def ensure_authenticated(self) -> bool:
        if self.token_valid():
            return True
        return self.authenticate()

    def get_accounts(self):
        """Retrieve trading accounts."""
        self.ensure_authenticated()
        url = f"{self.base_url}/api/Account/search"
        response = self.session.post(url, json={"onlyActiveAccounts": True}, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None

    def get_account_details(self, account_id: str) -> Optional[Dict[str, Any]]:
        self.ensure_authenticated()
        url = f"{self.base_url}/api/Account/get"
        response = self.session.post(url, json={"accountId": account_id}, timeout=30)
        if response.status_code != 200:
            return None
        try:
            data = response.json()
        except json.JSONDecodeError:
            return None
        if not data.get("success", False):
            return None
        return data.get("account")

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
        self.ensure_authenticated()

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
        self.ensure_authenticated()
        url = f"{self.base_url}/api/Contract/search"
        payload = {"searchText": symbol, "live": live}
        response = self.session.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None

    def get_contract_by_id(self, contract_id):
        """Retrieve a specific contract definition."""
        self.ensure_authenticated()
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
        self.ensure_authenticated()
        url = f"{self.base_url}/api/Order/place"
        payload = {
            "accountId": account_id,
            "contractId": contract_id,
            "type": order_type,
            "side": side,  # 0: buy, 1: sell
            "size": size,
            **kwargs
        }
        response = self.session.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None

    def search_orders(
        self,
        account_id: str,
        statuses: Optional[List[str]] = None,
        include_historical: bool = False,
        page: int = 1,
        page_size: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve live or historical orders for an account."""

        self.ensure_authenticated()
        payload: Dict[str, Any] = {
            "accountId": account_id,
            "page": int(max(page, 1)),
            "pageSize": int(max(min(page_size, 500), 1)),
            "includeHistorical": bool(include_historical),
        }

        if statuses:
            payload["statuses"] = statuses

        url = f"{self.base_url}/api/Order/search"
        response = self.session.post(url, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            print(f"Order search failed: {exc} | Payload: {payload}")
            return None

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Order search response was not valid JSON")
            return None

        if not data.get("success", False):
            print(f"Order search unsuccessful: {data}")
            return None

        return data

    def cancel_order(self, order_id):
        """Cancel an order."""
        self.ensure_authenticated()
        url = f"{self.base_url}/api/Order/cancel"
        response = self.session.post(url, json={"orderId": order_id}, timeout=30)
        return response.status_code == 200

    def get_positions(self, account_id):
        """Get open positions."""
        self.ensure_authenticated()
        url = f"{self.base_url}/api/Position/search"
        payload = {"accountId": account_id}
        response = self.session.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None

    def get_quotes(self, contract_id):
        """Get current quote for contract (if available via REST). Placeholder."""
        return None

    def search_trades(
        self,
        account_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Optional[Dict[str, Any]]:
        self.ensure_authenticated()

        payload: Dict[str, Any] = {
            "accountId": account_id,
            "page": int(max(page, 1)),
            "pageSize": int(max(min(page_size, 500), 1)),
            "sort": [{"field": "timestamp", "direction": "desc"}],
        }

        if start_time:
            payload["startTime"] = start_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if end_time:
            payload["endTime"] = end_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        url = f"{self.base_url}/api/Trade/search"
        response = self.session.post(url, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            print(f"Trade search failed: {exc} | Payload: {payload}")
            return None

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Trade search response was not valid JSON")
            return None

        if not data.get("success", False):
            print(f"Trade search unsuccessful: {data}")
            return None

        return data

if __name__ == "__main__":
    client = TopstepXClient()
    if client.authenticate():
        print("Authenticated")
        accounts = client.get_accounts()
        print(f"Accounts: {accounts}")
    else:
        print("Auth failed")