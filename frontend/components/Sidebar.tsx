'use client';

import {
  LayoutDashboard,
  TerminalSquare,
  Globe,
  ListTodo,
  Settings,
  Wifi,
  WifiOff,
} from 'lucide-react';

export type TabName = 'dashboard' | 'terminal' | 'browser' | 'tasks';

export type ConnectionStatus = 'Connected' | 'Connecting...' | 'Disconnected' | 'Closing...' | 'Uninstantiated';

export interface SidebarAgent {
  name: string;
  status: 'idle' | 'working' | 'error';
}

interface SidebarProps {
  activeTab: TabName;
  onTabChange: (tab: TabName) => void;
  connectionStatus: ConnectionStatus;
  agents: SidebarAgent[];
}

const navItems: { tab: TabName; label: string; icon: typeof LayoutDashboard }[] = [
  { tab: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { tab: 'terminal', label: 'Terminal', icon: TerminalSquare },
  { tab: 'browser', label: 'Browser', icon: Globe },
  { tab: 'tasks', label: 'Tasks', icon: ListTodo },
];

const statusDotColor: Record<SidebarAgent['status'], string> = {
  idle: 'bg-green-400',
  working: 'bg-yellow-400 animate-pulse',
  error: 'bg-red-400',
};

export default function Sidebar({
  activeTab,
  onTabChange,
  connectionStatus,
  agents,
}: SidebarProps) {
  const isConnected = connectionStatus === 'Connected';

  return (
    <aside className="sidebar flex flex-col h-screen w-64 bg-slate-900/80 backdrop-blur-sm border-r border-slate-700/50 p-4">
      {/* Logo */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold glow-text text-evo-primary tracking-wide">
          EvoSwarm
        </h1>
        <p className="text-xs text-slate-500 mt-1">Multi-Agent Collective</p>
      </div>

      {/* Navigation */}
      <nav className="space-y-1 mb-6">
        {navItems.map(({ tab, label, icon: Icon }) => (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === tab
                ? 'bg-evo-primary/20 text-evo-primary border border-evo-primary/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      {/* Divider */}
      <div className="border-t border-slate-700/50 mb-4" />

      {/* Agent Status Cards */}
      <div className="flex-1 overflow-y-auto">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 px-1">
          Agents
        </p>
        <div className="space-y-1.5">
          {agents.map((agent) => (
            <div
              key={agent.name}
              className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700/30"
            >
              <div
                className={`w-2 h-2 rounded-full flex-shrink-0 ${statusDotColor[agent.status]}`}
              />
              <span className="text-sm text-slate-300 truncate">
                {agent.name}
              </span>
            </div>
          ))}
          {agents.length === 0 && (
            <p className="text-xs text-slate-600 px-3 py-2">No agents active</p>
          )}
        </div>
      </div>

      {/* Connection Indicator */}
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <div className="flex items-center gap-2 px-2 py-1.5">
          {isConnected ? (
            <Wifi size={14} className="text-green-400" />
          ) : (
            <WifiOff size={14} className="text-red-400" />
          )}
          <span
            className={`text-xs font-medium ${
              isConnected ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {connectionStatus}
          </span>
        </div>

        {/* Settings */}
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all duration-200 mt-1">
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}
