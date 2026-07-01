import { api } from '@/lib/api'
import { IncidentTable } from '@/components/incident/IncidentTable'

export const revalidate = 0

export default async function IncidentsPage({
  searchParams,
}: {
  searchParams: Record<string, string>
}) {
  const incidents = await api.incidents
    .list({
      incident_type: searchParams.type,
      severity: searchParams.severity,
      resolved: searchParams.resolved ?? 'open',
      limit: '100',
    })
    .catch(() => [])

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Incidents</h1>
      <IncidentTable incidents={incidents} />
    </div>
  )
}
