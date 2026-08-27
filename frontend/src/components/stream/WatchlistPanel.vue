<script setup>
import { ref, watch } from 'vue'
import { Building2, Inbox, Plus } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { createWatchlist } from '@/api/StockVision'
import WatchlistManagerPage from '@/pages/WatchlistManagerPage.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import TrendingStocksStrip from '@/components/shared/TrendingStocksStrip.vue'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

const auth = useAuthStore()
const market = useMarketStore()
const notify = useNotify()

const editorTerbuka = ref(false)
const membuat = ref(false)
const strip = ref(null)

async function watchlistBaru() {
  if (!auth.user || membuat.value) return

  membuat.value = true
  try {
    const nama = `Daftar ${auth.watchlists.length + 1}`
    const created = await createWatchlist(auth.user.id, { name: nama, symbols: [] })
    await auth.fetchWatchlists()
    auth.selectWatchlist(created.id)
    notify.success(`"${nama}" dibuat`, 'Silakan tambahkan emiten.')
  } catch (err) {
    notify.error('Gagal membuat watchlist', err.message)
  } finally {
    membuat.value = false
  }
}

defineExpose({
  reload: () => strip.value?.reload()
})
</script>

<template>
  <div class="rounded-lg border-[0.5px] border-border bg-card overflow-hidden shadow-sm">
    <!-- Header Watchlist Panel -->
    <div class="flex flex-wrap items-center justify-start border-b-[0.5px] border-border bg-muted/20 px-4 py-3 gap-6">
      <div class="flex items-center gap-2.5">
        <Building2 class="size-5 text-primary" aria-hidden="true" />
        <h2 class="text-[16px] font-bold tracking-wide">Watchlist Emiten</h2>
      </div>

      <div class="flex items-center gap-2 w-full sm:w-auto">
        <Select
          :model-value="auth.activeWatchlistId ?? undefined"
          @update:model-value="auth.selectWatchlist($event)"
        >
          <SelectTrigger class="h-8 w-full sm:w-[220px]" aria-label="Pilih watchlist">
            <SelectValue placeholder="Pilih Daftar Pantau" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="w in auth.watchlists" :key="w.id" :value="w.id">
              {{ w.name }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="sm"
          class="h-8 shrink-0 gap-1.5"
          @click="editorTerbuka = true"
        >
          <Plus class="size-3.5" />
          <span class="hidden sm:inline">Kelola</span>
        </Button>
      </div>
    </div>

    <!-- Daftar Emiten (menggunakan TrendingStocksStrip) -->
    <div>
      <EmptyState
        v-if="!auth.watchlistTersimpan.length"
        :icon="Inbox"
        title="Watchlist Kosong"
        description="Tambahkan emiten lewat tombol Kelola di atas untuk memantau analisis."
        class="py-4"
      />

      <TrendingStocksStrip v-else ref="strip" class="border-b-0" />

      <div
        v-if="auth.watchlistTidakDidukung.length"
        class="mt-4 flex items-center gap-2 rounded-md bg-muted/40 px-3 py-2 text-[11px] text-muted-foreground"
      >
        <span class="font-semibold text-warning/80">Catatan:</span>
        Beberapa emiten disembunyikan karena belum didukung oleh sistem ({{ auth.watchlistTidakDidukung.join(', ') }})
      </div>
    </div>

    <!-- Watchlist Manager tidak punya route sendiri lagi — hanya muncul di sini. -->
    <Sheet v-model:open="editorTerbuka">
      <SheetContent side="right" class="w-full gap-0 sm:max-w-[420px]">
        <SheetHeader>
          <SheetTitle>Kelola Watchlist</SheetTitle>
          <SheetDescription>
            Pilih emiten yang ingin kamu pantau. Jangan lupa klik Simpan Perubahan.
          </SheetDescription>
        </SheetHeader>

        <div class="min-h-0 flex-1 overflow-y-auto" data-lenis-prevent>
          <WatchlistManagerPage
            :key="auth.activeWatchlistId"
            @close="editorTerbuka = false"
            @create-new="watchlistBaru"
          />
        </div>
      </SheetContent>
    </Sheet>


  </div>
</template>
