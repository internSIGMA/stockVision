import { reactive } from 'vue';

// Module-level (shared) state so any component can push a toast and
// a single <ToastStack /> mounted once in App.vue can render them all.
const toasts = reactive([]);
let uid = 0;

function push(message, { type = 'info', duration = 3200 } = {}) {
  const id = ++uid;
  toasts.push({ id, message, type });
  setTimeout(() => dismiss(id), duration);
  return id;
}

function dismiss(id) {
  const idx = toasts.findIndex((t) => t.id === id);
  if (idx !== -1) toasts.splice(idx, 1);
}

export function useNotify() {
  return {
    toasts,
    success: (msg, opts) => push(msg, { ...opts, type: 'success' }),
    error: (msg, opts) => push(msg, { ...opts, type: 'error' }),
    info: (msg, opts) => push(msg, { ...opts, type: 'info' }),
    dismiss,
  };
}
