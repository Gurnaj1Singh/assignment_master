import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { clearTokens } from '@/api/client'

const useAuthStore = create(
  persist(
    (set) => ({
      user: null,        // { name, email, role }
      isAuthenticated: false,

      login: (user, accessToken, refreshToken) => {
        localStorage.setItem('access_token', accessToken)
        localStorage.setItem('refresh_token', refreshToken)
        set({ user, isAuthenticated: true })
      },

      logout: () => {
        clearTokens()
        set({ user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
      // Only persist user shape — tokens live in localStorage directly
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
)

export default useAuthStore
