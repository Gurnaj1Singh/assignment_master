import axios from 'axios'
import { toast } from 'sonner'

const BASE_URL = 'http://127.0.0.1:8000/api/v1'

export const client = axios.create({
  baseURL: BASE_URL,
})

// ─── Token helpers ───────────────────────────────────────────────────────────
const getAccessToken = () => localStorage.getItem('access_token')
const getRefreshToken = () => localStorage.getItem('refresh_token')
const setAccessToken = (token) => localStorage.setItem('access_token', token)

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

// ─── Request interceptor: attach Bearer token ────────────────────────────────
client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Silent-refresh machinery ────────────────────────────────────────────────
let isRefreshing = false
// Buffer of { resolve, reject } for requests that arrived during a refresh
let pendingQueue = []

function processPendingQueue(error, newToken = null) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(newToken)
  })
  pendingQueue = []
}

// ─── Response interceptor: 401 → silent refresh → replay ────────────────────
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    // Rate limit — toast globally so individual callers don't need to handle it
    if (status === 429) {
      const retryAfter = error.response?.headers?.['retry-after']
      toast.error(
        retryAfter
          ? `Rate limited — please wait ${retryAfter}s before trying again.`
          : 'Too many requests — please slow down.'
      )
      return Promise.reject(error)
    }

    // Only attempt refresh once per request; skip if already retried or no token
    if (
      status !== 401 ||
      original._retry ||
      !getRefreshToken()
    ) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      // Another request triggered a refresh — queue this one
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject })
      }).then((newToken) => {
        original.headers.Authorization = `Bearer ${newToken}`
        return client(original)
      })
    }

    original._retry = true
    isRefreshing = true

    try {
      const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
        refresh_token: getRefreshToken(),
      })
      const newToken = data.access_token
      setAccessToken(newToken)
      processPendingQueue(null, newToken)
      original.headers.Authorization = `Bearer ${newToken}`
      return client(original)
    } catch (refreshError) {
      processPendingQueue(refreshError)
      clearTokens()
      // Redirect to login — using window.location so we don't need router here
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
