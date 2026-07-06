/**
 * Mock authentication service.
 *
 * Simulates a real backend: async latency, credential checks, account
 * lockout, and random network failures — so the UI can exercise every
 * error path without a server.
 */

const USERS = [
  {
    email: 'fariz@sahamscope.id',
    password: 'password123',
    name: 'Fariz',
    role: 'Trader — Perbankan',
    avatar: 'https://i.pravatar.cc/100?img=68',
    defaultTicker: 'BBCA',
    favorites: ['BBCA', 'BBRI', 'BMRI', 'TLKM', 'ANTM', 'PTBA', 'ADRO', 'INDF', 'SMGR'],
  },
  {
    email: 'dewi@sahamscope.id',
    password: 'password123',
    name: 'Dewi',
    role: 'Trader — Properti & Energi',
    avatar: 'https://i.pravatar.cc/100?img=47',
    defaultTicker: 'BBNI',
    favorites: ['BBNI', 'BJBR', 'ASII', 'GOTO', 'SMRA', 'ASRI', 'CTRA', 'INCO', 'MAPI'],
  },
]

// Simulated in-memory lockout tracking (per email).
const failedAttempts = {}
const MAX_ATTEMPTS = 5

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

/**
 * Custom error carrying a machine-readable `code` so the UI can react
 * differently per failure type.
 */
export class AuthError extends Error {
  constructor(code, message) {
    super(message)
    this.name = 'AuthError'
    this.code = code
  }
}

export async function login({ email, password }) {
  await delay(700 + Math.random() * 500)

  // Simulate an intermittent network/server failure (~8% of requests).
  if (Math.random() < 0.08) {
    throw new AuthError(
      'NETWORK',
      'Tidak dapat terhubung ke server. Periksa koneksi kamu lalu coba lagi.',
    )
  }

  const normalizedEmail = email.trim().toLowerCase()

  if (failedAttempts[normalizedEmail] >= MAX_ATTEMPTS) {
    throw new AuthError(
      'LOCKED',
      'Akun terkunci sementara karena terlalu banyak percobaan. Coba lagi dalam beberapa menit.',
    )
  }

  const user = USERS.find((u) => u.email === normalizedEmail)

  if (!user || user.password !== password) {
    failedAttempts[normalizedEmail] = (failedAttempts[normalizedEmail] || 0) + 1
    const remaining = MAX_ATTEMPTS - failedAttempts[normalizedEmail]
    throw new AuthError(
      'INVALID_CREDENTIALS',
      remaining > 0
        ? `Email atau kata sandi salah. Sisa ${remaining} percobaan.`
        : 'Email atau kata sandi salah.',
    )
  }

  // Success — reset lockout counter.
  delete failedAttempts[normalizedEmail]

  const token = `mock-jwt-${btoa(normalizedEmail)}-${Date.now()}`
  const { password: _pw, ...safeUser } = user
  return { token, user: safeUser }
}
