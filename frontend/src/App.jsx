import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import MessageList from './components/chat/MessageList';
import ChatInput from './components/chat/ChatInput';
import AuditModal from './components/audit/AuditModal';
import {
  fetchAuditLogs,
  fetchAuditMetrics,
  fetchAuditRecord,
  proposeAgentAction,
  validateActionContract,
  executeApprovedAction,
  submitSupervisorApproval
} from './services/api';

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 'intro-1',
      role: 'assistant',
      text: 'Hello employee_42. I am your enterprise agent powered by Qualcomm Cloud AI (Llama-3.1-8B). Any action I plan is mediated and independently checked by AgentShield before reaching any real tools or database layers.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('FinanceAgent');
  const [selectedRole, setSelectedRole] = useState('finance_operator');
  const [environment, setEnvironment] = useState('production');
  const [openChecks, setOpenChecks] = useState({});
  const [auditList, setAuditList] = useState([]);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [metrics, setMetrics] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    fetchAudit();
  }, []);

  const fetchAudit = async () => {
    try {
      const logs = await fetchAuditLogs();
      setAuditList(logs);
      const m = await fetchAuditMetrics();
      setMetrics(m);
    } catch (e) {
      console.warn('Audit trail fetch failed:', e);
    }
  };

  const handleSelectAgent = (agent) => {
    setSelectedAgent(agent);
    if (agent === 'FinanceAgent') setSelectedRole('finance_operator');
    if (agent === 'DatabaseOpsAgent') setSelectedRole('db_administrator');
    if (agent === 'SupportAgent') setSelectedRole('support_operator');
  };

  const handleSelectPreset = (p) => {
    setSelectedAgent(p.agent);
    setSelectedRole(p.role);
    handleSend(p.prompt, p.agent, p.role);
  };

  const handleSend = async (customPrompt = null, customAgent = null, customRole = null) => {
    const textToSend = customPrompt || input;
    if (!textToSend.trim() || loading) return;

    const agentToUse = customAgent || selectedAgent;
    const roleToUse = customRole || selectedRole;

    const userMsg = {
      id: `usr-${Date.now()}`,
      role: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setInput('');
    setLoading(true);

    try {
      const proposalData = await proposeAgentAction({
        user_id: 'employee_42',
        user_prompt: textToSend,
        agent_id: agentToUse,
        role: roleToUse,
        environment: environment,
        provenance_source: textToSend.includes('IGNORE ALL') ? 'external_web' : 'user',
        trusted: !textToSend.includes('IGNORE ALL')
      });

      const actionId = `ACT-${Math.floor(1000 + Math.random() * 9000)}`;
      const contractPayload = {
        action_id: actionId,
        agent: agentToUse,
        user: 'employee_42',
        role: roleToUse,
        intent: proposalData.intent,
        tool: proposalData.tool,
        target: proposalData.target,
        environment: environment,
        provenance: {
          source: textToSend.includes('IGNORE ALL') ? 'external_web' : 'user',
          trusted: !textToSend.includes('IGNORE ALL'),
          input_text: textToSend
        },
        user_prompt: textToSend
      };

      const validationData = await validateActionContract(contractPayload);

      let execResult = null;
      if (validationData.decision === 'ALLOW') {
        const execOk = await executeApprovedAction(actionId);
        if (execOk) {
          execResult = await fetchAuditRecord(actionId);
        }
      }

      const assistantMsg = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        text: `Proposed action: invoke tool ${proposalData.tool} with target ${JSON.stringify(proposalData.target)}.`,
        proposal: proposalData,
        validation: validationData,
        contract: contractPayload,
        audit: execResult,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMsg]);
      await fetchAudit();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          text: `Error processing request: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAction = async (msgId, actionId, approved) => {
    try {
      const updatedRecord = await submitSupervisorApproval({
        action_id: actionId,
        approved: approved,
        reviewer: 'manager_21',
        review_notes: approved ? 'Approved verified transaction.' : 'Rejected by supervisor.'
      });

      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, audit: updatedRecord } : m))
      );
      await fetchAudit();
    } catch (e) {
      alert('Approval error: ' + e.message);
    }
  };

  const toggleCheck = (id) => {
    setOpenChecks((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'intro-fresh',
        role: 'assistant',
        text: 'Chat reset. How can I help you today? All actions will be intercepted and checked by AgentShield.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  return (
    <div className="flex h-screen bg-[#111318] text-slate-100 font-sans overflow-hidden">
      <Sidebar
        onSelectPreset={handleSelectPreset}
        onOpenAudit={() => { fetchAudit(); setShowAuditModal(true); }}
        auditCount={auditList.length}
        onClearChat={clearChat}
      />

      <div className="flex-1 flex flex-col h-full bg-[#111318] overflow-hidden">
        <Header
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
          environment={environment}
          onChangeEnvironment={setEnvironment}
          onClearChat={clearChat}
        />

        <MessageList
          messages={messages}
          loading={loading}
          openChecks={openChecks}
          onToggleCheck={toggleCheck}
          onApprove={handleApproveAction}
          messagesEndRef={messagesEndRef}
        />

        <ChatInput
          input={input}
          onChangeInput={setInput}
          onSend={handleSend}
          loading={loading}
          onSelectPreset={handleSelectPreset}
        />
      </div>

      <AuditModal
        isOpen={showAuditModal}
        onClose={() => setShowAuditModal(false)}
        metrics={metrics}
        auditList={auditList}
      />
    </div>
  );
}
