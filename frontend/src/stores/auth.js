import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  loginUser,
  loginWithGoogle,
  registerUser,
  requestSignupCode,
  verifySignupCode,
  completeSignup,
  getProfile,
  deleteUser,
  getWatchlists,
  createWatchlist,
  updateWatchlist,
  deleteWatchlist,
  updateUser,
  isSupported,
  SUPPORTED_TICKERS,
} from '@/api/StockVision'
import { useMarketStore } from '@/stores/market'

const STORAGE_KEY = 'stockvision.auth'

// Satu-satunya akun yang boleh membuka Admin Management.
const ADMIN_EMAIL = 'admin@sahamscope.id'

const SEED_WATCHLISTS = {
  BBCA: ['BBCA', 'BBRI', 'BMRI'],
  BBNI: ['BBNI', 'BJBR'],
}

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
  const isInitializing = ref(true)
  const isNewRegistration = ref(false)

  const isLoggedIn = computed(() => !!user.value)
  const accessRole = computed(() => String(user.value?.accessRole || 'user').toLowerCase())

  // Hanya satu akun yang berstatus admin; sisanya user biasa. Pencocokan
  // dibuat persis (bukan `includes('admin')`) supaya alamat seperti
  // "admin.palsu@gmail.com" atau "notadmin@x.com" tidak ikut lolos.
  const isAdmin = computed(
    () => String(user.value?.email || '').trim().toLowerCase() === ADMIN_EMAIL,
  )

  const activeWatchlist = computed(
    () => watchlists.value.find((w) => w.id === activeWatchlistId.value) || watchlists.value[0] || null,
  )

  const watchlist = computed(() => {
    const symbols = (activeWatchlist.value?.symbols || []).filter(isSupported)
    if (!symbols.length) return SUPPORTED_TICKERS
    const utama = user.value?.defaultTicker
    return utama && isSupported(utama) && !symbols.includes(utama) ? [utama, ...symbols] : symbols
  })

  const watchlistTidakDidukung = computed(() =>
    (activeWatchlist.value?.symbols || []).filter((s) => !isSupported(s)),
  )

  /**
   * Simbol apa adanya dari watchlist aktif — tanpa dua perilaku milik
   * `watchlist` yang bikin penghapusan tidak kelihatan: fallback ke seluruh
   * SUPPORTED_TICKERS saat kosong, dan penyisipan emiten utama di depan.
   * Dipakai panel yang menampilkan daftar bisa-hapus.
   */
  const watchlistTersimpan = computed(() =>
    (activeWatchlist.value?.symbols || []).filter(isSupported),
  )

  const emitenUtama = computed(() => user.value?.defaultTicker || watchlist.value[0] || 'BBCA')

  function persist() {
    if (user.value) localStorage.setItem(STORAGE_KEY, JSON.stringify({ user: user.value }))
    else localStorage.removeItem(STORAGE_KEY)
  }

  function mapUser(raw) {
    let localPrefs = {}
    try {
      const saved = localStorage.getItem('stockvision.profile.' + raw.id)
      if (saved) localPrefs = JSON.parse(saved)
    } catch (e) {}

    return {
      id: raw.id,
      email: raw.email ?? '',
      username: raw.username ?? '',
      name: raw.name ?? raw.username ?? 'User',
      accessRole: raw.access_role ?? raw.accessRole ?? 'user',
      defaultTicker: raw.default_ticker ?? raw.defaultTicker ?? 'BBCA',
      phone: raw.phone ?? localPrefs.phone ?? '',
      avatar: raw.avatar ?? raw.avatar_url ?? localPrefs.photo ?? '',
      emailNotification: raw.email_notification ?? raw.emailNotification ?? localPrefs.emailNotif ?? true,
    }
  }

  async function mulaiSesi(raw) {
    user.value = mapUser(raw)
    persist()
    await fetchWatchlists()
    
    // Jika user belum punya watchlist sama sekali di backend, berarti ini adalah pendaftaran baru
    if (watchlists.value.length === 0) {
      isNewRegistration.value = true
      // Tidak lagi memaksa membuat watchlist di sini, biarkan onboarding yang membuatnya.
    } else {
      isNewRegistration.value = false
    }
    
    useMarketStore().resetTicker(user.value.defaultTicker)
    return user.value
  }

  async function login(email, password) {
    loading.value = true
    try {
      return await mulaiSesi(await loginUser(email, password))
    } finally {
      loading.value = false
    }
  }

  async function googleLogin(idToken) {
    loading.value = true
    try {
      return await mulaiSesi(await loginWithGoogle(idToken))
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    try {
      return await registerUser(payload)
    } finally {
      loading.value = false
    }
  }

  async function requestCode(email, username) {
    loading.value = true
    try {
      return await requestSignupCode({ email, username })
    } finally {
      loading.value = false
    }
  }

  async function verifyCode(email, code) {
    loading.value = true
    try {
      return await verifySignupCode({ email, code })
    } finally {
      loading.value = false
    }
  }

  async function registerWithOtp(payload) {
    loading.value = true
    try {
      const res = await completeSignup(payload)
      // Auto-login after successful OTP registration
      return await mulaiSesi(res)
    } finally {
      loading.value = false
    }
  }

  async function refreshUser() {
    if (!user.value) return null
    user.value = mapUser(await getProfile(user.value.id))
    persist()
    return user.value
  }

  async function hapusAkun() {
    if (!user.value) return
    await deleteUser(user.value.id)
    logout()
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

  async function saveWatchlist(symbols, name = null) {
    if (!user.value) return
    const active = activeWatchlist.value
    if (active) {
      const payload = { symbols }
      if (name) payload.name = name
      const updated = await updateWatchlist(user.value.id, active.id, payload)
      const i = watchlists.value.findIndex((w) => w.id === active.id)
      if (i !== -1) {
        watchlists.value.splice(i, 1, updated)
      }
    } else {
      const created = await createWatchlist(user.value.id, { name: name || 'Watchlist', symbols })
      watchlists.value.push(created)
      activeWatchlistId.value = created.id
    }
  }

  /**
   * Mengeluarkan satu emiten dari watchlist aktif. Perubahannya disimpan ke
   * backend lewat saveWatchlist, bukan cuma di memori.
   */
  async function removeFromWatchlist(ticker) {
    if (!user.value) return

    const sisa = watchlistTersimpan.value.filter((t) => t !== ticker)
    await saveWatchlist(sisa)

    // Emiten utama ikut pindah kalau yang barusan dihapus adalah dirinya.
    // Kalau tidak ada sisa, biarkan — updateProfile menolak ticker kosong.
    if (user.value.defaultTicker === ticker && sisa.length) {
      await setEmitenUtama(sisa[0])
    }

    // Jangan tinggalkan Stream menampilkan emiten yang sudah tidak dipantau.
    const market = useMarketStore()
    if (market.selectedTicker === ticker) market.setTicker(sisa[0] ?? null)

    return sisa
  }

  async function hapusWatchlist(watchlistId) {
    if (!user.value || watchlists.value.length <= 1) return
    await deleteWatchlist(user.value.id, watchlistId)
    watchlists.value = watchlists.value.filter((w) => w.id !== watchlistId)
    if (activeWatchlistId.value === watchlistId) {
      activeWatchlistId.value = watchlists.value[0]?.id ?? null
    }
  }

  async function updateProfile(profileData) {
    if (!user.value) throw new Error('User belum login.')

    const payload = {}
    if (profileData.name !== undefined) payload.name = profileData.name.trim()
    if (profileData.username !== undefined) payload.username = profileData.username.trim()
    if (profileData.email !== undefined) payload.email = profileData.email.trim()
    if (profileData.phone !== undefined) payload.phone = profileData.phone.trim()
    if (profileData.avatar !== undefined) payload.avatar = profileData.avatar
    if (profileData.emailNotification !== undefined) payload.email_notification = profileData.emailNotification
    if (profileData.defaultTicker !== undefined) {
      const ticker = profileData.defaultTicker.trim().toUpperCase()
      if (!isSupported(ticker)) throw new Error(`Ticker ${ticker} belum didukung.`)
      payload.default_ticker = ticker
    }

    const updatedRaw = await updateUser(user.value.id, payload)

    const currentRaw = {
      id: user.value.id,
      email: user.value.email,
      username: user.value.username,
      name: user.value.name,
      default_ticker: user.value.defaultTicker,
      phone: user.value.phone,
      avatar: user.value.avatar,
      email_notification: user.value.emailNotification,
    }

    user.value = mapUser({ ...currentRaw, ...payload, ...(updatedRaw || {}) })
    persist()

    try {
      localStorage.setItem('stockvision.profile.' + user.value.id, JSON.stringify({
        phone: user.value.phone,
        photo: user.value.avatar,
        emailNotif: user.value.emailNotification
      }))
    } catch (e) {}

    if (payload.default_ticker) useMarketStore().resetTicker(user.value.defaultTicker)
    return user.value
  }

  async function setEmitenUtama(ticker) {
    if (!user.value) return
    return updateProfile({ defaultTicker: ticker })
  }

  async function restore() {
    isInitializing.value = true
    try {
      if (!user.value) return

      // selectedTicker tidak ikut dipersistensi, jadi setelah refresh nilainya
      // kosong dan seluruh section Stream ikut kosong. Pulihkan dari profil user.
      useMarketStore().initTicker(user.value.defaultTicker)

      if (watchlists.value.length) return
      await fetchWatchlists()
    } finally {
      isInitializing.value = false
    }
  }

  return {
    user,
    watchlists,
    activeWatchlistId,
    activeWatchlist,
    watchlist,
    watchlistTersimpan,
    watchlistTidakDidukung,
    emitenUtama,
    loading,
    isInitializing,
    isNewRegistration,
    accessRole,
    isAdmin,
    isLoggedIn,
    login,
    googleLogin,
    register,
    requestCode,
    verifyCode,
    registerWithOtp,
    refreshUser,
    hapusAkun,
    hapusWatchlist,
    removeFromWatchlist,
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