'use client'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS: Record<string, string> = {
  low:      '#60a5fa',
  medium:   '#facc15',
  high:     '#f97316',
  critical: '#ef4444',
}

export function SeverityChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).map(([name, value]) => ({ name, value }))
  if (!entries.length) return <p className="text-gray-600 text-sm text-center py-8">No data</p>

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie data={entries} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
          {entries.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name] ?? '#6b7280'} />
          ))}
        </Pie>
        <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
