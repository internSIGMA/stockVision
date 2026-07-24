<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const remember = ref(true)

const error = ref('')
const showPassword = ref(false)

const googleButtonRef = ref(null)
const googleLoading = ref(false)
const googleError = ref('')

const GOOGLE_CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID

const sedangLogin = computed(() => {
  return auth.loading || googleLoading.value
})

function pesanError(err) {
  return (
    err?.response?.data?.error ||
    err?.response?.data?.message ||
    err?.message ||
    'Login gagal. Periksa email dan kata sandi.'
  )
}

async function lanjut() {
  const redirect =
    typeof route.query.redirect === 'string'
      ? route.query.redirect
      : '/stream'

  await router.replace(redirect)
}

async function onSubmit() {
  error.value = ''
  googleError.value = ''

  if (!email.value.trim()) {
    error.value = 'Email wajib diisi.'
    return
  }

  if (!password.value) {
    error.value = 'Kata sandi wajib diisi.'
    return
  }

  try {
    await auth.login(
      email.value.trim(),
      password.value,
      remember.value,
    )

    await lanjut()
  } catch (err) {
    error.value = pesanError(err)
  }
}

async function handleGoogleCredential(response) {
  error.value = ''
  googleError.value = ''

  if (!response?.credential) {
    googleError.value =
      'Token autentikasi Google tidak ditemukan.'
    return
  }

  googleLoading.value = true

  try {
    await auth.googleLogin(response.credential)
    await lanjut()
  } catch (err) {
    googleError.value = pesanError(err)
  } finally {
    googleLoading.value = false
  }
}

async function renderGoogleButton(attempt = 0) {
  await nextTick()

  if (!GOOGLE_CLIENT_ID) {
    googleError.value =
      'VITE_GOOGLE_CLIENT_ID belum diatur di file frontend/.env.'
    return
  }

  if (!googleButtonRef.value) {
    return
  }

  if (!window.google?.accounts?.id) {
    if (attempt >= 20) {
      googleError.value =
        'Layanan Google Login gagal dimuat. Periksa koneksi internet.'
      return
    }

    window.setTimeout(() => {
      renderGoogleButton(attempt + 1)
    }, 300)

    return
  }

  googleButtonRef.value.innerHTML = ''

  window.google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: handleGoogleCredential,
    auto_select: false,
    cancel_on_tap_outside: true,
  })

  const containerWidth =
    googleButtonRef.value.clientWidth || 440

  const buttonWidth = Math.min(
    Math.max(containerWidth, 240),
    440,
  )

  window.google.accounts.id.renderButton(
    googleButtonRef.value,
    {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'rectangular',
      logo_alignment: 'left',
      width: buttonWidth,
      locale: 'id',
    },
  )
}

onMounted(() => {
  renderGoogleButton()
})

onBeforeUnmount(() => {
  window.google?.accounts?.id?.cancel()
})
</script>

<template>
  <main class="login-page">
    <!-- Panel kiri -->
    <section class="brand-panel">
      <div class="brand-header">
        <div class="brand-title">
          <span class="brand-symbol">◆</span>
          <span>StockVision</span>
        </div>

        <p>Dashboard Pasar Saham Indonesia</p>
      </div>

      <div class="market-card">
        <div class="market-name">
          <strong>BBCA</strong>
          <span>IDX</span>
        </div>

        <div class="market-price">9.875</div>

        <div class="market-change">
          +125&nbsp;&nbsp;(+1,28%)
        </div>

        <div class="chart-area">
          <div class="chart-bar bar-1"></div>
          <div class="chart-bar bar-2"></div>
          <div class="chart-bar bar-3"></div>
          <div class="chart-bar bar-4"></div>
          <div class="chart-bar bar-5"></div>
          <div class="chart-bar bar-6"></div>
          <div class="chart-bar bar-7"></div>
          <div class="chart-bar bar-8"></div>
        </div>

        <div class="chart-periods">
          <span class="active">1D</span>
          <span>1W</span>
          <span>1Y</span>
        </div>
      </div>

      <p class="brand-description">
        Pantau data OHLC, foreign flow, insider transaction,
        dan jalankan crawling data saham Indonesia secara
        real-time.
      </p>
    </section>

    <!-- Panel kanan -->
    <section class="form-panel">
      <div class="form-wrapper">
        <header class="form-header">
          <h1>Masuk ke StockVision</h1>

          <p>
            Masukkan email dan kata sandi untuk melanjutkan
          </p>
        </header>

        <form
          class="login-form"
          @submit.prevent="onSubmit"
        >
          <div class="field-group">
            <label for="email">Email</label>

            <input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="email@contoh.com"
              :disabled="sedangLogin"
            />
          </div>

          <div class="field-group">
            <label for="password">Password</label>

            <div class="password-wrapper">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="Masukkan kata sandi"
                :disabled="sedangLogin"
              />

              <button
                type="button"
                class="password-toggle"
                :aria-label="
                  showPassword
                    ? 'Sembunyikan kata sandi'
                    : 'Tampilkan kata sandi'
                "
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
              </button>
            </div>
          </div>

          <div class="form-options">
            <label class="remember-option">
              <input
                v-model="remember"
                type="checkbox"
                :disabled="sedangLogin"
              />

              <span>Ingat saya</span>
            </label>

            <RouterLink
              to="/forgot-password"
              class="forgot-link"
            >
              Lupa password?
            </RouterLink>
          </div>

          <p
            v-if="error"
            class="error-message"
          >
            {{ error }}
          </p>

          <button
            type="submit"
            class="submit-button"
            :disabled="sedangLogin"
          >
            {{ auth.loading ? 'Memproses...' : 'Masuk' }}
          </button>
        </form>

        <div class="register-row">
          <span>Belum punya akun?</span>

          <RouterLink to="/register">
            Buat akun
          </RouterLink>
        </div>

        <!-- Pemisah Google Login -->
        <div class="divider">
          <span></span>

          <p>ATAU MASUK DENGAN</p>

          <span></span>
        </div>

        <!-- Tombol Google resmi -->
        <div class="google-login-area">
          <div
            ref="googleButtonRef"
            class="google-button"
          ></div>

          <p
            v-if="googleLoading"
            class="google-loading"
          >
            Memverifikasi akun Google...
          </p>

          <p
            v-if="googleError"
            class="error-message google-error"
          >
            {{ googleError }}
          </p>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(480px, 1fr);
  background: #ffffff;
  font-family:
    Archivo,
    Arial,
    sans-serif;
}

.brand-panel {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 58px 66px 50px;
  background: #171717;
  color: #ffffff;
}

.brand-header {
  margin-bottom: 40px;
}

.brand-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 23px;
  font-weight: 700;
}

.brand-symbol {
  font-size: 16px;
}

.brand-header p {
  margin: 10px 0 0;
  color: #b8b8b8;
  font-size: 14px;
}

.market-card {
  width: 100%;
  max-width: 720px;
  margin: auto 0;
  padding: 30px 28px 24px;
  border-radius: 18px;
  background: #303030;
}

.market-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.market-name strong {
  font-size: 28px;
}

.market-name span {
  padding: 5px 7px;
  border-radius: 5px;
  background: #505050;
  color: #d3d3d3;
  font-size: 11px;
}

.market-price {
  margin-top: 16px;
  font-family:
    'Spline Sans Mono',
    monospace;
  font-size: 40px;
  font-weight: 600;
}

.market-change {
  margin-top: 6px;
  color: #28d17c;
  font-family:
    'Spline Sans Mono',
    monospace;
  font-size: 16px;
  font-weight: 600;
}

.chart-area {
  height: 110px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 22px;
}

.chart-bar {
  flex: 1;
  min-width: 25px;
  border-radius: 7px;
  background: #9d9d9d;
}

.bar-1 {
  height: 31%;
}

.bar-2 {
  height: 43%;
}

.bar-3 {
  height: 36%;
}

.bar-4 {
  height: 52%;
}

.bar-5 {
  height: 47%;
}

.bar-6 {
  height: 61%;
}

.bar-7 {
  height: 55%;
}

.bar-8 {
  height: 70%;
  background: #c4c4c4;
}

.chart-periods {
  display: flex;
  gap: 18px;
  margin-top: 18px;
  color: #a7a7a7;
  font-size: 12px;
}

.chart-periods span {
  padding: 6px 8px;
}

.chart-periods .active {
  border-radius: 5px;
  background: #606060;
  color: #ffffff;
}

.brand-description {
  max-width: 640px;
  margin: 40px 0 0;
  color: #c5c5c5;
  font-size: 14px;
  line-height: 1.7;
}

.form-panel {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: #ffffff;
}

.form-wrapper {
  width: 100%;
  max-width: 440px;
}

.form-header h1 {
  margin: 0;
  color: #111111;
  font-size: 27px;
  line-height: 1.25;
}

.form-header p {
  margin: 10px 0 0;
  color: #777777;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 36px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-group label {
  color: #111111;
  font-size: 14px;
  font-weight: 600;
}

.field-group input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #dedede;
  border-radius: 8px;
  outline: none;
  background: #ffffff;
  color: #111111;
  font: inherit;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.field-group input:focus {
  border-color: #222222;
  box-shadow: 0 0 0 3px rgb(0 0 0 / 7%);
}

.field-group input:disabled {
  cursor: not-allowed;
  background: #f4f4f4;
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  padding-right: 82px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 12px;
  border: 0;
  background: transparent;
  color: #666666;
  font-size: 12px;
  cursor: pointer;
  transform: translateY(-50%);
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.remember-option {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #222222;
  font-size: 13px;
  cursor: pointer;
}

.remember-option input {
  width: 17px;
  height: 17px;
  accent-color: #171717;
}

.forgot-link {
  color: #777777;
  font-size: 13px;
  text-decoration: none;
}

.forgot-link:hover {
  color: #111111;
}

.error-message {
  margin: 0;
  color: #dc2626;
  font-size: 13px;
  line-height: 1.45;
}

.submit-button {
  width: 100%;
  height: 44px;
  border: 1px solid #171717;
  border-radius: 8px;
  background: #171717;
  color: #ffffff;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s,
    opacity 0.2s;
}

.submit-button:hover:not(:disabled) {
  background: #292929;
}

.submit-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.register-row {
  display: flex;
  justify-content: center;
  gap: 7px;
  margin-top: 20px;
  color: #777777;
  font-size: 13px;
}

.register-row a {
  color: #111111;
  font-weight: 600;
  text-decoration: none;
}

.divider {
  display: flex;
  align-items: center;
  gap: 15px;
  margin: 34px 0 24px;
}

.divider span {
  height: 1px;
  flex: 1;
  background: #dfdfdf;
}

.divider p {
  margin: 0;
  color: #777777;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.google-login-area {
  width: 100%;
}

.google-button {
  width: 100%;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.google-button :deep(div) {
  max-width: 100%;
}

.google-loading {
  margin: 12px 0 0;
  color: #777777;
  text-align: center;
  font-size: 12px;
}

.google-error {
  margin-top: 12px;
  text-align: center;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    display: none;
  }

  .form-panel {
    min-height: 100vh;
    padding: 36px 22px;
  }

  .form-wrapper {
    max-width: 520px;
  }
}

@media (max-width: 480px) {
  .form-panel {
    padding: 28px 18px;
  }

  .form-header h1 {
    font-size: 25px;
  }

  .form-options {
    align-items: flex-start;
  }

  .divider {
    gap: 10px;
  }

  .divider p {
    font-size: 10px;
  }
}
</style>