'use client';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ValidationEvent, ValidationStage, ValidationStatus } from '@/lib/types';
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import type { ReactNode } from 'react';

interface ValidationEventsProps {
  events: ValidationEvent[];
}

const stageLabels: Record<ValidationStage, string> = {
  started: 'Transaction Started',
  intent_analysis: 'Intent Analysis',
  policy_validation: 'Policy Validation',
  simulation: 'Simulation',
  honeypot_detection: 'Honeypot Detection',
  llm_validation: 'LLM Validation',
  completed: 'Completed',
};

const statusConfig: Record<
  ValidationStatus,
  { icon: ReactNode; variant: 'default' | 'secondary' | 'destructive' | 'warning' | 'outline' }
> = {
  started: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    variant: 'secondary',
  },
  passed: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    variant: 'secondary',
  },
  failed: {
    icon: <XCircle className="h-4 w-4 text-destructive" />,
    variant: 'destructive',
  },
  warning: {
    icon: <AlertTriangle className="h-4 w-4 text-yellow-600" />,
    variant: 'warning',
  },
  info: {
    icon: <Info className="h-4 w-4" />,
    variant: 'secondary',
  },
};

export function ValidationEvents({ events }: ValidationEventsProps) {
  if (!events || events.length === 0) return null;

  // Determine overall status
  const hasFailure = events.some((e) => e.status === 'failed');
  const completedEvent = events.find((e) => e.stage === 'completed');

  return (
    <Card className="mt-3">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Avatar className="h-5 w-5">
              <AvatarFallback className="bg-zinc-900 text-zinc-50">
                <ShieldCheck className="h-3 w-3" />
              </AvatarFallback>
            </Avatar>
            AgentARC Validation
          </CardTitle>
          {completedEvent && (
            <Badge variant={hasFailure ? 'destructive' : 'secondary'}>
              {hasFailure ? 'BLOCKED' : 'APPROVED'}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {events.map((event, idx) => {
          const config = statusConfig[event.status];
          return (
            <div
              key={idx}
              className="rounded-lg p-3 border bg-muted/50"
            >
              <div className="flex items-start gap-2">
                <span className="text-muted-foreground mt-0.5">{config.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-foreground">
                      {stageLabels[event.stage] || event.stage}
                    </span>
                    <span className="text-xs text-muted-foreground shrink-0 tabular-nums">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {event.message}
                  </div>

                  {event.details && Object.keys(event.details).length > 0 && (
                    <EventDetails details={event.details} status={event.status} />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function EventDetails({
  details,
}: {
  details: Record<string, unknown>;
  status: ValidationStatus;
}) {
  const relevantKeys = [
    'to',
    'value_eth',
    'gas_used',
    'function',
    'rule',
    'is_honeypot',
    'reason',
    'confidence',
    'risk_level',
    'indicators',
  ];

  const filteredDetails = Object.entries(details).filter(([key]) =>
    relevantKeys.includes(key)
  );

  if (filteredDetails.length === 0) return null;

  return (
    <div className="mt-2 pt-2 border-t border-border">
      <div className="flex flex-wrap gap-1.5">
        {filteredDetails.map(([key, value]) => (
          <DetailBadge key={key} label={key} value={value} />
        ))}
      </div>
    </div>
  );
}

function DetailBadge({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  const formatLabel = (l: string) =>
    l.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const formatValue = (v: unknown): string => {
    if (typeof v === 'boolean') return v ? 'Yes' : 'No';
    if (typeof v === 'number') {
      if (label.includes('eth')) return `${v} ETH`;
      if (label.includes('gas')) return v.toLocaleString();
      return String(v);
    }
    if (Array.isArray(v)) return v.join(', ');
    if (typeof v === 'string') {
      // Truncate long addresses
      if (v.startsWith('0x') && v.length > 15) {
        return `${v.slice(0, 8)}…${v.slice(-6)}`;
      }
      return v;
    }
    return String(v);
  };

  return (
    <Badge variant="secondary" className="text-xs font-normal">
      <span className="text-muted-foreground">{formatLabel(label)}:</span>
      <span className="ml-1 font-medium">{formatValue(value)}</span>
    </Badge>
  );
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}
