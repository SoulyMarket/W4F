import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

// Section 1: "dashboard and map" and "edit scoring weights" are listed
// only under manager — same defense-in-depth reasoning as RequireAdmin.
export function RequireManager() {
  const { user } = useAuth()
  if (user?.role !== 'manager') return <Navigate to="/" replace />
  return <Outlet />
}
