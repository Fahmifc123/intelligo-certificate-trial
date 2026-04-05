import { CheckCircle, Download, RotateCcw } from 'lucide-react'

interface AlreadyGeneratedStateProps {
  certificateId: string
  submittedAt: string
  certificateUrl: string
  onReset: () => void
}

const AlreadyGeneratedState = ({
  certificateId,
  submittedAt,
  certificateUrl,
  onReset
}: AlreadyGeneratedStateProps): React.JSX.Element => {
  const handleDownload = () => {
    window.open(certificateUrl, '_blank')
  }

  return (
    <div className="card p-12 text-center max-w-2xl mx-auto">
      <div className="flex flex-col items-center gap-6">
        <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
          <CheckCircle className="w-10 h-10 text-blue-600" />
        </div>

        <div>
          <h3 className="text-xl font-bold text-secondary mb-2">
            Sertifikat Sudah Pernah Dibuat
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Email Anda sudah pernah membuat sertifikat sebelumnya. Hanya diperbolehkan sekali generate per email.
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-md w-full text-left">
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-600 font-medium">ID Sertifikat</p>
              <p className="text-lg font-bold text-secondary break-words">{certificateId}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 font-medium">Dibuat Pada</p>
              <p className="text-sm text-gray-700">{submittedAt}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 w-full max-w-md mt-4">
          <button
            onClick={handleDownload}
            className="flex-1 btn-primary flex items-center justify-center gap-2"
          >
            <Download className="w-5 h-5" />
            Download Sertifikat
          </button>

          <button
            onClick={onReset}
            className="flex-1 bg-gray-100 text-secondary font-medium py-3 px-6 rounded-xl hover:bg-gray-200 transition-all duration-200 flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-5 h-5" />
            Kembali
          </button>
        </div>
      </div>
    </div>
  )
}

export default AlreadyGeneratedState
