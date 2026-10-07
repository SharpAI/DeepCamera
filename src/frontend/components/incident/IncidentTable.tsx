'use client'
import { useState } from 'react'
import type { Incident } from '@/types'
import { SEVERITY_COLOR, INCIDENT_LABEL, fmtDateTime } from '@/lib/utils'
import { api } from '@/lib/api'
import { CheckCircle, XCircle, Image as ImageIcon } from 'lucide-react'

export function IncidentTable({ incidents }: { incidents: Incident[] }) {
  const [rows, setRows] = useState(incidents)

  async function resolve(id: string, status: 'resolved' | 'false_alarm') {
    const updated = await api.incidents.resolve(id, status)
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, resolved: updated.resolved } : r)))
  }

  if (!rows.length)
    return <div className="text-center py-16 text-gray-600">No incidents found</div>

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
              <th className="px-4 py-3 text-left">Time</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Severity</th>
              <th className="px-4 py-3 text-left">Description</th>
              <th className="px-4 py-3 text-left">Conf.</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((inc) => (
              <tr key={inc.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{fmtDateTime(inc.occurred_at)}</td>
                <td className="px-4 py-3 text-white font-medium">{INCIDENT_LABEL[inc.incident_type]}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLOR[inc.severity]}`}>
                    {inc.severity}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 max-w-xs truncate">{inc.description ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400">
                  {inc.confidence != null ? `${(inc.confidence * 100).toFixed(0)}%` : '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    inc.resolved === 'open' ? 'bg-red-900/40 text-red-400' :
                    inc.resolved === 'resolved' ? 'bg-green-900/40 text-green-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                    {inc.resolved}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {inc.resolved === 'open' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => resolve(inc.id, 'resolved')}
                        className="text-green-500 hover:text-green-400"
                        title="Mark resolved"
                      >
                        <CheckCircle size={16} />
                      </button>
                      <button
                        onClick={() => resolve(inc.id, 'false_alarm')}
                        className="text-gray-500 hover:text-gray-400"
                        title="Mark false alarm"
                      >
                        <XCircle size={16} />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
