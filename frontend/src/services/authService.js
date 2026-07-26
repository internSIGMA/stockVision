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
  try {
    const response = await fetch('http://localhost:8080/users/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 401) {
        throw new AuthError('INVALID_CREDENTIALS', 'Email atau kata sandi salah.');
      }
      throw new AuthError('SERVER_ERROR', data.error || 'Terjadi kesalahan pada server.');
    }

    // Map backend snake_case keys to camelCase keys for Vue store
    const token = `jwt-${btoa(data.email)}-${Date.now()}`;
    const user = {
      email: data.email,
      name: data.name,
      role: data.role,
      defaultTicker: data.default_ticker || 'BBCA',
      avatar: data.email.toLowerCase() === 'fariz@sahamscope.id'
        ? 'https://i.pravatar.cc/100?img=68'
        : (data.email.toLowerCase() === 'dewi@sahamscope.id' ? 'https://i.pravatar.cc/100?img=47' : 'https://i.pravatar.cc/100?img=1')
    };

    return { token, user };
  } catch (err) {
    if (err instanceof AuthError) {
      throw err;
    }
    throw new AuthError(
      'NETWORK',
      'Tidak dapat terhubung ke server. Periksa koneksi kamu lalu coba lagi.',
    );
  }
}


