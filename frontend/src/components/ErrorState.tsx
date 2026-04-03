import { XCircle, RefreshCw } from 'lucide-react'
import type { ErrorStateProps } from '../types'

const ErrorState = ({ message, onRetry }: ErrorStateProps): React.JSX.Element => {
  return (
    <div className="card p-12 text-center max-w-2xl mx-auto">
      <div className="flex flex-col items-center gap-6">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
          <XCircle className="w-10 h-10 text-red-600" />
        </div>
        
        <div>
          <h3 className="text-xl font-bold text-secondary mb-2">
            Validasi Gagal
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            {message || 'Pastikan kamu sudah share project ke LinkedIn/Instagram dan tag @intelligo.id'}
          </p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-md w-full">
          <p className="text-sm text-red-700">
            <strong>Tips:</strong> Pastikan postingan bersifat publik dan 
            menggunakan hashtag yang sesuai.
          </p>
        </div>

        <button
          onClick={onRetry}
          className="btn-primary flex items-center gap-2"
        >
          <RefreshCw className="w-5 h-5" />
          Coba Lagi
        </button>
      </div>
    </div>
  )
}

export default ErrorState
