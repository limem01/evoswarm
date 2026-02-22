'use client';

import { useState, useEffect, useCallback } from 'react';
import { ShieldAlert, Check, X, Clock } from 'lucide-react';

export interface ApprovalRequest {
  id: string;
  action_type: string;
  action_detail: string;
  agent_name: string;
  tier: string;
  category: string;
  created_at: string;
}

interface ApprovalPopupProps {
  request: ApprovalRequest | null;
  onApprove: (id: string) => void;
  onDeny: (id: string) => void;
}

const TIMEOUT_SECONDS = 300; // 5 minutes

export default function ApprovalPopup({
  request,
  onApprove,
  onDeny,
}: ApprovalPopupProps) {
  const [remainingSeconds, setRemainingSeconds] = useState(TIMEOUT_SECONDS);

  // Reset and start countdown when a new request arrives
  useEffect(() => {
    if (!request) {
      setRemainingSeconds(TIMEOUT_SECONDS);
      return;
    }

    setRemainingSeconds(TIMEOUT_SECONDS);

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onDeny(request.id);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [request, onDeny]);

  const handleApprove = useCallback(() => {
    if (request) onApprove(request.id);
  }, [request, onApprove]);

  const handleDeny = useCallback(() => {
    if (request) onDeny(request.id);
  }, [request, onDeny]);

  if (!request) return null;

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  const timeDisplay = `${minutes}:${seconds.toString().padStart(2, '0')}`;
  const urgencyColor =
    remainingSeconds <= 60
      ? 'text-red-400'
      : remainingSeconds <= 120
        ? 'text-yellow-400'
        : 'text-slate-400';

  return (
    <div className="approval-popup fixed bottom-6 right-6 w-[420px] z-50">
      <div className="card border-yellow-500/50 shadow-lg shadow-yellow-500/10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-yellow-500/20">
            <ShieldAlert size={20} className="text-yellow-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-yellow-400">
              Approval Required
            </h3>
            <p className="text-xs text-slate-400">
              Tier: {request.tier} / {request.category}
            </p>
          </div>
          <div className={`flex items-center gap-1.5 ${urgencyColor}`}>
            <Clock size={14} />
            <span className="text-sm font-mono font-medium">{timeDisplay}</span>
          </div>
        </div>

        {/* Agent Info */}
        <div className="mb-3 px-3 py-2 bg-slate-900/60 rounded-lg">
          <p className="text-xs text-slate-500 mb-0.5">Agent</p>
          <p className="text-sm text-white font-medium">{request.agent_name}</p>
        </div>

        {/* Action Type */}
        <div className="mb-3 px-3 py-2 bg-slate-900/60 rounded-lg">
          <p className="text-xs text-slate-500 mb-0.5">Action</p>
          <p className="text-sm text-white font-medium">{request.action_type}</p>
        </div>

        {/* Action Detail */}
        <div className="mb-4 px-3 py-2 bg-slate-900/60 rounded-lg">
          <p className="text-xs text-slate-500 mb-0.5">Detail</p>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap break-all max-h-32 overflow-y-auto font-mono leading-relaxed">
            {request.action_detail}
          </pre>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleDeny}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all duration-200 text-sm font-medium"
          >
            <X size={16} />
            Deny
          </button>
          <button
            onClick={handleApprove}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 transition-all duration-200 text-sm font-medium"
          >
            <Check size={16} />
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
