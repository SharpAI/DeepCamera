import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { SeverityLevel, IncidentType } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const SEVERITY_COLOR: Record<SeverityLevel, string> = {
  low:      'bg-blue-100 text-blue-800',
  medium:   'bg-yellow-100 text-yellow-800',
  high:     'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

export const SEVERITY_DOT: Record<SeverityLevel, string> = {
  low:      'bg-blue-400',
  medium:   'bg-yellow-400',
  high:     'bg-orange-500',
  critical: 'bg-red-600',
}

export const INCIDENT_LABEL: Record<IncidentType, string> = {
  traffic_accident:  'Traffic Accident',
  suspicious_person: 'Suspicious Person',
  crowd_anomaly:     'Crowd Anomaly',
  wrong_way:         'Wrong Way',
  abandoned_object:  'Abandoned Object',
  fight:             'Fight',
  fire_smoke:        'Fire / Smoke',
  other:             'Other',
}

export function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
