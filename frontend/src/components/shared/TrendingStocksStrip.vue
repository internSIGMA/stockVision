<script setup>
import { onMounted, ref, watch } from 'vue'
import { getOhlcHistory, SUPPORTED_TICKERS } from '@/api/StockVision'
import { useMarketStore } from '@/stores/market'
import { useAuthStore } from '@/stores/auth'

const market = useMarketStore()
const auth = useAuthStore()

const items = ref([])
const loading = ref(true)

/** Sesi bursa yang digambar di sparkline. */
const SESI_SPARK = 30

/**
 * Harga dan perubahan dihitung dari satu deret yang sama dengan sparkline,
 * supaya angka persen dan garisnya tidak pernah bercerita beda.
 * Persennya adalah perubahan sesi terakhir, konvensi umum kartu emiten.
 */
function ringkas(ticker, rows) {
  const closes = (rows || [])
    .map((r) => Number(r.close))
    .filter(Number.isFinite)

  if (!closes.length) return null

  const price = closes[closes.length - 1]
  const sebelumnya = closes.length > 1 ? closes[closes.length - 2] : price
  const change = price - sebelumnya

  return {
    ticker,
    price,
    change,
    change_pct: sebelumnya ? (change / sebelumnya) * 100 : 0,
    spark: closes.slice(-SESI_SPARK),
  }
}

/**
 * Riwayat diambil penuh lalu dipotong di sini. Parameter from/to milik
 * /api/data/ohlc tidak dipakai karena membalas HTTP 500 ("column reference
 * tanggal is ambiguous"), jadi penyaringan tanggal dikerjakan di klien.
 */
async function muatSatu(ticker) {
  return ringkas(ticker, await getOhlcHistory(ticker))
}

async function reload() {
  loading.value = true

  const emitenDitampilkan = auth.isAdmin
    ? SUPPORTED_TICKERS
    : (auth.watchlistTersimpan.length 
        ? auth.watchlistTersimpan 
        : (auth.emitenUtama ? [auth.emitenUtama] : []))

  if (!emitenDitampilkan.length) {
    items.value = []
    loading.value = false
    return
  }

  // allSettled: satu emiten gagal tidak boleh mengosongkan seluruh strip.
  const hasil = await Promise.allSettled(emitenDitampilkan.map(muatSatu))

  hasil
    .filter((h) => h.status === 'rejected')
    .forEach((h) => console.error('Gagal mengambil data saham:', h.reason?.message || h.reason))

  items.value = hasil
    .filter((h) => h.status === 'fulfilled' && h.value)
    .map((h) => h.value)

  loading.value = false
}

onMounted(reload)

watch(() => auth.watchlistTersimpan, () => {
  reload()
}, { deep: true })

// StreamPage memanggil strip.reload() dari tombol segarkan.
defineExpose({ reload })

function fmt(number) {
  return Math.round(number).toLocaleString('id-ID')
}

function sparklinePath(values, width = 140, height = 22) {
  if (!values?.length) {
    return ''
  }

  const minimum = Math.min(...values)
  const maximum = Math.max(...values)
  const range = maximum - minimum || 1
  const step = width / (values.length - 1 || 1)

  return values
    .map((value, index) => {
      const x = index * step
      const y =
        height -
        ((value - minimum) / range) * height

      return `${
        index === 0 ? 'M' : 'L'
      }${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

function getColumns(count) {
  if (count === 0) return 1
  if (count <= 5) return count
  if (count <= 10) return Math.ceil(count / 2)
  return 5
}
</script>

<template>
  <div class="trend-strip-wrap">
    <!-- Loading skeleton -->
    <div
      v-if="loading"
      class="trend-strip"
      :style="{ '--cols': 5 }"
    >
      <div
        v-for="index in 5"
        :key="index"
        class="skel trend-skel"
      ></div>
    </div>

    <!-- Daftar saham -->
    <div
      v-else
      class="trend-strip"
      :style="{ '--cols': getColumns(items.length) }"
    >
      <button
        v-for="item in items"
        :key="item.ticker"
        type="button"
        class="trend-card"
        :class="{
          active:
            item.ticker === market.selectedTicker,
        }"
        @click="market.setTicker(item.ticker)"
      >
        <div class="trend-card-top">
          <span class="tk">
            {{ item.ticker }}
          </span>

          <svg
            viewBox="0 0 140 22"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path
              :d="sparklinePath(item.spark)"
              fill="none"
              :stroke="
                item.change >= 0
                  ? 'var(--up)'
                  : 'var(--down)'
              "
              stroke-width="1.6"
            />
          </svg>
        </div>

        <div class="trend-card-bottom">
          <span class="px">
            {{ fmt(item.price) }}
          </span>

          <span
            class="chg"
            :class="
              item.change >= 0
                ? 'text-up'
                : 'text-down'
            "
          >
            {{ item.change >= 0 ? '+' : '' }}
            {{ item.change_pct.toFixed(2) }}%
          </span>
        </div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.trend-strip-wrap {
  display: block;
  width: 100%;
  max-width: none;
  border-bottom: 1px solid var(--border);
  background: var(--card);
  box-sizing: border-box;
}

/*
  Lima saham dibagi rata ke seluruh lebar halaman.
*/
.trend-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;

  width: 100%;
  max-width: none;
  margin: 0;
  padding: 12px 16px;

  overflow: visible;
  box-sizing: border-box;
}

.trend-card {
  flex: 1 1 calc(100% / var(--cols, 5) - 12px);
  display: block;
  min-width: 0;

  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;

  background: var(--card);
  color: inherit;

  font-family: inherit;
  text-align: left;

  cursor: pointer;
  box-sizing: border-box;

  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.15s ease;
}

.trend-card:hover {
  border-color: var(--primary-light);
  transform: translateY(-1px);
}

.trend-card.active {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow:
    0 0 0 1px var(--primary) inset;
}

.trend-card-top,
.trend-card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.trend-card-bottom {
  margin-top: 5px;
}

.tk {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
}

.px {
  min-width: 0;
  color: var(--foreground);
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
}

.chg {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 11.5px;
  font-weight: 600;
}

.trend-card svg {
  display: block;
  width: 90px;
  height: 22px;
  margin-left: auto;
}

.trend-skel {
  flex: 1 1 calc(100% / var(--cols, 5) - 12px);
  height: 68px;
  border-radius: 10px;
  box-sizing: border-box;
}

/* Responsif */
@media (max-width: 640px) {
  .trend-strip {
    padding: 12px;
  }
  .trend-card, .trend-skel {
    flex-basis: calc(50% - 12px);
  }
}

@media (max-width: 400px) {
  .trend-strip {
    gap: 10px;
  }
  .trend-card, .trend-skel {
    flex-basis: 100%;
  }
}
</style>