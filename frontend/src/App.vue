<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'

const route = useRoute()

const tampilkanHeader = computed(() => {
  return route.meta.hideHeader !== true
})
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <AppHeader v-if="tampilkanHeader" />

    <RouterView />
  </div>
</template>