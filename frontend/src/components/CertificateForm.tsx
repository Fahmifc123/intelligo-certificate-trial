import React from 'react'
import { Upload, FileText, Image as ImageIcon, AlertCircle, Eye, X } from 'lucide-react'
import type { CertificateFormProps } from '../types'
import certificateOptions from '../data/certificateOptions.json'
import CustomDropdown from './CustomDropdown'

const CertificateForm = ({ 
  formData, 
  file, 
  screenshot,
  onInputChange, 
  onFileChange, 
  onScreenshotChange,
  onSubmit 
}: CertificateFormProps): React.JSX.Element => {
  const [showExampleModal, setShowExampleModal] = React.useState(false)
  
  return (
    <div className="card p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
          <FileText className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-xl font-semibold text-secondary">
          Formulir Klaim Sertifikat
        </h2>
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nama Lengkap
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={onInputChange}
              placeholder="Masukkan nama lengkap"
              required
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={onInputChange}
              placeholder="email@contoh.com"
              required
              className="input-field"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Judul Project
          </label>
          <input
            type="text"
            name="project_title"
            value={formData.project_title}
            onChange={onInputChange}
            placeholder="Contoh: Analisis Sentimen Twitter dengan Python"
            required
            className="input-field"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pilih Kelas
          </label>
          <CustomDropdown
            name="program_title"
            value={formData.program_title}
            onChange={onInputChange}
            options={certificateOptions.certificateOptions}
            placeholder="Pilih kelas yang diikuti"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tanggal Mulai
            </label>
            <input
              type="date"
              name="start_date"
              value={formData.start_date}
              onChange={onInputChange}
              required
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tanggal Selesai
            </label>
            <input
              type="date"
              name="end_date"
              value={formData.end_date}
              onChange={onInputChange}
              required
              className="input-field"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Link Postingan (LinkedIn/Instagram)
          </label>
          <input
            type="url"
            name="social_link"
            value={formData.social_link}
            onChange={onInputChange}
            placeholder="https://linkedin.com/in/username/post/..."
            required
            className="input-field"
          />
        </div>

        {/* Screenshot Upload Section */}
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-secondary">
                Upload screenshot bukti kamu sudah share project di LinkedIn/Instagram
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Pastikan terlihat caption dan tag @intelligo.id
              </p>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Screenshot Postingan <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type="file"
              onChange={onScreenshotChange}
              accept=".jpg,.jpeg,.png"
              required
              className="hidden"
              id="screenshot-upload"
            />
            <label
              htmlFor="screenshot-upload"
              className="flex items-center justify-center gap-3 w-full px-4 py-6 border-2 border-dashed border-primary/30 rounded-lg cursor-pointer hover:border-primary hover:bg-primary/5 transition-all duration-200 bg-primary/5"
            >
              <ImageIcon className="w-6 h-6 text-primary" />
              <div className="text-left">
                <p className="text-sm font-medium text-secondary">
                  {screenshot ? screenshot.name : 'Klik untuk upload screenshot'}
                </p>
                <p className="text-xs text-gray-500">
                  JPG atau PNG (Maksimal 2MB)
                </p>
              </div>
            </label>
          </div>
          
          {/* Example Button */}
          <button
            type="button"
            onClick={() => setShowExampleModal(true)}
            className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            Lihat Contoh Screenshot
          </button>
          
          {/* Screenshot Preview */}
          {screenshot && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-600">
                File: {screenshot.name} ({(screenshot.size / 1024).toFixed(1)} KB)
              </p>
            </div>
          )}
        </div>

        {/* Optional Project File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Project (Opsional)
          </label>
          <div className="relative">
            <input
              type="file"
              onChange={onFileChange}
              accept=".pdf,.ppt,.pptx,.zip"
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="flex items-center justify-center gap-3 w-full px-4 py-6 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-primary hover:bg-primary/5 transition-all duration-200"
            >
              <Upload className="w-6 h-6 text-gray-400" />
              <div className="text-left">
                <p className="text-sm font-medium text-gray-700">
                  {file ? file.name : 'Klik untuk upload file'}
                </p>
                <p className="text-xs text-gray-500">
                  PDF, PPT, atau ZIP (Max 10MB)
                </p>
              </div>
            </label>
          </div>
        </div>

        <button
          type="submit"
          className="w-full btn-primary text-lg font-semibold py-4"
        >
          Generate Sertifikat
        </button>
      </form>

      {/* Example Modal */}
      {showExampleModal && (
        <div 
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          onClick={() => setShowExampleModal(false)}
        >
          <div 
            className="relative bg-white rounded-xl shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setShowExampleModal(false)}
              className="absolute top-3 right-3 w-8 h-8 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg z-10"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
            <img
              src="/dummy.png"
              alt="Contoh Screenshot"
              className="max-w-2xl h-auto"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default CertificateForm
