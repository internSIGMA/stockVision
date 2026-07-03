<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { AuthError } from '@/services/authService'
import { generateOHLC, latestQuote } from '@/data/market'
import { number, pct } from '@/utils/format'
import AreaChart from '@/components/charts/AreaChart.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const market = useMarketStore()

const form = reactive({ email: '', password: '', remember: true })
const showPassword = ref(false)
const submitted = ref(false)
const formError = ref('')

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const touched = reactive({ email: false, password: false })

const errors = computed(() => {
  const e = {}
  if (!form.email.trim()) e.email = 'Email wajib diisi.'
  else if (!EMAIL_RE.test(form.email.trim())) e.email = 'Format email tidak valid.'
  if (!form.password) e.password = 'Kata sandi wajib diisi.'
  else if (form.password.length < 6) e.password = 'Kata sandi minimal 6 karakter.'
  return e
})
const isValid = computed(() => Object.keys(errors.value).length === 0)
function fieldError(name) {
  return (submitted.value || touched[name]) && errors.value[name]
}

async function handleSubmit() {
  submitted.value = true
  formError.value = ''
  if (!isValid.value) return
  try {
    const user = await auth.login({ email: form.email, password: form.password }, form.remember)
    if (user?.defaultTicker) market.select(user.defaultTicker)
    router.push(route.query.redirect || '/')
  } catch (err) {
    formError.value = err instanceof AuthError ? err.message : 'Terjadi kesalahan tak terduga. Coba lagi.'
  }
}

// Two demo accounts with different favorites. `ticker` is the top favorite
// shown in the preview when that account is selected.
const demos = [
  { name: 'Fariz', email: 'fariz@sahamscope.id', tag: 'Perbankan', ticker: 'BBCA', favs: 'BBCA · BBRI · BMRI · TLKM' },
  { name: 'Dewi', email: 'dewi@sahamscope.id', tag: 'Properti & Energi', ticker: 'BBNI', favs: 'BBNI · BJBR · ASII · GOTO' },
]
function fillDemo(d) {
  form.email = d.email
  form.password = 'password123'
  formError.value = ''
  preview.value = d.ticker
}

// Embedded chart overview of a single favorite emiten.
const preview = ref('BBCA')
const previewQuote = computed(() => latestQuote(preview.value))
const previewSeries = computed(() => [
  {
    name: preview.value,
    color: previewQuote.value.change >= 0 ? '#16c784' : '#ef4757',
    width: 2.2,
    data: generateOHLC(preview.value, 60).map((d) => ({ x: d.x, y: d.close })),
  },
])
const timeframes = ['1D', '5D', '1M', '3M', '6M', '1Y', '5Y']
</script>

<template>
  <div class="auth">
    <!-- Left: brand + live chart overview -->
    <aside class="auth__brand">
      <div class="brand-top">
        <span class="logo">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#3aab9d" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l5-6 4 3 4-6 5 4" /></svg>
          SahamScope
        </span>
        <span class="tag">Trading Terminal</span>
      </div>

      <div class="preview card">
        <div class="preview-head">
          <div class="pv-quote">
            <span class="pv-code">{{ preview }}</span>
            <span class="pv-price tabular">{{ number(previewQuote.price) }}</span>
            <span class="chg" :class="previewQuote.change >= 0 ? 'chg--up' : 'chg--down'">
              {{ pct(previewQuote.changePct) }}
            </span>
          </div>
          <span class="pv-fav">★ Emiten favorit</span>
        </div>
        <div class="pv-tf">
          <span v-for="(tf, i) in timeframes" :key="tf" :class="{ active: i === 2 }">{{ tf }}</span>
        </div>
        <AreaChart :series="previewSeries" type="area" :height="240" />
      </div>

      <p class="brand-copy">
        Pantau pergerakan bandar, harga, dan aktivitas insider secara real-time —
        langsung dari terminal.
      </p>
    </aside>

    <!-- Right: login form -->
    <main class="auth__panel">
      <div class="form-wrap">
        <header class="form-head">
          <h2>Masuk ke SahamScope 👋</h2>
          <p>Login untuk mengakses terminal & dashboard analisis.</p>
        </header>

        <transition name="fade">
          <div v-if="formError" class="alert" role="alert" aria-live="assertive">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
              <path d="M12 7v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              <circle cx="12" cy="16.5" r="1.2" fill="currentColor" />
            </svg>
            <span>{{ formError }}</span>
          </div>
        </transition>

        <form novalidate @submit.prevent="handleSubmit">
          <div class="field" :class="{ 'field--error': fieldError('email') }">
            <label for="email">Email</label>
            <div class="input">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6" />
                <path d="m4 7 8 6 8-6" stroke="currentColor" stroke-width="1.6" />
              </svg>
              <input id="email" v-model="form.email" type="email" autocomplete="email"
                placeholder="nama@email.com" :aria-invalid="!!fieldError('email')" @blur="touched.email = true" />
            </div>
            <small v-if="fieldError('email')">{{ errors.email }}</small>
          </div>

          <div class="field" :class="{ 'field--error': fieldError('password') }">
            <label for="password">Kata sandi</label>
            <div class="input">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <rect x="4" y="10" width="16" height="10" rx="2" stroke="currentColor" stroke-width="1.6" />
                <path d="M8 10V7a4 4 0 1 1 8 0v3" stroke="currentColor" stroke-width="1.6" />
              </svg>
              <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password" placeholder="••••••••" :aria-invalid="!!fieldError('password')"
                @blur="touched.password = true" />
              <button type="button" class="toggle" @click="showPassword = !showPassword">
                {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
              </button>
            </div>
            <small v-if="fieldError('password')">{{ errors.password }}</small>
          </div>

          <div class="row-between">
            <label class="check"><input v-model="form.remember" type="checkbox" /><span>Ingat saya</span></label>
            <a href="#" class="link" @click.prevent>Lupa kata sandi?</a>
          </div>

          <button type="submit" class="btn-primary" :disabled="auth.loading">
            <span v-if="!auth.loading">Masuk</span>
            <span v-else class="loading"><span class="spinner"></span>Memproses…</span>
          </button>
        </form>

        <div class="demos">
          <p class="demos-title">Akun demo (favorit berbeda)</p>
          <button v-for="d in demos" :key="d.email" type="button" class="demo" @click="fillDemo(d)">
            <span class="demo-avatar">{{ d.name.charAt(0) }}</span>
            <span class="demo-info">
              <strong>{{ d.name }} <em>· {{ d.tag }}</em></strong>
              <span class="demo-favs">★ {{ d.favs }}</span>
            </span>
            <span class="demo-go">Isi →</span>
          </button>
          <p class="hint">Semua akun: kata sandi <code>password123</code></p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  background: var(--bg);
}

/* Brand + preview */
.auth__brand {
  background:
    radial-gradient(90% 60% at 15% 10%, rgba(22, 184, 166, 0.12), transparent 60%),
    var(--surface);
  border-right: 1px solid var(--border);
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 26px;
}
.brand-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--text);
}
.tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--brand);
  background: rgba(22, 184, 166, 0.1);
  padding: 5px 10px;
  border-radius: 999px;
}
.preview {
  padding: 18px 18px 8px;
  background: var(--bg);
}
.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.pv-quote {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.pv-code {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.pv-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-muted);
}
.chg {
  font-size: 13px;
  font-weight: 700;
}
.chg--up {
  color: var(--up);
}
.chg--down {
  color: var(--down);
}
.pv-fav {
  font-size: 11.5px;
  font-weight: 700;
  color: #f5b301;
  background: rgba(245, 179, 1, 0.1);
  padding: 5px 10px;
  border-radius: 999px;
}
.pv-tf {
  display: flex;
  gap: 14px;
  margin: 12px 2px 0;
}
.pv-tf span {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-faint);
}
.pv-tf span.active {
  color: var(--text);
}
.brand-copy {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
  max-width: 460px;
  margin-top: auto;
}

/* Form */
.auth__panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.form-wrap {
  width: 100%;
  max-width: 400px;
}
.form-head h2 {
  font-size: 25px;
  letter-spacing: -0.02em;
}
.form-head p {
  color: var(--text-muted);
  margin: 8px 0 24px;
  font-size: 14px;
}
.alert {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--down-bg);
  color: #fda4af;
  border: 1px solid rgba(239, 71, 87, 0.35);
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  margin-bottom: 18px;
}
.field {
  margin-bottom: 18px;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}
.input {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0 14px;
  color: var(--text-faint);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus-within {
  border-color: var(--brand);
  box-shadow: 0 0 0 4px rgba(22, 184, 166, 0.12);
}
.input input {
  flex: 1;
  border: none;
  outline: none;
  padding: 13px 0;
  font-size: 15px;
  color: var(--text);
  background: transparent;
}
.toggle {
  font-size: 13px;
  font-weight: 600;
  color: var(--brand);
}
.field--error .input {
  border-color: var(--danger);
}
.field small {
  display: block;
  color: var(--danger);
  font-size: 12.5px;
  margin-top: 6px;
}
.row-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}
.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
}
.check input {
  width: 16px;
  height: 16px;
  accent-color: var(--brand);
}
.link {
  font-size: 14px;
  font-weight: 600;
  color: var(--brand);
}
.btn-primary {
  width: 100%;
  background: var(--brand);
  color: #04211e;
  font-weight: 700;
  font-size: 15px;
  padding: 14px;
  border-radius: var(--radius-sm);
  transition: background 0.15s, transform 0.05s;
}
.btn-primary:hover:not(:disabled) {
  background: var(--brand-600);
}
.btn-primary:active:not(:disabled) {
  transform: translateY(1px);
}
.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.loading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(4, 33, 30, 0.35);
  border-top-color: #04211e;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.demos {
  margin-top: 26px;
  border-top: 1px solid var(--border);
  padding-top: 18px;
}
.demos-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
  margin-bottom: 10px;
}
.demo {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}
.demo:hover {
  border-color: var(--brand);
  background: var(--surface);
}
.demo-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--brand-700);
  color: var(--brand);
  display: grid;
  place-items: center;
  font-weight: 700;
  flex-shrink: 0;
}
.demo-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.demo-info strong {
  font-size: 13.5px;
  color: var(--text);
}
.demo-info em {
  font-style: normal;
  color: var(--text-faint);
  font-weight: 500;
}
.demo-favs {
  font-size: 11.5px;
  color: var(--text-muted);
  margin-top: 2px;
}
.demo-go {
  font-size: 13px;
  font-weight: 700;
  color: var(--brand);
}
.hint {
  text-align: center;
  color: var(--text-faint);
  font-size: 12.5px;
  margin-top: 10px;
}
.hint code {
  background: var(--surface);
  padding: 2px 6px;
  border-radius: 6px;
  color: var(--text-muted);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
@media (max-width: 940px) {
  .auth {
    grid-template-columns: 1fr;
  }
  .auth__brand {
    display: none;
  }
}
</style>
