import { Button } from '@/components/ui/button';
import { Pen, Square, TrendingUp, Bell } from 'lucide-react';

interface LeftSidebarProps {
  activeTool: string | null;
  onToolSelect: (tool: string | null) => void;
}

const tools = [
  { id: 'draw', icon: Pen, label: 'Draw' },
  { id: 'measure', icon: Square, label: 'Measure' },
  { id: 'trendline', icon: TrendingUp, label: 'Trendline' },
  { id: 'alert', icon: Bell, label: 'Alert' },
];

export function LeftSidebar({ activeTool, onToolSelect }: LeftSidebarProps) {
  return (
    <aside className="flex w-16 flex-col justify-between border-r border-border/60 bg-sidebar/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3 py-6">
        <span className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Tools</span>
        <div className="flex flex-col items-center gap-2">
          {tools.map((tool) => {
            const isActive = activeTool === tool.id;
            return (
              <Button
                key={tool.id}
                variant="ghost"
                size="icon"
                className={`h-11 w-11 rounded-xl border border-transparent text-muted-foreground transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/30'
                    : 'hover:border-border/60 hover:bg-secondary/40 hover:text-foreground'
                }`}
                onClick={() => onToolSelect(isActive ? null : tool.id)}
                title={tool.label}
              >
                <tool.icon className="h-5 w-5" />
              </Button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col items-center gap-1 pb-6 text-[10px] text-muted-foreground">
        <span className="font-medium tracking-[0.3em] uppercase">v1.0</span>
        <span className="tracking-wide">Utilities</span>
      </div>
    </aside>
  );
}