<script setup>
import { watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'

const route = useRoute()
const auth = useAuthStore()
const market = useMarketStore()

// selectedTicker tidak dipersistensi, jadi setelah reload halaman nilainya null
// walaupun sesi user masih ada. Isi ulang dari emiten utama begitu auth siap.
watch(
  () => auth.emitenUtama,
  (utama) => {
    if (utama) market.initTicker(utama)
  },
  { immediate: true },
)
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden">
    <AppHeader />

    <main class="flex-1 overflow-y-auto bg-background">
      <RouterView v-slot="{ Component }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" :key="route.name" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
