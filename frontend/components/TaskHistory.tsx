'use client';

import { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronRight, ListTodo } from 'lucide-react';

export interface TaskRecord {
  id: string;
  task: string;
  result: string;
  timestamp: string;
}

interface TaskHistoryProps {
  tasks: TaskRecord[];
}

export default function TaskHistory({ tasks }: TaskHistoryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const filteredTasks = useMemo(() => {
    const query = searchQuery.toLowerCase();
    const filtered = tasks.filter(
      (t) =>
        t.task.toLowerCase().includes(query) ||
        t.result.toLowerCase().includes(query)
    );
    return filtered.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [tasks, searchQuery]);

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="relative mb-4">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search tasks..."
          className="w-full bg-slate-900/50 border border-slate-600 rounded-lg pl-10 pr-4 py-2.5
                     text-sm text-white placeholder-slate-500 focus:outline-none focus:border-evo-primary
                     transition-colors"
        />
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {filteredTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-500">
            <ListTodo size={40} className="mb-3" />
            <p className="text-sm">
              {tasks.length === 0 ? 'No tasks yet' : 'No matching tasks'}
            </p>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const isExpanded = expandedIds.has(task.id);
            const time = new Date(task.timestamp).toLocaleString();
            return (
              <div
                key={task.id}
                className="card border-slate-700/30 hover:border-slate-600/50 transition-colors"
              >
                <button
                  onClick={() => toggleExpanded(task.id)}
                  className="w-full flex items-start gap-3 text-left"
                >
                  <div className="mt-0.5 flex-shrink-0 text-slate-500">
                    {isExpanded ? (
                      <ChevronDown size={16} />
                    ) : (
                      <ChevronRight size={16} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{task.task}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{time}</p>
                  </div>
                </button>
                {isExpanded && task.result && (
                  <div className="mt-3 ml-7 px-3 py-2 bg-slate-900/60 rounded-lg">
                    <p className="text-xs text-slate-500 mb-1">Result</p>
                    <pre className="text-xs text-slate-300 whitespace-pre-wrap break-all font-mono leading-relaxed">
                      {task.result}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
