from __future__ import annotations

import json
import os
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

from execution.topstepx_client import TopstepXClient

TIMEFRAME_CONFIG: Dict[str, Tuple[int, int, timedelta]] = {
    "1m": (2, 1, timedelta(minutes=1)),
    "3m": (2, 3, timedelta(minutes=3)),
    "5m": (2, 5, timedelta(minutes=5)),
    "15m": (2, 15, timedelta(minutes=15)),
    "30m": (2, 30, timedelta(minutes=30)),
    "60m": (3, 1, timedelta(hours=1)),
    "1h": (3, 1, timedelta(hours=1)),
    "2h": (3, 2, timedelta(hours=2)),
    "4h": (3, 4, timedelta(hours=4)),
    "1d": (4, 1, timedelta(days=1)),
    "d": (4, 1, timedelta(days=1)),
    "1w": (5, 1, timedelta(weeks=1)),
    "w": (5, 1, timedelta(weeks=1)),
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str) and not value.strip():
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_iso8601(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class TopstepService:
    """High-level service wrapper around TopstepXClient for dashboard consumption."""

    def __init__(self) -> None:
        self._client = TopstepXClient()
        self._lock = Lock()
        self._contract_cache: Dict[str, Dict[str, Any]] = {}

        self._status_path = Path(os.getenv("TOPSTEP_STATUS_FILE", "config/status.json"))
        self._start_balance = _to_float(os.getenv("COMBINE_START_BALANCE", 0))
        self._profit_target = _to_float(os.getenv("COMBINE_PROFIT_TARGET", 0))
        self._max_loss = _to_float(os.getenv("COMBINE_MAX_LOSS", 0))
        self._daily_loss_cap = _to_float(os.getenv("DAILY_LOSS_CAP", 0))
        self._trailing_dd_killswitch = _to_float(os.getenv("TRAILING_DD_KILLSWITCH", 0))

        raw_watchlist = os.getenv("TOPSTEPX_WATCHLIST_SYMBOLS", "ESM25,NQZ25,CLF25,GCZ25")
        self._default_watchlist = [symbol.strip().upper() for symbol in raw_watchlist.split(",") if symbol.strip()]

    def ensure_session(self) -> None:
        with self._lock:
            if not self._client.ensure_authenticated():
                raise RuntimeError("TopstepX authentication failed")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_candles(self, symbol: str, timeframe: str, limit: int = 500) -> Dict[str, Any]:
        self.ensure_session()
        symbol = symbol.strip().upper()
        unit, unit_number, delta = self._resolve_timeframe(timeframe)

        contract = self._resolve_contract(symbol)
        if not contract:
            raise RuntimeError(f"No contract matches symbol '{symbol}'.")

        end_time = datetime.now(timezone.utc)
        # request slightly more history than needed to ensure full slice
        horizon = delta * max(limit + 5, limit)
        start_time = end_time - horizon

        response = self._client.retrieve_bars(
            contract_id=contract["id"],
            start_time=start_time,
            end_time=end_time,
            unit=unit,
            unit_number=unit_number,
            limit=min(max(limit, 10), 2000),
            include_partial_bar=True,
            live=True,
        )

        if not response or not response.get("success"):
            message = response.get("errorMessage") if isinstance(response, dict) else "Unknown error"
            raise RuntimeError(f"Failed to retrieve bars for {symbol}: {message}")

        candles: List[Dict[str, Any]] = []
        for bar in response.get("bars", []):
            ts = _parse_iso8601(bar.get("t"))
            if not ts:
                continue
            candles.append(
                {
                    "time": int(ts.timestamp()),
                    "open": _to_float(bar.get("o")),
                    "high": _to_float(bar.get("h")),
                    "low": _to_float(bar.get("l")),
                    "close": _to_float(bar.get("c")),
                    "volume": _to_float(bar.get("v")),
                }
            )

        candles.sort(key=lambda item: item["time"])

        compact_contract = {
            "id": contract.get("id"),
            "symbol": contract.get("symbol") or symbol,
            "description": contract.get("description"),
            "exchange": contract.get("exchange"),
        }

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "contract": compact_contract,
            "candles": candles[-limit:],
        }

    def get_dashboard_snapshot(
        self,
        symbol: str,
        timeframe: str = "5m",
        watchlist: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        self.ensure_session()

        accounts_payload = self._client.get_accounts()
        accounts = self._normalize_accounts(accounts_payload)
        active_account = self._select_active_account(accounts)

        positions: List[Dict[str, Any]] = []
        orders: List[Dict[str, Any]] = []
        trades: List[Dict[str, Any]] = []

        if active_account:
            positions_payload = self._client.get_positions(active_account["id"])
            positions = self._normalize_positions(positions_payload)

            orders_payload = self._client.search_orders(active_account["id"], statuses=["Working", "Pending", "Accepted"], include_historical=False)
            orders = self._normalize_orders(orders_payload)

            trades_payload = self._client.search_trades(active_account["id"], page_size=100)
            trades = self._normalize_trades(trades_payload)
            self._seed_contract_cache_from_trades(trades)

        status_snapshot = self._load_status()

        metrics = self._build_metrics(active_account, positions, trades, status_snapshot)
        alerts = self._build_alerts(metrics, status_snapshot)
        strategy = self._build_strategy(metrics, trades)

        watchlist_symbols = list(dict.fromkeys([
            symbol.strip().upper(),
            *(watchlist or self._default_watchlist),
        ]))
        watchlist_items = self._build_watchlist(watchlist_symbols)

        return {
            "accounts": accounts,
            "activeAccount": active_account,
            "positions": positions,
            "orders": orders,
            "trades": trades,
            "metrics": metrics,
            "watchlist": watchlist_items,
            "alerts": alerts,
            "strategy": strategy,
            "status": status_snapshot,
            "symbol": symbol,
            "timeframe": timeframe,
        }

    def search_contracts(self, query: str, live: bool = True) -> List[Dict[str, Any]]:
        self.ensure_session()
        query = query.strip()
        if not query:
            return []

        payload = self._client.search_contracts(query, live=live)
        if not payload:
            return []

        candidates = self._extract_collection(payload, "contracts")
        result: List[Dict[str, Any]] = []
        for contract in candidates:
            if not isinstance(contract, dict):
                continue
            contract_id = contract.get("id")
            if not contract_id:
                continue
            self._cache_contract(contract)
            symbol = contract.get("symbol") or contract.get("name") or contract_id
            result.append(
                {
                    "id": contract_id,
                    "symbol": symbol,
                    "description": contract.get("description"),
                    "exchange": contract.get("exchange"),
                    "isActive": contract.get("isActive", True),
                }
            )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_timeframe(self, timeframe: str) -> Tuple[int, int, timedelta]:
        key = timeframe.lower().strip()
        if key.endswith("m") and key[:-1].isdigit():
            minutes = int(key[:-1])
            custom_key = f"{minutes}m"
            if custom_key in TIMEFRAME_CONFIG:
                return TIMEFRAME_CONFIG[custom_key]
            return 2, minutes, timedelta(minutes=minutes)
        if key.endswith("h") and key[:-1].isdigit():
            hours = int(key[:-1])
            custom_key = f"{hours}h"
            if custom_key in TIMEFRAME_CONFIG:
                return TIMEFRAME_CONFIG[custom_key]
            return 3, hours, timedelta(hours=hours)
        if key in TIMEFRAME_CONFIG:
            return TIMEFRAME_CONFIG[key]
        raise ValueError(f"Unsupported timeframe '{timeframe}'")

    def _resolve_contract(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized = symbol.upper()
        if normalized in self._contract_cache:
            return self._contract_cache[normalized]

        payload = self._client.search_contracts(normalized, live=True)
        candidates = self._extract_collection(payload or {}, "contracts")

        if not candidates:
            fallback_payload = self._client.search_contracts(normalized, live=False)
            candidates = self._extract_collection(fallback_payload or {}, "contracts")

        for contract in candidates:
            if not isinstance(contract, dict):
                continue
            contract_id = contract.get("id")
            if not contract_id:
                continue

            cached = self._cache_contract(contract, alias=normalized)
            if cached:
                return cached

        if self._looks_like_contract_id(normalized):
            return self._cache_contract_by_id(normalized)

        return None

    def _seed_contract_cache_from_trades(self, trades: Iterable[Dict[str, Any]]) -> None:
        for trade in trades or []:
            contract_id = trade.get("contractId")
            if not contract_id:
                continue
            alias = str(trade.get("symbol") or "").strip().upper() or None
            self._cache_contract_by_id(contract_id, alias=alias)

    def _cache_contract(self, contract: Dict[str, Any], alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not isinstance(contract, dict):
            return None
        contract_id = contract.get("id")
        if not contract_id:
            return None

        normalized_id = contract_id.strip().upper()
        self._contract_cache[normalized_id] = contract

        symbol = contract.get("symbol")
        if isinstance(symbol, str) and symbol.strip():
            self._contract_cache[symbol.strip().upper()] = contract

        if alias:
            self._contract_cache[alias.upper()] = contract

        return contract

    def _cache_contract_by_id(self, contract_id: str, alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
        normalized_id = contract_id.strip().upper()
        if normalized_id in self._contract_cache:
            contract = self._contract_cache[normalized_id]
            if alias:
                self._contract_cache[alias.upper()] = contract
            return contract

        contract = self._client.get_contract_by_id(normalized_id)
        if not contract:
            return None

        return self._cache_contract(contract, alias=alias)

    @staticmethod
    def _looks_like_contract_id(candidate: str) -> bool:
        text = candidate.strip().upper()
        return text.startswith("CON.") and text.count(".") >= 3

    @staticmethod
    def _extract_collection(payload: Dict[str, Any], key: str) -> List[Any]:
        if not isinstance(payload, dict):
            return []
        if key in payload and isinstance(payload[key], list):
            return payload[key]
        for candidate_key in ("data", "items", "result"):
            candidate = payload.get(candidate_key)
            if isinstance(candidate, list):
                return candidate
            if isinstance(candidate, dict):
                inner = candidate.get(key)
                if isinstance(inner, list):
                    return inner
                inner_items = candidate.get("items")
                if isinstance(inner_items, list):
                    return inner_items
        return []

    def _normalize_accounts(self, payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        accounts: List[Dict[str, Any]] = []
        for account in self._extract_collection(payload or {}, "accounts"):
            if not isinstance(account, dict):
                continue
            account_id = str(account.get("id") or account.get("accountId") or "")
            if not account_id:
                continue
            accounts.append(
                {
                    "id": account_id,
                    "name": account.get("name") or account.get("accountName") or account_id,
                    "status": account.get("status"),
                    "canTrade": bool(account.get("canTrade", account.get("isActive", True))),
                    "balance": _to_float(account.get("balance") or account.get("netLiq")),
                    "buyingPower": _to_float(account.get("buyingPower") or account.get("availableFunds")),
                    "dayPnl": _to_float(account.get("dayPnl") or account.get("todaysPL")),
                    "realizedPnl": _to_float(account.get("realizedPnl") or account.get("totalRealizedPL")),
                    "unrealizedPnl": _to_float(account.get("unrealizedPnl") or account.get("openPL")),
                }
            )
        return accounts

    def _normalize_positions(self, payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        positions: List[Dict[str, Any]] = []
        for position in self._extract_collection(payload or {}, "positions"):
            if not isinstance(position, dict):
                continue
            contract_info = position.get("contract") if isinstance(position.get("contract"), dict) else {}
            symbol = contract_info.get("symbol") or position.get("symbol") or position.get("contractId")
            timestamp = _parse_iso8601(position.get("timestamp") or position.get("updated") or position.get("openTime"))
            positions.append(
                {
                    "id": str(position.get("id") or position.get("positionId") or symbol or ""),
                    "contractId": position.get("contractId") or contract_info.get("id"),
                    "symbol": symbol,
                    "quantity": _to_float(position.get("quantity") or position.get("netPosition")),
                    "entryPrice": _to_float(position.get("entryPrice") or position.get("averagePrice")),
                    "marketPrice": _to_float(position.get("marketPrice") or position.get("lastPrice")),
                    "unrealizedPnl": _to_float(position.get("unrealizedPnl") or position.get("openPL")),
                    "realizedPnl": _to_float(position.get("realizedPnl") or position.get("realizedPL")),
                    "timestamp": int(timestamp.timestamp()) if timestamp else None,
                }
            )
        return positions

    def _normalize_trades(self, payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        trades: List[Dict[str, Any]] = []
        for trade in self._extract_collection(payload or {}, "trades"):
            if not isinstance(trade, dict):
                continue
            timestamp = _parse_iso8601(
                trade.get("timestamp")
                or trade.get("time")
                or trade.get("tradeTime")
                or trade.get("executed")
                or trade.get("filledTime")
            )
            price = _to_float(trade.get("price") or trade.get("fillPrice") or trade.get("executedPrice"))
            quantity = _to_float(trade.get("quantity") or trade.get("fillQuantity") or trade.get("size"))
            side_value = trade.get("side") or trade.get("action") or trade.get("direction") or trade.get("buySell")
            side = self._normalize_side(side_value)
            trades.append(
                {
                    "id": str(trade.get("id") or trade.get("tradeId") or trade.get("orderId") or len(trades)),
                    "accountId": trade.get("accountId"),
                    "contractId": trade.get("contractId"),
                    "symbol": trade.get("symbol") or trade.get("contractSymbol"),
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "realizedPnl": _to_float(trade.get("realizedPnl") or trade.get("realizedPL")),
                    "timestamp": int(timestamp.timestamp()) if timestamp else None,
                }
            )

        trades.sort(key=lambda item: item.get("timestamp") or 0, reverse=True)
        return trades

    def _normalize_orders(self, payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        orders: List[Dict[str, Any]] = []
        for order in self._extract_collection(payload or {}, "orders"):
            if not isinstance(order, dict):
                continue

            submitted = _parse_iso8601(
                order.get("submitted")
                or order.get("timestamp")
                or order.get("created")
                or order.get("createdTime")
            )

            filled = _parse_iso8601(order.get("filled") or order.get("filledTime"))

            side_value = order.get("side") or order.get("action") or order.get("direction")
            side = self._normalize_side(side_value)

            orders.append(
                {
                    "id": str(order.get("id") or order.get("orderId") or len(orders)),
                    "accountId": order.get("accountId"),
                    "contractId": order.get("contractId"),
                    "symbol": order.get("symbol") or order.get("contractSymbol"),
                    "quantity": _to_float(order.get("quantity") or order.get("size") or order.get("orderQuantity")),
                    "filledQuantity": _to_float(order.get("filledQuantity") or order.get("filled") or 0.0),
                    "price": _to_float(order.get("price") or order.get("limitPrice") or order.get("avgFillPrice")),
                    "type": order.get("type") or order.get("orderType"),
                    "status": order.get("status") or order.get("statusText"),
                    "side": side,
                    "submitted": int(submitted.timestamp()) if submitted else None,
                    "filled": int(filled.timestamp()) if filled else None,
                }
            )

        orders.sort(key=lambda item: item.get("submitted") or 0, reverse=True)
        return orders

    @staticmethod
    def _normalize_side(value: Any) -> str:
        if value is None:
            return "Buy"
        if isinstance(value, (int, float)):
            return "Buy" if int(value) == 0 else "Sell"
        text = str(value).strip().lower()
        if text in {"buy", "b", "long"}:
            return "Buy"
        if text in {"sell", "s", "short"}:
            return "Sell"
        return "Buy"

    def _select_active_account(self, accounts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not accounts:
            return None
        for account in accounts:
            if account.get("canTrade"):
                return account
        return accounts[0]

    def _load_status(self) -> Dict[str, Any]:
        if not self._status_path.exists():
            return {}
        try:
            return json.loads(self._status_path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def _build_metrics(
        self,
        account: Optional[Dict[str, Any]],
        positions: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        status: Dict[str, Any],
    ) -> Dict[str, Any]:
        balance = account.get("balance") if account else 0.0
        open_risk = sum(abs(pos["quantity"]) * _to_float(pos.get("entryPrice")) for pos in positions)

        realized = account.get("realizedPnl") if account else 0.0
        unrealized = account.get("unrealizedPnl") if account else 0.0
        day_pnl = account.get("dayPnl") if account else 0.0

        metrics = {
            "equity": balance,
            "startBalance": self._start_balance,
            "profitTarget": status.get("profit_target", self._profit_target),
            "remainingMaxLoss": status.get("remaining_mll", self._max_loss),
            "dailyLossCap": status.get("daily_loss_cap", self._daily_loss_cap),
            "trailingDrawdown": status.get("trailing_dd", 0.0),
            "killswitchThreshold": status.get("killswitch_threshold", self._trailing_dd_killswitch),
            "openRisk": open_risk,
            "realizedPnl": realized,
            "unrealizedPnl": unrealized,
            "dayPnl": day_pnl,
            "tradeCountToday": status.get("trade_count_today", 0),
            "consecutiveLosses": status.get("consecutive_losses", 0),
            "rulesStatus": status.get("rules_status", {}),
        }

        if trades:
            today = datetime.now(timezone.utc).date()
            metrics["tradeCountToday"] = sum(
                1 for trade in trades if trade.get("timestamp") and datetime.fromtimestamp(trade["timestamp"], tz=timezone.utc).date() == today
            )

        return metrics

    def _build_alerts(self, metrics: Dict[str, Any], status: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []

        open_risk = _to_float(metrics.get("openRisk"))
        daily_cap = _to_float(metrics.get("dailyLossCap"))
        if daily_cap and open_risk > daily_cap * 0.85:
            alerts.append(
                {
                    "id": "open-risk",
                    "description": f"Open risk ${open_risk:,.0f} approaching daily cap ${daily_cap:,.0f}",
                    "severity": "warning",
                    "timeAgo": "moments ago",
                }
            )

        for idx, breach in enumerate(status.get("recent_breaches", []) or []):
            alerts.append(
                {
                    "id": f"breach-{idx}",
                    "description": breach,
                    "severity": "critical",
                    "timeAgo": "today",
                }
            )

        if not alerts:
            alerts.append(
                {
                    "id": "system-ok",
                    "description": "All systems nominal. Rule checks passing.",
                    "severity": "info",
                    "timeAgo": "just now",
                }
            )

        return alerts

    def _build_strategy(self, metrics: Dict[str, Any], trades: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not metrics:
            return None

        start_equity = _to_float(metrics.get("startBalance"), 0.0) or 1.0
        current_equity = _to_float(metrics.get("equity"), start_equity)
        profit_pct = ((current_equity - start_equity) / start_equity) * 100.0

        recent_trades = list(reversed(trades[:20]))
        cumulative: Deque[float] = deque([start_equity])
        running_equity = start_equity
        for trade in recent_trades:
            running_equity += _to_float(trade.get("realizedPnl"))
            cumulative.append(running_equity)
            if len(cumulative) > 48:
                cumulative.popleft()

        equity_curve = list(cumulative)
        if len(equity_curve) < 2:
            equity_curve = [start_equity, current_equity]
        else:
            equity_curve[-1] = current_equity

        mapped_trades = [
            {
                "id": trade.get("id"),
                "type": trade.get("side", "Buy"),
                "price": trade.get("price"),
                "size": trade.get("quantity"),
                "timestamp": trade.get("timestamp"),
            }
            for trade in trades[:10]
        ]

        return {
            "profitPct": round(profit_pct, 2),
            "equityCurve": [round(value, 2) for value in equity_curve],
            "trades": mapped_trades,
        }

    def _build_watchlist(self, symbols: Iterable[str]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for symbol in symbols:
            try:
                snapshot = self.get_candles(symbol, "1m", limit=2)
            except Exception:
                continue
            candles = snapshot.get("candles", [])
            if not candles:
                continue
            last = candles[-1]
            prev = candles[-2] if len(candles) > 1 else candles[-1]
            last_close = _to_float(last.get("close"))
            prev_close = _to_float(prev.get("close"), last_close)
            change = last_close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0
            items.append(
                {
                    "symbol": symbol,
                    "last": round(last_close, 2),
                    "change": round(change, 2),
                    "changePercent": round(change_pct, 2),
                }
            )
        return items


__all__ = ["TopstepService"]
