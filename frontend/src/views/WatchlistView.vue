<script setup>
import { ref, reactive, computed } from 'vue'
import { useMarketStore } from '@/stores/market'

const market = useMarketStore()

const showModal = ref(false)
const editing = ref(null) // code being edited, or null when adding
const formError = ref('')

const blank = () => ({
  code: '', name: '', sector: 'Perbankan',
  sources: { broker: true, price: true, insider: false },
  interval: 15, enabled: true,
})
const form = reactive(blank())

const modalTitle = computed(() => (editing.value ? `Edit ${editing.value}` : 'Tambah Emiten Crawler'))

function openAdd() {
  Object.assign(form, blank())
  editing.value = null
  formError.value = ''
  showModal.value = true
}
function openEdit(item) {
  Object.assign(form, structuredClone(item))
  editing.value = item.code
  formError.value = ''
  showModal.value = true
}
function close() {
  showModal.value = false
}

function save() {
  formError.value = ''
  const code = form.code.trim().toUpperCase()
  if (!code) return (formError.value = 'Kode emiten wajib diisi.')
  if (!/^[A-Z]{4}$/.test(code)) return (formError.value = 'Kode emiten harus 4 huruf (mis. BBRI).')
  if (!form.name.trim()) return (formError.value = 'Nama emiten wajib diisi.')
  if (!form.sources.broker && !form.sources.price && !form.sources.insider)
    return (formError.value = 'Pilih minimal satu sumber data untuk di-crawl.')

  const payload = { ...structuredClone(form), code }
  try {
    if (editing.value) {
      market.updateWatch(editing.value, payload)
    } else {
      market.addWatch(payload)
    }
    close()
  } catch (e) {
    formError.value = e.message
  }
}

function remove(item) {
  if (confirm(`Hapus ${item.code} dari daftar crawling?`)) market.removeWatch(item.code)
}

const activeSources = (s) =>
  [s.broker && 'Broker', s.price && 'Harga', s.insider && 'Insider'].filter(Boolean)
</script>

<template>
  <div>
    <div class="page-intro head-flex">
      <div>
        <h2>Watchlist Crawler</h2>
        <p>Kelola emiten mana yang akan di-crawl beserta sumber data & intervalnya (CRUD).</p>
      </div>
      <button class="btn btn--primary" @click="openAdd">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
        Tambah emiten
      </button>
    </div>

    <section class="card">
      <div style="overflow-x:auto">
        <table class="dtable">
          <thead>
            <tr>
              <th>Emiten</th><th>Sektor</th><th>Sumber Data</th><th>Interval</th><th>Status</th><th class="num">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in market.watchlist" :key="item.code">
              <td>
                <strong class="strong">{{ item.code }}</strong>
                <span class="ename">{{ item.name }}</span>
              </td>
              <td>{{ item.sector }}</td>
              <td>
                <span v-for="s in activeSources(item.sources)" :key="s" class="pill pill--neutral src">{{ s }}</span>
              </td>
              <td class="tabular">tiap {{ item.interval }} mnt</td>
              <td>
                <button class="switch" :class="{ on: item.enabled }" @click="market.toggleEnabled(item.code)" :aria-label="item.enabled ? 'Nonaktifkan' : 'Aktifkan'">
                  <span class="knob"></span>
                </button>
              </td>
              <td class="num">
                <button class="icon-btn" @click="openEdit(item)" aria-label="Edit">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                </button>
                <button class="icon-btn danger" @click="remove(item)" aria-label="Hapus">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>
                </button>
              </td>
            </tr>
            <tr v-if="market.watchlist.length === 0">
              <td colspan="6" class="empty">Belum ada emiten. Klik "Tambah emiten" untuk mulai.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Modal -->
    <transition name="fade">
      <div v-if="showModal" class="overlay" @click.self="close">
        <div class="modal card">
          <div class="modal-head">
            <h3>{{ modalTitle }}</h3>
            <button class="close" @click="close" aria-label="Tutup">✕</button>
          </div>

          <div v-if="formError" class="modal-error">{{ formError }}</div>

          <div class="fields">
            <div class="f">
              <label>Kode Emiten</label>
              <input v-model="form.code" :disabled="!!editing" maxlength="4" placeholder="BBRI" style="text-transform:uppercase" />
            </div>
            <div class="f">
              <label>Nama Emiten</label>
              <input v-model="form.name" placeholder="Bank Rakyat Indonesia" />
            </div>
            <div class="f">
              <label>Sektor</label>
              <select v-model="form.sector">
                <option>Perbankan</option><option>Telekomunikasi</option><option>Energi</option>
                <option>Konsumer</option><option>Properti</option><option>Teknologi</option>
              </select>
            </div>
            <div class="f">
              <label>Interval crawl (menit)</label>
              <input v-model.number="form.interval" type="number" min="1" max="1440" />
            </div>
          </div>

          <div class="sources">
            <label class="s-title">Sumber data yang di-crawl</label>
            <label class="chk"><input type="checkbox" v-model="form.sources.broker" /> Broker Summary</label>
            <label class="chk"><input type="checkbox" v-model="form.sources.price" /> Harga Harian</label>
            <label class="chk"><input type="checkbox" v-model="form.sources.insider" /> Insider Activity</label>
          </div>

          <label class="chk enabled"><input type="checkbox" v-model="form.enabled" /> Aktifkan crawler untuk emiten ini</label>

          <div class="modal-actions">
            <button class="btn btn--ghost" @click="close">Batal</button>
            <button class="btn btn--primary" @click="save">{{ editing ? 'Simpan' : 'Tambah' }}</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.head-flex {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.ename {
  display: block;
  font-size: 12px;
  color: var(--text-faint);
  margin-top: 2px;
}
.src {
  margin-right: 5px;
}
.empty {
  text-align: center;
  color: var(--text-faint);
  padding: 30px;
}
.switch {
  width: 40px;
  height: 22px;
  border-radius: 999px;
  background: #d6dce2;
  position: relative;
  transition: background 0.15s;
}
.switch.on {
  background: var(--up);
}
.knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s;
}
.switch.on .knob {
  transform: translateX(18px);
}
.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: var(--text-muted);
  transition: background 0.14s, color 0.14s;
}
.icon-btn:hover {
  background: var(--surface-2);
  color: var(--brand);
}
.icon-btn.danger:hover {
  background: var(--down-bg);
  color: var(--down);
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(16, 35, 31, 0.45);
  display: grid;
  place-items: center;
  z-index: 100;
  padding: 20px;
}
.modal {
  width: 100%;
  max-width: 480px;
  padding: 24px;
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.close {
  color: var(--text-faint);
  font-size: 16px;
}
.modal-error {
  background: var(--down-bg);
  color: #b42318;
  border: 1px solid #fecdca;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  margin-bottom: 16px;
}
.fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.f {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.f label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-muted);
}
.f input,
.f select {
  border: 1.5px solid var(--border);
  border-radius: 9px;
  padding: 10px 12px;
  font-size: 14px;
  color: var(--text);
  background: var(--surface);
}
.f input:focus,
.f select:focus {
  outline: none;
  border-color: var(--brand);
}
.f input:disabled {
  background: var(--surface-2);
  color: var(--text-faint);
}
.sources {
  background: var(--surface-2);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 14px;
}
.s-title {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 10px;
}
.chk {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text);
  padding: 5px 0;
  cursor: pointer;
}
.chk input {
  accent-color: var(--brand);
  width: 16px;
  height: 16px;
}
.enabled {
  margin-bottom: 18px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
@media (max-width: 560px) {
  .fields {
    grid-template-columns: 1fr;
  }
}
</style>
