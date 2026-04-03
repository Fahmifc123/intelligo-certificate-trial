import { Loader2 } from 'lucide-react'

const LoadingState = (): React.JSX.Element => {
  return (
    <div className="card p-12 text-center max-w-2xl mx-auto">
      <div className="flex flex-col items-center gap-6">
        <div className="relative">
          <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
          </div>
        </div>
        
        <div>
          <h3 className="text-xl font-semibold text-secondary mb-2">
            Memvalidasi Submission
          </h3>
          <p className="text-gray-600">
            Mohon tunggu sebentar, kami sedang memeriksa postingan kamu...
          </p>
        </div>

        <div className="w-full max-w-md bg-gray-200 rounded-full h-2 mt-4">
          <div className="bg-primary h-2 rounded-full animate-pulse w-3/4"></div>
        </div>
      </div>
    </div>
  )
}

export default LoadingState
