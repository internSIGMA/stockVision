<script setup>
import { ref, watch } from 'vue';
import { useAuthStore } from '../store/auth.js';
import { useNotify } from '../composables/useNotify.js';

const emit = defineEmits(['done']);
const auth = useAuthStore();
const notify = useNotify();

const local = ref([...auth.user.watchlist]);
const newTicker = ref('');

watch(
  () => auth.user.watchlist,
  (v) => (local.value = [...v])
);

function add() {
  const t = newTicker.value.trim().toUpperCase();
  if (!t) return;
  if (local.value.includes(t)) {
    notify.info(`${t} sudah ada di watchlist.`);
    return;
  }
  local.value.push(t);
  newTicker.value = '';
}

function remove(t) {
  local.value = local.value.filter((x) => x !== t);
}

function save() {
  auth.updateWatchlist(local.value);
  notify.success('Watchlist diperbarui.');
  emit('done');
}
</script>

<template>
  <div class="wl-manager">
    <div class="card-sub" style="margin-bottom: 16px;">
      Tambah atau hapus ticker dari daftar pantau utama.
    </div>

    <div class="add-row">
      <input
        v-model="newTicker"
        type="text"
        placeholder="Kode ticker, mis. BBCA"
        class="mono"
        @keyup.enter="add"
      />
      <button class="btn btn-primary" @click="add">Tambah</button>
    </div>

    <div v-for="t in local" :key="t" class="wl-item">
      <span class="mono item-name">{{ t }}</span>
      <button class="btn" @click="remove(t)">Hapus</button>
    </div>

    <button class="btn btn-primary btn-block" style="margin-top: 16px;" @click="save">
      Simpan Perubahan
    </button>
  </div>
</template>

<style scoped>
.add-row { display: flex; gap: 8px; margin-bottom: 14px; }
.add-row input {
  flex: 1; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--paper); color: var(--ink); text-transform: uppercase;
}
.wl-item {
  display: flex; align-items: center; justify-content: space-between; padding: 9px 10px;
  border-radius: 8px; margin-bottom: 4px;
}
.wl-item:hover { background: var(--surface-sunken); }
.item-name { font-weight: 700; font-size: 13.5px; }
</style>
