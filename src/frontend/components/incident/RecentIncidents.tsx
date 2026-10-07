import type { Incident } from '@/types'
import { SEVERITY_COLOR, INCIDENT_LABEL, fmtDateTime } from '@/lib/utils'

export function RecentIncidents({ incidents }: { incidents: Incident[] }) {
  if (!incidents.length)
    return <p className="text-gray-600 text-sm text-center py-6">No open incidents</p>

  return (
    <ul className="space-y-3 overflow-y-auto max-h-72 scrollbar-thin pr-1">
      {incidents.map((inc) => (
        <li key={inc.id} className="bg-gray-800 rounded-lg p-3 space-y-1">
          <div className="flex items-center justify-between gap-2">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SEVERITY_COLOR[inc.severity]}`}>
              {inc.severity}
            </span>
            <span className="text-xs text-gray-500">{fmtDateTime(inc.occurred_at)}</span>
          </div>
          <p className="text-sm text-white font-medium">{INCIDENT_LABEL[inc.incident_type]}</p>
          {inc.description && (
            <p className="text-xs text-gray-400 line-clamp-2">{inc.description}</p>
          )}
        </li>
      ))}
    </ul>
  )
}
