<script setup>
import { RefreshCw } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'

defineEmits(['refresh'])

const auth = useAuthStore()
const market = useMarketStore()
</script>

<template>
  <!-- data-lenis-prevent: cegah Lenis membajak scroll di dalam sidebar -->
  <aside
    class="h-full w-[172px] shrink-0 overflow-y-auto border-r-[0.5px] border-sidebar-border bg-sidebar"
    data-lenis-prevent
  >
    <div class="flex items-center justify-between border-b-[0.5px] border-sidebar-border px-3 pb-1.5 pt-2">
      <span class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">Watchlist</span>
      <button
        type="button"
        aria-label="Muat ulang data watchlist"
        class="text-muted-foreground transition-colors hover:text-foreground"
        @click="$emit('refresh')"
      >
        <RefreshCw class="size-[13px]" />
      </button>
    </div>

    <ul>
      <li
        v-for="ticker in auth.watchlist"
        :key="ticker"
        class="cursor-pointer px-3 py-2 transition-colors duration-100"
        :class="
          market.selectedTicker === ticker
            ? 'bg-sidebar-accent font-medium text-sidebar-accent-foreground'
            : 'hover:bg-sidebar-accent'
        "
        @click="market.setTicker(ticker)"
      >
        <p class="text-[13px] font-medium">{{ ticker }}</p>
        <!-- Harga tidak di-fetch oleh sidebar; diisi pada fase berikutnya. -->
        <p class="tabular text-[11px] text-muted-foreground">—</p>
      </li>
    </ul>
  </aside>
</template>
