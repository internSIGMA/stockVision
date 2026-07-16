<script setup>
import { useNotify } from '../composables/useNotify.js';

const { toasts, dismiss } = useNotify();
</script>

<template>
  <div class="toast-stack" role="status" aria-live="polite">
    <transition-group name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type" @click="dismiss(t.id)">
        {{ t.message }}
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-stack { position: fixed; bottom: 18px; right: 18px; z-index: 100; display: flex; flex-direction: column; gap: 8px; }
.toast {
  background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--ink-muted);
  border-radius: 8px; padding: 10px 14px; font-size: 12.5px; font-weight: 600; box-shadow: var(--shadow-card);
  cursor: pointer; max-width: 280px;
}
.toast.success { border-left-color: var(--up); }
.toast.error { border-left-color: var(--down); }
.toast.info { border-left-color: var(--primary); }
.toast-enter-active, .toast-leave-active { transition: all .2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(8px); }
</style>
