import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import ErrorBoundary from '@/components/shared/ErrorBoundary'
import useThemeStore from '@/stores/themeStore'
import App from './App.jsx'
import './index.css'

// Apply persisted theme before first paint
useThemeStore.getState().hydrate()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2,      // data considered fresh for 2 minutes
      gcTime: 1000 * 60 * 10,        // garbage collect after 10 minutes
      retry: 1,                       // 1 retry on network failure
      refetchOnWindowFocus: true,
    },
    mutations: {
      retry: 0,
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <ErrorBoundary>
            <App />
          </ErrorBoundary>
          <Toaster
            position="top-right"
            richColors
            closeButton
            duration={4000}
          />
        </TooltipProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
)
