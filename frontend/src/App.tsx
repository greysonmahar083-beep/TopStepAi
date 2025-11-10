import { Suspense, lazy, useCallback, useEffect, useMemo, useState } from 'react';
import { TopNavigation } from './components/TopNavigation';
import type {
  AccountSummary,
  AlertItem,
  Candle,
  Contract,
  DashboardSummary,
  MetricsSummary,
  OrderRecord,
  PositionSnapshot,
  StrategyResult,
  TradeRecord,
  WatchlistItem,
} from './types';
import { fetchCandles, fetchDashboard } from './lib/api';

const ChartArea = lazy(() =>
  import('./components/ChartArea').then((module) => ({ default: module.ChartArea }))
);

const StrategyPanel = lazy(() =>
  import('./components/StrategyPanel').then((module) => ({ default: module.StrategyPanel }))
);

const RightSidebar = lazy(() =>
  import('./components/RightSidebar').then((module) => ({ default: module.RightSidebar }))
);

const LeftSidebar = lazy(() =>
  import('./components/LeftSidebar').then((module) => ({ default: module.LeftSidebar }))
);

// Mock data
const mockCandles: Candle[] = Array.from({ length: 100 }, (_, i) => ({
  time: Date.now() / 1000 - (100 - i) * 3600,
  open: 4500 + Math.random() * 100,
  high: 4520 + Math.random() * 100,
  low: 4480 + Math.random() * 100,
  close: 4500 + Math.random() * 100,
  volume: Math.floor(Math.random() * 1000),
}));

const mockStrategyResult: StrategyResult = {
  profitPct: 12.5,
  equityCurve: [10000, 10120, 10260, 10180, 10340, 10480],
  trades: [
    { id: '1', type: 'Buy', price: 4500, size: 1, timestamp: Date.now() - 2 * 86400000 },
    { id: '2', type: 'Sell', price: 4520, size: 1, timestamp: Date.now() - 86400000 },
    { id: '3', type: 'Buy', price: 4512, size: 2, timestamp: Date.now() - 6 * 3600000 },
  ],
};

const mockWatchlist: WatchlistItem[] = [
  { symbol: 'ESM25', last: 4520.5, change: 15.25, changePercent: 0.34 },
  { symbol: 'NQH25', last: 15850.75, change: -25.50, changePercent: -0.16 },
  { symbol: 'CLF25', last: 78.45, change: 2.10, changePercent: 2.75 },
  { symbol: 'GCZ25', last: 2050.30, change: -15.80, changePercent: -0.76 },
];

const mockAlerts: AlertItem[] = [
  { id: '1', description: 'Break through 9.01m', timeAgo: '10 min ago', severity: 'info' },
  { id: '2', description: 'Volume spike detected', timeAgo: '25 min ago', severity: 'warning' },
  { id: '3', description: 'Support level breached', timeAgo: '1 hour ago', severity: 'critical' },
];

const mockAccount: AccountSummary = {
  id: 'mock-account',
  name: 'Sim Account',
  status: 'Active',
  canTrade: true,
  balance: 150_000,
  buyingPower: 300_000,
  dayPnl: 1_250,
  realizedPnl: 25_000,
  unrealizedPnl: 650,
};

const mockMetrics: MetricsSummary = {
  equity: 150_000,
  startBalance: 125_000,
  profitTarget: 9_000,
  remainingMaxLoss: 4_500,
  dailyLossCap: -3_000,
  trailingDrawdown: 119_000,
  killswitchThreshold: -5_000,
  openRisk: 2_750,
  realizedPnl: 25_000,
  unrealizedPnl: 650,
  dayPnl: 1_250,
  tradeCountToday: 8,
  consecutiveLosses: 1,
  rulesStatus: {
    dailyLoss: 'within_limits',
    trailingDrawdown: 'within_limits',
  },
};

const mockPositions: PositionSnapshot[] = [
  {
    id: 'pos-1',
    contractId: 'ESM25',
    symbol: 'ESM25',
    quantity: 1,
    entryPrice: 4505.75,
    marketPrice: 4524.25,
    unrealizedPnl: 925,
    realizedPnl: 0,
    timestamp: Date.now() / 1000,
  },
  {
    id: 'pos-2',
    contractId: 'CLF25',
    symbol: 'CLF25',
    quantity: -2,
    entryPrice: 79.1,
    marketPrice: 78.45,
    unrealizedPnl: 130,
    realizedPnl: 0,
    timestamp: Date.now() / 1000,
  },
];

const mockTrades: TradeRecord[] = [
  {
    id: 'trade-1',
    accountId: 'mock-account',
    contractId: 'ESM25',
    symbol: 'ESM25',
    side: 'Buy',
    price: 4500.25,
    quantity: 1,
    realizedPnl: 525,
    timestamp: Date.now() / 1000 - 60 * 35,
  },
  {
    id: 'trade-2',
    accountId: 'mock-account',
    contractId: 'NQH25',
    symbol: 'NQH25',
    side: 'Sell',
    price: 15890.5,
    quantity: 1,
    realizedPnl: -120,
    timestamp: Date.now() / 1000 - 60 * 75,
  },
];

const mockOrders: OrderRecord[] = [
  {
    id: 'order-1',
    accountId: 'mock-account',
    contractId: 'ESM25',
    symbol: 'ESM25',
    side: 'Buy',
    type: 'Limit',
    status: 'Working',
    price: 4495.25,
    quantity: 1,
    filledQuantity: 0.25,
    submitted: Date.now() / 1000 - 600,
  },
  {
    id: 'order-2',
    accountId: 'mock-account',
    contractId: 'NQH25',
    symbol: 'NQH25',
    side: 'Sell',
    type: 'Stop',
    status: 'Accepted',
    price: 15920.0,
    quantity: 1,
    filledQuantity: 0,
    submitted: Date.now() / 1000 - 1200,
  },
];

const workspacePages = [
  {
    id: 'terminal',
    label: 'Trading Terminal',
    description: 'Live market view with active charting tools',
  },
  {
    id: 'strategy',
    label: 'Strategy Analytics',
    description: 'Performance metrics and tester insights',
  },
  {
    id: 'behavior',
    label: 'Price Behavior',
    description: 'Behavioral studies and pattern explorer',
  },
];

function App() {
  const [symbol, setSymbol] = useState('ESM25');
  const [timeframe, setTimeframe] = useState('5m');
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [activePage, setActivePage] = useState<string>(workspacePages[0].id);
  const [candles, setCandles] = useState<Candle[]>(mockCandles);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([{ symbol: 'ESM25', name: 'E-Mini S&P 500' }]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refreshData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [candlesResponse, dashboardResponse] = await Promise.all([
        fetchCandles(symbol, timeframe, 500),
        fetchDashboard(symbol, timeframe),
      ]);

      setCandles(candlesResponse.candles ?? []);
      setDashboard(dashboardResponse);

      const derivedContracts: Contract[] = [];
      if (candlesResponse.contract) {
        derivedContracts.push({
          symbol: candlesResponse.contract.symbol,
          name: candlesResponse.contract.name ?? candlesResponse.contract.symbol,
          description: candlesResponse.contract.description,
          exchange: candlesResponse.contract.exchange,
        });
      }

      const watchlistContracts: Contract[] = (dashboardResponse.watchlist ?? []).map((item) => ({
        symbol: item.symbol,
        name: item.symbol,
      }));

      const uniqueContracts = [...derivedContracts, ...watchlistContracts].reduce<Contract[]>((acc, contract) => {
        if (!acc.some((existing) => existing.symbol === contract.symbol)) {
          acc.push(contract);
        }
        return acc;
      }, []);

      setContracts(uniqueContracts.length > 0 ? uniqueContracts : [{ symbol, name: symbol }]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load live data. Showing cached values.';
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    void refreshData();
  }, [refreshData]);

  const sidebarWatchlist = useMemo<WatchlistItem[]>(
    () => dashboard?.watchlist ?? mockWatchlist,
    [dashboard?.watchlist],
  );

  const sidebarAlerts = useMemo<AlertItem[]>(
    () => dashboard?.alerts ?? mockAlerts,
    [dashboard?.alerts],
  );

  const sidebarPositions = useMemo<PositionSnapshot[]>(
    () => dashboard?.positions ?? mockPositions,
    [dashboard?.positions],
  );

  const sidebarTrades = useMemo<TradeRecord[]>(
    () => dashboard?.trades ?? mockTrades,
    [dashboard?.trades],
  );

  const sidebarOrders = useMemo<OrderRecord[]>(
    () => dashboard?.orders ?? mockOrders,
    [dashboard?.orders],
  );

  const activeAccount = useMemo<AccountSummary | null>(
    () => dashboard?.activeAccount ?? dashboard?.accounts?.[0] ?? mockAccount,
    [dashboard?.activeAccount, dashboard?.accounts],
  );

  const activeMetrics = useMemo<MetricsSummary | null>(
    () => dashboard?.metrics ?? mockMetrics,
    [dashboard?.metrics],
  );

  const renderWorkspace = () => {
    switch (activePage) {
      case 'strategy':
        return (
          <Suspense
            fallback={
              <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
                Loading strategy analytics…
              </div>
            }
          >
            <div className="flex flex-1 flex-col overflow-hidden p-6">
              <StrategyPanel strategyResult={mockStrategyResult} layout="full" />
            </div>
          </Suspense>
        );
      case 'behavior':
        return (
          <Suspense
            fallback={
              <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
                Loading behavior analytics…
              </div>
            }
          >
            <div className="flex flex-1 flex-col gap-6 p-6">
              <StrategyPanel strategyResult={mockStrategyResult} layout="full" />
              <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-border/40 text-sm text-muted-foreground">
                Behavioral analytics module coming soon.
              </div>
            </div>
          </Suspense>
        );
      case 'terminal':
      default:
        return (
          <Suspense
            fallback={
              <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
                Loading chart workspace…
              </div>
            }
          >
            <ChartArea
              candles={candles}
              symbol={symbol}
              timeframe={timeframe}
              activeTool={activeTool}
              isLoading={isLoading}
              onRefresh={refreshData}
              errorMessage={errorMessage}
            />
          </Suspense>
        );
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <TopNavigation
        onSymbolChange={setSymbol}
        onTimeframeChange={setTimeframe}
        currentSymbol={symbol}
        currentTimeframe={timeframe}
        pages={workspacePages}
        currentPage={activePage}
        onPageChange={setActivePage}
        contracts={contracts}
        account={activeAccount}
        metrics={activeMetrics}
        onRefresh={refreshData}
      />

      <div className="flex flex-1 overflow-hidden">
        <Suspense
          fallback={
            <aside
              className="flex w-16 flex-col border-r border-border/60 bg-sidebar/80"
              aria-label="Loading tools"
              aria-busy="true"
            />
          }
        >
          <LeftSidebar activeTool={activeTool} onToolSelect={setActiveTool} />
        </Suspense>

        <div className="flex flex-col flex-1 bg-gradient-to-b from-slate-900/30 via-transparent to-slate-900/60 border-x border-border min-h-0">
          {renderWorkspace()}
        </div>

        <Suspense
          fallback={
            <aside
              className="hidden w-80 flex-col border-l border-border/60 bg-sidebar/80 lg:flex"
              aria-label="Loading market data"
              aria-busy="true"
            />
          }
        >
          <RightSidebar
            watchlist={sidebarWatchlist}
            alerts={sidebarAlerts}
            account={activeAccount}
            metrics={activeMetrics}
            positions={sidebarPositions}
            orders={sidebarOrders}
            trades={sidebarTrades}
            onSymbolSelect={setSymbol}
            isLoading={isLoading}
          />
        </Suspense>
      </div>
    </div>
  );
}

export default App;
