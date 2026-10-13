import React from 'react';
import { Shield, User } from 'lucide-react';
import ContractCard from '../validation/ContractCard';

export default function ChatMessage({
  message,
  isOpenChecks,
  onToggleChecks,
  onApprove
}) {
  const isAssistant = message.role === 'assistant';

  return (
    <div className="flex gap-4 items-start">
      {isAssistant ? (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
          <Shield className="w-4 h-4 text-white" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 mt-0.5">
          <User className="w-4 h-4 text-slate-300" />
        </div>
      )}

      <div className="flex-1 space-y-3 overflow-hidden">
        <div className="text-sm text-slate-200 leading-relaxed font-sans">
          {message.text}
        </div>

        {message.validation && (
          <ContractCard
            contract={message.contract}
            validation={message.validation}
            audit={message.audit}
            isOpenChecks={isOpenChecks}
            onToggleChecks={onToggleChecks}
            onApprove={(actionId, approved) => onApprove(message.id, actionId, approved)}
          />
        )}
      </div>
    </div>
  );
}
