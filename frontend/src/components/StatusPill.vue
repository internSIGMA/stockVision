<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: { type: String, required: true }, // SUCCESS | FAILED | SKIP | BUY | SELL
});

const variant = computed(() => {
  const s = props.status.toUpperCase();
  if (s === 'SUCCESS' || s === 'BUY') return 'pill-success';
  if (s === 'FAILED' || s === 'SELL') return 'pill-failed';
  return 'pill-skip';
});
</script>

<template>
  <span class="pill" :class="variant">{{ status }}</span>
</template>
