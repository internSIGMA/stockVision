<script setup>
import { computed, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import WatchlistSidebar from '@/components/watchlist/WatchlistSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'

const route = useRoute()
const auth = useAuthStore()
const market = useMarketStore()

/** Stream satu-satunya halaman berbasis emiten; dua lainnya full-width. */
const showSidebar = computed(() => route.name === 'stream')

// selectedTicker tidak dipersistensi, jadi setelah reload halaman nilainya null
// walaupun sesi user masih ada. Isi ulang dari emiten utama begitu auth siap.
watch(
  () => auth.emitenUtama,
  (utama) => {
    if (utama) market.initTicker(utama)
  },
  { immediate: true },
)

const refreshKey = ref(0)
function onRefresh() {
  refreshKey.value++
}
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden">
    <AppHeader />

    <div class="flex flex-1 overflow-hidden">
      <!-- Di mobile sidebar disembunyikan; EmitenHeader menyediakan dropdown "Pilih Emiten". -->
      <WatchlistSidebar v-if="showSidebar" class="hidden md:block" @refresh="onRefresh" />

      <main class="flex-1 overflow-y-auto bg-background">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" :key="`${route.name}-${refreshKey}`" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>
