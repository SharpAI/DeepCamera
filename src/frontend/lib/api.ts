import type { Camera, Incident, IncidentStats } from '@/types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}

// ---------- Cameras ----------
export const api = {
  cameras: {
    list: (district?: string) =>
      req<Camera[]>(`/cameras/${district ? `?district=${district}` : ''}`),
    get: (id: string) => req<Camera>(`/cameras/${id}`),
    create: (body: Partial<Camera>) =>
      req<Camera>('/cameras/', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: Partial<Camera>) =>
      req<Camera>(`/cameras/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (id: string) =>
      fetch(`${BASE}/api/v1/cameras/${id}`, { method: 'DELETE' }),
    streamUrls: (id: string) =>
      req<{ hls: string; webrtc: string; snapshot: string }>(`/cameras/${id}/stream-url`),
  },

  incidents: {
    list: (params?: Record<string, string | undefined>) => {
      const qs = new URLSearchParams(
        Object.fromEntries(Object.entries(params ?? {}).filter(([, v]) => v != null)) as Record<string, string>
      ).toString()
      return req<Incident[]>(`/incidents/${qs ? `?${qs}` : ''}`)
    },
    get: (id: string) => req<Incident>(`/incidents/${id}`),
    stats: (params?: { from_time?: string; to_time?: string }) => {
      const qs = new URLSearchParams(params as Record<string, string>).toString()
      return req<IncidentStats>(`/incidents/stats${qs ? `?${qs}` : ''}`)
    },
    resolve: (id: string, status: 'resolved' | 'false_alarm', resolved_by?: string) =>
      req<Incident>(`/incidents/${id}/resolve`, {
        method: 'PATCH',
        body: JSON.stringify({ status, resolved_by }),
      }),
  },

  analyze: {
    trigger: (camera_id: string) =>
      req<{ job_id: string; status: string; message: string }>('/analyze/trigger', {
        method: 'POST',
        body: JSON.stringify({ camera_id }),
      }),
    jobStatus: (job_id: string) =>
      req<{ job_id: string; status: string; result?: Record<string, unknown> }>(`/analyze/jobs/${job_id}`),
  },

  agent: {
    query: (question: string, from_time?: string, to_time?: string) =>
      req<{ question: string; answer: string; incidents_in_context: number }>('/agent/query', {
        method: 'POST',
        body: JSON.stringify({ question, from_time, to_time }),
      }),
    report: (from_time?: string, to_time?: string, district?: string) => {
      const qs = new URLSearchParams(
        Object.fromEntries(
          Object.entries({ from_time, to_time, district }).filter(([, v]) => v != null)
        ) as Record<string, string>
      ).toString()
      return req<{ period: object; district: string; total_incidents: number; report: string }>(
        `/agent/report${qs ? `?${qs}` : ''}`,
        { method: 'POST' }
      )
    },
  },
}
