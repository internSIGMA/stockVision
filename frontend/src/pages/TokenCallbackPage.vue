<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { updateStockbitToken } from '@/api/StockVision'

const router = useRouter()
const route  = useRoute()

const status  = ref('loading') // 'loading' | 'success' | 'error'
const message = ref('')

onMounted(async () => {
  let token = route.query.t || route.query.token || ''
  token = String(token).trim()
  if (token.toLowerCase().startsWith('bearer ')) {
    token = token.slice(7).trim()
  }

  if (!token || !token.startsWith('eyJhbGciOi')) {
    status.value  = 'error'
    message.value = 'Token tidak valid atau tidak ditemukan di URL.'
    return
  }

  try {
    await updateStockbitToken(token)
    status.value  = 'success'
    message.value = 'Token Stockbit berhasil dikirim ke backend!'
    // Redirect ke scheduler setelah 2 detik
    setTimeout(() => router.replace('/auto-scheduler'), 2000)
  } catch (err) {
    status.value  = 'error'
    message.value = `Gagal mengirim token: ${err?.response?.data?.error || err.message || 'Unknown error'}`
  }
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background p-6">
    <div class="w-full max-w-sm rounded-xl border border-border bg-card p-8 text-center shadow-lg">

      <!-- Loading -->
      <template v-if="status === 'loading'">
        <div class="mx-auto mb-4 size-12 animate-spin rounded-full border-4 border-muted border-t-primary" />
        <h1 class="text-[15px] font-semibold">Mengirim token ke backend…</h1>
        <p class="mt-2 text-[12px] text-muted-foreground">Harap tunggu sebentar.</p>
      </template>

      <!-- Success -->
      <template v-else-if="status === 'success'">
        <div class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-green-100 text-green-600 dark:bg-green-900/30 text-2xl">
          ✅
        </div>
        <h1 class="text-[15px] font-semibold text-green-600 dark:text-green-400">Berhasil!</h1>
        <p class="mt-2 text-[12px] text-muted-foreground">{{ message }}</p>
        <p class="mt-3 text-[11px] text-muted-foreground">Mengarahkan ke halaman Scheduler…</p>
      </template>

      <!-- Error -->
      <template v-else>
        <div class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/30 text-2xl">
          ❌
        </div>
        <h1 class="text-[15px] font-semibold text-red-600 dark:text-red-400">Gagal</h1>
        <p class="mt-2 text-[12px] text-muted-foreground">{{ message }}</p>
        <button
          class="mt-4 rounded-md border border-border px-4 py-1.5 text-[12px] hover:bg-accent"
          @click="$router.replace('/auto-scheduler')"
        >
          Kembali ke Scheduler
        </button>
      </template>

    </div>
  </div>
</template>
