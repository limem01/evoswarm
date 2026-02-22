'use client';

import { Bot } from 'lucide-react';

export interface AgentCardData {
  name: string;
  status: 'idle' | 'working' | 'error';
  currentAction?: string;
}

interface AgentCardsProps {
  agents: AgentCardData[];
}

const statusConfig: Record<
  AgentCardData['status'],
  { dot: string; label: string; border: string }
> = {
  idle: {
    dot: 'bg-green-400',
    label: 'Idle',
    border: 'border-green-500/20',
  },
  working: {
    dot: 'bg-yellow-400 animate-pulse',
    label: 'Working',
    border: 'border-yellow-500/20',
  },
  error: {
    dot: 'bg-red-400',
    label: 'Error',
    border: 'border-red-500/20',
  },
};

export default function AgentCards({ agents }: AgentCardsProps) {
  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-500">
        <Bot size={40} className="mb-3" />
        <p className="text-sm">No agents registered</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {agents.map((agent) => {
        const config = statusConfig[agent.status];
        return (
          <div
            key={agent.name}
            className={`card ${config.border} hover:bg-slate-800/70 transition-all duration-200`}
          >
            <div className="flex items-center gap-3 mb-2">
              <Bot size={18} className="text-evo-secondary flex-shrink-0" />
              <h3 className="text-sm font-semibold text-white truncate">
                {agent.name}
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full flex-shrink-0 ${config.dot}`}
              />
              <span className="text-xs text-slate-400">{config.label}</span>
            </div>
            {agent.currentAction && (
              <p className="mt-2 text-xs text-slate-500 truncate">
                {agent.currentAction}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
