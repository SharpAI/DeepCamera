'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { INCIDENT_LABEL } from '@/lib/utils'
import type { IncidentType } from '@/types'

export function IncidentTypeChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).map(([key, value]) => ({
    name: INCIDENT_LABEL[key as IncidentType] ?? key,
    value,
  })).sort((a, b) => b.value - a.value)

  if (!entries.length) return <p className="text-gray-600 text-sm text-center py-8">No data</p>

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={entries} layout="vertical" margin={{ left: 8, right: 8 }}>
        <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={110} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
        <Bar dataKey="value" radius={4}>
          {entries.map((_, i) => <Cell key={i} fill="#0284c7" />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
