import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { StrategyResult } from '@/types';

function buildSparkline(values: number[], width = 260, height = 80) {
  if (!values.length) {
    return { line: '', area: '' };
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);
  const step = values.length > 1 ? width / (values.length - 1) : width;

  const coordinates = values.map((value, index) => {
    const x = Number((index * step).toFixed(2));
    const y = Number((height - ((value - min) / range) * height).toFixed(2));
    return `${x},${y}`;
  });

  const line = `M ${coordinates.join(' L ')}`;
  const area = `M 0 ${height} L ${coordinates.join(' L ')} L ${width} ${height} Z`;

  return { line, area };
}

interface StrategyPanelProps {
  strategyResult: StrategyResult | null;
  layout?: 'compact' | 'full';
}

export function StrategyPanel({ strategyResult, layout = 'compact' }: StrategyPanelProps) {
  const safeResult: StrategyResult =
    strategyResult ?? { profitPct: 0, equityCurve: [], trades: [] };

  const { profitPct, equityCurve, trades } = safeResult;
  const equityDelta = equityCurve.length >= 2 ? equityCurve[equityCurve.length - 1] - equityCurve[0] : 0;
  const averageEquity = equityCurve.length > 0 ? equityCurve.reduce((sum, value) => sum + value, 0) / equityCurve.length : 0;
  const { line: equitySparkLine, area: equitySparkArea } = useMemo(() => buildSparkline(equityCurve), [equityCurve]);

  if (!strategyResult) {
    return (
      <div className="h-64 bg-background border-t border-border p-4">
        <p className="text-muted-foreground">No strategy data available</p>
      </div>
    );
  }

  const containerClasses =
    layout === 'full'
      ? 'flex flex-1 flex-col overflow-hidden rounded-2xl border border-border/40 bg-background/95'
      : 'h-64 border-t border-border bg-background/95';

  const tabsClasses = layout === 'full' ? 'flex h-full flex-col' : 'h-full';
  const testerContentClasses = layout === 'full' ? 'flex-1 space-y-4 overflow-auto p-6' : 'h-full space-y-4 p-4';
  const secondaryContentClasses = layout === 'full' ? 'flex flex-1 p-6' : 'h-full p-4';
  const placeholderPanelClasses =
    layout === 'full'
      ? 'flex flex-1 items-center justify-center rounded-xl border border-border/40 bg-secondary/40'
      : 'flex h-full items-center justify-center rounded-xl border border-border/40 bg-secondary/40';
  const equityPanelClasses =
    layout === 'full'
      ? 'relative h-48 overflow-hidden rounded-xl border border-border/40 bg-secondary/40 p-6'
      : 'relative h-32 overflow-hidden rounded-xl border border-border/40 bg-secondary/40 p-4';

  return (
    <div className={containerClasses}>
      <Tabs defaultValue="tester" className={tabsClasses}>
        <TabsList className="grid w-full grid-cols-3 bg-transparent">
          <TabsTrigger value="tester" className="font-display text-xs tracking-[0.2em] uppercase">Strategy Tester</TabsTrigger>
          <TabsTrigger value="behavior" className="font-display text-xs tracking-[0.2em] uppercase">Price Behavior</TabsTrigger>
          <TabsTrigger value="performance" className="font-display text-xs tracking-[0.2em] uppercase">Performance Chart</TabsTrigger>
        </TabsList>

        <TabsContent value="tester" className={testerContentClasses}>
          <div className="grid grid-cols-4 gap-4">
            <Card className="border-border/40 bg-secondary/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-xs uppercase tracking-[0.25em] text-muted-foreground">Net Profit</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-display text-2xl text-emerald-400">
                  +{profitPct.toFixed(2)}%
                </div>
              </CardContent>
            </Card>
            <Card className="border-border/40 bg-secondary/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-xs uppercase tracking-[0.25em] text-muted-foreground"># of Trades</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-display text-2xl text-foreground/90">{trades.length}</div>
              </CardContent>
            </Card>
            <Card className="border-border/40 bg-secondary/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-xs uppercase tracking-[0.25em] text-muted-foreground">Avg Win %</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-display text-2xl text-emerald-400">
                  {(Math.max(equityDelta, 0) / Math.max(averageEquity, 1)).toFixed(2)}%
                </div>
              </CardContent>
            </Card>
            <Card className="border-border/40 bg-secondary/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-xs uppercase tracking-[0.25em] text-muted-foreground">Avg Loss %</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-display text-2xl text-rose-400">
                  {(-Math.min(equityDelta, 0) / Math.max(averageEquity, 1)).toFixed(2)}%
                </div>
              </CardContent>
            </Card>
          </div>

          <div className={equityPanelClasses}>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span className="text-label text-[10px]">Equity Curve</span>
              <span className="font-medium text-foreground/70">Last {equityCurve.length} trades</span>
            </div>
            <svg viewBox="0 0 260 80" className="mt-2 h-full w-full">
              <defs>
                <linearGradient id="equityGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="rgba(38,166,154,0.35)" />
                  <stop offset="100%" stopColor="rgba(38,166,154,0)" />
                </linearGradient>
              </defs>
              <path d={equitySparkArea} fill="url(#equityGradient)" />
              <path d={equitySparkLine} fill="none" stroke="#26a69a" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div className="absolute bottom-3 left-4 flex gap-6 text-xs text-muted-foreground">
              <div>
                <span className="block text-[10px] uppercase tracking-[0.2em]">Start</span>
                <span className="font-medium text-foreground/80">${equityCurve[0]?.toLocaleString(undefined, { maximumFractionDigits: 0 }) ?? '--'}</span>
              </div>
              <div>
                <span className="block text-[10px] uppercase tracking-[0.2em]">Current</span>
                <span className="font-medium text-foreground/80">${equityCurve[equityCurve.length - 1]?.toLocaleString(undefined, { maximumFractionDigits: 0 }) ?? '--'}</span>
              </div>
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="font-display text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Entry Date</TableHead>
                <TableHead className="font-display text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Exit Date</TableHead>
                <TableHead className="font-display text-[11px] uppercase tracking-[0.2em] text-muted-foreground">P/L %</TableHead>
                <TableHead className="font-display text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Type</TableHead>
                <TableHead className="font-display text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Duration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.slice(0, 5).map((trade) => (
                <TableRow key={trade.id} className="border-border/40">
                  <TableCell className="text-sm text-foreground/80">
                    {trade.timestamp ? new Date(trade.timestamp).toLocaleDateString() : '--'}
                  </TableCell>
                  <TableCell className="text-sm text-foreground/80">
                    {trade.timestamp ? new Date(trade.timestamp + 86400000).toLocaleDateString() : '--'}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={trade.type === 'Buy' ? 'default' : 'destructive'}
                      className="font-display text-[11px] uppercase tracking-[0.18em]"
                    >
                      {trade.type === 'Buy' ? '+' : '-'}{(Math.random() * 5).toFixed(2)}%
                    </Badge>
                  </TableCell>
                  <TableCell>{trade.type}</TableCell>
                  <TableCell>1d</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="behavior" className={secondaryContentClasses}>
          <div className={placeholderPanelClasses}>
            <p className="font-display text-sm tracking-[0.2em] text-muted-foreground">Price Behavior Explorer</p>
          </div>
        </TabsContent>

        <TabsContent value="performance" className={secondaryContentClasses}>
          <div className={placeholderPanelClasses}>
            <p className="font-display text-sm tracking-[0.2em] text-muted-foreground">Performance Chart</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}