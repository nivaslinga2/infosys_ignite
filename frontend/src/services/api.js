import { API_BASE } from '../constants/config';

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/api/audit`);
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}

export async function fetchAuditMetrics() {
  const res = await fetch(`${API_BASE}/api/audit/metrics`);
  if (!res.ok) throw new Error('Failed to fetch audit metrics');
  return res.json();
}

export async function fetchAuditRecord(actionId) {
  const res = await fetch(`${API_BASE}/api/audit/${actionId}`);
  if (!res.ok) throw new Error(`Failed to fetch audit record ${actionId}`);
  return res.json();
}

export async function proposeAgentAction(payload) {
  const res = await fetch(`${API_BASE}/api/agent/propose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Agent proposal failed');
  return res.json();
}

export async function validateActionContract(contract) {
  const res = await fetch(`${API_BASE}/api/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(contract)
  });
  if (!res.ok) throw new Error('Action contract validation failed');
  return res.json();
}

export async function executeApprovedAction(actionId) {
  const res = await fetch(`${API_BASE}/api/execution/execute/${actionId}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error(`Action execution failed: ${res.statusText}`);
  return res.json();
}

export async function submitSupervisorApproval(approvalPayload) {
  const res = await fetch(`${API_BASE}/api/approval`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(approvalPayload)
  });
  if (!res.ok) throw new Error('Supervisor approval submission failed');
  return res.json();
}
