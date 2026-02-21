'use client';

import { useMemo } from 'react';

interface Event {
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

interface AgentFeedProps {
  events: Event[];
}

const eventIcons: Record<string, string> = {
  agent_started: '🤖',
  agent_message: '💬',
  handoff: '🤝',
  task_assigned: '📋',
  task_complete: '✅',
  evolution_round_start: '🧬',
  evolution_round_end: '🎉',
  training_started: '🏋️',
  training_complete: '🎓',
  merge_complete: '🔀',
  lineage_update: '🌳',
  error: '❌',
};

const eventColors: Record<string, string> = {
  agent_started: 'text-blue-400',
  agent_message: 'text-slate-300',
  handoff: 'text-purple-400',
  task_assigned: 'text-yellow-400',
  task_complete: 'text-green-400',
  evolution_round_start: 'text-cyan-400',
  evolution_round_end: 'text-emerald-400',
  training_started: 'text-orange-400',
  training_complete: 'text-lime-400',
  merge_complete: 'text-pink-400',
  lineage_update: 'text-teal-400',
  error: 'text-red-400',
};

export default function AgentFeed({ events }: AgentFeedProps) {
  const formattedEvents = useMemo(() => {
    return events.map((event) => {
      const time = new Date(event.timestamp).toLocaleTimeString();
      const icon = eventIcons[event.event_type] || '📌';
      const color = eventColors[event.event_type] || 'text-slate-400';
      
      let message = event.event_type.replace(/_/g, ' ');
      
      // Format specific event types
      if (event.data) {
        if (event.event_type === 'agent_message' && event.data.agent) {
          message = `${event.data.agent}: ${event.data.content || ''}`;
        } else if (event.event_type === 'handoff') {
          message = `Handoff: ${event.data.from} → ${event.data.to}`;
        } else if (event.event_type === 'task_assigned') {
          message = `Task: ${String(event.data.task || '').slice(0, 100)}...`;
        } else if (event.event_type === 'task_complete') {
          message = `Completed: ${event.data.thread_id}`;
        } else if (event.event_type === 'training_complete') {
          message = `Training complete: ${event.data.version}`;
        } else if (event.event_type === 'error') {
          message = `Error: ${event.data.error}`;
        }
      }
      
      return { ...event, time, icon, color, message };
    });
  }, [events]);

  return (
    <div className="card">
      <div className="card-header">
        <span>📡</span>
        <span>Live Agent Feed</span>
        <span className="badge badge-primary ml-auto">{events.length} events</span>
      </div>
      
      <div className="h-[300px] overflow-y-auto space-y-2">
        {formattedEvents.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <p>No events yet</p>
            <p className="text-sm">Run a task to see agent activity</p>
          </div>
        ) : (
          formattedEvents.map((event, index) => (
            <div
              key={`${event.timestamp}-${index}`}
              className="flex items-start gap-3 p-2 rounded-lg bg-slate-900/30 hover:bg-slate-900/50 transition-colors"
            >
              <span className="text-lg">{event.icon}</span>
              <div className="flex-1 min-w-0">
                <p className={`${event.color} truncate`}>{event.message}</p>
                <p className="text-xs text-slate-500">{event.time}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
