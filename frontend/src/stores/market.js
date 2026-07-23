import { defineStore } from 'pinia'

/**
 * Emiten yang sedang dilihat. Disimpan terpisah dari auth supaya berganti
 * ticker tidak menyentuh sesi user.
 *
 * initTicker dipakai saat boot (hanya mengisi kalau masih kosong), sedangkan
 * resetTicker dipakai saat login/logout untuk memaksa nilai baru.
 */
export const useMarketStore = defineStore('market', {
  state: () => ({
    selectedTicker: null,
  }),
  actions: {
    setTicker(ticker) {
      this.selectedTicker = ticker
    },
    initTicker(ticker) {
      if (!this.selectedTicker) this.selectedTicker = ticker
    },
    resetTicker(ticker = null) {
      this.selectedTicker = ticker
    },
  },
})
