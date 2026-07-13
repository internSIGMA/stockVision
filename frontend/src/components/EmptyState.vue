<script setup>
import { Inbox } from 'lucide-vue-next';

defineProps({
  text: { type: String, default: 'Belum ada data.' },
});
</script>

<template>
  <div class="empty-state" role="status">
    <Inbox :size="26" :stroke-width="1.6" />
    <div>{{ text }}</div>
  </div>
</template>

<style scoped>
.empty-state { display: flex; flex-direction: column; align-items: center; }
.empty-state svg { opacity: .5; margin-bottom: 8px; }
</style>
