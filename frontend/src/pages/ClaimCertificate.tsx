import { useState } from 'react'
import HeroSection from '../components/HeroSection'
import CertificateForm from '../components/CertificateForm'
import RequirementsBox from '../components/RequirementsBox'
import LoadingState from '../components/LoadingState'
import SuccessState from '../components/SuccessState'
import ErrorState from '../components/ErrorState'
import type { CertificateFormData, CertificateResponse } from '../types'

type Status = 'idle' | 'loading' | 'success' | 'error'

const ClaimCertificate = (): React.JSX.Element => {
  const [formData, setFormData] = useState<CertificateFormData>({
    name: '',
    email: '',
    project_title: '',
    program_title: '',
    start_date: '',
    end_date: '',
    social_link: '',
  })
  const [file, setFile] = useState<File | null>(null)
  const [screenshot, setScreenshot] = useState<File | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [certificateUrl, setCertificateUrl] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string>('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>): void => {
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
      const endpoint = 'http://43.134.70.75:8002/submit'
      
      // Create FormData for multipart/form-data submission
      const formDataToSend = new FormData()
      formDataToSend.append('full_name', formData.name)
      formDataToSend.append('email', formData.email)
      formDataToSend.append('project_title', formData.project_title)
      formDataToSend.append('program_title', formData.program_title)
      formDataToSend.append('start_date', formData.start_date)
      formDataToSend.append('end_date', formData.end_date)
      formDataToSend.append('social_link', formData.social_link)
      formDataToSend.append('screenshot', screenshot)

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formDataToSend,
      })

      const data: CertificateResponse = await response.json()

      if (data.success) {
        setCertificateUrl(data.certificate_url || '')
        setStatus('success')
      } else {
        setErrorMessage(data.message || data.error || 'Validasi gagal, pastikan kamu sudah share project')
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
      program_title: '',
      start_date: '',
      end_date: '',
      social_link: '',
    })
    setFile(null)
    setScreenshot(null)
    setCertificateUrl('')
    setErrorMessage('')
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
