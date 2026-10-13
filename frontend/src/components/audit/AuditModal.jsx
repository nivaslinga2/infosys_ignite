import React from 'react';
import { FileText } from 'lucide-react';

export default function AuditModal({
  isOpen,
  onClose,
  metrics,
  auditList
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0f121a] border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" /> Audit Log & System Metrics
          </h3>
          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-white"
          >
            Close [✕]
          </button>
        </div>

        {metrics && (
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase">Total</span>
              <div className="text-base font-bold text-white mt-0.5">{metrics.total_actions}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-emerald-400 uppercase">Allow</span>
              <div className="text-base font-bold text-emerald-400 mt-0.5">{metrics.allowed_count}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-amber-400 uppercase">Review</span>
              <div className="text-base font-bold text-amber-400 mt-0.5">{metrics.reviewed_count}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-rose-400 uppercase">Blocked</span>
              <div className="text-base font-bold text-rose-400 mt-0.5">{metrics.blocked_count}</div>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto space-y-2 text-xs font-mono">
          {auditList.map((rec, i) => (
            <div key={i} className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center justify-between">
              <div>
                <span className="text-slate-200 font-bold">{rec.action_id}</span>
                <span className="text-slate-500 ml-2">({rec.agent})</span>
                <div className="text-slate-400 text-[11px] font-sans mt-0.5">
                  Tool: {rec.tool} • Risk: {rec.validation_report?.composite_risk_score}/100
                </div>
              </div>
              <div className="text-right">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  rec.decision === 'ALLOW' ? 'bg-emerald-500/15 text-emerald-400' :
                  rec.decision === 'REVIEW' ? 'bg-amber-500/15 text-amber-400' :
                  'bg-rose-500/15 text-rose-400'
                }`}>
                  {rec.decision}
                </span>
                <div className="text-[10px] text-slate-500 mt-1 font-mono">
                  {rec.execution_status}
                </div>
              </div>
            </div>
          ))}
          {auditList.length === 0 && (
            <div className="p-8 text-center text-slate-500">No audit records logged yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
