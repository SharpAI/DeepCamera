'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Camera, AlertTriangle, MessageSquare, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/dashboard',  label: 'Dashboard',  icon: LayoutDashboard },
  { href: '/cameras',    label: 'Cameras',    icon: Camera },
  { href: '/incidents',  label: 'Incidents',  icon: AlertTriangle },
  { href: '/agent',      label: 'AI Agent',   icon: MessageSquare },
  { href: '/report',     label: 'Reports',    icon: FileText },
]

export function Sidebar() {
  const path = usePathname()
  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="px-5 py-5 border-b border-gray-800">
        <span className="text-brand-500 font-bold text-lg tracking-tight">NamuCam</span>
        <p className="text-gray-500 text-xs mt-0.5">City Surveillance</p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              path.startsWith(href)
                ? 'bg-brand-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-gray-800 text-xs text-gray-600">
        v1.0.0
      </div>
    </aside>
  )
}
