export interface Camera {
  id: string
  name: string
  rtsp_url: string
  location: string | null
  latitude: number | null
  longitude: number | null
  district: string | null
  is_active: boolean
  notes: string | null
}

export interface Incident {
  id: string
  camera_id: string
  incident_type: IncidentType
  severity: SeverityLevel
  description: string | null
  snapshot_url: string | null
  clip_url: string | null
  confidence: number | null
  objects_detected: Record<string, unknown> | null
  resolved: 'open' | 'resolved' | 'false_alarm'
  occurred_at: string
  created_at: string
}

export type IncidentType =
  | 'traffic_accident'
  | 'suspicious_person'
  | 'crowd_anomaly'
  | 'wrong_way'
  | 'abandoned_object'
  | 'fight'
  | 'fire_smoke'
  | 'other'

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical'

export interface IncidentStats {
  total: number
  by_type: Record<string, number>
  by_severity: Record<string, number>
  by_camera: Record<string, number>
}

export interface AlertMessage {
  type: 'incident'
  camera_id: string
  incident_type: IncidentType
  severity: SeverityLevel
  description: string
  occurred_at: string
}
