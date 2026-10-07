'use client'
import { useEffect, useRef, useState } from 'react'
import type { AlertMessage } from '@/types'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000'
const MAX_ALERTS = 50

export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertMessage[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`${WS_URL}/ws/alerts`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        setTimeout(connect, 3000) // reconnect
      }
      ws.onmessage = (e) => {
        try {
          const msg: AlertMessage = JSON.parse(e.data)
          setAlerts((prev) => [msg, ...prev].slice(0, MAX_ALERTS))
        } catch {}
      }
    }
    connect()
    return () => wsRef.current?.close()
  }, [])

  return { alerts, connected }
}
