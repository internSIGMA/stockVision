<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import { Toaster } from '@/components/ui/sonner'

const route = useRoute()

const tampilkanHeader = computed(() => {
  return route.meta.hideHeader !== true
})
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <AppHeader v-if="tampilkanHeader" />

    <RouterView />

    <!-- Wadah toast dipasang sekali di sini; useNotify di komponen mana pun
         tidak menampilkan apa-apa tanpa ini. -->
    <Toaster position="top-right" :duration="4000" close-button />
  </div>
</template>