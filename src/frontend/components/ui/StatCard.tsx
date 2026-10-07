import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const COLOR = {
  blue:   'text-blue-400 bg-blue-900/30',
  red:    'text-red-400 bg-red-900/30',
  green:  'text-green-400 bg-green-900/30',
  yellow: 'text-yellow-400 bg-yellow-900/30',
}

interface Props {
  label: string
  value: number
  icon: LucideIcon
  color: keyof typeof COLOR
}

export function StatCard({ label, value, icon: Icon, color }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 flex items-center gap-4">
      <div className={cn('p-2.5 rounded-lg', COLOR[color])}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      </div>
    </div>
  )
}
