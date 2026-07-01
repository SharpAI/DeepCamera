import { api } from '@/lib/api'
import { StatCard } from '@/components/ui/StatCard'
import { SeverityChart } from '@/components/incident/SeverityChart'
import { IncidentTypeChart } from '@/components/incident/IncidentTypeChart'
import { RecentIncidents } from '@/components/incident/RecentIncidents'
import { CameraGrid } from '@/components/camera/CameraGrid'
import { AlertTriangle, Camera, Activity, ShieldAlert } from 'lucide-react'

export const revalidate = 30

export default async function DashboardPage() {
  const [cameras, stats, recentIncidents] = await Promise.all([
    api.cameras.list().catch(() => []),
    api.incidents.stats().catch(() => ({ total: 0, by_type: {}, by_severity: {}, by_camera: {} })),
    api.incidents.list({ limit: '10', resolved: 'open' }).catch(() => []),
  ])

  const critical = stats.by_severity['critical'] ?? 0
  const activeCams = cameras.filter((c) => c.is_active).length

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Incidents" value={stats.total} icon={AlertTriangle} color="blue" />
        <StatCard label="Critical" value={critical} icon={ShieldAlert} color="red" />
        <StatCard label="Active Cameras" value={activeCams} icon={Camera} color="green" />
        <StatCard label="Open Cases" value={recentIncidents.length} icon={Activity} color="yellow" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-sm font-medium text-gray-400 mb-3">Incidents by Severity</p>
          <SeverityChart data={stats.by_severity} />
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-sm font-medium text-gray-400 mb-3">Incidents by Type</p>
          <IncidentTypeChart data={stats.by_type} />
        </div>
      </div>

      {/* Camera grid + recent incidents */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <CameraGrid cameras={cameras.slice(0, 6)} />
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-sm font-medium text-gray-400 mb-3">Open Incidents</p>
          <RecentIncidents incidents={recentIncidents} />
        </div>
      </div>
    </div>
  )
}
