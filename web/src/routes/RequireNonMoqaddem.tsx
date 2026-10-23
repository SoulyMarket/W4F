import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

// Defense in depth: the backend's own `/reports` etc. allow every role
// (territory scope does the real filtering), but section 1 is explicit
// that moqaddem has no web screens at all — direct navigation to a URL
// like /reports shouldn't work for that role just because ProtectedRoute
// already let it past the "is anyone logged in" check.
export function RequireNonMoqaddem() {
  const { user } = useAuth()
  if (user?.role === 'moqaddem') return <Navigate to="/" replace />
  return <Outlet />
}
