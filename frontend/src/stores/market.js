import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { emitens, latestQuote, FOCUS_CODES } from '@/data/market'
import { useAuthStore } from '@/stores/auth'

const WATCHLIST_KEY = 'sahamscope.watchlist'

// Default crawl targets — the emiten the Python crawler is configured to
// scrape. This is the data behind the "CRUD mana yang akan di-crawl" page.
const DEFAULT_WATCHLIST = [
  { code: 'BBRI', name: 'Bank Rakyat Indonesia', sector: 'Perbankan', sources: { broker: true, price: true, insider: true }, interval: 15, enabled: true },
  { code: 'BBCA', name: 'Bank Central Asia', sector: 'Perbankan', sources: { broker: true, price: true, insider: true }, interval: 15, enabled: true },
  { code: 'BBNI', name: 'Bank Negara Indonesia', sector: 'Perbankan', sources: { broker: true, price: true, insider: false }, interval: 30, enabled: true },
]

function loadWatchlist() {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY)
    return raw ? JSON.parse(raw) : structuredClone(DEFAULT_WATCHLIST)
  } catch {
    return structuredClone(DEFAULT_WATCHLIST)
  }
}

export const useMarketStore = defineStore('market', () => {
  const auth = useAuthStore()
  const selected = ref(auth.user?.defaultTicker || 'BBCA')
  const watchlist = ref(loadWatchlist())

  const universe = computed(() => emitens)
  const quote = computed(() => latestQuote(selected.value))

  // The logged-in user's favorite tickers (drives the bottom favorites bar).
  const favorites = computed(() =>
    auth.user?.favorites?.length ? auth.user.favorites : FOCUS_CODES,
  )
  const favoriteQuotes = computed(() => favorites.value.map((c) => latestQuote(c)))

  // Quotes for the five focus bank tickers, always available on the dashboard.
  const focusQuotes = computed(() => FOCUS_CODES.map((c) => latestQuote(c)))

  function select(code) {
    selected.value = code
  }

  function persist() {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist.value))
  }

  function addWatch(item) {
    if (watchlist.value.some((w) => w.code === item.code)) {
      throw new Error(`${item.code} sudah ada di daftar crawling.`)
    }
    watchlist.value.push(item)
    persist()
  }

  function updateWatch(code, patch) {
    const idx = watchlist.value.findIndex((w) => w.code === code)
    if (idx !== -1) {
      watchlist.value[idx] = { ...watchlist.value[idx], ...patch }
      persist()
    }
  }

  function removeWatch(code) {
    watchlist.value = watchlist.value.filter((w) => w.code !== code)
    persist()
  }

  function toggleEnabled(code) {
    const w = watchlist.value.find((x) => x.code === code)
    if (w) {
      w.enabled = !w.enabled
      persist()
    }
  }

  return {
    selected, watchlist, universe, quote, focusQuotes,
    favorites, favoriteQuotes,
    select, addWatch, updateWatch, removeWatch, toggleEnabled,
  }
})
