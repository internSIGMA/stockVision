<script setup>
import { ref } from 'vue'
import { Building2, Plus, Star } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { createWatchlist } from '@/api/StockVision'
import WatchlistManagerPage from '@/pages/WatchlistManagerPage.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
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

async function watchlistBaru() {
  if (!auth.user || membuat.value) return

  membuat.value = true
  try {
    const nama = `Daftar Pantau ${auth.watchlists.length + 1}`
    const created = await createWatchlist(auth.user.id, { name: nama, symbols: [] })
    await auth.fetchWatchlists()
    auth.selectWatchlist(created.id)
    notify.success(`"${nama}" dibuat`, 'Tambahkan emiten lewat tombol Edit.')
  } catch (err) {
    notify.error('Gagal membuat watchlist', err.message)
  } finally {
    membuat.value = false
  }
}

async function jadikanUtama(ticker) {
  try {
    await auth.setEmitenUtama(ticker)
    notify.success(`${ticker} jadi emiten utama`)
  } catch (err) {
    notify.error('Gagal menyimpan emiten utama', err.message)
  }
}
</script>

<template>
  <div class="flex flex-col gap-4 rounded-lg border-[0.5px] border-border bg-card p-3.5">
    <!-- Pemilih watchlist -->
    <div class="flex flex-col gap-2">
      <p class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
        Pilihan Watchlist
      </p>

      <!-- min-w-0: SelectTrigger bawaan shadcn punya w-fit + whitespace-nowrap, jadi
           tanpa ini nama watchlist yang panjang melebarkan baris sampai bocor keluar kartu. -->
      <div class="flex min-w-0 items-center gap-1.5">
        <Select
          :model-value="auth.activeWatchlistId ?? undefined"
          @update:model-value="auth.selectWatchlist($event)"
        >
          <SelectTrigger class="h-8 min-w-0 flex-1" aria-label="Pilih watchlist">
            <SelectValue placeholder="Daftar Pantau" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="w in auth.watchlists" :key="w.id" :value="w.id">
              {{ w.name }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="icon"
          class="size-8 shrink-0"
          :disabled="membuat"
          aria-label="Tambah watchlist baru"
          @click="watchlistBaru"
        >
          <Plus class="size-3.5" />
        </Button>

        <Button variant="outline" size="sm" class="h-8 shrink-0" @click="editorTerbuka = true">
          Edit
        </Button>
      </div>
    </div>

    <!-- Focus Emiten -->
    <div class="flex flex-col gap-2">
      <div class="flex items-center gap-1.5">
        <Building2 class="size-3.5 text-muted-foreground" aria-hidden="true" />
        <p class="text-[12px] font-medium">Focus Emiten</p>
      </div>
      <p class="text-[11px] leading-relaxed text-muted-foreground">
        Emiten yang kamu pantau. Klik untuk membuka, klik bintang untuk menjadikannya utama.
      </p>

      <EmptyState
        v-if="!auth.watchlist.length"
        title="Belum ada emiten"
        description="Tambahkan emiten lewat tombol Edit di atas."
      />

      <ul v-else class="flex flex-col gap-1">
        <li
          v-for="ticker in auth.watchlist"
          :key="ticker"
          class="flex items-center justify-between rounded-md border px-2.5 py-2 transition-colors"
          :class="
            market.selectedTicker === ticker
              ? 'border-[var(--color-info)] bg-[var(--color-info-bg)]'
              : 'border-transparent hover:bg-accent'
          "
        >
          <button
            type="button"
            class="flex-1 text-left text-[12px] font-medium"
            :aria-pressed="market.selectedTicker === ticker"
            @click="market.setTicker(ticker)"
          >
            {{ ticker }}
          </button>

          <!-- Padding, bukan ikon lebih besar: ikon 14px tetap proporsional,
               tapi area kliknya naik dari 14px ke 32px. -->
          <button
            type="button"
            class="-mr-1 flex size-8 shrink-0 items-center justify-center rounded-md transition-colors hover:bg-accent"
            :class="
              auth.emitenUtama === ticker
                ? 'text-[var(--color-skip)]'
                : 'text-muted-foreground/50 hover:text-[var(--color-skip)]'
            "
            :aria-label="`Jadikan ${ticker} emiten utama`"
            :aria-pressed="auth.emitenUtama === ticker"
            @click="jadikanUtama(ticker)"
          >
            <Star class="size-3.5" :class="{ 'fill-current': auth.emitenUtama === ticker }" />
          </button>
        </li>
      </ul>

      <p
        v-if="auth.watchlistTidakDidukung.length"
        class="text-[10px] leading-relaxed text-muted-foreground"
      >
        Disembunyikan (belum didukung backend):
        <span class="tabular">{{ auth.watchlistTidakDidukung.join(', ') }}</span>
      </p>
    </div>

    <!-- Watchlist Manager tidak punya route sendiri lagi — hanya muncul di sini. -->
    <Sheet v-model:open="editorTerbuka">
      <SheetContent side="right" class="w-full gap-0 sm:max-w-[420px]">
        <SheetHeader>
          <SheetTitle>Kelola Watchlist</SheetTitle>
          <SheetDescription>
            Pilih emiten yang ingin kamu pantau. Perubahan langsung tersimpan.
          </SheetDescription>
        </SheetHeader>

        <div class="min-h-0 flex-1 overflow-y-auto" data-lenis-prevent>
          <WatchlistManagerPage />
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>
