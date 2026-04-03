import { useState } from 'react'
import HeroSection from '../components/HeroSection'
import CertificateForm from '../components/CertificateForm'
import RequirementsBox from '../components/RequirementsBox'
import LoadingState from '../components/LoadingState'
import SuccessState from '../components/SuccessState'
import ErrorState from '../components/ErrorState'
import type { CertificateFormData, CertificateResponse } from '../types'
import { Beaker } from 'lucide-react'

type Status = 'idle' | 'loading' | 'success' | 'error'

const ClaimCertificate = (): React.JSX.Element => {
  const [formData, setFormData] = useState<CertificateFormData>({
    name: '',
    email: '',
    project_title: '',
    social_link: '',
  })
  const [file, setFile] = useState<File | null>(null)
  const [screenshot, setScreenshot] = useState<File | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [certificateUrl, setCertificateUrl] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string>('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleScreenshotChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      
      // Validate file size (max 2MB)
      if (selectedFile.size > 2 * 1024 * 1024) {
        alert('Ukuran file terlalu besar. Maksimal 2MB.')
        return
      }
      
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
      if (!allowedTypes.includes(selectedFile.type)) {
        alert('Format file tidak didukung. Gunakan JPG atau PNG.')
        return
      }
      
      setScreenshot(selectedFile)
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault()
    
    // Validate screenshot is uploaded (skip for dummy data mode if needed)
    if (!screenshot) {
      alert('Silakan upload screenshot bukti postingan.')
      return
    }
    
    setStatus('loading')

    try {
      // Check if using dummy data (screenshot name contains 'dummy')
      const isDummyData = screenshot?.name.includes('dummy')
      const endpoint = isDummyData ? 'http://localhost:8000/generate-dummy' : 'http://localhost:8000/submit'
      
      // Create FormData for multipart/form-data submission
      const formDataToSend = new FormData()
      formDataToSend.append('name', formData.name)
      formDataToSend.append('email', formData.email)
      formDataToSend.append('project_title', formData.project_title)
      formDataToSend.append('social_link', formData.social_link)
      
      // Only append screenshot for real submission
      if (!isDummyData && screenshot) {
        formDataToSend.append('screenshot', screenshot)
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formDataToSend,
      })

      const data: CertificateResponse = await response.json()

      if (data.status === 'success') {
        setCertificateUrl(data.certificate_url || '')
        setStatus('success')
      } else {
        setErrorMessage(data.message || 'Validasi gagal, pastikan kamu sudah share project')
        setStatus('error')
      }
    } catch (error) {
      setErrorMessage('Terjadi kesalahan. Silakan coba lagi.')
      setStatus('error')
    }
  }

  const handleReset = (): void => {
    setStatus('idle')
    setFormData({
      name: '',
      email: '',
      project_title: '',
      social_link: '',
    })
    setFile(null)
    setScreenshot(null)
    setCertificateUrl('')
    setErrorMessage('')
  }

  // Generate dummy data for testing
  const generateDummyData = async (): Promise<void> => {
    const dummyData: CertificateFormData = {
      name: 'Mukhamad Alyasyi Thobiq',
      email: 'alyasyi.thobiq@email.com',
      project_title: 'Implementasi Chatbot Assistant Menggunakan Metode TF-IDF dan Cosine Similarity',
      social_link: 'https://linkedin.com/in/alyasyi-thobiq',
    }
    setFormData(dummyData)
    
    // Fetch the dummy.png file from backend
    try {
      const response = await fetch('http://localhost:8000/static/dummy.png')
      if (!response.ok) {
        throw new Error('Failed to fetch dummy image')
      }
      const blob = await response.blob()
      const dummyFile = new File([blob], 'screenshot_dummy.png', { type: 'image/png' })
      setScreenshot(dummyFile)
      alert('Dummy data generated! Click "Generate Sertifikat" to create certificate.')
    } catch (error) {
      console.error('Failed to load dummy image:', error)
      alert('Failed to load dummy image. Please upload a screenshot manually.')
    }
  }

  return (
    <div className="min-h-screen bg-accent">
      <HeroSection />
      
      <main className="container mx-auto px-4 py-12 max-w-6xl">
        {status === 'loading' && <LoadingState />}
        
        {status === 'success' && (
          <SuccessState 
            certificateUrl={certificateUrl} 
            onReset={handleReset}
          />
        )}
        
        {status === 'error' && (
          <ErrorState 
            message={errorMessage}
            onRetry={handleReset}
          />
        )}
        
        {status === 'idle' && (
          <>
            {/* Dummy Data Button */}
            <div className="mb-6 flex justify-end">
              <button
                onClick={generateDummyData}
                type="button"
                className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-all duration-200 text-sm font-medium"
              >
                <Beaker className="w-4 h-4" />
                Generate Dummy Data
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <CertificateForm 
                  formData={formData}
                  file={file}
                  screenshot={screenshot}
                  onInputChange={handleInputChange}
                  onFileChange={handleFileChange}
                  onScreenshotChange={handleScreenshotChange}
                  onSubmit={handleSubmit}
                />
              </div>
              <div className="lg:col-span-1">
                <RequirementsBox />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default ClaimCertificate
