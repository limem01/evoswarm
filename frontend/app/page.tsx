'use client';

import { useState, useCallback, useEffect } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Sidebar, { TabName, ConnectionStatus, SidebarAgent } from '@/components/Sidebar';
import AgentCards, { AgentCardData } from '@/components/AgentCards';
import AgentFeed from '@/components/AgentFeed';
import MetricsPanel from '@/components/MetricsPanel';
import Terminal from '@/components/Terminal';
import TaskInput from '@/components/TaskInput';
import TaskHistory, { TaskRecord } from '@/components/TaskHistory';
import ScreenshotViewer, { Screenshot } from '@/components/ScreenshotViewer';
import ApprovalPopup, { ApprovalRequest } from '@/components/ApprovalPopup';
import { LayoutDashboard, TerminalSquare, ListTodo } from 'lucide-react';

interface Event {
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

interface TerminalOutput {
  command: string;
  output: string;
  timestamp: string;
}

const tabConfig: { tab: TabName; label: string; icon: typeof LayoutDashboard }[] = [
  { tab: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { tab: 'terminal', label: 'Terminal', icon: TerminalSquare },
  { tab: 'tasks', label: 'Tasks', icon: ListTodo },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabName>('dashboard');
  const [events, setEvents] = useState<Event[]>([]);
  const [agents, setAgents] = useState<AgentCardData[]>([
    { name: 'Architect', status: 'idle' },
    { name: 'Coder', status: 'idle' },
    { name: 'Critic', status: 'idle' },
    { name: 'Researcher', status: 'idle' },
    { name: 'Tester', status: 'idle' },
    { name: 'Optimizer', status: 'idle' },
    { name: 'MemoryCurator', status: 'idle' },
    { name: 'Evolutor', status: 'idle' },
  ]);
  const [terminalOutputs, setTerminalOutputs] = useState<TerminalOutput[]>([]);
  const [screenshots, setScreenshots] = useState<Screenshot[]>([]);
  const [approvalRequest, setApprovalRequest] = useState<ApprovalRequest | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [taskHistory, setTaskHistory] = useState<string[]>([]);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);

  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { sendMessage, lastMessage, readyState } = useWebSocket(WS_URL, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });

  const connectionStatus: ConnectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting...' as ConnectionStatus,
    [ReadyState.OPEN]: 'Connected' as ConnectionStatus,
    [ReadyState.CLOSING]: 'Closing...' as ConnectionStatus,
    [ReadyState.CLOSED]: 'Disconnected' as ConnectionStatus,
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated' as ConnectionStatus,
  }[readyState] || 'Disconnected';

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const msg = JSON.parse(lastMessage.data);

        // Handle different event types
        if (msg.type === 'approval_required' || msg.event_type === 'approval_required') {
          const data = msg.data || msg;
          setApprovalRequest({
            id: data.id,
            action_type: data.action_type,
            action_detail: data.action_detail,
            agent_name: data.agent_name,
            tier: data.tier || 'ASK',
            category: data.category || 'unknown',
            created_at: data.created_at || new Date().toISOString(),
          });
          return;
        }

        if (msg.type === 'command_output' || msg.event_type === 'command_output') {
          const data = msg.data || msg;
          setTerminalOutputs((prev) => [
            ...prev,
            {
              command: data.command || '',
              output: data.output || '',
              timestamp: data.timestamp || new Date().toISOString(),
            },
          ]);
        }

        if (msg.type === 'screenshot_captured' || msg.event_type === 'screenshot_captured') {
          const data = msg.data || msg;
          setScreenshots((prev) => [
            ...prev,
            {
              filename: data.filename || 'screenshot.png',
              url: data.url || '',
              timestamp: data.timestamp || new Date().toISOString(),
            },
          ]);
        }

        if (msg.type === 'agent_status' || msg.event_type === 'agent_status') {
          const data = msg.data || msg;
          setAgents((prev) =>
            prev.map((agent) =>
              agent.name === data.agent_name
                ? {
                    ...agent,
                    status: data.status || agent.status,
                    currentAction: data.current_action,
                  }
                : agent
            )
          );
        }

        // Generic event for feed and metrics
        if (msg.event_type) {
          const event: Event = {
            event_type: msg.event_type,
            timestamp: msg.timestamp || new Date().toISOString(),
            data: msg.data || {},
          };
          setEvents((prev) => [event, ...prev].slice(0, 200));
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    }
  }, [lastMessage]);

  // Handle approval responses
  const handleApprove = useCallback(
    (id: string) => {
      sendMessage(
        JSON.stringify({ type: 'approval_response', id, approved: true })
      );
      setApprovalRequest(null);
    },
    [sendMessage]
  );

  const handleDeny = useCallback(
    (id: string) => {
      sendMessage(
        JSON.stringify({ type: 'approval_response', id, approved: false })
      );
      setApprovalRequest(null);
    },
    [sendMessage]
  );

  // Run a task
  const runTask = useCallback(
    async (task: string) => {
      if (isRunning) return;

      setIsRunning(true);
      setTaskHistory((prev) => [task, ...prev]);

      try {
        const response = await fetch(`${API_URL}/api/run_task`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task }),
        });

        if (!response.ok) throw new Error('Task failed');

        const result = await response.json();
        setTasks((prev) => [
          {
            id: result.id || crypto.randomUUID(),
            task,
            result: typeof result.result === 'string' ? result.result : JSON.stringify(result, null, 2),
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ]);
      } catch (error) {
        console.error('Error running task:', error);
        setTasks((prev) => [
          {
            id: crypto.randomUUID(),
            task,
            result: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ]);
      } finally {
        setIsRunning(false);
      }
    },
    [isRunning, API_URL]
  );

  // Sidebar agents (simplified view)
  const sidebarAgents: SidebarAgent[] = agents.map((a) => ({
    name: a.name,
    status: a.status,
  }));

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        connectionStatus={connectionStatus}
        agents={sidebarAgents}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Tab Bar */}
        <div className="flex items-center border-b border-slate-700/50 bg-slate-900/40 px-6">
          {tabConfig.map(({ tab, label, icon: Icon }) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all duration-200 ${
                activeTab === tab
                  ? 'border-evo-primary text-evo-primary'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Agent Cards */}
              <section>
                <h2 className="text-lg font-semibold text-white mb-4">Agents</h2>
                <AgentCards agents={agents} />
              </section>

              {/* Metrics + Feed Grid */}
              <div className="grid grid-cols-12 gap-6">
                <div className="col-span-8">
                  <AgentFeed events={events} />
                </div>
                <div className="col-span-4">
                  <MetricsPanel events={events} />
                </div>
              </div>

              {/* Screenshots */}
              {screenshots.length > 0 && (
                <section>
                  <h2 className="text-lg font-semibold text-white mb-4">
                    Screenshots
                  </h2>
                  <ScreenshotViewer screenshots={screenshots} />
                </section>
              )}
            </div>
          )}

          {/* Terminal Tab */}
          {activeTab === 'terminal' && (
            <div className="h-full">
              <Terminal outputs={terminalOutputs} />
            </div>
          )}

          {/* Tasks Tab */}
          {activeTab === 'tasks' && (
            <div className="space-y-6">
              <section>
                <h2 className="text-lg font-semibold text-white mb-4">
                  New Task
                </h2>
                <TaskInput
                  onSubmit={runTask}
                  isRunning={isRunning}
                  history={taskHistory}
                />
              </section>

              <section className="flex-1">
                <h2 className="text-lg font-semibold text-white mb-4">
                  Task History
                </h2>
                <TaskHistory tasks={tasks} />
              </section>
            </div>
          )}

          {/* Browser Tab - placeholder */}
          {activeTab === 'browser' && (
            <div className="space-y-6">
              <section>
                <h2 className="text-lg font-semibold text-white mb-4">
                  Browser Screenshots
                </h2>
                <ScreenshotViewer screenshots={screenshots} />
              </section>
            </div>
          )}
        </div>
      </main>

      {/* Approval Popup (overlay) */}
      <ApprovalPopup
        request={approvalRequest}
        onApprove={handleApprove}
        onDeny={handleDeny}
      />
    </div>
  );
}
