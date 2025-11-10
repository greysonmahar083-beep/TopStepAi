export interface Contract {
  id?: string;
  symbol: string;
  name?: string;
  description?: string;
  exchange?: string;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistItem {
  symbol: string;
  last: number;
  change: number;
  changePercent: number;
}

export interface AlertItem {
  id: string;
  description: string;
  timeAgo: string;
  severity?: 'info' | 'warning' | 'critical';
}

export interface AccountSummary {
  id: string;
  name: string;
  status?: string;
  canTrade: boolean;
  balance: number;
  buyingPower: number;
  dayPnl: number;
  realizedPnl: number;
  unrealizedPnl: number;
}

export interface PositionSnapshot {
  id: string;
  contractId?: string;
  symbol?: string;
  quantity: number;
  entryPrice: number;
  marketPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  timestamp?: number | null;
}

export interface TradeRecord {
  id: string;
  accountId?: string;
  contractId?: string;
  symbol?: string;
  side: 'Buy' | 'Sell';
  price: number;
  quantity: number;
  realizedPnl: number;
  timestamp?: number | null;
}

export interface TradeEvent {
  id: string;
  type: 'Buy' | 'Sell';
  price: number;
  size: number;
  timestamp: number | null | undefined;
}

export interface OrderRecord {
  id: string;
  accountId?: string;
  contractId?: string;
  symbol?: string;
  side: 'Buy' | 'Sell';
  type?: string;
  status?: string;
  price?: number;
  quantity: number;
  filledQuantity?: number;
  submitted?: number | null;
  filled?: number | null;
}

export interface StrategyResult {
  profitPct: number;
  equityCurve: number[];
  trades: TradeEvent[];
}

export interface MetricsSummary {
  equity: number;
  startBalance: number;
  profitTarget: number;
  remainingMaxLoss: number;
  dailyLossCap: number;
  trailingDrawdown: number;
  killswitchThreshold: number;
  openRisk: number;
  realizedPnl: number;
  unrealizedPnl: number;
  dayPnl: number;
  tradeCountToday: number;
  consecutiveLosses: number;
  rulesStatus: Record<string, string>;
}

export interface DashboardSummary {
  accounts: AccountSummary[];
  activeAccount: AccountSummary | null;
  positions: PositionSnapshot[];
  orders: OrderRecord[];
  trades: TradeRecord[];
  metrics: MetricsSummary;
  watchlist: WatchlistItem[];
  alerts: AlertItem[];
  strategy: StrategyResult | null;
  status?: Record<string, unknown>;
  symbol: string;
  timeframe: string;
}