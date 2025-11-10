import { useMemo } from 'react';
import { ArrowDownRight, ArrowUpRight, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import type {
  AccountSummary,
  AlertItem,
  MetricsSummary,
  PositionSnapshot,
  TradeRecord,
  WatchlistItem,
} from '@/types';
import type { OrderRecord } from '@/types';

interface RightSidebarProps {
  watchlist: WatchlistItem[];
  alerts: AlertItem[];
  account: AccountSummary | null;
  metrics?: MetricsSummary | null;
  positions: PositionSnapshot[];
  orders: OrderRecord[];
  trades: TradeRecord[];
  onSymbolSelect: (symbol: string) => void;
  isLoading?: boolean;
}

function formatTimeAgo(timestamp?: number | null): string {
  if (!timestamp) return '—';
  const now = Date.now();
  const diffMs = now - timestamp * 1000;
  if (diffMs < 60_000) return 'Just now';
  const diffMinutes = Math.floor(diffMs / 60_000);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return new Date(timestamp * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function RightSidebar({
  watchlist,
  alerts,
  account,
  metrics,
  positions,
  orders,
  trades,
  onSymbolSelect,
  isLoading = false,
}: RightSidebarProps) {
  const currencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }),
    [],
  );
  const preciseCurrencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }),
    [],
  );
  const priceFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    [],
  );
  const percentFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    [],
  );

  const openRisk = metrics ? currencyFormatter.format(metrics.openRisk ?? 0) : '—';
  const realizedPnl = account ? currencyFormatter.format(account.realizedPnl ?? 0) : '—';
  const unrealizedPnl = account ? currencyFormatter.format(account.unrealizedPnl ?? 0) : '—';
  const dayPnl = metrics ? currencyFormatter.format(metrics.dayPnl ?? 0) : '—';
  const buyingPower = account ? currencyFormatter.format(account.buyingPower ?? 0) : '—';

  const severityBadge = (severity: AlertItem['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-rose-500/10 text-rose-400 border border-rose-500/30';
      case 'warning':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/30';
      default:
        return 'bg-sky-500/10 text-sky-300 border border-sky-500/20';
    }
  };

  return (
    <aside className="flex w-80 flex-col border-l border-border/40 bg-background/95" aria-busy={isLoading}>
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
        {isLoading ? (
          <div className="rounded-xl border border-border/40 bg-secondary/20 px-3 py-2 text-[11px] uppercase tracking-[0.3em] text-muted-foreground">
            Syncing latest account data…
          </div>
        ) : null}

        <Card className="border-border/40 bg-secondary/30 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-sm tracking-[0.18em] uppercase text-muted-foreground">Account Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {account ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Account</span>
                  <span className="font-medium text-foreground/90">{account.name}</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <MetricTile label="Balance" value={currencyFormatter.format(account.balance ?? 0)} />
                  <MetricTile label="Buying Power" value={buyingPower} />
                  <MetricTile label="Day P/L" value={dayPnl} accentValue={metrics?.dayPnl ?? 0} />
                  <MetricTile label="Open Risk" value={openRisk} />
                  <MetricTile label="Realized" value={realizedPnl} accentValue={account.realizedPnl ?? 0} />
                  <MetricTile label="Unrealized" value={unrealizedPnl} accentValue={account.unrealizedPnl ?? 0} />
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Connect a TopstepX account to activate live data.</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-secondary/30 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-sm tracking-[0.18em] uppercase text-muted-foreground">Open Positions</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {positions.length === 0 ? (
              <div className="px-4 py-6 text-sm text-muted-foreground">No open positions.</div>
            ) : (
              <ScrollArea className="h-40">
                <div className="space-y-2 px-4 py-2">
                  {positions.slice(0, 8).map((position) => {
                    const pnl = position.unrealizedPnl ?? 0;
                    const pnlClass = pnl >= 0 ? 'text-emerald-400' : 'text-rose-400';
                    return (
                      <div
                        key={position.id}
                        className="flex items-center justify-between rounded-lg border border-transparent bg-secondary/20 p-3 transition-colors hover:border-border/50 hover:bg-secondary/35"
                      >
                        <div className="flex flex-col">
                          <span className="font-display text-sm text-foreground">{position.symbol ?? position.contractId ?? '—'}</span>
                          <span className="text-xs text-muted-foreground">
                            {(position.quantity ?? 0).toFixed(2)} @ {priceFormatter.format(position.entryPrice ?? 0)}
                          </span>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className={`font-display text-sm ${pnlClass}`}>{currencyFormatter.format(pnl)}</span>
                          <span className="text-xs text-muted-foreground">
                            Last {priceFormatter.format(position.marketPrice ?? position.entryPrice ?? 0)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-secondary/30 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-sm tracking-[0.18em] uppercase text-muted-foreground">Working Orders</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {orders.length === 0 ? (
              <div className="px-4 py-6 text-sm text-muted-foreground">No working orders.</div>
            ) : (
              <ScrollArea className="h-40">
                <div className="space-y-2 px-4 py-2">
                  {orders.slice(0, 8).map((order) => {
                    const quantity = order.quantity ?? 0;
                    const filled = order.filledQuantity ?? 0;
                    const sideClass = order.side === 'Sell' ? 'text-rose-400' : 'text-emerald-400';
                    return (
                      <div
                        key={order.id}
                        className="flex items-center justify-between rounded-lg border border-transparent bg-secondary/20 p-3 transition-colors hover:border-border/50 hover:bg-secondary/35"
                      >
                        <div className="flex flex-col">
                          <span className="font-display text-sm text-foreground">{order.symbol ?? order.contractId ?? '—'}</span>
                          <span className="text-xs text-muted-foreground">
                            {order.side} {quantity.toFixed(2)} {order.type ? `(${order.type})` : ''}
                          </span>
                        </div>
                        <div className="flex flex-col items-end text-xs text-muted-foreground">
                          <span className={`font-display text-sm ${sideClass}`}>
                            {order.price ? priceFormatter.format(order.price) : 'MKT'}
                          </span>
                          <span>
                            Filled {filled.toFixed(2)} / {quantity.toFixed(2)}
                          </span>
                          <span>{order.status ?? formatTimeAgo(order.submitted)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-secondary/30 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-sm tracking-[0.18em] uppercase text-muted-foreground">Watchlist</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {watchlist.length === 0 ? (
              <div className="px-4 py-6 text-sm text-muted-foreground">Add symbols to your watchlist to track live moves.</div>
            ) : (
              <ScrollArea className="h-56">
                <div className="space-y-2 px-4 py-2">
                  {watchlist.map((item) => {
                    const positive = (item.change ?? 0) >= 0;
                    return (
                      <button
                        key={item.symbol}
                        type="button"
                        onClick={() => onSymbolSelect(item.symbol)}
                        className="group flex w-full items-center justify-between rounded-lg border border-transparent bg-secondary/20 p-3 text-left transition-colors hover:border-border/50 hover:bg-secondary/35"
                      >
                        <div className="flex flex-col">
                          <span className="font-display text-sm text-foreground">{item.symbol}</span>
                          <span className="text-xs text-muted-foreground">{priceFormatter.format(item.last ?? 0)}</span>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className={`font-display text-sm ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {positive ? '+' : ''}{priceFormatter.format(item.change ?? 0)}
                          </span>
                          <span className={`text-xs ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            ({positive ? '+' : ''}{percentFormatter.format(item.changePercent ?? 0)}%)
                          </span>
                          <div className="mt-2 flex items-center gap-1 text-[10px] uppercase tracking-[0.3em] text-muted-foreground/70 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                            <span>Focus</span>
                            <ArrowUpRight className="h-3 w-3" />
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-secondary/30 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-sm tracking-[0.18em] uppercase text-muted-foreground">Recent Trades</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {trades.length === 0 ? (
              <div className="px-4 py-6 text-sm text-muted-foreground">No executions reported yet.</div>
            ) : (
              <ScrollArea className="h-56">
                <div className="space-y-2 px-4 py-2">
                  {trades.slice(0, 12).map((trade) => {
                    const pnl = trade.realizedPnl ?? 0;
                    const positive = pnl >= 0;
                    const Icon = positive ? ArrowUpRight : ArrowDownRight;
                    return (
                      <div
                        key={trade.id}
                        className="flex items-center justify-between rounded-lg border border-transparent bg-secondary/20 p-3 transition-colors hover:border-border/50 hover:bg-secondary/35"
                      >
                        <div className="flex flex-col">
                          <span className="font-display text-sm text-foreground">{trade.symbol ?? trade.contractId ?? '—'}</span>
                          <span className="text-xs text-muted-foreground">
                            {(trade.side ?? '—')} {(trade.quantity ?? 0).toFixed(2)} @ {priceFormatter.format(trade.price ?? 0)}
                          </span>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className={`font-display text-sm ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {preciseCurrencyFormatter.format(pnl)}
                          </span>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Icon className={`h-3.5 w-3.5 ${positive ? 'text-emerald-400' : 'text-rose-400'}`} />
                            <span>{formatTimeAgo(trade.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card className="mb-8 border-border/40 bg-secondary/30 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-sm tracking-[0.18em] uppercase text-muted-foreground">Alerts &amp; Signals</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {alerts.length === 0 ? (
              <div className="px-4 py-6 text-sm text-muted-foreground">No active alerts.</div>
            ) : (
              <ScrollArea className="h-48">
                <div className="space-y-2 px-4 py-2">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start gap-3 rounded-lg border border-transparent bg-secondary/20 p-3 transition-colors hover:border-border/50 hover:bg-secondary/35"
                    >
                      <div className={`flex h-7 w-7 items-center justify-center rounded-full ${severityBadge(alert.severity)} bg-opacity-80`}>
                        <Zap className="h-3.5 w-3.5" />
                      </div>
                      <div className="flex-1">
                        <div className="font-display text-sm text-foreground/90">{alert.description}</div>
                        <div className="text-xs text-muted-foreground">{alert.timeAgo}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </aside>
  );
}

interface MetricTileProps {
  label: string;
  value: string;
  accentValue?: number;
}

function MetricTile({ label, value, accentValue }: MetricTileProps) {
  const accentClass = accentValue === undefined
    ? 'text-foreground/90'
    : accentValue > 0
      ? 'text-emerald-400'
      : accentValue < 0
        ? 'text-rose-400'
        : 'text-muted-foreground';

  return (
    <div className="flex flex-col rounded-lg border border-border/40 bg-background/60 px-3 py-2">
      <span className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground">{label}</span>
      <span className={`font-display text-sm ${accentClass}`}>{value}</span>
    </div>
  );
}

export default RightSidebar;
