<script setup>
import { ref } from 'vue'
import { ChevronDown } from '@lucide/vue'

/**
 * Container chart indikator yang bisa dibuka-tutup, satu section per indikator.
 * Chrome-nya sengaja disamakan dengan section Candlestick & Forecasting supaya
 * halaman Stream tetap terbaca sebagai satu tumpukan yang seragam.
 */
const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  /** Ticker aktif, ditampilkan di judul seperti section lain. */
  ticker: { type: String, default: null },
  /** Kunci localStorage untuk mengingat pilihan buka/tutup user. */
  storageKey: { type: String, required: true },
  /** Label kecil di kanan header, mis. asal datanya. */
  badge: { type: String, default: '' },
  badgeTitle: { type: String, default: '' },
})

function bacaPreferensi() {
  // localStorage bisa melempar error di mode privasi ketat — anggap tertutup.
  try {
    return localStorage.getItem(props.storageKey) === 'true'
  } catch {
    return false
  }
}

// Default tertutup: chart indikator adalah pendalaman, bukan info utama halaman.
const terbuka = ref(bacaPreferensi())

/**
 * Isi baru dipasang saat pertama kali dibuka, setelah itu cukup disembunyikan.
 * Canvas Chart.js yang lahir di dalam display:none tidak punya lebar untuk
 * diukur — ditunda begini, chart-nya langsung tergambar dengan ukuran benar.
 */
const pernahDibuka = ref(terbuka.value)

function alihkan() {
  terbuka.value = !terbuka.value
  if (terbuka.value) pernahDibuka.value = true
  try {
    localStorage.setItem(props.storageKey, String(terbuka.value))
  } catch {
    // Preferensinya saja yang tidak tersimpan; section-nya tetap bisa dibuka.
  }
}

const idIsi = `indikator-${props.storageKey}`
</script>

<template>
  <section class="rounded-lg border-[0.5px] border-border bg-card">
    <!-- Seluruh header jadi tombol: target kliknya jauh lebih mudah dikenai
         daripada ikon 12px, dan statusnya terbaca screen reader. -->
    <button
      type="button"
      class="flex w-full flex-wrap items-center gap-3 px-3.5 py-2.5 text-left transition-colors hover:bg-[var(--card-hover)] focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--ring)]"
      :class="terbuka ? 'rounded-t-lg border-b-[0.5px] border-border' : 'rounded-lg'"
      :aria-expanded="terbuka"
      :aria-controls="idIsi"
      @click="alihkan"
    >
      <div class="min-w-0">
        <h2 class="text-[13px] font-medium">
          {{ title }} — <span class="tabular">{{ ticker ?? '—' }}</span>
        </h2>
        <p v-if="subtitle" class="mt-0.5 text-[10px] text-muted-foreground">{{ subtitle }}</p>
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-2">
        <span
          v-if="badge"
          class="rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
          :title="badgeTitle || undefined"
        >
          {{ badge }}
        </span>

        <span class="text-[10px] text-muted-foreground">
          {{ terbuka ? 'Sembunyikan' : 'Tampilkan' }}
        </span>

        <ChevronDown
          class="size-4 text-muted-foreground transition-transform duration-200"
          :class="{ 'rotate-180': terbuka }"
          aria-hidden="true"
        />
      </div>
    </button>

    <!-- v-if hanya untuk pemasangan pertama; sesudahnya v-show supaya canvas
         Chart.js tidak dibangun ulang setiap section dibuka-tutup. -->
    <div v-if="pernahDibuka" v-show="terbuka" :id="idIsi" class="p-3.5">
      <slot />
    </div>
  </section>
</template>
