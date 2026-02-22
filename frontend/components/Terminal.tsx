'use client';

import { useEffect, useRef } from 'react';
import { TerminalSquare } from 'lucide-react';

interface TerminalOutput {
  command: string;
  output: string;
  timestamp: string;
}

interface TerminalProps {
  outputs: TerminalOutput[];
}

export default function Terminal({ outputs }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new output
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [outputs]);

  return (
    <div className="flex flex-col h-full">
      {/* Terminal Header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/80 border-b border-slate-700/50 rounded-t-xl">
        <TerminalSquare size={16} className="text-evo-primary" />
        <span className="text-sm font-medium text-slate-300">
          Command Output
        </span>
        <span className="ml-auto text-xs text-slate-500">
          {outputs.length} commands
        </span>
      </div>

      {/* Terminal Body */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto bg-slate-950 p-4 font-mono text-sm rounded-b-xl"
      >
        {outputs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600">
            <TerminalSquare size={40} className="mb-3" />
            <p>No command output yet</p>
            <p className="text-xs mt-1">
              Agent command output will appear here
            </p>
          </div>
        ) : (
          outputs.map((entry, index) => {
            const time = new Date(entry.timestamp).toLocaleTimeString();
            return (
              <div key={`${entry.timestamp}-${index}`} className="mb-4">
                {/* Timestamp */}
                <div className="text-xs text-slate-600 mb-1">{time}</div>
                {/* Command */}
                <div className="flex items-start gap-2">
                  <span className="text-evo-accent select-none">$</span>
                  <span className="text-green-400 break-all">
                    {entry.command}
                  </span>
                </div>
                {/* Output */}
                {entry.output && (
                  <pre className="mt-1 ml-4 text-slate-300 whitespace-pre-wrap break-all leading-relaxed">
                    {entry.output}
                  </pre>
                )}
                {/* Separator */}
                {index < outputs.length - 1 && (
                  <div className="border-t border-slate-800/50 mt-3" />
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
