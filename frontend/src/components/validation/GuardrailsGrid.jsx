import React from 'react';

export default function GuardrailsGrid({ validation }) {
  if (!validation) return null;

  return (
    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/70">
        <span className="font-semibold text-slate-300 block">1. Qualcomm AI Semantics</span>
        <span className="text-slate-400">{validation.ai_semantic?.reason}</span>
      </div>
      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/70">
        <span className="font-semibold text-slate-300 block">2. OPA Policy Gate</span>
        <span className="text-slate-400">{validation.authorization?.reason}</span>
      </div>
      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/70">
        <span className="font-semibold text-slate-300 block">3. Risk Assessment</span>
        <span className="text-slate-400">{validation.risk_assessment?.reason}</span>
      </div>
      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/70">
        <span className="font-semibold text-slate-300 block">4. Reversibility Tier</span>
        <span className="text-slate-400">{validation.reversibility?.reason}</span>
      </div>
      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/70">
        <span className="font-semibold text-slate-300 block">5. Intent Alignment</span>
        <span className="text-slate-400">{validation.intent_alignment?.reason}</span>
      </div>
      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/70">
        <span className="font-semibold text-slate-300 block">6. Provenance Gate</span>
        <span className="text-slate-400">{validation.provenance?.reason}</span>
      </div>

      {validation.content_safety && (
        <div className={`p-2 rounded-lg bg-slate-950 border ${validation.content_safety.passed ? 'border-slate-800/70' : 'border-rose-500/40'}`}>
          <span className={`font-semibold block ${validation.content_safety.passed ? 'text-slate-300' : 'text-rose-400'}`}>
            7. 🛡️ Content Safety Rail
          </span>
          <span className="text-slate-400">{validation.content_safety.reason}</span>
        </div>
      )}

      {validation.topic_control && (
        <div className={`p-2 rounded-lg bg-slate-950 border ${validation.topic_control.passed ? 'border-slate-800/70' : 'border-rose-500/40'}`}>
          <span className={`font-semibold block ${validation.topic_control.passed ? 'text-slate-300' : 'text-rose-400'}`}>
            8. 🎯 Topic Control Rail
          </span>
          <span className="text-slate-400">{validation.topic_control.reason}</span>
        </div>
      )}

      {validation.pii_assessment && (
        <div className={`p-2 rounded-lg bg-slate-950 border ${validation.pii_assessment.passed ? 'border-slate-800/70' : 'border-rose-500/40'}`}>
          <span className={`font-semibold block ${validation.pii_assessment.passed ? 'text-slate-300' : 'text-rose-400'}`}>
            9. 🔏 PII Detection & Masking
          </span>
          <span className="text-slate-400">{validation.pii_assessment.reason}</span>
        </div>
      )}

      {validation.jailbreak_defense && (
        <div className={`p-2 rounded-lg bg-slate-950 border ${validation.jailbreak_defense.passed ? 'border-slate-800/70' : 'border-rose-500/40'}`}>
          <span className={`font-semibold block ${validation.jailbreak_defense.passed ? 'text-slate-300' : 'text-rose-400'}`}>
            10. 🔒 Jailbreak Defense
          </span>
          <span className="text-slate-400">{validation.jailbreak_defense.reason}</span>
        </div>
      )}
    </div>
  );
}
