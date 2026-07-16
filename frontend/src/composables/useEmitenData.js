import { ref, watch, toValue } from 'vue';
import {
  getOhlc,
  getSummary,
  getInsiderTransactions,
  getBrokerSummary,
  getFundamental,
} from '../lib/mockApi.js';
import { computeTechnical } from '../utils/technicalIndicators.js';

/**
 * Shared data-fetching composable for a single emiten (ticker).
 *
 * Usage:
 *   const { ohlc, summary, loading } = useEmitenData(tickerRef, { ohlc: true, summary: true })
 *   const { insider } = useEmitenData(tickerRef, { insider: true })
 *
 * `ticker` may be a ref, getter, or plain string — re-fetches automatically
 * whenever it changes. All fields not requested via `options` stay null.
 */
export function useEmitenData(ticker, options = {}) {
  const {
    ohlc: wantOhlc = false,
    summary: wantSummary = false,
    insider: wantInsider = false,
    broker: wantBroker = false,
    fundamental: wantFundamental = false,
    technical: wantTechnical = false,
    days = null,
  } = options;

  const ohlc = ref([]);
  const summary = ref(null);
  const insider = ref([]);
  const broker = ref(null);
  const fundamental = ref(null);
  const technical = ref([]);
  const loading = ref(false);
  const error = ref(null);

  async function load() {
    const tk = toValue(ticker);
    if (!tk) return;
    loading.value = true;
    error.value = null;
    try {
      const tasks = [];
      if (wantOhlc || wantTechnical) tasks.push(getOhlc(tk, { days }).then((r) => (ohlc.value = r)));
      if (wantSummary) tasks.push(getSummary(tk).then((r) => (summary.value = r)));
      if (wantInsider) tasks.push(getInsiderTransactions(tk).then((r) => (insider.value = r)));
      if (wantBroker) tasks.push(getBrokerSummary(tk).then((r) => (broker.value = r)));
      if (wantFundamental) tasks.push(getFundamental(tk).then((r) => (fundamental.value = r)));
      await Promise.all(tasks);
      if (wantTechnical) technical.value = computeTechnical(tk, ohlc.value);
    } catch (e) {
      error.value = e;
    } finally {
      loading.value = false;
    }
  }

  watch(() => toValue(ticker), load, { immediate: true });

  return { ohlc, summary, insider, broker, fundamental, technical, loading, error, refresh: load };
}
