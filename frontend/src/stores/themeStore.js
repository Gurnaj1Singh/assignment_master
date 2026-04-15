import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useThemeStore = create(
  persist(
    (set, get) => ({
      theme: 'light', // 'light' | 'dark'

      toggle: () => {
        const next = get().theme === 'light' ? 'dark' : 'light'
        document.documentElement.classList.toggle('dark', next === 'dark')
        set({ theme: next })
      },

      hydrate: () => {
        const { theme } = get()
        document.documentElement.classList.toggle('dark', theme === 'dark')
      },
    }),
    { name: 'theme-storage' }
  )
)

export default useThemeStore
