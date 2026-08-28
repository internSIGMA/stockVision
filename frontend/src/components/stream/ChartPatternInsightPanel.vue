<script setup>
import { computed } from 'vue'
import {
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Award,
  Zap,
  Target,
  HelpCircle,
  Search,
  BookOpen,
  Calendar,
} from '@lucide/vue'
import { formatDate, formatNumber, formatPercent } from '@/utils/format'
import EmptyState from '@/components/ui/EmptyState.vue'

const props = defineProps({
  pattern: { type: Object, default: null },
  pricing: { type: Object, default: () => ({}) },
  rulesChecklist: { type: Array, default: () => [] },
  statisticalNotes: { type: String, default: '' },
  description: { type: String, default: '' },
  detectionReasons: { type: Array, default: () => [] },
  timeline: { type: Object, default: () => ({}) },
  calendarInfo: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const isBullish = computed(() => {
  const bias = props.pattern?.directional_bias?.toLowerCase() || ''
  return bias.includes('bullish')
})

const isConfirmed = computed(() => {
  const st = props.pattern?.pattern_status || ''
  return st === 'CONFIRMED_BREAKOUT' || st === 'TARGET_REACHED'
})

// Dynamic Action Strategy recommendation based on pattern properties
const strategyAction = computed(() => {
  if (!props.pattern) return null
  const status = props.pattern.pattern_status
  const bias = isBullish.value

  if (bias) {
    if (status === 'CONFIRMED_BREAKOUT') {
      return {
        badge: 'BUY ON CONFIRMED BREAKOUT',
        tone: 'up',
        title: 'Breakout Terkonfirmasi — Peluang Akumulasi / Momentum',
        desc: 'Harga telah menembus level resistensi / neckline dengan validasi volume. Pasang Stop Loss disiplin di bawah area support atau swing low pola.',
      }
    } else if (status === 'PENDING_BREAKOUT') {
      return {
        badge: 'WAIT FOR BREAKOUT / BUY ON SUPPORT',
        tone: 'neutral',
        title: 'Formasi Pola Matang — Tunggu Konfirmasi Breakout',
        desc: 'Pola mendekati titik penyelesaian. Disarankan menunggu penutupan candle menembus breakout level atau melakukan cicil beli di batas bawah Buy Area.',
      }
    } else if (status === 'TARGET_REACHED') {
      return {
        badge: 'PROFIT TAKING ZONE',
        tone: 'up',
        title: 'Target Harga Telah Tercapai — Amankan Profit',
        desc: 'Target proyeksi pola telah terealisasi. Disarankan melakukan take profit bertahap (TP1–TP3) dan menaikkan trailing stop untuk mengunci keuntungan.',
      }
    } else {
      return {
        badge: 'WATCHLIST & MONITOR',
        tone: 'down',
        title: 'Pola Tertekan / Invalidation Watch',
        desc: 'Amati reaksi harga di sekitar level support dan stop loss. Hindari masuk posisi agresif sebelum terjadi rejection atau breakout pembalikan.',
      }
    }
  } else {
    // Bearish
    if (status === 'CONFIRMED_BREAKOUT') {
      return {
        badge: 'SELL ON BREAKDOWN / AVOID',
        tone: 'down',
        title: 'Breakdown Terkonfirmasi — Kurangi Posisi / Amankan Modal',
        desc: 'Harga menembus neckline support ke arah bawah. Hindari membuka posisi beli baru atau pertimbangkan cut loss / exit jika masih memegang posisi.',
      }
    } else {
      return {
        badge: 'DEFENSIVE HOLD / PREPARE EXIT',
        tone: 'down',
        title: 'Potensi Pola Penurunan — Waspada Support Kritis',
        desc: 'Formasi pola distribusi bearish terdeteksi. Pasang trailing stop ketat di bawah neckline breakout untuk mengantisipasi akselerasi penurunan.',
      }
    }
  }
})
</script>

<template>
  <div class="flex flex-col gap-4 rounded-xl border-[0.5px] border-border bg-card p-4 sm:p-5 mt-2">
    <!-- Header Card Pola Terdeteksi (Gaya Reference Screenshot) -->
    <header class="flex flex-wrap items-center justify-between gap-3 border-b-[0.5px] border-border pb-3.5">
      <div class="flex flex-wrap items-center gap-2.5">
        <span class="text-base">🌸</span>
        <h3 class="text-sm sm:text-[15px] font-bold text-foreground">
          {{ pattern?.pattern_name || 'Chart Pattern' }}
        </h3>

        <!-- Directional Bias Pill -->
        <span
          class="flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
          :class="
            isBullish
              ? 'bg-[var(--up)]/15 text-[var(--up)] border border-[var(--up)]/30'
              : 'bg-[var(--down)]/15 text-[var(--down)] border border-[var(--down)]/30'
          "
        >
          <span class="h-1.5 w-1.5 rounded-full" :class="isBullish ? 'bg-[var(--up)]' : 'bg-[var(--down)]'" />
          {{ pattern?.directional_bias || 'Neutral' }}
        </span>

        <!-- Pattern Type Pill -->
        <span
          v-if="pattern?.pattern_type"
          class="flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground"
        >
          <span>📐</span>
          {{ pattern.pattern_type }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <span
          class="rounded-md px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wider"
          :class="
            isConfirmed
              ? 'bg-[var(--up)]/15 text-[var(--up)]'
              : 'bg-[var(--warning)]/15 text-[var(--warning)]'
          "
        >
          {{ pattern?.pattern_status?.replace('_', ' ') }}
        </span>
      </div>
    </header>

    <div v-if="loading" class="flex flex-col gap-3 py-4">
      <div v-for="i in 5" :key="i" class="h-4 animate-pulse rounded bg-muted/60" />
    </div>

    <EmptyState
      v-else-if="!pattern"
      title="Belum ada pola chart aktif"
      description="Emiten ini belum memiliki pola chart yang teridentifikasi oleh mesin deteksi."
    />

    <template v-else>
      <!-- Section 1: Apa itu pola ini? -->
      <div class="flex flex-col gap-1.5">
        <h4 class="text-[12px] font-bold text-foreground flex items-center gap-1.5">
          <HelpCircle class="h-3.5 w-3.5 text-[#3B82F6]" />
          Apa itu pola ini?
        </h4>
        <p class="text-[12px] leading-relaxed text-muted-foreground pl-5">
          {{ description || 'Pola grafik pembalikan atau kelanjutan arah yang terbentuk dari struktur ayunan harga (swing high & low).' }}
        </p>
      </div>

      <!-- Section 2: Mengapa pola ini terdeteksi? -->
      <div v-if="detectionReasons.length" class="flex flex-col gap-2">
        <h4 class="text-[12px] font-bold text-foreground flex items-center gap-1.5">
          <Search class="h-3.5 w-3.5 text-[#8B5CF6]" />
          Mengapa pola ini terdeteksi?
        </h4>
        <ul class="flex flex-col gap-1.5 pl-5 text-[11.5px] text-foreground/90">
          <li
            v-for="(reason, idx) in detectionReasons"
            :key="idx"
            class="flex items-start gap-2 leading-relaxed"
          >
            <span class="text-muted-foreground">•</span>
            <span>{{ reason }}</span>
          </li>
        </ul>
      </div>

      <!-- Section 3: Catatan Statistik (Bulkowski) -->
      <div v-if="statisticalNotes" class="flex flex-col gap-1.5 rounded-lg border-[0.5px] border-[#8B5CF6]/30 bg-[#8B5CF6]/5 p-3">
        <h4 class="text-[12px] font-bold text-[#8B5CF6] flex items-center gap-1.5">
          <BookOpen class="h-3.5 w-3.5" />
          Catatan Statistik (Bulkowski)
        </h4>
        <p class="text-[11.5px] leading-relaxed text-muted-foreground">
          {{ statisticalNotes }}
        </p>
      </div>

      <!-- Section 4: Action Strategy & Setup Trading -->
      <div
        v-if="strategyAction"
        class="rounded-lg border p-3.5"
        :class="
          strategyAction.tone === 'up'
            ? 'border-[var(--up)]/30 bg-[var(--up)]/5'
            : strategyAction.tone === 'down'
              ? 'border-[var(--down)]/30 bg-[var(--down)]/5'
              : 'border-[var(--warning)]/30 bg-[var(--warning)]/5'
        "
      >
        <div class="flex flex-wrap items-center justify-between gap-2 mb-1.5">
          <div class="flex items-center gap-1.5">
            <Zap
              class="h-4 w-4"
              :class="
                strategyAction.tone === 'up'
                  ? 'text-[var(--up)]'
                  : strategyAction.tone === 'down'
                    ? 'text-[var(--down)]'
                    : 'text-[var(--warning)]'
              "
            />
            <span class="text-[11.5px] font-bold uppercase tracking-wider text-foreground">
              {{ strategyAction.badge }}
            </span>
          </div>

          <span class="text-[11px] text-muted-foreground">
            Risk-to-Reward: <strong class="text-foreground tabular">{{ pricing.risk_reward_ratio ? `${pricing.risk_reward_ratio}:1` : '—' }}</strong>
          </span>
        </div>
        <p class="text-[11.5px] leading-relaxed text-muted-foreground">
          {{ strategyAction.desc }}
        </p>
      </div>

      <!-- Setup Grid & Fibonacci Targets -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-[11px]">
        <!-- Buy Area -->
        <div class="rounded-md border-[0.5px] border-border bg-card-secondary/50 p-2.5">
          <span class="text-[10px] text-muted-foreground block mb-0.5">Area Beli</span>
          <span class="font-bold tabular text-foreground">
            {{ pricing.buy_area?.min ? `${formatNumber(pricing.buy_area.min)}–${formatNumber(pricing.buy_area.max)}` : formatNumber(pricing.current_price) }}
          </span>
        </div>

        <!-- Breakout Level -->
        <div class="rounded-md border-[0.5px] border-border bg-card-secondary/50 p-2.5">
          <span class="text-[10px] text-muted-foreground block mb-0.5">Level Breakout</span>
          <span class="font-bold tabular text-[#3B82F6]">
            {{ formatNumber(pricing.breakout_level) }}
          </span>
        </div>

        <!-- TP1 Measured Move -->
        <div class="rounded-md border-[0.5px] border-border bg-card-secondary/50 p-2.5">
          <span class="text-[10px] text-muted-foreground block mb-0.5">TP1 (Measured)</span>
          <span class="font-bold tabular text-[var(--up)]">
            {{ formatNumber(pricing.tp1_measured_move || pricing.target_price) }}
          </span>
        </div>

        <!-- TP2 Fibo 127% -->
        <div class="rounded-md border-[0.5px] border-border bg-card-secondary/50 p-2.5">
          <span class="text-[10px] text-muted-foreground block mb-0.5">TP2 (Fibo 127%)</span>
          <span class="font-bold tabular text-[#06B6D4]">
            {{ formatNumber(pricing.tp2_fibo_127) }}
          </span>
        </div>

        <!-- TP3 Golden 161.8% -->
        <div class="rounded-md border-[0.5px] border-border bg-card-secondary/50 p-2.5">
          <span class="text-[10px] text-muted-foreground block mb-0.5">TP3 (Golden 161%)</span>
          <span class="font-bold tabular text-[#EAB308]">
            {{ formatNumber(pricing.tp3_fibo_161_golden) }}
          </span>
        </div>

        <!-- Stop Loss -->
        <div class="rounded-md border-[0.5px] border-border bg-card-secondary/50 p-2.5">
          <span class="text-[10px] text-muted-foreground block mb-0.5">Batas Stop Loss</span>
          <span class="font-bold tabular text-[var(--down)]">
            {{ formatNumber(pricing.stop_loss) }}
          </span>
        </div>
      </div>

      <!-- Checklist Aturan Geometri -->
      <div v-if="rulesChecklist.length" class="flex flex-col gap-2 rounded-lg border-[0.5px] border-border bg-card-secondary/30 p-3">
        <div class="flex items-center justify-between mb-0.5">
          <span class="text-[11.5px] font-bold text-foreground flex items-center gap-1.5">
            <Award class="h-3.5 w-3.5 text-[#10B981]" />
            Checklist Validasi Aturan Pola
          </span>
          <span class="text-[10px] text-muted-foreground">
            {{ rulesChecklist.filter(r => r.passed).length }}/{{ rulesChecklist.length }} Aturan Terpenuhi
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div
            v-for="(item, idx) in rulesChecklist"
            :key="idx"
            class="flex items-start gap-2 rounded-md border-[0.5px] border-border bg-card p-2 text-[11px]"
          >
            <CheckCircle2 v-if="item.passed" class="h-3.5 w-3.5 text-[var(--up)] shrink-0 mt-0.5" />
            <AlertCircle v-else class="h-3.5 w-3.5 text-[var(--warning)] shrink-0 mt-0.5" />

            <div class="min-w-0 flex-1">
              <span class="font-semibold text-foreground block">{{ item.rule }}</span>
              <p class="text-[10.5px] text-muted-foreground leading-snug">
                {{ item.description }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Timeline & Market Status -->
      <footer class="flex flex-wrap items-center justify-between gap-2 border-t-[0.5px] border-border pt-2.5 text-[10.5px] text-muted-foreground">
        <div class="flex flex-wrap items-center gap-3">
          <span v-if="timeline?.start_date">
            Mulai: <strong class="text-foreground">{{ formatDate(timeline.start_date) }}</strong>
          </span>
          <span v-if="timeline?.end_date">
            Selesai: <strong class="text-foreground">{{ formatDate(timeline.end_date) }}</strong>
          </span>
          <span v-if="timeline?.target_date">
            Estimasi Target: <strong class="text-foreground">{{ formatDate(timeline.target_date) }}</strong>
          </span>
        </div>

        <div v-if="calendarInfo?.next_trading_day" class="flex items-center gap-1.5">
          <Calendar class="h-3.5 w-3.5 text-muted-foreground" />
          <span>Hari Bursa Berikutnya: <strong class="text-foreground">{{ formatDate(calendarInfo.next_trading_day) }}</strong></span>
        </div>
      </footer>
    </template>
  </div>
</template>
