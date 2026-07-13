<script setup>
import { X } from 'lucide-vue-next';

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
});
const emit = defineEmits(['close']);
</script>

<template>
  <transition name="fade">
    <div v-if="open" class="sheet-scrim" @click.self="emit('close')">
      <transition name="slide" appear>
        <div class="sheet-panel" role="dialog" aria-modal="true">
          <div class="sheet-head">
            <div class="sheet-title">{{ title }}</div>
            <button class="icon-btn" aria-label="Tutup" @click="emit('close')"><X :size="15" /></button>
          </div>
          <div class="sheet-body">
            <slot />
          </div>
        </div>
      </transition>
    </div>
  </transition>
</template>

<style scoped>
.sheet-scrim { position: fixed; inset: 0; z-index: 80; background: rgba(0, 0, 0, .35); display: flex; justify-content: flex-end; }
.sheet-panel { width: 380px; max-width: 92vw; height: 100%; background: var(--surface); border-left: 1px solid var(--border); padding: 20px; overflow-y: auto; }
.sheet-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.sheet-title { font-weight: 800; font-size: 16px; }
.slide-enter-active, .slide-leave-active { transition: transform .2s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
</style>
