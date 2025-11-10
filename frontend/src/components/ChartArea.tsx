import { useEffect, useMemo, useRef, useState } from 'react';
import { CandlestickSeries, LineSeries, createChart } from 'lightweight-charts';
import type { CandlestickData, ISeriesApi, LineData, UTCTimestamp } from 'lightweight-charts';
import type { Candle } from '@/types';

interface ChartAreaProps {
  candles: Candle[];
  symbol: string;
  timeframe: string;
  activeTool?: string | null;
  isLoading?: boolean;
  onRefresh?: () => void;
  errorMessage?: string | null;
}

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

export function ChartArea({
  candles,
  symbol,
  timeframe,
  activeTool = null,
  isLoading = false,
  onRefresh,
  errorMessage,
}: ChartAreaProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ema20SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const vwapSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  const [showEMA20, setShowEMA20] = useState(true);
  const [showEMA50, setShowEMA50] = useState(false);
  const [showVWAP, setShowVWAP] = useState(false);

  const latestCandle = useMemo(() => candles[candles.length - 1], [candles]);
  const previousCandle = useMemo(() => candles[candles.length - 2], [candles]);
  const change = latestCandle && previousCandle ? latestCandle.close - previousCandle.close : 0;
  const changePct = latestCandle && previousCandle ? (change / previousCandle.close) * 100 : 0;

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#131313' },
        textColor: '#E2E8F0',
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: '#1F2937' },
        horzLines: { color: '#1F2937' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#1F2937',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#1F2937',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#38d39f',
      wickDownColor: '#f87171',
      priceLineVisible: true,
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;

    return () => {
      ema20SeriesRef.current = null;
      ema50SeriesRef.current = null;
      vwapSeriesRef.current = null;
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!candlestickSeriesRef.current) return;

    const data: CandlestickData[] = candles.map((candle) => ({
      time: Math.floor(candle.time) as UTCTimestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    candlestickSeriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [candles, symbol, timeframe]);

  const ema20Data = useMemo(() => computeEMA(candles, 20), [candles]);
  const ema50Data = useMemo(() => computeEMA(candles, 50), [candles]);
  const vwapData = useMemo(() => computeVWAP(candles), [candles]);

  useEffect(() => {
    if (!chartRef.current) return;

    if (showEMA20 && ema20Data.length) {
      if (!ema20SeriesRef.current) {
        ema20SeriesRef.current = chartRef.current.addSeries(LineSeries, {
          color: '#38bdf8',
          lineWidth: 2,
          priceLineVisible: false,
          title: 'EMA 20',
        });
      }
      ema20SeriesRef.current.setData(ema20Data);
    } else if (ema20SeriesRef.current) {
      chartRef.current.removeSeries(ema20SeriesRef.current);
      ema20SeriesRef.current = null;
    }
  }, [showEMA20, ema20Data]);

  useEffect(() => {
    if (!chartRef.current) return;

    if (showEMA50 && ema50Data.length) {
      if (!ema50SeriesRef.current) {
        ema50SeriesRef.current = chartRef.current.addSeries(LineSeries, {
          color: '#a855f7',
          lineWidth: 2,
          priceLineVisible: false,
          title: 'EMA 50',
        });
      }
      ema50SeriesRef.current.setData(ema50Data);
    } else if (ema50SeriesRef.current) {
      chartRef.current.removeSeries(ema50SeriesRef.current);
      ema50SeriesRef.current = null;
    }
  }, [showEMA50, ema50Data]);

  useEffect(() => {
    if (!chartRef.current) return;

    if (showVWAP && vwapData.length) {
      if (!vwapSeriesRef.current) {
        vwapSeriesRef.current = chartRef.current.addSeries(LineSeries, {
          color: '#22c55e',
          lineWidth: 2,
          priceLineVisible: false,
          title: 'VWAP',
        });
      }
      vwapSeriesRef.current.setData(vwapData);
    } else if (vwapSeriesRef.current) {
      chartRef.current.removeSeries(vwapSeriesRef.current);
      vwapSeriesRef.current = null;
    }
  }, [showVWAP, vwapData]);

  useEffect(() => {
    if (!chartRef.current || !chartContainerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chartRef.current?.resize(width, height);
      }
    });

    resizeObserver.observe(chartContainerRef.current);

    return () => resizeObserver.disconnect();
  }, []);

  const statBlocks = [
    { label: 'Open', value: latestCandle ? latestCandle.open.toFixed(2) : '--' },
    { label: 'High', value: latestCandle ? latestCandle.high.toFixed(2) : '--' },
    { label: 'Low', value: latestCandle ? latestCandle.low.toFixed(2) : '--' },
    { label: 'Close', value: latestCandle ? latestCandle.close.toFixed(2) : '--' },
    { label: 'Volume', value: latestCandle ? latestCandle.volume.toLocaleString() : '--' },
  ];

  const hasCandles = candles.length > 0;

  return (
    <section className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-border/30 px-6 py-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline gap-3">
            <span className="font-display text-3xl tracking-tight text-foreground">{symbol}</span>
            <span className="rounded-full border border-primary/40 bg-primary/10 px-3 py-0.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary">
              {timeframe}
            </span>
            <span className={`font-display text-lg ${change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {latestCandle ? latestCandle.close.toFixed(2) : '--'}
              <span className="ml-2 text-xs font-normal text-muted-foreground">
                {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%)
              </span>
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            Last update {latestCandle ? dateFormatter.format(new Date(latestCandle.time * 1000)) : '—'}
          </span>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex flex-col gap-2 text-xs text-muted-foreground">
            <span className="text-label text-[10px] uppercase tracking-[0.3em] text-muted-foreground/70">Indicators</span>
            <div className="flex items-center gap-2">
              <IndicatorToggle
                label="EMA 20"
                colorClass="bg-sky-500/80"
                active={showEMA20}
                onClick={() => setShowEMA20((prev) => !prev)}
                disabled={!hasCandles}
              />
              <IndicatorToggle
                label="EMA 50"
                colorClass="bg-fuchsia-500/80"
                active={showEMA50}
                onClick={() => setShowEMA50((prev) => !prev)}
                disabled={!hasCandles}
              />
              <IndicatorToggle
                label="VWAP"
                colorClass="bg-emerald-500/80"
                active={showVWAP}
                onClick={() => setShowVWAP((prev) => !prev)}
                disabled={!hasCandles}
              />
            </div>
          </div>

          <div className="grid grid-cols-5 gap-4 text-xs text-muted-foreground">
            {statBlocks.map((stat) => (
              <div key={stat.label} className="flex flex-col items-start">
                <span className="text-label text-[10px] text-muted-foreground/70">{stat.label}</span>
                <span className="font-medium text-foreground/80">{stat.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="relative flex flex-1 flex-col overflow-hidden">
        {activeTool && (
          <div className="pointer-events-none absolute left-6 top-6 z-20 rounded-full border border-border/50 bg-background/80 px-4 py-1 text-[11px] font-medium uppercase tracking-[0.32em] text-muted-foreground">
            {activeTool} tool active
          </div>
        )}

        {isLoading && !hasCandles && (
          <div className="absolute inset-0 z-30 flex items-center justify-center bg-background/60 backdrop-blur">
            <span className="text-xs uppercase tracking-[0.28em] text-muted-foreground">Loading market data…</span>
          </div>
        )}

        {isLoading && hasCandles && (
          <div className="pointer-events-none absolute right-6 top-6 z-20 rounded-full border border-border/40 bg-background/80 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.3em] text-muted-foreground">
            Refreshing…
          </div>
        )}

        {!isLoading && !hasCandles && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 bg-background/40 backdrop-blur-sm">
            <span className="text-sm text-muted-foreground">{errorMessage ?? `No candles available for ${symbol}.`}</span>
            {onRefresh ? (
              <button
                type="button"
                onClick={onRefresh}
                className="rounded-full border border-border/60 bg-secondary/40 px-4 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-foreground hover:border-primary/40 hover:bg-primary/10"
              >
                Retry
              </button>
            ) : null}
          </div>
        )}

        <div ref={chartContainerRef} className="flex-1" />
      </div>
    </section>
  );
}

interface IndicatorToggleProps {
  label: string;
  colorClass: string;
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function IndicatorToggle({ label, colorClass, active, onClick, disabled = false }: IndicatorToggleProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      className={`flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] transition-colors ${
        disabled
          ? 'cursor-not-allowed border-border/40 bg-secondary/30 text-muted-foreground/70 opacity-60'
          : active
            ? 'border-transparent bg-primary text-primary-foreground shadow-lg shadow-primary/20'
            : 'border-border/60 bg-secondary/50 text-muted-foreground hover:border-border hover:text-foreground'
      }`}
    >
      <span className={`h-2.5 w-2.5 rounded-full ${colorClass}`} />
      {label}
    </button>
  );
}

function computeEMA(candles: Candle[], period: number): LineData[] {
  if (!candles.length || period <= 0) return [];

  const k = 2 / (period + 1);
  let ema = candles[0].close;
  const data: LineData[] = [];

  candles.forEach((candle, index) => {
    const price = candle.close;
    if (index === 0) {
      ema = price;
    } else {
      ema = price * k + ema * (1 - k);
    }

    if (index >= period - 1) {
      data.push({ time: Math.floor(candle.time) as UTCTimestamp, value: Number(ema.toFixed(2)) });
    }
  });

  return data;
}

function computeVWAP(candles: Candle[]): LineData[] {
  if (!candles.length) return [];

  let cumulativePV = 0;
  let cumulativeVolume = 0;
  const data: LineData[] = [];

  candles.forEach((candle) => {
    const typicalPrice = (candle.high + candle.low + candle.close) / 3;
    cumulativePV += typicalPrice * candle.volume;
    cumulativeVolume += candle.volume;

    if (cumulativeVolume > 0) {
      const vwap = cumulativePV / cumulativeVolume;
      data.push({ time: Math.floor(candle.time) as UTCTimestamp, value: Number(vwap.toFixed(2)) });
    }
  });

  return data;
}