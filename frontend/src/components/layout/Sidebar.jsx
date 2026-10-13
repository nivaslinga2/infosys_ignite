import React from 'react';
import { Shield, Plus, ArrowRight, FileText, Cpu } from 'lucide-react';
import { QUICK_PROMPTS } from '../../constants/quickPrompts';

export default function Sidebar({ onSelectPreset, onOpenAudit, auditCount = 0, onClearChat }) {
  return (
    <aside className="w-64 bg-[#0d0f14] border-r border-slate-800/80 flex flex-col justify-between hidden md:flex shrink-0">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-rose-500 to-indigo-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold text-sm tracking-tight text-white">AgentShield</span>
          </div>
          <button
            onClick={onClearChat}
            title="New Chat"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-2 mb-2">
            Test Scenarios
          </div>
          {QUICK_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPreset(p)}
              className="w-full text-left px-3 py-2 rounded-lg text-xs text-slate-300 hover:bg-slate-800/70 hover:text-white transition flex items-center justify-between group"
            >
              <span className="truncate">{p.label}</span>
              <ArrowRight className="w-3 h-3 text-slate-600 group-hover:text-slate-300 opacity-0 group-hover:opacity-100 transition" />
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 border-t border-slate-800/80 space-y-3">
        <button
          onClick={onOpenAudit}
          className="w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 hover:text-white flex items-center justify-between border border-slate-800"
        >
          <span className="flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-indigo-400" /> Audit Log
          </span>
          <span className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
            {auditCount}
          </span>
        </button>

        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/60 text-[11px] text-slate-400 space-y-1">
          <div className="flex items-center justify-between text-slate-300 font-medium">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-rose-400" /> Qualcomm Cloud AI
            </span>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            Cloud AI 100 • Llama-3.1-8B
          </div>
        </div>
      </div>
    </aside>
  );
}
