'use client';

import { useState, useCallback, useRef, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface TaskInputProps {
  onSubmit: (task: string) => void;
  isRunning: boolean;
  history: string[];
}

export default function TaskInput({
  onSubmit,
  isRunning,
  history,
}: TaskInputProps) {
  const [value, setValue] = useState('');
  const [historyIndex, setHistoryIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isRunning) return;
    onSubmit(trimmed);
    setValue('');
    setHistoryIndex(-1);
  }, [value, isRunning, onSubmit]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        handleSubmit();
        return;
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (history.length === 0) return;
        const nextIndex = Math.min(historyIndex + 1, history.length - 1);
        setHistoryIndex(nextIndex);
        setValue(history[nextIndex]);
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (historyIndex <= 0) {
          setHistoryIndex(-1);
          setValue('');
          return;
        }
        const nextIndex = historyIndex - 1;
        setHistoryIndex(nextIndex);
        setValue(history[nextIndex]);
      }
    },
    [handleSubmit, history, historyIndex]
  );

  return (
    <div className="flex items-center gap-3">
      <div className="relative flex-1">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setHistoryIndex(-1);
          }}
          onKeyDown={handleKeyDown}
          placeholder={isRunning ? 'Task running...' : 'Enter a task for the swarm...'}
          disabled={isRunning}
          className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-4 py-3 pr-12
                     text-white placeholder-slate-500 focus:outline-none focus:border-evo-primary
                     transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        />
        {isRunning && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <Loader2 size={18} className="text-evo-primary animate-spin" />
          </div>
        )}
      </div>
      <button
        onClick={handleSubmit}
        disabled={isRunning || !value.trim()}
        className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-evo-primary hover:bg-evo-primary/80
                   text-white font-medium transition-all duration-200
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isRunning ? (
          <Loader2 size={18} className="animate-spin" />
        ) : (
          <Send size={18} />
        )}
        <span className="hidden sm:inline">
          {isRunning ? 'Running...' : 'Send'}
        </span>
      </button>
    </div>
  );
}
