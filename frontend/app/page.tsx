'use client';

import { useState, useCallback, useEffect } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import dynamic from 'next/dynamic';
import AgentFeed from '@/components/AgentFeed';
import MetricsPanel from '@/components/MetricsPanel';

// Dynamic import for 3D graph (client-side only)
const EvolutionTree = dynamic(() => import('@/components/EvolutionTree'), {
  ssr: false,
  loading: () => (
    <div className="h-full flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-evo-primary"></div>
    </div>
  ),
});

interface Event {
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

interface LineageData {
  nodes: { id: string; label: string }[];
  links: { source: string; target: string }[];
}

export default function Dashboard() {
  const [events, setEvents] = useState<Event[]>([]);
  const [lineage, setLineage] = useState<LineageData>({ nodes: [], links: [] });
  const [taskInput, setTaskInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { sendMessage, lastMessage, readyState } = useWebSocket(WS_URL, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const event: Event = JSON.parse(lastMessage.data);
        setEvents((prev) => [event, ...prev].slice(0, 100));
      } catch (e) {
        console.error('Failed to parse event:', e);
      }
    }
  }, [lastMessage]);

  // Fetch initial lineage data
  useEffect(() => {
    fetch(`${API_URL}/api/lineage`)
      .then((res) => res.json())
      .then((data) => setLineage(data))
      .catch(console.error);
  }, [API_URL]);

  // Refresh lineage when evolution events occur
  useEffect(() => {
    const evolutionEvents = events.filter(
      (e) =>
        e.event_type === 'lineage_update' ||
        e.event_type === 'evolution_round_end'
    );
    if (evolutionEvents.length > 0) {
      fetch(`${API_URL}/api/lineage`)
        .then((res) => res.json())
        .then((data) => setLineage(data))
        .catch(console.error);
    }
  }, [events, API_URL]);

  const runTask = useCallback(async () => {
    if (!taskInput.trim() || isRunning) return;

    setIsRunning(true);
    try {
      const response = await fetch(`${API_URL}/api/run_task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskInput }),
      });

      if (!response.ok) throw new Error('Task failed');

      const result = await response.json();
      console.log('Task result:', result);
      setTaskInput('');
    } catch (error) {
      console.error('Error running task:', error);
    } finally {
      setIsRunning(false);
    }
  }, [taskInput, isRunning, API_URL]);

  const triggerEvolution = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/evolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ generations: 1 }),
      });

      if (!response.ok) throw new Error('Evolution failed');

      const result = await response.json();
      console.log('Evolution result:', result);
    } catch (error) {
      console.error('Error triggering evolution:', error);
    }
  }, [API_URL]);

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting...',
    [ReadyState.OPEN]: 'Connected',
    [ReadyState.CLOSING]: 'Closing...',
    [ReadyState.CLOSED]: 'Disconnected',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState];

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold glow-text text-evo-primary">
              EvoSwarm
            </h1>
            <p className="text-slate-400 mt-1">
              Self-Evolving Multi-Agent Collective
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span
              className={`badge ${
                readyState === ReadyState.OPEN
                  ? 'badge-success'
                  : 'badge-warning'
              }`}
            >
              {connectionStatus}
            </span>
            <button onClick={triggerEvolution} className="btn btn-secondary">
              🧬 Evolve
            </button>
          </div>
        </div>
      </header>

      {/* Task Input */}
      <div className="card mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runTask()}
            placeholder="Enter a task for the swarm..."
            className="flex-1 bg-slate-900/50 border border-slate-600 rounded-lg px-4 py-3 
                     text-white placeholder-slate-400 focus:outline-none focus:border-evo-primary
                     transition-colors"
          />
          <button
            onClick={runTask}
            disabled={isRunning || !taskInput.trim()}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⚙️</span>
                Running...
              </span>
            ) : (
              '🚀 Run Task'
            )}
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Evolution Tree */}
        <div className="col-span-8">
          <div className="card h-[500px]">
            <div className="card-header">
              <span>🌳</span>
              <span>Evolution Lineage</span>
              <span className="badge badge-primary ml-auto">
                {lineage.nodes.length} versions
              </span>
            </div>
            <div className="h-[420px]">
              <EvolutionTree nodes={lineage.nodes} links={lineage.links} />
            </div>
          </div>
        </div>

        {/* Metrics Panel */}
        <div className="col-span-4">
          <MetricsPanel events={events} />
        </div>

        {/* Agent Feed */}
        <div className="col-span-12">
          <AgentFeed events={events} />
        </div>
      </div>
    </div>
  );
}
