<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import { Toaster } from '@/components/ui/sonner'

const route = useRoute()

const tampilkanHeader = computed(() => {
  return route.meta.hideHeader !== true
})
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background text-foreground">
    <AppHeader v-if="tampilkanHeader" />

    <main class="flex-1">
      <RouterView />
    </main>

    <AppFooter v-if="tampilkanHeader" />

    <!-- Wadah toast dipasang sekali di sini; useNotify di komponen mana pun
         tidak menampilkan apa-apa tanpa ini. -->
    <Toaster position="top-right" :duration="4000" close-button />
  </div>
</template>