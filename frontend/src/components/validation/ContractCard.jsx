import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import GuardrailsGrid from './GuardrailsGrid';
import HumanReviewGate from './HumanReviewGate';

export default function ContractCard({
  contract,
  validation,
  audit,
  isOpenChecks,
  onToggleChecks,
  onApprove
}) {
  if (!validation) return null;

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0a0d14] overflow-hidden text-xs">
      <div className="p-3.5 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 font-mono text-slate-300">
          <span className="text-slate-500">Contract:</span>
          <span className="text-indigo-400 font-semibold">{contract?.action_id}</span>
          <span className="text-slate-600">•</span>
          <span className="text-emerald-400">{contract?.tool}</span>
        </div>
        <div>
          {validation.decision === 'ALLOW' && (
            <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> ALLOWED
            </span>
          )}
          {validation.decision === 'REVIEW' && (
            <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> HUMAN REVIEW
            </span>
          )}
          {validation.decision === 'BLOCK' && (
            <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center gap-1">
              <XCircle className="w-3 h-3" /> BLOCKED
            </span>
          )}
        </div>
      </div>

      <div className="p-3.5 space-y-3">
        <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">
          {validation.explanation}
        </p>

        <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] font-mono text-slate-400">
          <span>Risk: <strong className="text-slate-200">{validation.composite_risk_score}/100</strong></span>
          <span>Reversibility: <strong className="text-slate-200">Tier {validation.reversibility_tier}</strong></span>
          <span>Origin: <strong className="text-slate-200">{contract?.provenance?.source}</strong></span>
        </div>

        {validation.decision === 'REVIEW' && (
          <HumanReviewGate
            actionId={contract?.action_id}
            audit={audit}
            onApprove={onApprove}
          />
        )}

        {audit?.execution_result && (
          <div className="mt-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-[11px] text-emerald-300 overflow-x-auto">
            <span className="text-slate-500 block text-[10px] uppercase font-bold mb-1">Tool Output</span>
            <pre>{JSON.stringify(audit.execution_result, null, 2)}</pre>
          </div>
        )}

        <div className="pt-2">
          <button
            onClick={onToggleChecks}
            className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
          >
            {isOpenChecks ? 'Hide security & guardrails breakdown' : 'View 10 security & guardrail checks'}
            {isOpenChecks ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {isOpenChecks && <GuardrailsGrid validation={validation} />}
        </div>
      </div>
    </div>
  );
}
