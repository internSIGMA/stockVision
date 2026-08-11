<script setup>
import { computed } from 'vue'
import { Check } from '@lucide/vue'
import Sparkline from '@/components/charts/Sparkline.vue'

const props = defineProps({
  ticker: { type: String, required: true },
  name: { type: String, required: true },
  sector: { type: String, default: 'Perbankan' },
  price: { type: Number, default: 0 },
  changePct: { type: Number, default: 0 },
  sparkline: { type: Array, default: () => [] },
  selected: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle'])

const formatPrice = (val) => {
  if (!val) return '0'
  return val.toLocaleString('id-ID')
}

const formatPct = (val) => {
  if (val == null) return '0.00%'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`.replace('.', ',')
}
</script>

<template>
  <button
    type="button"
    class="group relative flex w-full flex-col overflow-hidden rounded-xl border-[1.5px] p-4 text-left transition-all duration-200"
    :class="[
      selected
        ? 'border-[var(--primary)] bg-[var(--primary-soft)]'
        : 'border-border bg-card hover:border-[var(--primary)] hover:shadow-sm'
    ]"
    @click="emit('toggle')"
  >
    <!-- Checkmark indicator -->
    <div
      v-if="selected"
      class="absolute right-3 top-3 z-10 flex size-5 items-center justify-center rounded-full bg-[var(--primary)] text-primary-foreground shadow-sm"
    >
      <Check class="size-3" stroke-width="3" />
    </div>

    <!-- Sparkline -->
    <div class="mb-4 h-[40px] w-full rounded-md bg-[var(--background-secondary)]/50 px-2 py-1">
      <Sparkline :values="sparkline" :width="180" :height="32" class="w-full" />
    </div>

    <!-- Price and Change -->
    <div class="mb-1 flex items-baseline gap-2">
      <span class="text-lg font-bold leading-none tracking-tight">{{ formatPrice(price) }}</span>
      <span
        class="text-xs font-semibold"
        :class="changePct >= 0 ? 'text-[var(--color-up-ink)]' : 'text-[var(--color-down-ink)]'"
      >
        {{ formatPct(changePct) }}
      </span>
    </div>

    <!-- Ticker and Name -->
    <div class="flex items-end justify-between gap-2 mt-2">
      <div class="min-w-0">
        <h3 class="text-sm font-bold tracking-tight text-foreground">{{ ticker }}</h3>
        <p class="truncate text-[10px] text-muted-foreground">{{ name }}</p>
      </div>

      <!-- Sector Badge -->
      <span
        class="shrink-0 rounded-full px-2 py-0.5 text-[9px] font-medium"
        :class="
          selected
            ? 'bg-[var(--primary)]/10 text-[var(--primary)]'
            : 'bg-muted text-muted-foreground'
        "
      >
        {{ sector }}
      </span>
    </div>
  </button>
</template>
