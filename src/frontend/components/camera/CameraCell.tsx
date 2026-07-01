'use client'
import { useState } from 'react'
import type { Camera } from '@/types'
import { Scan, MapPin, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

interface Props { camera: Camera }

export function CameraCell({ camera }: Props) {
  const [analyzing, setAnalyzing] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  async function triggerAnalysis() {
    setAnalyzing(true)
    setMsg(null)
    try {
      const job = await api.analyze.trigger(camera.id)
      setMsg(`Job queued: ${job.job_id.slice(0, 8)}…`)
    } catch {
      setMsg('Failed to queue job')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden group relative">
      {/* Stream placeholder — replace src with actual HLS URL in production */}
      <div className="aspect-video bg-gray-900 flex items-center justify-center relative">
        <img
          src={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/cameras/${camera.id}/stream-url`}
          alt={camera.name}
          className="w-full h-full object-cover hidden"
          onError={(e) => (e.currentTarget.style.display = 'none')}
        />
        <div className="flex flex-col items-center gap-1 text-gray-600">
          <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
            <div className={`w-2 h-2 rounded-full ${camera.is_active ? 'bg-green-400' : 'bg-gray-600'}`} />
          </div>
          <span className="text-xs">{camera.is_active ? 'Live' : 'Offline'}</span>
        </div>

        {/* Analyze button overlay */}
        <button
          onClick={triggerAnalysis}
          disabled={analyzing}
          className="absolute top-2 right-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white p-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
          title="Trigger VLM analysis"
        >
          {analyzing ? <Loader2 size={13} className="animate-spin" /> : <Scan size={13} />}
        </button>
      </div>

      <div className="p-2">
        <p className="text-xs font-medium text-white truncate">{camera.name}</p>
        {camera.location && (
          <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
            <MapPin size={10} /> {camera.location}
          </p>
        )}
        {msg && <p className="text-xs text-brand-500 mt-1">{msg}</p>}
      </div>
    </div>
  )
}
