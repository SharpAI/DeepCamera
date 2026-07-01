'use client'
import { useState } from 'react'
import type { Camera } from '@/types'
import { api } from '@/lib/api'
import { Plus, Trash2, ToggleLeft, ToggleRight, MapPin } from 'lucide-react'

interface Props { initialCameras: Camera[] }

const EMPTY: Partial<Camera> = { name: '', rtsp_url: '', location: '', district: '' }

export function CameraManager({ initialCameras }: Props) {
  const [cameras, setCameras] = useState(initialCameras)
  const [form, setForm] = useState<Partial<Camera>>(EMPTY)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)

  async function addCamera() {
    if (!form.name || !form.rtsp_url) return
    setSaving(true)
    try {
      const cam = await api.cameras.create(form)
      setCameras((prev) => [...prev, cam])
      setForm(EMPTY)
      setShowForm(false)
    } finally {
      setSaving(false)
    }
  }

  async function toggleActive(cam: Camera) {
    const updated = await api.cameras.update(cam.id, { is_active: !cam.is_active })
    setCameras((prev) => prev.map((c) => (c.id === cam.id ? updated : c)))
  }

  async function deleteCamera(id: string) {
    if (!confirm('Delete this camera?')) return
    await api.cameras.delete(id)
    setCameras((prev) => prev.filter((c) => c.id !== id))
  }

  return (
    <div className="space-y-4">
      {/* Add camera button */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={15} /> Add Camera
        </button>
      </div>

      {/* Add camera form */}
      {showForm && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
          <p className="text-sm font-medium text-white mb-1">New Camera</p>
          <div className="grid grid-cols-2 gap-3">
            {[
              { key: 'name', placeholder: 'Camera name *', required: true },
              { key: 'rtsp_url', placeholder: 'rtsp://... *', required: true },
              { key: 'location', placeholder: 'Location (e.g. Main St & 5th Ave)' },
              { key: 'district', placeholder: 'District' },
            ].map(({ key, placeholder }) => (
              <input
                key={key}
                type="text"
                placeholder={placeholder}
                value={(form as Record<string, string>)[key] ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                className="bg-gray-800 text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-brand-500 placeholder-gray-600"
              />
            ))}
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="text-sm text-gray-400 hover:text-white px-3 py-2">Cancel</button>
            <button
              onClick={addCamera}
              disabled={saving || !form.name || !form.rtsp_url}
              className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg"
            >
              {saving ? 'Adding…' : 'Add'}
            </button>
          </div>
        </div>
      )}

      {/* Camera list */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">RTSP URL</th>
              <th className="px-4 py-3 text-left">Location</th>
              <th className="px-4 py-3 text-left">District</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((cam) => (
              <tr key={cam.id} className="border-b border-gray-800 hover:bg-gray-800/40">
                <td className="px-4 py-3 text-white font-medium">{cam.name}</td>
                <td className="px-4 py-3 text-gray-400 font-mono text-xs truncate max-w-xs">{cam.rtsp_url}</td>
                <td className="px-4 py-3 text-gray-400 text-xs">
                  {cam.location ? <span className="flex items-center gap-1"><MapPin size={10}/>{cam.location}</span> : '—'}
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{cam.district ?? '—'}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${cam.is_active ? 'bg-green-900/40 text-green-400' : 'bg-gray-700 text-gray-500'}`}>
                    {cam.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2 text-gray-500">
                    <button onClick={() => toggleActive(cam)} className="hover:text-white" title="Toggle active">
                      {cam.is_active ? <ToggleRight size={16} className="text-green-400" /> : <ToggleLeft size={16} />}
                    </button>
                    <button onClick={() => deleteCamera(cam.id)} className="hover:text-red-400" title="Delete">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!cameras.length && (
              <tr><td colSpan={6} className="text-center py-10 text-gray-600">No cameras yet. Add one above.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
