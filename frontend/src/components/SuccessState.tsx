import { CheckCircle, Download, RotateCcw } from 'lucide-react'
import type { SuccessStateProps } from '../types'

const SuccessState = ({ certificateUrl, onReset }: SuccessStateProps): React.JSX.Element => {
  const handleDownload = (): void => {
    window.open(certificateUrl, '_blank')
  }

  return (
    <div className="card p-12 text-center max-w-2xl mx-auto">
      <div className="flex flex-col items-center gap-6">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>
        
        <div>
          <h3 className="text-2xl font-bold text-secondary mb-2">
            Selamat! Sertifikat Berhasil Dibuat
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Sertifikat trial bootcamp kamu telah berhasil dibuat. 
            Silakan download sertifikatmu sekarang.
          </p>
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
            Klaim Lagi
          </button>
        </div>
      </div>
    </div>
  )
}

export default SuccessState
