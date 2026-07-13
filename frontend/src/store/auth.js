import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: {
      name: 'Investor',
      watchlist: ['BBCA', 'BBRI', 'TLKM', 'ASII', 'BMRI'],
      emitenUtama: 'BBCA',
    },
  }),
  actions: {
    setEmitenUtama(ticker) {
      this.user.emitenUtama = ticker;
    },
    updateWatchlist(list) {
      this.user.watchlist = list;
      if (!list.includes(this.user.emitenUtama) && list.length) {
        this.user.emitenUtama = list[0];
      }
    },
    addToWatchlist(ticker) {
      const t = ticker.trim().toUpperCase();
      if (t && !this.user.watchlist.includes(t)) this.user.watchlist.push(t);
    },
    removeFromWatchlist(ticker) {
      this.user.watchlist = this.user.watchlist.filter((t) => t !== ticker);
    },
  },
});
