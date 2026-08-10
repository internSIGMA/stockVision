<script setup>
import { RouterLink } from 'vue-router'
import { TrendingUp } from '@lucide/vue'
import { useLandingSpotlight } from '@/composables/useLandingSpotlight'
import { useAuthStore } from '@/stores/auth'
import { formatNumber, formatPercent, trendClass } from '@/utils/format'

const auth = useAuthStore()

const { ticker, candles, hargaTerakhir, perubahanPersen, loading, error } =
  useLandingSpotlight()
</script>

<template>
  <div class="flex min-h-screen flex-col bg-[var(--background-secondary)]">
    <header class="flex h-16 items-center justify-between border-b-[0.5px] border-border bg-background px-6 md:px-10">
      <RouterLink to="/" class="flex items-center gap-2.5">
        <span
          class="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"
          aria-hidden="true"
        >
          <TrendingUp class="size-[18px]" />
        </span>
        <span class="text-[15px] font-bold tracking-tight">
          Stock<span class="text-primary">Vision</span>
        </span>
      </RouterLink>

      <div v-if="auth.isInitializing" class="h-9 w-24 animate-pulse rounded-md bg-muted"></div>
      <RouterLink
        v-else
        :to="auth.isLoggedIn ? '/stream' : '/login'"
        class="rounded-md bg-primary px-6 py-2 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90"
      >
        {{ auth.isLoggedIn ? 'Dashboard' : 'Login' }}
      </RouterLink>
    </header>

    <main class="flex flex-1 flex-col items-center px-6 py-16 text-center md:py-20">
      <h1 class="max-w-3xl text-[32px] font-bold leading-[1.15] tracking-tight md:text-[44px]">
        Mulai Analisis Saham dengan
        <span class="block text-primary">Data Cerdas</span>
      </h1>

      <p class="mt-6 max-w-xl text-[13px] leading-relaxed text-muted-foreground">
        Platform interaktif untuk memonitor aliran dana asing, pergerakan bandar, dan prediksi harga
        saham menggunakan machine learning tanpa broker trading.
      </p>

      <!-- Mock jendela browser berisi candlestick OHLC nyata dari backend. -->
      <div class="mt-12 w-full max-w-[820px] rounded-xl border-[0.5px] border-border bg-card p-4 shadow-sm">
        <div class="flex items-center justify-between gap-3 px-1 pb-3">
          <div class="flex items-center gap-2">
            <div class="flex gap-1.5" aria-hidden="true">
              <span v-for="i in 3" :key="i" class="size-2 rounded-full bg-muted-foreground/25"></span>
            </div>

            <!-- Etalase: emiten berperforma terbaik, sama untuk semua pengunjung. -->
            <span v-if="ticker" class="flex items-center gap-1.5">
              <span class="tabular text-[11px] font-semibold">{{ ticker }}</span>
              <span
                class="rounded bg-[var(--color-info-bg)] px-1.5 py-0.5 text-[9px] font-medium text-[var(--color-info-ink)]"
              >
                Performa terbaik
              </span>
            </span>
          </div>

          <div v-if="hargaTerakhir != null" class="flex items-baseline gap-2">
            <span class="tabular text-[12px] font-semibold">{{ formatNumber(hargaTerakhir) }}</span>
            <span class="tabular text-[10px] font-medium" :class="trendClass(perubahanPersen)">
              {{ formatPercent(perubahanPersen) }}
            </span>
          </div>
          <span v-else class="tabular text-[9px] text-muted-foreground">Live Market Overview</span>
        </div>

        <div class="flex h-[260px] items-end gap-[5px] rounded-md border-[0.5px] border-border px-3 pb-3 pt-4">
          <!-- Memuat -->
          <template v-if="loading">
            <div
              v-for="i in 40"
              :key="i"
              class="flex-1 animate-pulse rounded-[1px] bg-muted-foreground/15"
              :style="{ height: `${30 + ((i * 37) % 55)}%` }"
              aria-hidden="true"
            />
          </template>

          <!-- Gagal / kosong -->
          <p v-else-if="error || !candles.length" class="m-auto text-[11px] text-muted-foreground">
            {{ error || 'Data pasar belum tersedia.' }}
          </p>

          <!-- Candlestick nyata -->
          <div
            v-for="(c, i) in candles"
            v-else
            :key="i"
            class="relative h-full flex-1"
            :title="`${c.tanggal}`"
          >
            <span
              class="absolute left-1/2 w-px -translate-x-1/2"
              :class="c.naik ? 'bg-[var(--color-up)]' : 'bg-[var(--color-down)]'"
              :style="{ bottom: `${c.wickBottom}%`, height: `${c.wickHeight}%` }"
            ></span>
            <span
              class="absolute inset-x-0 rounded-[1px]"
              :class="c.naik ? 'bg-[var(--color-up)]' : 'bg-[var(--color-down)]'"
              :style="{ bottom: `${c.bodyBottom}%`, height: `${c.bodyHeight}%` }"
            ></span>
          </div>
        </div>
      </div>

      <div v-if="auth.isInitializing" class="mt-12 h-[52px] w-[240px] animate-pulse rounded-full bg-muted"></div>
      <RouterLink
        v-else
        :to="auth.isLoggedIn ? '/stream' : '/login'"
        class="mt-12 inline-flex h-[52px] items-center justify-center rounded-full bg-primary px-8 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90"
      >
        {{ auth.isLoggedIn ? 'Lanjut ke Dashboard' : 'Mulai Sekarang' }}
      </RouterLink>
    </main>
  </div>
</template>
