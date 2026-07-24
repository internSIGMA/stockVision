import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  loginUser,
  loginWithGoogle,
  getWatchlists,
  createWatchlist,
  updateWatchlist,
  updateUser,
  isSupported,
  SUPPORTED_TICKERS,
} from '@/api/StockVision'
import { useMarketStore } from '@/stores/market'

const STORAGE_KEY = 'stockvision.auth'

/**
 * Watchlist awal untuk user yang belum punya satu pun di DB, dipilih dari
 * emiten utamanya. Emiten di luar peta ini cukup jadi watchlist berisi
 * dirinya sendiri.
 */
const SEED_WATCHLISTS = {
  BBCA: ['BBCA', 'BBRI', 'BMRI'],
  BBNI: ['BBNI', 'BJBR'],
}

/** Sesi bertahan di localStorage; JSON rusak diperlakukan seperti belum login. */
function readPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const persisted = readPersisted()

  const user = ref(persisted?.user ?? null)
  const watchlists = ref([])
  const activeWatchlistId = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  const accessRole = computed(() => {
    return String(user.value?.accessRole || 'user').toLowerCase()
  })

  const isAdmin = computed(() => {
    return accessRole.value === 'admin'
  })

  const activeWatchlist = computed(
    () => watchlists.value.find((w) => w.id === activeWatchlistId.value) || watchlists.value[0] || null,
  )

  /**
   * Emiten yang benar-benar bisa ditampilkan. Backend menolak emiten di luar
   * SUPPORTED_TICKERS, jadi simbol lain disaring keluar di sini — dan kalau
   * tidak tersisa apa pun, jatuh ke seluruh daftar yang didukung supaya
   * halaman tidak pernah kosong total.
   */
  const watchlist = computed(() => {
    const symbols = (activeWatchlist.value?.symbols || []).filter(isSupported)
    if (!symbols.length) return SUPPORTED_TICKERS

    const utama = user.value?.defaultTicker
    return utama && isSupported(utama) && !symbols.includes(utama) ? [utama, ...symbols] : symbols
  })

  /** Simbol yang disimpan user tapi ditolak backend — dipakai untuk memberi tahu. */
  const watchlistTidakDidukung = computed(() =>
    (activeWatchlist.value?.symbols || []).filter((s) => !isSupported(s)),
  )

  const emitenUtama = computed(() => user.value?.defaultTicker || watchlist.value[0] || 'BBCA')

  function persist() {
    if (user.value) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ user: user.value }))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  /** Backend memakai snake_case; sisa aplikasi memakai camelCase. */
  function mapUser(raw) {
  return {
    id: raw.id,
    email: raw.email ?? '',
    username: raw.username ?? '',
    name: raw.name ?? raw.username ?? 'User',
    role: raw.role,

    accessRole:
      raw.access_role ??
      raw.accessRole ??
      'user',

    defaultTicker:
      raw.default_ticker ??
      raw.defaultTicker ??
      'BBCA',

    phone: raw.phone ?? '',

    avatar:
      raw.avatar ??
      raw.avatar_url ??
      '',

    emailNotification:
      raw.email_notification ??
      raw.emailNotification ??
      true,
    }
  }

  async function login(email, password) {
    loading.value = true
    try {
      const raw = await loginUser(email, password)
      user.value = mapUser(raw)
      persist()
      await fetchWatchlists()
      await ensureWatchlist()
      useMarketStore().resetTicker(user.value.defaultTicker)
      return user.value
    } finally {
      loading.value = false
    }
  }

  async function googleLogin(idToken) {
  loading.value = true

  try {
    const raw = await loginWithGoogle(idToken)

    user.value = mapUser(raw)

    persist()

    await fetchWatchlists()
    await ensureWatchlist()

    useMarketStore().resetTicker(user.value.defaultTicker)

    return user.value
  } finally {
    loading.value = false
  }
}

  function logout() {
    user.value = null
    watchlists.value = []
    activeWatchlistId.value = null
    useMarketStore().resetTicker(null)
    persist()
  }

  async function fetchWatchlists() {
    if (!user.value) return
    const list = await getWatchlists(user.value.id)
    watchlists.value = list || []
    if (!activeWatchlistId.value && watchlists.value.length) {
      activeWatchlistId.value = watchlists.value[0].id
    }
  }

  async function ensureWatchlist() {
    if (!user.value || watchlists.value.length) return
    const utama = user.value.defaultTicker
    const symbols = SEED_WATCHLISTS[utama] || [utama]
    const created = await createWatchlist(user.value.id, { name: 'Watchlist Saya', symbols })
    watchlists.value = [created]
    activeWatchlistId.value = created.id
  }

  function selectWatchlist(id) {
    activeWatchlistId.value = id
  }

  async function saveWatchlist(symbols) {
    if (!user.value) return

    const active = activeWatchlist.value
    if (active) {
      const updated = await updateWatchlist(user.value.id, active.id, { symbols })
      const i = watchlists.value.findIndex((w) => w.id === active.id)
      if (i !== -1) watchlists.value[i] = updated
    } else {
      const created = await createWatchlist(user.value.id, { name: 'Watchlist', symbols })
      watchlists.value.push(created)
      activeWatchlistId.value = created.id
    }
  }

    async function updateProfile(profileData) {
    if (!user.value) {
      throw new Error('User belum login.')
    }

    const payload = {}

    if (profileData.name !== undefined) {
      payload.name = profileData.name.trim()
    }

    if (profileData.username !== undefined) {
      payload.username = profileData.username.trim()
    }

    if (profileData.email !== undefined) {
      payload.email = profileData.email.trim()
    }

    if (profileData.phone !== undefined) {
      payload.phone = profileData.phone.trim()
    }

    if (profileData.avatar !== undefined) {
      payload.avatar = profileData.avatar
    }

    if (profileData.emailNotification !== undefined) {
      payload.email_notification = profileData.emailNotification
    }

    if (profileData.defaultTicker !== undefined) {
      const ticker = profileData.defaultTicker.trim().toUpperCase()

    if (!isSupported(ticker)) {
      throw new Error(`Ticker ${ticker} belum didukung.`)
    }

    payload.default_ticker = ticker
    }

    const updatedRaw = await updateUser(user.value.id, payload)

    /*
    * Digunakan sebagai cadangan jika backend hanya mengembalikan
    * sebagian data user atau tidak mengembalikan body.
    */
    const currentRaw = {
      id: user.value.id,
      email: user.value.email,
      username: user.value.username,
      name: user.value.name,
      role: user.value.role,
      default_ticker: user.value.defaultTicker,
      phone: user.value.phone,
      avatar: user.value.avatar,
      email_notification: user.value.emailNotification,
    }

    user.value = mapUser({
      ...currentRaw,
      ...payload,
      ...(updatedRaw || {}),
    })

    persist()

    if (payload.default_ticker) {
      useMarketStore().resetTicker(user.value.defaultTicker)
    }

    return user.value
  }


    async function setEmitenUtama(ticker) {
      if (!user.value) return

    return updateProfile({
      defaultTicker: ticker,
    })
  }

  /** Dipanggil saat boot: sesi ada di localStorage, tapi watchlist tidak. */
  async function restore() {
    if (!user.value || watchlists.value.length) return
    await fetchWatchlists()
  }

  return {
    user,
    watchlists,
    activeWatchlistId,
    activeWatchlist,
    watchlist,
    watchlistTidakDidukung,
    emitenUtama,
    loading,
    accessRole,
    isAdmin,
    isLoggedIn,
    login,
    googleLogin,
    logout,
    fetchWatchlists,
    ensureWatchlist,
    selectWatchlist,
    saveWatchlist,
    updateProfile,
    setEmitenUtama,
    restore,
  }
})
