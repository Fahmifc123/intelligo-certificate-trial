import { useEffect, useRef, useState } from 'react'
import { RefreshCw, Trash2, LogOut, Search, Send, CheckCircle2, XCircle, Upload, Download } from 'lucide-react'
import type { Submission } from '../types'

interface BulkRowResult {
  name: string
  email: string
  success: boolean
  certificate_url?: string
  email_sent?: boolean
  email_message?: string
  error?: string
}

interface BulkResult {
  success: boolean
  total?: number
  succeeded?: number
  failed?: number
  results?: BulkRowResult[]
  error?: string
}

const SAMPLE_CSV = 'name,email,program_title\nBudi Santoso,budi@example.com,\nAni Wijaya,ani@example.com,Trial Bootcamp Artificial Intelligence - Intelligo ID\n'

const STORAGE_KEY = 'intelligo_admin_key'

const AdminDashboard = (): React.JSX.Element => {
  const [adminKey, setAdminKey] = useState<string>(() => sessionStorage.getItem(STORAGE_KEY) || '')
  const [keyInput, setKeyInput] = useState('')
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [deletingEmail, setDeletingEmail] = useState<string | null>(null)

  const [manualName, setManualName] = useState('')
  const [manualEmail, setManualEmail] = useState('')
  const [manualProgram, setManualProgram] = useState('')
  const [manualLoading, setManualLoading] = useState(false)
  const [manualResult, setManualResult] = useState<{
    success: boolean
    certificate_url?: string
    email_sent?: boolean
    email_message?: string
    error?: string
  } | null>(null)

  const [bulkFile, setBulkFile] = useState<File | null>(null)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkResult, setBulkResult] = useState<BulkResult | null>(null)
  const bulkFileInputRef = useRef<HTMLInputElement>(null)

  const baseUrl = import.meta.env.VITE_APP_BASE_URL

  const fetchSubmissions = async (key: string): Promise<void> => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${baseUrl}/admin/submissions`, {
        headers: { 'X-Admin-Key': key }
      })
      const data = await response.json()

      if (response.status === 401) {
        setError('Kode akses salah.')
        sessionStorage.removeItem(STORAGE_KEY)
        setAdminKey('')
        return
      }
      if (response.status === 503) {
        setError('Dashboard admin belum dikonfigurasi di server (ADMIN_API_KEY belum di-set).')
        return
      }
      if (!data.success) {
        setError(data.error || 'Gagal memuat data.')
        return
      }

      setSubmissions(data.submissions)
      sessionStorage.setItem(STORAGE_KEY, key)
      setAdminKey(key)
    } catch (err) {
      setError('Tidak bisa terhubung ke server.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (adminKey) {
      fetchSubmissions(adminKey)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleLogin = (e: React.FormEvent): void => {
    e.preventDefault()
    if (keyInput.trim()) {
      fetchSubmissions(keyInput.trim())
    }
  }

  const handleLogout = (): void => {
    sessionStorage.removeItem(STORAGE_KEY)
    setAdminKey('')
    setSubmissions([])
    setKeyInput('')
  }

  const handleReset = async (email: string): Promise<void> => {
    if (!confirm(`Reset submission untuk ${email}? Email ini akan bisa generate sertifikat lagi.`)) {
      return
    }
    setDeletingEmail(email)
    try {
      const response = await fetch(`${baseUrl}/admin/submissions/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Key': adminKey }
      })
      const data = await response.json()
      if (data.success) {
        setSubmissions(prev => prev.filter(s => s.email !== email))
      } else {
        alert(data.error || 'Gagal menghapus.')
      }
    } catch (err) {
      alert('Tidak bisa terhubung ke server.')
    } finally {
      setDeletingEmail(null)
    }
  }

  const handleManualGenerate = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!manualName.trim() || !manualEmail.trim()) return

    setManualLoading(true)
    setManualResult(null)
    try {
      const response = await fetch(`${baseUrl}/admin/generate-manual`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: manualName.trim(),
          email: manualEmail.trim(),
          program_title: manualProgram.trim() || undefined
        })
      })
      const data = await response.json()
      setManualResult(data)
      if (data.success) {
        setManualName('')
        setManualEmail('')
        setManualProgram('')
        fetchSubmissions(adminKey)
      }
    } catch (err) {
      setManualResult({ success: false, error: 'Tidak bisa terhubung ke server.' })
    } finally {
      setManualLoading(false)
    }
  }

  const handleBulkUpload = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!bulkFile) return

    setBulkLoading(true)
    setBulkResult(null)
    try {
      const formData = new FormData()
      formData.append('file', bulkFile)

      const response = await fetch(`${baseUrl}/admin/generate-bulk`, {
        method: 'POST',
        headers: { 'X-Admin-Key': adminKey },
        body: formData
      })
      const data = await response.json()
      setBulkResult(data)
      if (data.success) {
        setBulkFile(null)
        if (bulkFileInputRef.current) bulkFileInputRef.current.value = ''
        fetchSubmissions(adminKey)
      }
    } catch (err) {
      setBulkResult({ success: false, error: 'Tidak bisa terhubung ke server. Kalau file CSV besar, coba pecah jadi beberapa file lebih kecil.' })
    } finally {
      setBulkLoading(false)
    }
  }

  const handleDownloadSample = (): void => {
    const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'contoh-bulk-sertifikat.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const filtered = submissions.filter(s => {
    const q = search.toLowerCase()
    return (
      s.email.toLowerCase().includes(q) ||
      s.full_name.toLowerCase().includes(q) ||
      s.certificate_id.toLowerCase().includes(q)
    )
  })

  if (!adminKey) {
    return (
      <div className="min-h-screen bg-accent flex items-center justify-center px-4">
        <div className="card p-8 max-w-sm w-full">
          <h1 className="text-xl font-bold text-secondary mb-1">Admin Dashboard</h1>
          <p className="text-sm text-gray-500 mb-6">Intelligo ID - Certificate Trial</p>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="password"
              className="input-field"
              placeholder="Kode akses admin"
              value={keyInput}
              onChange={e => setKeyInput(e.target.value)}
              autoFocus
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? 'Memeriksa...' : 'Masuk'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-accent px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-secondary">Admin Dashboard</h1>
            <p className="text-sm text-gray-500">Intelligo ID - Certificate Trial</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => fetchSubmissions(adminKey)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-sm font-medium"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-sm font-medium"
            >
              <LogOut className="w-4 h-4" />
              Keluar
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="card p-6 mb-4">
          <h2 className="text-lg font-semibold text-secondary mb-1">Generate Manual</h2>
          <p className="text-sm text-gray-500 mb-4">
            Generate sertifikat dengan nama bebas dan langsung kirim ke email peserta, tanpa lewat form/validasi publik.
          </p>
          <form onSubmit={handleManualGenerate} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              className="input-field"
              placeholder="Nama Lengkap"
              value={manualName}
              onChange={e => setManualName(e.target.value)}
              required
            />
            <input
              type="email"
              className="input-field"
              placeholder="Email Tujuan"
              value={manualEmail}
              onChange={e => setManualEmail(e.target.value)}
              required
            />
            <input
              type="text"
              className="input-field"
              placeholder="Judul Program (opsional, default: Trial Bootcamp Data Science & AI)"
              value={manualProgram}
              onChange={e => setManualProgram(e.target.value)}
            />
            <button
              type="submit"
              className="btn-primary md:col-span-3 flex items-center justify-center gap-2"
              disabled={manualLoading}
            >
              <Send className="w-4 h-4" />
              {manualLoading ? 'Memproses...' : 'Generate & Kirim Email'}
            </button>
          </form>

          {manualResult && (
            <div className={`mt-4 p-3 rounded-lg text-sm ${manualResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              {manualResult.success ? (
                <div className="space-y-1">
                  <p className="flex items-center gap-2 text-green-700 font-medium">
                    <CheckCircle2 className="w-4 h-4" /> Sertifikat berhasil digenerate.
                  </p>
                  {manualResult.certificate_url && (
                    <a
                      href={manualResult.certificate_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline text-xs block"
                    >
                      Lihat PDF sertifikat
                    </a>
                  )}
                  <p className={`flex items-center gap-2 text-xs ${manualResult.email_sent ? 'text-green-700' : 'text-orange-600'}`}>
                    {manualResult.email_sent ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                    {manualResult.email_message}
                  </p>
                </div>
              ) : (
                <p className="flex items-center gap-2 text-red-700">
                  <XCircle className="w-4 h-4" /> {manualResult.error || 'Gagal generate sertifikat.'}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="card p-6 mb-4">
          <div className="flex items-start justify-between gap-4 mb-1">
            <h2 className="text-lg font-semibold text-secondary">Bulk Generate (CSV)</h2>
            <button
              type="button"
              onClick={handleDownloadSample}
              className="flex items-center gap-1.5 text-xs text-primary hover:underline whitespace-nowrap"
            >
              <Download className="w-3.5 h-3.5" />
              Download contoh CSV
            </button>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Generate & kirim email untuk banyak peserta sekaligus. Kolom CSV: <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">name</code>, <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">email</code> (wajib), <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">program_title</code> (opsional).
          </p>
          <form onSubmit={handleBulkUpload} className="flex flex-col sm:flex-row gap-3">
            <input
              ref={bulkFileInputRef}
              type="file"
              accept=".csv"
              onChange={e => setBulkFile(e.target.files?.[0] || null)}
              className="input-field flex-1"
              required
            />
            <button
              type="submit"
              className="btn-primary flex items-center justify-center gap-2 whitespace-nowrap"
              disabled={bulkLoading || !bulkFile}
            >
              <Upload className="w-4 h-4" />
              {bulkLoading ? 'Memproses...' : 'Upload & Generate Semua'}
            </button>
          </form>

          {bulkLoading && (
            <p className="text-xs text-gray-400 mt-3">
              Sedang diproses satu per satu, bisa memakan waktu untuk banyak baris. Jangan tutup halaman ini.
            </p>
          )}

          {bulkResult && (
            <div className="mt-4">
              {!bulkResult.success ? (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 flex items-center gap-2">
                  <XCircle className="w-4 h-4" /> {bulkResult.error}
                </div>
              ) : (
                <div>
                  <div className="p-3 rounded-lg bg-gray-50 border border-gray-200 text-sm text-secondary mb-3">
                    Total {bulkResult.total} baris — <span className="text-green-700 font-medium">{bulkResult.succeeded} berhasil</span>
                    {bulkResult.failed! > 0 && <span className="text-red-600 font-medium">, {bulkResult.failed} gagal</span>}.
                  </div>
                  <div className="overflow-x-auto max-h-72 overflow-y-auto border border-gray-100 rounded-lg">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-gray-50">
                        <tr className="text-left text-gray-600 border-b border-gray-200">
                          <th className="px-3 py-2 font-medium">Nama</th>
                          <th className="px-3 py-2 font-medium">Email</th>
                          <th className="px-3 py-2 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bulkResult.results?.map((r, i) => (
                          <tr key={i} className="border-b border-gray-100 last:border-0">
                            <td className="px-3 py-2">{r.name}</td>
                            <td className="px-3 py-2 text-gray-600">{r.email}</td>
                            <td className="px-3 py-2">
                              {r.success ? (
                                <span className={`flex items-center gap-1 ${r.email_sent ? 'text-green-700' : 'text-orange-600'}`}>
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  Sertifikat OK{r.email_sent ? ', email terkirim' : ', email gagal terkirim'}
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-red-600">
                                  <XCircle className="w-3.5 h-3.5" /> {r.error}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="card p-4 mb-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              className="input-field pl-9"
              placeholder="Cari nama, email, atau certificate ID..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-left text-gray-600">
                  <th className="px-4 py-3 font-medium">Nama</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Certificate ID</th>
                  <th className="px-4 py-3 font-medium">Waktu Submit</th>
                  <th className="px-4 py-3 font-medium text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                      {loading ? 'Memuat...' : 'Tidak ada data.'}
                    </td>
                  </tr>
                )}
                {filtered.map(s => (
                  <tr key={s.email} className="border-b border-gray-100 last:border-0">
                    <td className="px-4 py-3">{s.full_name}</td>
                    <td className="px-4 py-3 text-gray-600">{s.email}</td>
                    <td className="px-4 py-3 font-mono text-xs">{s.certificate_id}</td>
                    <td className="px-4 py-3 text-gray-500">{s.submitted_at}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleReset(s.email)}
                        disabled={deletingEmail === s.email}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-red-600 hover:bg-red-50 text-xs font-medium disabled:opacity-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Reset
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <p className="text-xs text-gray-400 mt-4">
          Total: {submissions.length} sertifikat sudah pernah digenerate.
        </p>
      </div>
    </div>
  )
}

export default AdminDashboard
