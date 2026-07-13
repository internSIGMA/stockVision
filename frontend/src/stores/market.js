import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { emitens, latestQuote, FOCUS_CODES } from '@/data/market'
import { useAuthStore } from '@/stores/auth'

export const useMarketStore = defineStore('market', () => {
  const auth = useAuthStore()
  const selected = ref(auth.user?.defaultTicker || 'BBCA')

  const universe = computed(() => emitens)
  const quote = computed(() => latestQuote(selected.value))

  // Watchlist states
  const watchlists = ref([])
  const activeWatchlistId = ref(null)

  const activeWatchlist = computed(() => {
    if (!watchlists.value || watchlists.value.length === 0) return null
    return watchlists.value.find((w) => w.id === activeWatchlistId.value) || watchlists.value[0]
  })

  const watchlistSymbols = computed(() => {
    return activeWatchlist.value?.symbols?.length ? activeWatchlist.value.symbols : FOCUS_CODES
  })

  // To prevent breaking other views/components that use favorites, we alias them
  const favorites = computed(() => watchlistSymbols.value)
  const favoriteQuotes = computed(() => watchlistSymbols.value.map((c) => latestQuote(c)).filter(Boolean))

  // Quotes for the five focus bank tickers, always available on the dashboard.
  const focusQuotes = computed(() => FOCUS_CODES.map((c) => latestQuote(c)))

  function select(code) {
    selected.value = code
  }

  async function fetchWatchlists() {
    if (!auth.user) {
      watchlists.value = []
      activeWatchlistId.value = null
      return
    }
    try {
      const response = await fetch(`http://localhost:8080/users/${auth.user.id}/watchlists`)
      if (response.ok) {
        const data = await response.json()
        watchlists.value = data
        if (data.length > 0 && !activeWatchlistId.value) {
          activeWatchlistId.value = data[0].id
        }
      }
    } catch (e) {
      console.error('Gagal memuat daftar pantau:', e)
    }
  }

  function selectWatchlist(id) {
    activeWatchlistId.value = id
  }

  async function toggleWatchlistSymbol(symbol) {
    if (!auth.user) return
    const wl = activeWatchlist.value
    if (!wl) return

    let updatedSymbols = [...wl.symbols]
    if (updatedSymbols.includes(symbol)) {
      updatedSymbols = updatedSymbols.filter((s) => s !== symbol)
    } else {
      updatedSymbols.push(symbol)
    }

    try {
      const response = await fetch(`http://localhost:8080/users/${auth.user.id}/watchlists/${wl.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols: updatedSymbols })
      })
      if (response.ok) {
        const data = await response.json()
        const idx = watchlists.value.findIndex((w) => w.id === wl.id)
        if (idx !== -1) {
          watchlists.value[idx] = data
        }
      }
    } catch (e) {
      console.error('Gagal memperbarui simbol daftar pantau:', e)
    }
  }

  function clearWatchlists() {
    watchlists.value = []
    activeWatchlistId.value = null
  }

  // Load watchlists initially if user is logged in
  if (auth.user) {
    fetchWatchlists()
  }

  return {
    selected, universe, quote, focusQuotes,
    watchlists, activeWatchlistId, activeWatchlist, watchlistSymbols,
    favorites, favoriteQuotes,
    select, fetchWatchlists, selectWatchlist, toggleWatchlistSymbol, clearWatchlists,
  }
})
