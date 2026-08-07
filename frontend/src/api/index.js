import axios from 'axios'

const getBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8080'
    }
    return `${protocol}//${hostname}:8080`
  }
  return 'http://localhost:8080'
}

export const BASE_URL = getBaseUrl()

// Database berada di server remote — kueri pertama bisa memakan ~10 detik.
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

/** Backend selalu mengirim error sebagai { error: "..." } dengan status 4xx/5xx. */
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const message = error.response.data?.error || `Permintaan gagal (${error.response.status})`
      return Promise.reject(new Error(message))
    }
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Permintaan timeout — server terlalu lama merespons.'))
    }
    return Promise.reject(new Error('Tidak dapat terhubung ke server. Periksa koneksi kamu.'))
  },
)

export default api
