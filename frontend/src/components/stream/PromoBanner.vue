<script setup>
import { Button } from '@/components/ui/button'

/**
 * Materi promo — teks statis, bukan dari API.
 * Satu-satunya elemen yang boleh memakai gradient (branding, bukan data).
 */
const PROMO = {
  badge: 'StockVision Pro Features',
  judul: 'Pantau arus bandar sebelum harga bergerak',
  deskripsi: 'Foreign flow, broker summary, dan sinyal teknikal dalam satu aliran.',
  cta: 'Pelajari',
}
</script>

<template>
  <div
    class="flex items-center gap-4 rounded-lg bg-gradient-to-r from-[#1e3a8a] to-[#0f172a] px-4 py-3.5"
  >
    <div class="min-w-0 flex-1">
      <span
        class="inline-flex w-fit rounded-full border border-white/20 bg-white/10 px-2 py-0.5 text-[9px] font-medium uppercase tracking-[0.08em] text-white/90"
      >
        {{ PROMO.badge }}
      </span>

      <p class="mt-1.5 truncate text-[14px] font-semibold text-white">{{ PROMO.judul }}</p>
      <p class="mt-0.5 truncate text-[11px] text-white/70">{{ PROMO.deskripsi }}</p>
    </div>

    <Button size="sm" class="shrink-0 bg-white text-[#0f172a] hover:bg-white/90">
      {{ PROMO.cta }}
    </Button>
  </div>
</template>
