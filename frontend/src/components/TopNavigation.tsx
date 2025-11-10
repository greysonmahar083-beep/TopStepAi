import { useMemo, useState } from 'react';
import { Search, Settings, Bell, Sun, Moon, Signal, Wallet, RefreshCcw, ChevronsUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import type { AccountSummary, Contract, MetricsSummary } from '@/types';

interface WorkspacePage {
  id: string;
  label: string;
  description?: string;
}

interface TopNavigationProps {
  onSymbolChange: (symbol: string) => void;
  onTimeframeChange: (timeframe: string) => void;
  currentSymbol: string;
  currentTimeframe: string;
  pages: WorkspacePage[];
  currentPage: string;
  onPageChange: (pageId: string) => void;
  contracts: Contract[];
  account?: AccountSummary | null;
  metrics?: MetricsSummary | null;
  onRefresh?: () => void;
}

const timeframeOptions = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: 'D' },
  { value: '1w', label: 'W' },
];

export function TopNavigation({
  onSymbolChange,
  onTimeframeChange,
  currentSymbol,
  currentTimeframe,
  pages,
  currentPage,
  onPageChange,
  contracts,
  account,
  metrics,
  onRefresh,
}: TopNavigationProps) {
  const [open, setOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  const contractOptions = useMemo<Contract[]>(() => {
    if (contracts.length > 0) {
      return contracts;
    }
    return [{ symbol: currentSymbol, name: currentSymbol }];
  }, [contracts, currentSymbol]);

  const selectedContract = contractOptions.find((contract) => contract.symbol === currentSymbol) ?? contractOptions[0];
  const selectedWorkspace = pages.find((page) => page.id === currentPage);
  const activeThemeIcon = theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />;

  const currencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }),
    [],
  );

  const equityDisplay = account ? currencyFormatter.format(account.balance) : '—';
  const dayPnlValue = metrics?.dayPnl;
  const dayPnlDisplay = account && dayPnlValue !== undefined ? currencyFormatter.format(dayPnlValue) : '—';
  const dayPnlClass = dayPnlValue !== undefined
    ? dayPnlValue > 0
      ? 'text-emerald-400'
      : dayPnlValue < 0
        ? 'text-rose-400'
        : 'text-muted-foreground'
    : 'text-muted-foreground';
  const openRiskValue = metrics?.openRisk;
  const openRiskDisplay = openRiskValue !== undefined ? currencyFormatter.format(openRiskValue) : '—';

  return (
    <header className="border-b border-border/50 bg-gradient-to-b from-background/95 via-background/80 to-background/60 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6">
        {/* Left Zone */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/90 text-sm font-semibold uppercase text-primary-foreground shadow-lg shadow-primary/20">
              TS
            </div>
            <div className="flex flex-col leading-tight">
              <span className="font-display text-sm text-foreground/90">TopstepX Terminal</span>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <span className="relative flex h-2 w-2 items-center justify-center">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400"></span>
                </span>
                MTPA Connected
              </span>
            </div>
          </div>

          <div className="hidden items-center gap-3 rounded-xl border border-border/60 bg-secondary/20 px-4 py-2 text-xs text-muted-foreground sm:flex">
            <Wallet className="h-4 w-4" />
            <div className="flex flex-col leading-tight">
              <span className="text-[10px] uppercase tracking-[0.32em] text-muted-foreground">Account</span>
              <span className="font-medium text-foreground/90">{account?.name ?? 'Link account'}</span>
            </div>
            <div className="flex flex-col leading-tight text-right">
              <span className="text-[10px] uppercase tracking-[0.32em] text-muted-foreground">Equity</span>
              <span className="font-semibold text-foreground/90">{equityDisplay}</span>
            </div>
            <div className="flex flex-col leading-tight text-right">
              <span className="text-[10px] uppercase tracking-[0.32em] text-muted-foreground">Day P/L</span>
              <span className={`font-semibold ${dayPnlClass}`}>{dayPnlDisplay}</span>
            </div>
          </div>
        </div>

        {/* Center Zone */}
        <div className="flex items-center gap-4">
          {pages.length > 0 && (
            <Popover open={workspaceOpen} onOpenChange={setWorkspaceOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex w-[220px] items-center justify-between rounded-xl border border-border/60 bg-secondary/20 px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
                >
                  <span className="font-display text-sm tracking-tight text-foreground/90">
                    {selectedWorkspace?.label ?? 'Select workspace'}
                  </span>
                  <ChevronsUpDown className="h-4 w-4 opacity-60" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[240px] rounded-xl border-border/80 bg-background/95 p-0 backdrop-blur-xl">
                <Command>
                  <CommandInput placeholder="Search workspaces..." />
                  <CommandList>
                    <CommandEmpty>No workspaces found.</CommandEmpty>
                    <CommandGroup>
                      {pages.map((page) => (
                        <CommandItem
                          key={page.id}
                          value={page.id}
                          onSelect={() => {
                            onPageChange(page.id);
                            setWorkspaceOpen(false);
                          }}
                        >
                          <div className="flex flex-col">
                            <span className="font-display text-sm tracking-tight text-foreground">{page.label}</span>
                            {page.description ? (
                              <span className="text-xs text-muted-foreground">{page.description}</span>
                            ) : null}
                          </div>
                          {currentPage === page.id ? (
                            <span className="ml-auto text-[10px] uppercase tracking-[0.2em] text-primary">Active</span>
                          ) : null}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          )}

          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={open}
                className="w-[240px] justify-between rounded-xl border-border/70 bg-secondary/30/80 px-4 py-2 hover:bg-secondary/50"
              >
                <div className="flex flex-col items-start">
                  <span className="font-display text-base tracking-tight">{selectedContract?.symbol || 'Select symbol'}</span>
                  <span className="text-xs text-muted-foreground">
                    {(selectedContract?.name ?? selectedContract?.description ?? 'Choose contract')}
                    {selectedContract?.exchange ? ` · ${selectedContract.exchange}` : ''}
                  </span>
                </div>
                <Search className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[240px] rounded-xl border-border/80 bg-background/95 p-0 backdrop-blur-xl">
              <Command>
                <CommandInput placeholder="Search contracts..." />
                <CommandList>
                  <CommandEmpty>No contracts found.</CommandEmpty>
                  <CommandGroup>
                    {contractOptions.map((contract) => (
                      <CommandItem
                        key={contract.symbol}
                        value={contract.symbol}
                        onSelect={() => {
                          onSymbolChange(contract.symbol);
                          setOpen(false);
                        }}
                      >
                        <div className="flex flex-col">
                          <span className="font-display text-sm tracking-tight text-foreground">{contract.symbol}</span>
                          <span className="text-xs text-muted-foreground">{contract.name} · {contract.exchange}</span>
                        </div>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          <div className="flex rounded-full border border-border/60 bg-secondary/30 p-1">
            {timeframeOptions.map(({ value, label }) => {
              const isActive = currentTimeframe.toLowerCase() === value.toLowerCase();
              const variantClass = isActive
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-secondary/40 hover:text-foreground';

              return (
                <Button
                  key={value}
                  variant="ghost"
                  size="sm"
                  className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] transition-colors duration-150 ${variantClass}`}
                  onClick={() => onTimeframeChange(value)}
                >
                  {label}
                </Button>
              );
            })}
          </div>
        </div>

        {/* Right Zone */}
        <div className="flex items-center gap-1.5">
          <div className="hidden items-center gap-2 rounded-xl border border-border/60 bg-secondary/20 px-3 py-1.5 text-[11px] uppercase tracking-[0.28em] text-muted-foreground lg:flex">
            <span>Open Risk</span>
            <span className="font-semibold text-foreground/80">{openRiskDisplay}</span>
          </div>
          {onRefresh ? (
            <Button
              variant="ghost"
              size="icon"
              className="rounded-xl border border-transparent text-muted-foreground hover:border-border/60 hover:bg-secondary/40"
              onClick={onRefresh}
              title="Refresh data"
            >
              <RefreshCcw className="h-4 w-4" />
            </Button>
          ) : null}
          <Button
            variant="ghost"
            size="icon"
            className="rounded-xl border border-transparent text-muted-foreground hover:border-border/60 hover:bg-secondary/40"
            title={`Open risk ${openRiskDisplay}`}
          >
            <Signal className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="rounded-xl border border-transparent text-muted-foreground hover-border-border/60 hover:bg-secondary/40">
            <Settings className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="rounded-xl border border-transparent text-muted-foreground hover-border-border/60 hover:bg-secondary/40">
            <Bell className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-xl border border-transparent text-muted-foreground hover-border-border/60 hover:bg-secondary/40"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            {activeThemeIcon}
          </Button>
        </div>
      </div>
    </header>
  );
}
