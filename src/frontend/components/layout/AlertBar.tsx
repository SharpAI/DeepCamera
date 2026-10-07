'use client'
import { useAlerts } from '@/hooks/useAlerts'
import { SEVERITY_DOT, INCIDENT_LABEL, fmtTime } from '@/lib/utils'
import { Wifi, WifiOff } from 'lucide-react'

export function AlertBar() {
  const { alerts, connected } = useAlerts()
  const latest = alerts[0]

  return (
    <div className="h-10 bg-gray-900 border-b border-gray-800 flex items-center px-4 gap-4 text-sm">
      {/* Connection indicator */}
      <span className={`flex items-center gap-1.5 text-xs ${connected ? 'text-green-400' : 'text-gray-500'}`}>
        {connected ? <Wifi size={13} /> : <WifiOff size={13} />}
        {connected ? 'Live' : 'Offline'}
      </span>

      {/* Latest alert ticker */}
      {latest ? (
        <div className="flex items-center gap-2 overflow-hidden">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${SEVERITY_DOT[latest.severity]}`} />
          <span className="text-gray-300 truncate">
            [{fmtTime(latest.occurred_at)}] {INCIDENT_LABEL[latest.incident_type]} —{' '}
            <span className="text-gray-400">{latest.description?.slice(0, 100)}</span>
          </span>
        </div>
      ) : (
        <span className="text-gray-600 text-xs">No alerts yet</span>
      )}

      <span className="ml-auto text-xs text-gray-600">
        {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
      </span>
    </div>
  )
}
