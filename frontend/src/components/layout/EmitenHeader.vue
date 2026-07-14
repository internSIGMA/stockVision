<script setup>
import { computed, ref } from 'vue'
import { RefreshCw, Star, Zap } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { triggerCrawl, triggerCrawlAll } from '@/api/StockVision'
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

const crawlingOne = ref(false)
const crawlingAll = ref(false)
const sibuk = computed(() => crawlingOne.value || crawlingAll.value)

const isUtama = computed(() => market.selectedTicker === auth.emitenUtama)

async function crawlSatu() {
  const ticker = market.selectedTicker
  if (!ticker || sibuk.value) return

  crawlingOne.value = true
  try {
    await triggerCrawl(ticker)
    notify.success(`${ticker} berhasil di-crawl`, 'Data terbaru sudah tersimpan.')
    emit('crawled')
  } catch (err) {
    notify.error(`Crawl ${ticker} gagal`, err.message)
  } finally {
    crawlingOne.value = false
  }
}

async function crawlSemua() {
  if (sibuk.value) return

  crawlingAll.value = true
  try {
    const hasil = await triggerCrawlAll(auth.watchlist)
    const gagal = hasil.filter((r) => !r.ok)
    if (gagal.length) {
      notify.error(
        `${hasil.length - gagal.length}/${hasil.length} emiten berhasil`,
        `Gagal: ${gagal.map((g) => g.ticker).join(', ')}`,
      )
    } else {
      notify.success(`${hasil.length} emiten berhasil di-crawl`)
    }
    emit('crawled')
  } catch (err) {
    notify.error('Crawl gagal', err.message)
  } finally {
    crawlingAll.value = false
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
      <Button variant="outline" size="sm" :disabled="sibuk" @click="crawlSatu">
        <RefreshCw class="size-3.5" :class="{ 'animate-spin': crawlingOne }" />
        {{ crawlingOne ? 'Meng-crawl…' : 'Trigger Crawler' }}
      </Button>

      <Button variant="outline" size="sm" :disabled="sibuk" @click="crawlSemua">
        <Zap class="size-3.5" :class="{ 'animate-pulse': crawlingAll }" />
        {{ crawlingAll ? 'Meng-crawl…' : 'Crawl All' }}
      </Button>
    </div>
  </header>
</template>
