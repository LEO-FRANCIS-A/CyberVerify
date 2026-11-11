const BASE_URL = '/api';

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${BASE_URL}/dashboard/stats`);
  if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
  return res.json();
}

export async function fetchInvestigations(search = '', verdict = '') {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (verdict && verdict !== 'ALL') params.append('verdict', verdict);
  
  const res = await fetch(`${BASE_URL}/investigations?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch investigations');
  return res.json();
}

export async function fetchInvestigation(id) {
  const res = await fetch(`${BASE_URL}/investigations/${id}`);
  if (!res.ok) throw new Error('Investigation not found');
  return res.json();
}

export async function deleteInvestigation(id) {
  const res = await fetch(`${BASE_URL}/investigations/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete investigation');
  return res.json();
}

export async function reinvestigateClaim(id) {
  const res = await fetch(`${BASE_URL}/investigations/${id}/reinvestigate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Reinvestigation failed');
  return res.json();
}

export async function compareInvestigations(id1, id2) {
  const res = await fetch(`${BASE_URL}/compare?id1=${id1}&id2=${id2}`);
  if (!res.ok) throw new Error('Failed to compare investigations');
  return res.json();
}

export function getExportPdfUrl(id) {
  return `${BASE_URL}/investigations/${id}/export?format=pdf`;
}

export function getExportJsonUrl(id) {
  return `${BASE_URL}/investigations/${id}/export?format=json`;
}

export async function submitInvestigationDirect(claim) {
  const res = await fetch(`${BASE_URL}/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Investigation failed');
  }
  return res.json();
}

export function streamInvestigation(claim, onProgress, onComplete, onError) {
  const url = `${BASE_URL}/investigate/stream?claim=${encodeURIComponent(claim)}`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'progress') {
        onProgress(data);
      } else if (data.type === 'complete') {
        eventSource.close();
        onComplete(data.data);
      } else if (data.type === 'error') {
        eventSource.close();
        onError(data.message || 'Stream failed');
      }
    } catch (e) {
      console.error('Failed to parse SSE payload:', e);
    }
  };

  eventSource.onerror = (err) => {
    eventSource.close();
    onError('Connection to investigation stream was lost. Please verify backend status.');
  };

  return () => {
    eventSource.close();
  };
}

// ==========================================================
// EVENT INTELLIGENCE APIS
// ==========================================================

export async function fetchEvents(search = '', status = '', cve = '', limit = 50) {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (status && status !== 'ALL') params.append('status', status);
  if (cve) params.append('cve', cve);
  params.append('limit', limit);

  const res = await fetch(`${BASE_URL}/events?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function fetchEvent(id) {
  const res = await fetch(`${BASE_URL}/events/${id}`);
  if (!res.ok) throw new Error('Event not found');
  return res.json();
}

export async function fetchEventTimeline(id) {
  const res = await fetch(`${BASE_URL}/events/${id}/timeline`);
  if (!res.ok) throw new Error('Failed to fetch event timeline');
  return res.json();
}

export async function triggerEventAudit() {
  const res = await fetch(`${BASE_URL}/events/audit`, { method: 'POST' });
  if (!res.ok) throw new Error('HDBSCAN Audit failed');
  return res.json();
}

export async function fetchEventAudits() {
  const res = await fetch(`${BASE_URL}/events/audits`);
  if (!res.ok) throw new Error('Failed to fetch event audits');
  return res.json();
}

export async function triggerIngestion() {
  const res = await fetch(`${BASE_URL}/ingest/trigger`, { method: 'POST' });
  if (!res.ok) throw new Error('Ingestion trigger failed');
  return res.json();
}

export async function fetchSourceRegistry() {
  const res = await fetch(`${BASE_URL}/sources/registry`);
  if (!res.ok) throw new Error('Failed to fetch source registry');
  return res.json();
}

export async function fetchModelStatus() {
  const res = await fetch(`${BASE_URL}/model/status`);
  if (!res.ok) throw new Error('Failed to fetch model status');
  return res.json();
}
