import { defineStore } from 'pinia';

export const useMarketStore = defineStore('market', {
  state: () => ({
    selectedTicker: 'BBCA',
  }),
  actions: {
    setTicker(ticker) {
      this.selectedTicker = ticker;
    },
  },
});
