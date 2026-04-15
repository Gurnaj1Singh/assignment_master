import { Navigate, useLocation } from 'react-router-dom'
import useAuthStore from '@/stores/authStore'

/**
 * Wraps a route and enforces authentication + optional role check.
 * Usage:
 *   <ProtectedRoute>          — any authenticated user
 *   <ProtectedRoute role="professor">  — professor only
 */
export default function ProtectedRoute({ children, role }) {
  const { isAuthenticated, user } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (role && user?.role !== role) {
    // Wrong role — redirect to their correct dashboard
    const home = user?.role === 'professor' ? '/professor' : '/student'
    return <Navigate to={home} replace />
  }

  return children
}
