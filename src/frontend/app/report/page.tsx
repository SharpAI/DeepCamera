'use client'
import { useState } from 'react'
import { api } from '@/lib/api'
import { FileText, Download, Loader2 } from 'lucide-react'

export default function ReportPage() {
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<{ period: { from: string; to: string }; district: string; total_incidents: number; report: string } | null>(null)
  const [district, setDistrict] = useState('')
  const [hours, setHours] = useState('8')

  async function generate() {
    setLoading(true)
    setReport(null)
    try {
      const to = new Date()
      const from = new Date(to.getTime() - parseInt(hours) * 3600 * 1000)
      const result = await api.agent.report(from.toISOString(), to.toISOString(), district || undefined)
      setReport(result)
    } finally {
      setLoading(false)
    }
  }

  function download() {
    if (!report) return
    const blob = new Blob([report.report], { type: 'text/plain' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `report-${new Date().toISOString().slice(0, 16)}.txt`
    a.click()
  }

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-xl font-semibold text-white">Shift Report Generator</h1>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Time Window</label>
            <select
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="4">Last 4 hours</option>
              <option value="8">Last 8 hours (shift)</option>
              <option value="12">Last 12 hours</option>
              <option value="24">Last 24 hours</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">District (optional)</label>
            <input
              type="text"
              placeholder="All districts"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-brand-500 placeholder-gray-600"
            />
          </div>
        </div>

        <button
          onClick={generate}
          disabled={loading}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-sm px-5 py-2.5 rounded-lg transition-colors"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <FileText size={15} />}
          {loading ? 'Generating…' : 'Generate Report'}
        </button>
      </div>

      {report && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">
                Report — {report.district === 'all' ? 'All Districts' : report.district}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {new Date(report.period.from).toLocaleString()} → {new Date(report.period.to).toLocaleString()}
                {' · '}{report.total_incidents} incidents
              </p>
            </div>
            <button
              onClick={download}
              className="flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-300"
            >
              <Download size={14} /> Download
            </button>
          </div>
          <pre className="whitespace-pre-wrap text-sm text-gray-300 bg-gray-800 rounded-lg p-4 overflow-auto max-h-96 scrollbar-thin">
            {report.report}
          </pre>
        </div>
      )}
    </div>
  )
}
