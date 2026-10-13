import React from 'react';
import { Send } from 'lucide-react';
import { QUICK_PROMPTS } from '../../constants/quickPrompts';

export default function ChatInput({
  input,
  onChangeInput,
  onSend,
  loading,
  onSelectPreset
}) {
  return (
    <div className="p-4 border-t border-slate-800/80 bg-[#0d0f14]/80 backdrop-blur shrink-0">
      <div className="max-w-3xl mx-auto space-y-2.5">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
          {QUICK_PROMPTS.slice(0, 5).map((p, i) => (
            <button
              key={i}
              onClick={() => onSelectPreset(p)}
              className="px-2.5 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-[11px] whitespace-nowrap transition"
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 bg-[#181a20] rounded-2xl border border-slate-800 px-4 py-2.5 shadow-lg focus-within:border-indigo-500/70 transition">
          <input
            type="text"
            value={input}
            onChange={(e) => onChangeInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
            placeholder="Ask the agent (e.g. Refund ₹7,500 to customer C1024)..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            onClick={() => onSend()}
            disabled={!input.trim() || loading}
            className="w-8 h-8 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 flex items-center justify-center text-white shrink-0 transition"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-[10px] text-center text-slate-500">
          AgentShield validates all agent proposals via Qualcomm AI semantic analysis, RBAC policies & the Action Integrity Gate before tool execution.
        </p>
      </div>
    </div>
  );
}
