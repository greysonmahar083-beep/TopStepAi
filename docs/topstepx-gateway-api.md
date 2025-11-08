# TopstepX Gateway API — Comprehensive Documentation (Text-Only Edition)

This document provides a fully textual overview of the TopstepX Gateway API, based on the ProjectX Gateway architecture. It covers REST endpoints, authentication, account and market operations, and SignalR real-time data hubs — without any code snippets or scripts.

---

## Table of Contents

1. Overview
2. API Connection Information
3. Authentication Flow
4. Account Endpoints
5. Market Data Endpoints
6. Order Management Endpoints
7. Position and Trade Endpoints
8. Real-Time (SignalR) Communication
9. Example API Workflow (Conceptual)
10. Key Notes and Usage Guidelines

---

## 1. Overview

The TopstepX API enables professional traders and developers to integrate their trading tools and strategies directly with the TopstepX trading environment. Built on the ProjectX Gateway framework, this API allows access to account data, market contracts, order management, and real-time market feeds.

The API provides two modes of interaction:

* REST API: for managing authentication, accounts, orders, positions, and historical data.
* SignalR Hubs: for subscribing to live user and market data streams.

The system uses JWT session tokens for authentication and supports secure, real-time communication via HTTPS and WebSocket (SignalR).

---

## 2. API Connection Information

Official production endpoints for TopstepX:

* API Endpoint: https://api.topstepx.com
* User Hub (SignalR): https://rtc.topstepx.com/hubs/user
* Market Hub (SignalR): https://rtc.topstepx.com/hubs/market

All REST and WebSocket communications use these URLs.

---

## 3. Authentication Flow

Authentication is required for all API and hub operations. Use your TopstepX API key and username to obtain a session token.

Authentication process:

1. POST to `/api/Auth/loginKey` with username and API key.
2. Response contains `token`, `success` flag, and optional error message.
3. Include the token in all future REST API calls using the header `Authorization: Bearer <token>`.
4. For SignalR connections, append the token as a query parameter: `?access_token=<token>`.

Tokens generally expire after 24 hours. Revalidate your session by calling `/api/Auth/validate`.

---

## 4. Account Endpoints

### `/api/Account/search`

Retrieves a list of accounts linked to your API credentials. Filter for active accounts by including `{ onlyActiveAccounts: true }` in the request body.

Response fields include:

* Account ID
* Account name
* Status (active/inactive)
* Can trade (true/false)

Typically called after login to confirm available trading accounts.

---

## 5. Market Data Endpoints

### `/api/Contract/search`

Search for available contracts by symbol or description. Specify live or historical contracts.

Parameters:

* `searchText` — partial contract name (e.g., "NQ", "ES", "CL").
* `live` — Boolean indicating if only currently tradable contracts are desired.

### `/api/Contract/get`

Retrieve full details of a specific contract by its ID.

Common contract data fields:

* Contract ID
* Symbol
* Description
* Tick size and value
* Exchange
* Active status

Use these endpoints to identify tradable markets and instruments.

### `/api/History/retrieveBars`

Retrieve historical OHLCV bars for a contract. The official Swagger reference is available at
`https://api.topstepx.com/swagger/index.html#/History/History_RetrieveBars`.

Request body fields:

* `contractId` *(string, required)* — example `"CON.F.US.MGC.Z25"`.
* `live` *(boolean, required)* — `false` for sim/historical stream, `true` for the live subscription.
* `startTime` *(ISO-8601, required)* — earliest timestamp to include. Example `"2025-01-01T00:00:00Z"`.
* `endTime` *(ISO-8601, required)* — latest timestamp. Example `"2025-01-31T23:59:59Z"`.
* `unit` *(int, required)* — aggregation unit (`1=Second`, `2=Minute`, `3=Hour`, `4=Day`, `5=Week`, `6=Month`).
* `unitNumber` *(int, required)* — number of units per bar (e.g., `5` with unit `2` = 5-minute bars).
* `limit` *(int, required)* — maximum bars to return (up to 20,000 as per Swagger notes).
* `includePartialBar` *(boolean, required)* — include the currently forming bar when `true`.

Successful responses contain `bars` (array) where each bar provides:

* `t` — timestamp (ISO-8601 with offset)
* `o` — open price
* `h` — high price
* `l` — low price
* `c` — close price
* `v` — volume

`success`, `errorCode`, and `errorMessage` mirror the standard TopstepX response envelope. Always check `success`
before using the payload and log `errorMessage` when present.

---

## 6. Order Management Endpoints

### `/api/Order/place`

Place a new order. Required parameters:

* `accountId` — trading account identifier.
* `contractId` — market contract ID.
* `type` — order type (Limit, Market, Stop, Trailing Stop, etc.).
* `side` — buy (0) or sell (1).
* `size` — quantity of contracts.

Optional fields: `limitPrice`, `stopPrice`, `trailPrice`.

Response includes success confirmation and generated order ID.

### `/api/Order/cancel`

Cancel an existing order. Request body must contain `orderId`.

### `/api/Order/modify`

Modify price or size of an existing order.

### `/api/Order/search`

Search for orders via filters: status, contract, date range, etc.

Together these endpoints form the order lifecycle: place → monitor → modify/cancel → record.

---

## 7. Position and Trade Endpoints

### `/api/Position/search`

Retrieve open positions for one or more accounts. Returns:

* Position ID
* Account ID
* Contract ID
* Quantity
* Entry price
* Unrealized profit/loss

### `/api/Position/get`

Return details for a specific position by ID.

### `/api/Trade/search`

Retrieve trade history for tracking fills and performance statistics.

These endpoints enable position tracking, reporting, and performance analysis.

---

## 8. Real-Time (SignalR) Communication

TopstepX uses SignalR hubs for live event streaming. After authentication, connect using the session token.

Hubs:

* User Hub: notifications about account events, order updates, fills, and session changes.
* Market Hub: live market data, quotes, trades, and depth information.

Common event types:

* `GatewayQuote` — live price updates.
* `GatewayTrade` — trade tick data.
* `GatewayDepth` — order book changes.

Available subscriptions (by contract ID):

* SubscribeContractQuotes
* SubscribeContractTrades
* SubscribeContractMarketDepth

Unsubscribe using corresponding calls (e.g., UnsubscribeContractQuotes).

Hubs maintain persistent connections for real-time feedback, ensuring synchronization between local systems and the TopstepX trading environment.

---

## 9. Example API Workflow (Conceptual)

1. Authenticate with `/api/Auth/loginKey`.
2. Retrieve accounts via `/api/Account/search`.
3. Search instruments via `/api/Contract/search`.
4. Place an order using `/api/Order/place`.
5. Monitor execution via `/api/Order/search` and User Hub events.
6. Manage positions via `/api/Position/search`.
7. Retrieve trade history using `/api/Trade/search`.
8. Subscribe to quotes and trades via Market Hub for real-time strategy updates.

This sequence provides a complete trading automation loop.

---

## 10. Key Notes and Usage Guidelines

* No sandbox environment; all activity is live.
* All requests must include a valid session token.
* Market data and user events require stable internet and persistent WebSocket connections.
* VPN or VPS usage for trading execution is prohibited per TopstepX compliance rules.
* Integration must adhere to program rules and limits.

---

**End of Document — Text-Only Comprehensive Reference for TopstepX Gateway API**
