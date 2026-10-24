import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

// Defense in depth on top of the backend's own `require_roles(ADMIN)` —
// same reasoning as RequireNonMoqaddem: a route existing doesn't mean
// every role should be able to navigate straight to it.
export function RequireAdmin() {
  const { user } = useAuth()
  if (user?.role !== 'admin') return <Navigate to="/" replace />
  return <Outlet />
}
