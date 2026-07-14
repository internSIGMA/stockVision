<script setup>
import { computed } from 'vue'

/**
 * Label status berwarna: BUY/SELL, SUCCESS/FAILED/SKIP, Bullish/Bearish.
 * Nada bisa diberikan langsung lewat `tone`, atau dibiarkan ditebak dari `label`.
 */
const props = defineProps({
  label: { type: String, required: true },
  tone: { type: String, default: null }, // up | down | skip | info | neutral
})

const TONE_BY_LABEL = {
  BUY: 'up',
  SELL: 'down',
  SUCCESS: 'up',
  FAILED: 'down',
  SKIP: 'skip',
  OPEN: 'up',
  CLOSED: 'down',
  BREAK: 'skip',
}

const tone = computed(
  () => props.tone || TONE_BY_LABEL[String(props.label).toUpperCase()] || 'neutral',
)

// Teks memakai token *-ink (varian gelap) agar tetap >=4.5:1 di atas tint;
// warna dasar hanya untuk border, yang ambangnya cuma 3:1.
const CLASSES = {
  up: 'text-[var(--color-up-ink)] bg-[var(--color-up-bg)] border-[var(--color-up)]/30',
  down: 'text-[var(--color-down-ink)] bg-[var(--color-down-bg)] border-[var(--color-down)]/30',
  skip: 'text-[var(--color-skip-ink)] bg-[var(--color-skip-bg)] border-[var(--color-skip)]/30',
  info: 'text-[var(--color-info-ink)] bg-[var(--color-info-bg)] border-[var(--color-info)]/30',
  neutral: 'text-foreground/75 bg-muted border-border',
}
</script>

<template>
  <span
    class="inline-flex w-fit shrink-0 items-center whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.04em]"
    :class="CLASSES[tone]"
  >
    {{ label }}
  </span>
</template>
