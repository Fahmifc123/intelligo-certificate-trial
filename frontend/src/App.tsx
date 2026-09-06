import ClaimCertificate from './pages/ClaimCertificate'
import AdminDashboard from './pages/AdminDashboard'

function App(): React.JSX.Element {
  const isAdmin = window.location.pathname.startsWith('/admin')

  if (isAdmin) {
    return <AdminDashboard />
  }

  return (
    <div className="min-h-screen bg-accent">
      <ClaimCertificate />
    </div>
  )
}

export default App
