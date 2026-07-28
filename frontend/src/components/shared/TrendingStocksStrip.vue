<script setup>
import { onMounted, ref } from 'vue'
import { TICKERS, getSummary } from '@/lib/mockApi.js'
import { useMarketStore } from '@/store/market.js'

const market = useMarketStore()

const items = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const results = await Promise.all(
      TICKERS.map((ticker) => getSummary(ticker)),
    )

    items.value = results
  } catch (error) {
    console.error('Gagal mengambil data saham:', error)
    items.value = []
  } finally {
    loading.value = false
  }
})

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
</script>

<template>
  <div class="trend-strip-wrap">
    <!-- Loading skeleton -->
    <div
      v-if="loading"
      class="trend-strip"
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
                ? 'up-text'
                : 'down-text'
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
  background: var(--surface);
  box-sizing: border-box;
}

/*
  Lima saham dibagi rata ke seluruh lebar halaman.
*/
.trend-strip {
  display: grid;
  grid-template-columns: repeat(
    5,
    minmax(0, 1fr)
  );
  gap: 12px;

  width: 100%;
  max-width: none;
  margin: 0;
  padding: 12px 16px;

  overflow: visible;
  box-sizing: border-box;
}

.trend-card {
  display: block;
  width: 100%;
  min-width: 0;
  max-width: none;

  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;

  background: var(--surface);
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
  border-color: var(--border-strong);
  transform: translateY(-1px);
}

.trend-card.active {
  border-color: var(--primary);
  background: var(--primary-bg);
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
  color: var(--ink);
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
  width: 100%;
  min-width: 0;
  max-width: none;
  height: 68px;
  border-radius: 10px;
  box-sizing: border-box;
}

/* Tablet besar */
@media (max-width: 1100px) {
  .trend-strip {
    grid-template-columns: repeat(
      3,
      minmax(0, 1fr)
    );
  }
}

/* Tablet */
@media (max-width: 760px) {
  .trend-strip {
    grid-template-columns: repeat(
      2,
      minmax(0, 1fr)
    );
    padding: 12px;
  }
}

/* Mobile */
@media (max-width: 480px) {
  .trend-strip {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>