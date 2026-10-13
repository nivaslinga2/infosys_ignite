import React from 'react';
import { Shield, RefreshCw } from 'lucide-react';
import ChatMessage from './ChatMessage';

export default function MessageList({
  messages,
  loading,
  openChecks,
  onToggleCheck,
  onApprove,
  messagesEndRef
}) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {messages.map((m) => (
          <ChatMessage
            key={m.id}
            message={m}
            isOpenChecks={!!openChecks[m.id]}
            onToggleChecks={() => onToggleCheck(m.id)}
            onApprove={onApprove}
          />
        ))}

        {loading && (
          <div className="flex gap-4 items-start">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center shrink-0">
              <Shield className="w-4 h-4 text-white animate-pulse" />
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 pt-1.5">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Intercepting and evaluating action through 10 security & guardrail gates...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
