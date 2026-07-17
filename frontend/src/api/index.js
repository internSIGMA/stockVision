import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

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
