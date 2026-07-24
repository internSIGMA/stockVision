<script setup>
import { computed, ref } from 'vue'
import { RefreshCw, Star } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { triggerSchedulerNow } from '@/api/StockVision'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const emit = defineEmits(['crawled'])

const auth = useAuthStore()
const market = useMarketStore()
const notify = useNotify()

const sibuk = ref(false)

const isUtama = computed(() => market.selectedTicker === auth.emitenUtama)

/**
 * Crawl manual per emiten sudah dimatikan backend (semua endpoint-nya 403).
 * Yang tersisa hanya /scheduler/trigger, dan itu selalu menjalankan seluruh
 * emiten target sekaligus — jadi satu tombol saja, bukan dua yang identik.
 */
async function crawlSekarang() {
  if (sibuk.value) return

  sibuk.value = true
  try {
    const hasil = await triggerSchedulerNow()
    notify.success('Crawl dijalankan', hasil?.message || 'Seluruh emiten target diperbarui.')
    emit('crawled')
  } catch (err) {
    notify.error('Crawl gagal', err.message)
  } finally {
    sibuk.value = false
  }
}
</script>

<template>
  <header
    class="flex flex-wrap items-center gap-3 border-b-[0.5px] border-border bg-card px-4 py-3"
  >
    <div class="flex items-center gap-2">
      <h1 class="tabular text-[18px] font-semibold tracking-[-0.01em]">
        {{ market.selectedTicker ?? '—' }}
      </h1>
      <Star
        v-if="isUtama"
        class="size-[15px] fill-current text-[var(--color-skip)]"
        aria-label="Emiten utama"
      />
    </div>

    <!-- Di layar sempit sidebar disembunyikan, jadi pemilih emiten harus ada di sini. -->
    <Select
      class="md:hidden"
      :model-value="market.selectedTicker ?? undefined"
      @update:model-value="market.setTicker($event)"
    >
      <SelectTrigger class="h-8 w-[132px] md:hidden" aria-label="Pilih emiten">
        <SelectValue placeholder="Pilih Emiten" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem v-for="t in auth.watchlist" :key="t" :value="t">{{ t }}</SelectItem>
      </SelectContent>
    </Select>

    <div class="ml-auto flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        :disabled="sibuk"
        title="Menjalankan crawl untuk seluruh emiten target scheduler"
        @click="crawlSekarang"
      >
        <RefreshCw class="size-3.5" :class="{ 'animate-spin': sibuk }" />
        {{ sibuk ? 'Meng-crawl…' : 'Trigger Crawler' }}
      </Button>
    </div>
  </header>
</template>
