import { api } from '@/lib/api'
import { CameraManager } from '@/components/camera/CameraManager'

export const revalidate = 0

export default async function CamerasPage() {
  const cameras = await api.cameras.list().catch(() => [])
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Cameras</h1>
      <CameraManager initialCameras={cameras} />
    </div>
  )
}
