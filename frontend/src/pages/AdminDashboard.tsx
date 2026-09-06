import { useEffect, useState } from 'react'
import { RefreshCw, Trash2, LogOut, Search } from 'lucide-react'
import type { Submission } from '../types'

const STORAGE_KEY = 'intelligo_admin_key'

const AdminDashboard = (): React.JSX.Element => {
  const [adminKey, setAdminKey] = useState<string>(() => sessionStorage.getItem(STORAGE_KEY) || '')
  const [keyInput, setKeyInput] = useState('')
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [deletingEmail, setDeletingEmail] = useState<string | null>(null)

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
