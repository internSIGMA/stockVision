<script setup>
import { ref } from 'vue';
import { RefreshCw, Zap, Loader2 } from 'lucide-vue-next';
import { useEmitenData } from '../composables/useEmitenData.js';
import { useNotify } from '../composables/useNotify.js';

const props = defineProps({
  ticker: { type: String, required: true },
});

const { summary } = useEmitenData(() => props.ticker, { summary: true });
const notify = useNotify();
const triggering = ref(false);

function fmt(n) {
  return Math.round(n).toLocaleString('id-ID');
}

async function triggerCrawler() {
  triggering.value = true;
  await new Promise((r) => setTimeout(r, 1100));
  triggering.value = false;
  notify.success(`Crawler untuk ${props.ticker} dijalankan.`);
}

async function crawlAll() {
  notify.info('Crawl All dijadwalkan untuk seluruh watchlist.');
}
</script>

<template>
  <div class="card card-pad emiten-header">
    <div v-if="summary" class="price-block">
      <div class="ticker">{{ ticker }}</div>
      <div class="price mono">Rp {{ fmt(summary.price) }}</div>
      <div class="change mono" :class="summary.change >= 0 ? 'up-text' : 'down-text'">
        {{ summary.change >= 0 ? '+' : '' }}{{ fmt(summary.change) }} ({{ summary.change_pct.toFixed(2) }}%)
      </div>
    </div>
    <div v-else class="price-block">
      <div class="skel" style="width:200px;height:24px;"></div>
    </div>

    <div class="actions">
      <button class="btn" :disabled="triggering" @click="triggerCrawler">
        <Loader2 v-if="triggering" :size="13" class="spin" />
        <RefreshCw v-else :size="13" />
        Trigger Crawler
      </button>
      <button class="btn" @click="crawlAll">
        <Zap :size="13" />
        Crawl All
      </button>
    </div>
  </div>
</template>

<style scoped>
.emiten-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.price-block { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
.ticker { font-size: 22px; font-weight: 800; letter-spacing: -.01em; }
.price { font-size: 24px; font-weight: 600; }
.change { font-weight: 700; font-size: 14px; }
.actions { display: flex; gap: 8px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
