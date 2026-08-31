<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Activity, CalendarDays, ChevronLeft, ChevronRight, Copy, Target, BookMarked, ExternalLink } from '@lucide/vue'
import { getSchedulerStatus } from '@/api/StockVision'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useNotify } from '@/composables/useNotify'
import { useAuthStore } from '@/stores/auth'
import { formatNumber } from '@/utils/format'
import TrendingStocksStrip from '@/components/shared/TrendingStocksStrip.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'

const REFRESH_MS = 5000

// Bookmarklet: scans localStorage, sessionStorage, cookies, and XHR headers for Stockbit JWT.
// Then opens StockVision /token-callback which passes it securely to the backend.
const FRONTEND_URL = import.meta.env.VITE_FRONTEND_URL || 'http://localhost:5173'
const BOOKMARKLET_CODE = `javascript:(function(){
  function findJWT(){
    var re=/eyJhbGciOi[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+/;
    try{
      for(var i=0;i<localStorage.length;i++){
        var k=localStorage.key(i);
        var v=localStorage.getItem(k);
        var m=v&&v.match(re);
        if(m)return m[0];
      }
    }catch(e){}
    try{
      for(var j=0;j<sessionStorage.length;j++){
        var sk=sessionStorage.key(j);
        var sv=sessionStorage.getItem(sk);
        var sm=sv&&sv.match(re);
        if(sm)return sm[0];
      }
    }catch(e){}
    try{
      var cm=document.cookie.match(re);
      if(cm)return cm[0];
    }catch(e){}
    return null;
  }

  var t=findJWT();
  if(t){
    window.open('${FRONTEND_URL}/token-callback?t='+encodeURIComponent(t),'_blank');
    return;
  }

  var _orig=XMLHttpRequest.prototype.setRequestHeader;
  var _token=null;
  XMLHttpRequest.prototype.setRequestHeader=function(h,v){
    if(h.toLowerCase()==='authorization'&&v.startsWith('Bearer ')){_token=v.split(' ')[1];}
    _orig.apply(this,arguments);
  };
  function check(){
    if(_token){
      window.open('${FRONTEND_URL}/token-callback?t='+encodeURIComponent(_token),'_blank');
    } else {
      alert('Token belum tertangkap. Silakan klik salah satu menu/saham di Stockbit (misal BBCA), lalu jalankan bookmarklet ini lagi.');
    }
  }
  setTimeout(check,1200);
})()`

const bookmarkletSalin = ref(false)

async function salinBookmarklet() {
  try {
    await navigator.clipboard.writeText(BOOKMARKLET_CODE)
    bookmarkletSalin.value = true
    notify.success('Kode bookmarklet disalin!')
    setTimeout(() => (bookmarkletSalin.value = false), 2500)
  } catch {
    notify.error('Gagal menyalin, coba manual')
  }
}

const auth = useAuthStore()
const notify = useNotify()

const data = ref(null)
const loading = ref(true)
const error = ref(null)

const scheduler = computed(() => data.value?.scheduler ?? null)
const market = computed(() => data.value?.market ?? null)

/** Scheduler mengabarkan target-nya sendiri; watchlist user hanya cadangan. */
const targets = computed(() => {
  const t = data.value?.targets
  return Array.isArray(t) && t.length ? t : auth.watchlist
})

// --- Paginasi target emiten: 20 kartu (5 baris x 4 kolom) per halaman. ---
const PER_HALAMAN = 20

const halaman = ref(1)
const seksiEmiten = ref(null)

const totalHalaman = computed(() => Math.max(1, Math.ceil(targets.value.length / PER_HALAMAN)))

// Daftar target ikut disegarkan tiap 5 detik dan bisa menyusut. Tanpa penjepitan
// ini halaman aktif bisa menunjuk rentang yang sudah tidak berisi apa pun.
const halamanAktif = computed(() => Math.min(halaman.value, totalHalaman.value))

const targetsHalaman = computed(() => {
  const mulai = (halamanAktif.value - 1) * PER_HALAMAN
  return targets.value.slice(mulai, mulai + PER_HALAMAN)
})

const rentangTampil = computed(() => {
  if (!targets.value.length) return ''
  const mulai = (halamanAktif.value - 1) * PER_HALAMAN + 1
  const akhir = Math.min(mulai + PER_HALAMAN - 1, targets.value.length)
  return `${mulai}-${akhir} dari ${targets.value.length} emiten`
})

/**
 * Target bisa mencapai ratusan emiten, jadi nomor halaman diringkas jadi
 * maksimal 5 tombol + elipsis supaya tetap muat di layar ponsel.
 */
const nomorHalaman = computed(() => {
  const total = totalHalaman.value
  const kini = halamanAktif.value

  const wajib = new Set([1, total, kini])
  if (kini > 1) wajib.add(kini - 1)
  if (kini < total) wajib.add(kini + 1)

  const urut = [...wajib].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b)

  const hasil = []
  let sebelumnya = 0
  for (const n of urut) {
    if (sebelumnya && n - sebelumnya > 1) hasil.push({ key: `gap-${n}`, elipsis: true })
    hasil.push({ key: `hal-${n}`, nomor: n })
    sebelumnya = n
  }
  return hasil
})

async function keHalaman(tujuan) {
  const n = Math.min(Math.max(1, tujuan), totalHalaman.value)
  if (n === halamanAktif.value) return
  halaman.value = n
  // Tombol paginasi berada di bawah 20 kartu, jadi tanpa ini user mendarat di
  // ujung bawah daftar baru dan harus menggulir manual ke atas.
  await nextTick()
  seksiEmiten.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const hariTrading = computed(() => !!market.value?.is_trading_day)
const jamBursaBuka = computed(() => !!market.value?.is_trading_hours)

// Jam dinding lokal: backend hanya mengirim waktu saat response dibuat,
// jadi detiknya akan membeku kalau tidak diticking sendiri.
const sekarang = ref(new Date())
let jam = null
onMounted(() => {
  jam = setInterval(() => (sekarang.value = new Date()), 1000)
})
onUnmounted(() => clearInterval(jam))

const waktuWib = computed(() => {
  const d = sekarang.value
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
})

async function muat() {
  try {
    data.value = await getSchedulerStatus()
    error.value = null
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => muat())

// Halaman ini kini hanya memantau, tidak mengendalikan — jadi penyegaran
// berkala tidak perlu dijeda oleh aksi apa pun.
useAutoRefresh(muat, REFRESH_MS, ref(true))
</script>

<template>
  <div class="flex flex-col gap-4 p-4">
    <TrendingStocksStrip />

    <div v-if="loading" class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div v-for="i in 4" :key="i" class="h-[124px] animate-pulse rounded-lg bg-muted" />
    </div>

    <EmptyState v-else-if="error" title="Gagal memuat status scheduler" :description="error">
      <template #action>
        <Button variant="outline" size="sm" @click="muat()">Coba lagi</Button>
      </template>
    </EmptyState>

    <template v-else>
      <!-- Dua kartu sejajar: Sesi Bursa | Statistik Crawl -->
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <!-- Sesi bursa: hari trading + status buka/tutup + jam & waktu berjalan -->
        <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex min-h-[45px] items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
            <CalendarDays class="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
            <h2 class="text-[13px] font-medium">Sesi Bursa</h2>
            <StatusPill
              class="ml-auto"
              :label="jamBursaBuka ? 'BUKA' : 'TUTUP'"
              :tone="jamBursaBuka ? 'up' : 'neutral'"
            />
          </header>

          <div class="flex flex-1 flex-col p-3.5">
            <div class="flex items-baseline gap-2">
              <span
                class="text-[19px] font-semibold leading-none"
                :class="hariTrading ? 'text-up' : 'text-muted-foreground'"
              >
                {{ hariTrading ? 'YA' : 'TIDAK' }}
              </span>
              <span class="text-[11px] text-muted-foreground">hari trading</span>
            </div>

            <p class="tabular mt-3 text-[11px] text-muted-foreground">
              Jam Bursa: {{ market?.market_hours || '—' }}
            </p>
            <p class="tabular mt-0.5 text-[11px] text-muted-foreground" role="status">
              {{ waktuWib }} WIB
            </p>
          </div>
        </section>

        <!-- Statistik -->
        <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex min-h-[45px] items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
            <Activity class="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
            <h2 class="text-[13px] font-medium">Statistik Crawl</h2>
          </header>

          <div class="flex flex-1 flex-col justify-center p-3.5">
            <dl class="grid grid-cols-3 gap-2">
              <div>
                <dd class="tabular text-[19px] font-semibold leading-none">
                  {{ formatNumber(scheduler?.total_runs) }}
                </dd>
                <dt class="mt-1 text-[10px] text-muted-foreground">Total</dt>
              </div>
              <div>
                <dd class="tabular text-[19px] font-semibold leading-none text-up">
                  {{ formatNumber(scheduler?.total_success) }}
                </dd>
                <dt class="mt-1 text-[10px] text-muted-foreground">Sukses</dt>
              </div>
              <div>
                <dd class="tabular text-[19px] font-semibold leading-none text-skip">
                  {{ formatNumber(scheduler?.total_skipped) }}
                </dd>
                <dt class="mt-1 text-[10px] text-muted-foreground">Skip</dt>
              </div>
            </dl>
          </div>
        </section>

      </div>

      <!-- Target emiten melebar penuh di bawah kedua kartu -->
      <section ref="seksiEmiten" class="flex flex-col scroll-mt-3 rounded-lg border-[0.5px] border-border bg-card">
        <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
          <Target class="size-3.5 text-muted-foreground" aria-hidden="true" />
          <h2 class="text-[13px] font-medium">Target Emiten</h2>
        </header>

        <div class="flex flex-col gap-3 p-3.5">
          <p class="text-[12px] leading-relaxed text-muted-foreground">
            Emiten yang akan di-crawl otomatis (Stock Info + OHLC).
          </p>

          <EmptyState v-if="!targets.length" title="Belum ada target emiten" />

          <ul v-else class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            <li
              v-for="t in targetsHalaman"
              :key="t"
              class="flex items-center gap-2 rounded-md border-[0.5px] border-border px-2.5 py-2"
            >
              <span
                class="flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-info-bg)] text-[11px] font-semibold text-[var(--color-info-ink)]"
                aria-hidden="true"
              >
                {{ t.charAt(0) }}
              </span>
              <div class="min-w-0">
                <p class="tabular truncate text-[12px] font-semibold">{{ t }}</p>
                <p class="truncate text-[10px] text-muted-foreground">Stock Info + OHLC</p>
              </div>
            </li>
          </ul>

          <nav
            v-if="targets.length"
            class="flex flex-col items-center justify-between gap-2 border-t-[0.5px] border-border pt-3 sm:flex-row"
            aria-label="Navigasi halaman target emiten"
          >
            <p class="tabular text-[11px] text-muted-foreground">{{ rentangTampil }}</p>

            <div v-if="totalHalaman > 1" class="flex items-center gap-1">
              <Button
                variant="outline"
                size="xs"
                :disabled="halamanAktif === 1"
                aria-label="Halaman sebelumnya"
                @click="keHalaman(halamanAktif - 1)"
              >
                <ChevronLeft />
                <span class="hidden sm:inline">Previous</span>
              </Button>

              <template v-for="item in nomorHalaman" :key="item.key">
                <span
                  v-if="item.elipsis"
                  class="px-1 text-[11px] text-muted-foreground"
                  aria-hidden="true"
                >
                  &hellip;
                </span>
                <Button
                  v-else
                  :variant="item.nomor === halamanAktif ? 'default' : 'ghost'"
                  size="icon-xs"
                  class="tabular text-[11px]"
                  :aria-label="`Halaman ${item.nomor}`"
                  :aria-current="item.nomor === halamanAktif ? 'page' : undefined"
                  @click="keHalaman(item.nomor)"
                >
                  {{ item.nomor }}
                </Button>
              </template>

              <Button
                variant="outline"
                size="xs"
                :disabled="halamanAktif === totalHalaman"
                aria-label="Halaman berikutnya"
                @click="keHalaman(halamanAktif + 1)"
              >
                <span class="hidden sm:inline">Next</span>
                <ChevronRight />
              </Button>
            </div>
          </nav>
        </div>
      </section>

      <!-- Bookmarklet Stockbit Token -->
      <section class="rounded-lg border-[0.5px] border-border bg-card">
        <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
          <BookMarked class="size-3.5 text-muted-foreground" aria-hidden="true" />
          <h2 class="text-[13px] font-medium">Bookmarklet Token Stockbit</h2>
        </header>

        <div class="flex flex-col gap-3 p-3.5">
          <p class="text-[12px] leading-relaxed text-muted-foreground">
            Karena Stockbit memblokir login otomatis dari IP server, gunakan bookmarklet ini
            <strong>sekali</strong> untuk mengirim token aktif Anda ke backend.
            Setelah itu backend akan menyegarkan token secara otomatis.
          </p>

          <ol class="flex flex-col gap-1 text-[11px] leading-relaxed text-muted-foreground">
            <li>1. Login ke
              <a href="https://stockbit.com" target="_blank" rel="noopener" class="text-primary underline inline-flex items-center gap-0.5">
                stockbit.com <ExternalLink class="size-3" />
              </a>
            </li>
            <li>2. Klik salah satu saham (contoh: <strong>BBCA, BBRI, BMRI</strong>) — tunggu hingga chart terbuka</li>
            <li>3. Klik tombol <strong>Salin Kode Bookmarklet</strong> di bawah ini</li>
            <li>4. Di browser: <em>Bookmark Manager</em> → buat bookmark baru → paste kode sebagai URL → simpan</li>
            <li>5. Kembali ke tab Stockbit (yang sudah buka halaman saham), klik bookmark tersebut</li>
            <li>6. Tab StockVision baru terbuka otomatis → token terkirim ke backend ✅</li>
          </ol>

          <div class="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              class="gap-1.5"
              @click="salinBookmarklet"
            >
              <Copy class="size-3.5" :class="{ 'text-up': bookmarkletSalin }" />
              {{ bookmarkletSalin ? '✅ Disalin!' : 'Salin Kode Bookmarklet' }}
            </Button>
          </div>

          <p class="rounded-md bg-muted px-3 py-2 text-[10px] text-muted-foreground">
            <strong>Catatan:</strong> Bookmarklet hanya perlu dijalankan <strong>sekali</strong>.
            Backend menyimpan token + refresh token secara otomatis — crawl harian tetap berjalan tanpa intervensi manual.
            Ulangi proses ini hanya jika token benar-benar kedaluwarsa (biasanya setelah beberapa hari tanpa akses).
          </p>
        </div>
      </section>


    </template>
  </div>
</template>
