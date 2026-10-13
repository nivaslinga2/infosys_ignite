import React from 'react';
import { Check } from 'lucide-react';

export default function HumanReviewGate({
  actionId,
  audit,
  onApprove
}) {
  return (
    <div className="mt-3 p-3 rounded-lg bg-amber-950/20 border border-amber-500/30 space-y-2.5">
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-semibold text-amber-300">Supervisor Authorization Required</span>
        <span className="font-mono text-slate-400">Reviewer: manager_21</span>
      </div>

      {audit?.execution_status === 'EXECUTED' ? (
        <div className="p-2 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-1.5">
          <Check className="w-3.5 h-3.5" /> Action approved and executed by {audit.approved_by}
        </div>
      ) : audit?.execution_status === 'REJECTED' ? (
        <div className="p-2 rounded bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs">
          Action rejected by supervisor. Tool layer was not reached.
        </div>
      ) : (
        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={() => onApprove(actionId, false)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
          >
            Reject
          </button>
          <button
            onClick={() => onApprove(actionId, true)}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5" /> Approve & Execute Tool
          </button>
        </div>
      )}
    </div>
  );
}
