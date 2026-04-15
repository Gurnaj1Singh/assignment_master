import { useRoutes, Navigate } from 'react-router-dom'
import { routes } from './routes'
import useAuthStore from '@/stores/authStore'

// Root-level auth redirect: if already logged in and hits /login, go to dashboard
function AuthRedirect({ children }) {
  const { isAuthenticated, user } = useAuthStore()

  // We let individual routes handle their redirects
  // This component is just the route renderer
  return useRoutes(routes)
}

export default function App() {
  return <AuthRedirect />
}
