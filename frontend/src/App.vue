<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from '@/layouts/AppShell.vue'
import { Toaster } from '@/components/ui/sonner'

const route = useRoute()

/** Login berdiri sendiri tanpa header/sidebar. */
const tanpaShell = computed(() => route.meta.layout === 'none')
</script>

<template>
  <RouterView v-if="tanpaShell" />
  <AppShell v-else />

  <Toaster position="top-right" />
</template>
