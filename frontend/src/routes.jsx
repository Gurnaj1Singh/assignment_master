import { lazy, Suspense } from 'react'
import { Navigate } from 'react-router-dom'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import AppShell from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

// Lazy-load every page for code splitting
const LoginPage           = lazy(() => import('@/pages/auth/LoginPage'))
const SignupPage          = lazy(() => import('@/pages/auth/SignupPage'))
const VerifyOtpPage       = lazy(() => import('@/pages/auth/VerifyOtpPage'))
const ForgotPasswordPage  = lazy(() => import('@/pages/auth/ForgotPasswordPage'))
const ResetPasswordPage   = lazy(() => import('@/pages/auth/ResetPasswordPage'))
const ProfessorDashboard  = lazy(() => import('@/pages/dashboard/ProfessorDashboard'))
const StudentDashboard    = lazy(() => import('@/pages/dashboard/StudentDashboard'))
const ClassroomDetailPage = lazy(() => import('@/pages/classroom/ClassroomDetailPage'))
const TaskDetailPage      = lazy(() => import('@/pages/task/TaskDetailPage'))
const StudentSubmissions  = lazy(() => import('@/pages/dashboard/StudentSubmissions'))
const NotFoundPage        = lazy(() => import('@/pages/NotFoundPage'))

function PageLoader() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-48" />
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
      </div>
    </div>
  )
}

function Shell({ children, role }) {
  return (
    <ProtectedRoute role={role}>
      <AppShell>
        <Suspense fallback={<PageLoader />}>{children}</Suspense>
      </AppShell>
    </ProtectedRoute>
  )
}

export const routes = [
  // Auth (public)
  { path: '/login',           element: <Suspense fallback={null}><LoginPage /></Suspense> },
  { path: '/signup',          element: <Suspense fallback={null}><SignupPage /></Suspense> },
  { path: '/verify-otp',      element: <Suspense fallback={null}><VerifyOtpPage /></Suspense> },
  { path: '/forgot-password', element: <Suspense fallback={null}><ForgotPasswordPage /></Suspense> },
  { path: '/reset-password',  element: <Suspense fallback={null}><ResetPasswordPage /></Suspense> },

  // Professor
  {
    path: '/professor',
    element: <Shell role="professor"><ProfessorDashboard /></Shell>,
  },
  {
    path: '/professor/classroom/:classroomId',
    element: <Shell role="professor"><ClassroomDetailPage /></Shell>,
  },
  {
    path: '/professor/task/:taskId',
    element: <Shell role="professor"><TaskDetailPage /></Shell>,
  },

  // Student
  {
    path: '/student',
    element: <Shell role="student"><StudentDashboard /></Shell>,
  },
  {
    path: '/student/classroom/:classroomId',
    element: <Shell role="student"><ClassroomDetailPage /></Shell>,
  },
  {
    path: '/student/task/:taskId',
    element: <Shell role="student"><TaskDetailPage /></Shell>,
  },
  {
    path: '/student/submissions',
    element: <Shell role="student"><StudentSubmissions /></Shell>,
  },

  // Default redirects
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '*', element: <Suspense fallback={null}><NotFoundPage /></Suspense> },
]
