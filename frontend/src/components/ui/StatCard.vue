<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  sub: { type: String, default: null },
  change: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  /** Pewarnaan opsional untuk angka utama, mis. arah tren. */
  valueClass: { type: String, default: null },
})

// Nol adalah "tidak bergerak", bukan kenaikan — jangan diwarnai hijau.
const changeClass = computed(() => {
  if (props.change == null || props.change === 0) return 'text-muted-foreground'
  return props.change > 0 ? 'text-up' : 'text-down'
})
</script>

<template>
  <div class="rounded-lg border-[0.5px] border-border bg-card p-3.5">
    <div class="flex items-start justify-between gap-2">
      <p class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">{{ label }}</p>
      <slot name="badge" />
    </div>

    <template v-if="loading">
      <div class="mt-2 h-[22px] w-24 animate-pulse rounded bg-muted"></div>
      <div class="mt-2 h-[12px] w-16 animate-pulse rounded bg-muted"></div>
    </template>

    <template v-else>
      <p
        class="tabular mt-1.5 text-[19px] font-semibold leading-none tracking-[-0.01em]"
        :class="valueClass"
      >
        {{ value ?? '—' }}
      </p>

      <div class="mt-2 flex items-center gap-1.5 text-[11px]">
        <span v-if="change != null" class="tabular font-medium" :class="changeClass">
          {{ change > 0 ? '▲' : change < 0 ? '▼' : '' }} {{ Math.abs(change).toFixed(2) }}%
        </span>
        <span v-if="sub" class="tabular truncate text-muted-foreground">{{ sub }}</span>
      </div>
    </template>
  </div>
</template>
