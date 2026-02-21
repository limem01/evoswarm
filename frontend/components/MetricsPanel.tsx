'use client';

import { useMemo } from 'react';

interface Event {
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

interface MetricsPanelProps {
  events: Event[];
}

export default function MetricsPanel({ events }: MetricsPanelProps) {
  const metrics = useMemo(() => {
    const counts: Record<string, number> = {};
    let tasksCompleted = 0;
    let evolutionRounds = 0;
    let handoffs = 0;
    let errors = 0;

    events.forEach((event) => {
      counts[event.event_type] = (counts[event.event_type] || 0) + 1;

      switch (event.event_type) {
        case 'task_complete':
          tasksCompleted++;
          break;
        case 'evolution_round_end':
          evolutionRounds++;
          break;
        case 'handoff':
          handoffs++;
          break;
        case 'error':
          errors++;
          break;
      }
    });

    return {
      tasksCompleted,
      evolutionRounds,
      handoffs,
      errors,
      totalEvents: events.length,
    };
  }, [events]);

  const statCards = [
    {
      label: 'Tasks Completed',
      value: metrics.tasksCompleted,
      icon: '✅',
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
    },
    {
      label: 'Evolution Rounds',
      value: metrics.evolutionRounds,
      icon: '🧬',
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
    },
    {
      label: 'Agent Handoffs',
      value: metrics.handoffs,
      icon: '🤝',
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
    {
      label: 'Errors',
      value: metrics.errors,
      icon: '❌',
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
    },
  ];

  return (
    <div className="card h-[500px]">
      <div className="card-header">
        <span>📊</span>
        <span>Metrics</span>
      </div>

      <div className="space-y-4">
        {statCards.map((stat) => (
          <div
            key={stat.label}
            className={`${stat.bgColor} rounded-lg p-4 border border-slate-700/50`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">{stat.label}</p>
                <p className={`text-3xl font-bold ${stat.color}`}>
                  {stat.value}
                </p>
              </div>
              <span className="text-3xl">{stat.icon}</span>
            </div>
          </div>
        ))}

        {/* Total Events */}
        <div className="mt-6 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Total Events</span>
            <span className="font-medium text-white">{metrics.totalEvents}</span>
          </div>
        </div>

        {/* Status indicator */}
        <div className="mt-4 p-3 bg-evo-primary/10 rounded-lg border border-evo-primary/30">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-evo-primary rounded-full animate-pulse"></div>
            <span className="text-sm text-evo-primary">System Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
