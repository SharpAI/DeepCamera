'use client'
import { useState } from 'react'
import type { Camera } from '@/types'
import { CameraCell } from './CameraCell'
import { Grid2X2, Grid3X3 } from 'lucide-react'

export function CameraGrid({ cameras }: { cameras: Camera[] }) {
  const [cols, setCols] = useState<2 | 3>(2)

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-gray-400">Live Cameras</p>
        <div className="flex gap-1">
          <button onClick={() => setCols(2)} className={`p-1.5 rounded ${cols === 2 ? 'bg-brand-600 text-white' : 'text-gray-500 hover:text-white'}`}><Grid2X2 size={14} /></button>
          <button onClick={() => setCols(3)} className={`p-1.5 rounded ${cols === 3 ? 'bg-brand-600 text-white' : 'text-gray-500 hover:text-white'}`}><Grid3X3 size={14} /></button>
        </div>
      </div>
      <div className={`grid gap-2 ${cols === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
        {cameras.map((cam) => <CameraCell key={cam.id} camera={cam} />)}
        {!cameras.length && (
          <div className="col-span-2 text-center py-12 text-gray-600 text-sm">No cameras configured</div>
        )}
      </div>
    </div>
  )
}
