import React from 'react';
import { Bot, RefreshCw } from 'lucide-react';

export default function Header({
  selectedAgent,
  onSelectAgent,
  environment,
  onChangeEnvironment,
  onClearChat
}) {
  return (
    <header className="h-14 border-b border-slate-800/80 flex items-center justify-between px-4 sm:px-6 shrink-0 bg-[#0d0f14]/80 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
          <Bot className="w-3.5 h-3.5 text-indigo-400" />
          <select
            value={selectedAgent}
            onChange={(e) => onSelectAgent(e.target.value)}
            className="bg-transparent text-xs text-slate-200 font-medium focus:outline-none"
          >
            <option value="FinanceAgent">FinanceAgent</option>
            <option value="DatabaseOpsAgent">DatabaseOpsAgent</option>
            <option value="SupportAgent">SupportAgent</option>
          </select>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900/50 border border-slate-800 px-2.5 py-1 rounded-lg">
          <span>Env:</span>
          <select
            value={environment}
            onChange={(e) => onChangeEnvironment(e.target.value)}
            className="bg-transparent text-slate-300 focus:outline-none text-xs"
          >
            <option value="production">production</option>
            <option value="staging">staging</option>
          </select>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> PEP Guard Active
        </span>
        <button
          onClick={onClearChat}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white md:hidden"
          title="Reset Chat"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
