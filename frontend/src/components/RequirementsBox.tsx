import { CheckCircle, Share2, Hash, AtSign } from 'lucide-react'
import type { Requirement } from '../types'

const RequirementsBox = (): React.JSX.Element => {
  const requirements: Requirement[] = [
    {
      icon: Share2,
      text: 'Share project ke LinkedIn atau Instagram'
    },
    {
      icon: AtSign,
      text: 'Tag akun resmi @intelligo.id di postingan'
    },
    {
      icon: Hash,
      text: 'Gunakan hashtag #IntelligoID #TrialBootcamp'
    }
  ]

  return (
    <div className="card p-6 sticky top-6">
      <h3 className="text-lg font-semibold text-secondary mb-4">
        Syarat Klaim Sertifikat
      </h3>
      
      <div className="space-y-4">
        {requirements.map((req, index) => (
          <div key={index} className="flex items-start gap-3">
            <div className="flex-shrink-0 w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center mt-0.5">
              <CheckCircle className="w-4 h-4 text-primary" />
            </div>
            <div className="flex items-start gap-2">
              <req.icon className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
              <p className="text-sm text-gray-600">{req.text}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-accent rounded-lg">
        <p className="text-xs text-gray-500 text-center">
          Pastikan postingan kamu bersifat publik agar dapat diverifikasi oleh sistem kami.
        </p>
      </div>
    </div>
  )
}

export default RequirementsBox
