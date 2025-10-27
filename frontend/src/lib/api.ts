import axios from 'axios'

// Build base URL ensuring API version (/v1) is included
// Accept both VITE_API_BASE_URL (preferred) and legacy VITE_API_URL
const rawBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api'
const baseURL = rawBase.endsWith('/v1')
  ? rawBase
  : `${rawBase.replace(/\/$/, '')}/v1`

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
})

// Attach access token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Optionally handle 401s here (refresh flow can be added later if needed)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    return Promise.reject(error)
  }
)

export default api
