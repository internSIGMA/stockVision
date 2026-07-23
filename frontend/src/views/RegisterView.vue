<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()

const nama = ref('')
const email = ref('')
const password = ref('')
const konfirmasiPassword = ref('')

const tampilkanPassword = ref(false)
const tampilkanKonfirmasi = ref(false)

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const passwordCocok = computed(() => {
  if (!konfirmasiPassword.value) return true

  return password.value === konfirmasiPassword.value
})

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''

  if (
    !nama.value.trim() ||
    !email.value.trim() ||
    !password.value ||
    !konfirmasiPassword.value
  ) {
    errorMessage.value = 'Semua kolom wajib diisi.'
    return
  }

  if (nama.value.trim().length < 3) {
    errorMessage.value = 'Nama minimal terdiri dari 3 karakter.'
    return
  }

  if (password.value.length < 8) {
    errorMessage.value = 'Password minimal terdiri dari 8 karakter.'
    return
  }

  if (password.value !== konfirmasiPassword.value) {
    errorMessage.value = 'Konfirmasi password tidak sesuai.'
    return
  }

  loading.value = true

  try {
    /*
      Untuk sementara, kode ini menyimpan akun secara lokal
      agar tampilan register dapat diuji.

      Setelah endpoint backend tersedia, bagian ini akan diganti
      dengan request ke backend Flask.
    */

    const accounts = JSON.parse(
      localStorage.getItem('stockvision.accounts') || '[]'
    )

    const emailSudahTerdaftar = accounts.some(
      (account) =>
        account.email.toLowerCase() === email.value.trim().toLowerCase()
    )

    if (emailSudahTerdaftar) {
      throw new Error('Email tersebut sudah terdaftar.')
    }

    accounts.push({
      id: Date.now(),
      name: nama.value.trim(),
      email: email.value.trim().toLowerCase(),
      password: password.value
    })

    localStorage.setItem(
      'stockvision.accounts',
      JSON.stringify(accounts)
    )

    successMessage.value =
      'Akun berhasil dibuat. Anda akan diarahkan ke halaman login.'

    setTimeout(() => {
      router.push('/login')
    }, 1200)
  } catch (error) {
    errorMessage.value =
      error.message || 'Terjadi kesalahan saat membuat akun.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="register-page">
    <!-- Bagian kiri -->
    <section class="brand-section">
      <div class="brand-header">
        <h1>
          <span class="brand-icon">◆</span>
          StockVision
        </h1>

        <p>Dashboard Pasar Saham Indonesia</p>
      </div>

      <div class="preview-card">
        <div class="stock-heading">
          <h2>BBCA</h2>
          <span>IDX</span>
        </div>

        <h3>9.875</h3>

        <p class="stock-profit">
          +125&nbsp;&nbsp;(+1,28%)
        </p>

        <div class="chart-preview">
          <div class="bar bar-1"></div>
          <div class="bar bar-2"></div>
          <div class="bar bar-3"></div>
          <div class="bar bar-4"></div>
          <div class="bar bar-5"></div>
          <div class="bar bar-6"></div>
          <div class="bar bar-7"></div>
          <div class="bar bar-8"></div>
        </div>

        <div class="chart-period">
          <span class="active">1D</span>
          <span>1W</span>
          <span>1M</span>
          <span>3M</span>
        </div>
      </div>

      <p class="brand-footer">
        Buat akun untuk menyimpan watchlist, melihat pergerakan saham,
        dan menggunakan seluruh fitur StockVision.
      </p>
    </section>

    <!-- Bagian kanan -->
    <section class="form-section">
      <form class="register-form" @submit.prevent="handleRegister">
        <div class="form-heading">
          <h2>Buat akun StockVision</h2>
          <p>Lengkapi data berikut untuk membuat akun baru</p>
        </div>

        <div
          v-if="errorMessage"
          class="alert alert-error"
        >
          {{ errorMessage }}
        </div>

        <div
          v-if="successMessage"
          class="alert alert-success"
        >
          {{ successMessage }}
        </div>

        <div class="form-group">
          <label for="nama">Nama lengkap</label>

          <input
            id="nama"
            v-model="nama"
            type="text"
            placeholder="Masukkan nama lengkap"
            autocomplete="name"
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>

          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="email@contoh.com"
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>

          <div class="password-wrapper">
            <input
              id="password"
              v-model="password"
              :type="tampilkanPassword ? 'text' : 'password'"
              placeholder="Minimal 8 karakter"
              autocomplete="new-password"
            />

            <button
              class="password-toggle"
              type="button"
              @click="tampilkanPassword = !tampilkanPassword"
            >
              {{ tampilkanPassword ? 'Sembunyikan' : 'Lihat' }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="konfirmasi-password">
            Konfirmasi password
          </label>

          <div class="password-wrapper">
            <input
              id="konfirmasi-password"
              v-model="konfirmasiPassword"
              :class="{ invalid: !passwordCocok }"
              :type="tampilkanKonfirmasi ? 'text' : 'password'"
              placeholder="Masukkan kembali password"
              autocomplete="new-password"
            />

            <button
              class="password-toggle"
              type="button"
              @click="tampilkanKonfirmasi = !tampilkanKonfirmasi"
            >
              {{ tampilkanKonfirmasi ? 'Sembunyikan' : 'Lihat' }}
            </button>
          </div>

          <small
            v-if="!passwordCocok"
            class="field-error"
          >
            Konfirmasi password belum sesuai.
          </small>
        </div>

        <button
          class="register-button"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? 'Membuat akun...' : 'Buat akun' }}
        </button>

        <p class="login-link">
          Sudah memiliki akun?
          <RouterLink to="/login">
            Masuk
          </RouterLink>
        </p>
      </form>
    </section>
  </main>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.register-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  background: #ffffff;
}

.brand-section {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100vh;
  padding: 56px;
  color: #ffffff;
  background: #171717;
}

.brand-header h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.brand-icon {
  font-size: 16px;
}

.brand-header p {
  margin-top: 8px;
  color: #b5b5b5;
  font-size: 15px;
}

.preview-card {
  width: 100%;
  max-width: 720px;
  padding: 30px 24px 24px;
  border-radius: 16px;
  background: #303030;
}

.stock-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-heading h2 {
  margin: 0;
  font-size: 29px;
}

.stock-heading span {
  padding: 4px 7px;
  border-radius: 5px;
  color: #ffffff;
  background: #585858;
  font-size: 12px;
  font-weight: 600;
}

.preview-card h3 {
  margin: 16px 0 4px;
  font-size: 40px;
  letter-spacing: 2px;
}

.stock-profit {
  margin: 0;
  color: #39dc82;
  font-weight: 600;
}

.chart-preview {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 95px;
  margin-top: 26px;
}

.bar {
  flex: 1;
  min-width: 20px;
  border-radius: 7px;
  background: #ababab;
}

.bar-1 {
  height: 28px;
}

.bar-2 {
  height: 38px;
}

.bar-3 {
  height: 34px;
}

.bar-4 {
  height: 47px;
}

.bar-5 {
  height: 43px;
}

.bar-6 {
  height: 56px;
}

.bar-7 {
  height: 50px;
}

.bar-8 {
  height: 64px;
}

.chart-period {
  display: flex;
  gap: 20px;
  margin-top: 18px;
  color: #a8a8a8;
  font-size: 12px;
}

.chart-period span {
  padding: 6px 8px;
  border-radius: 5px;
}

.chart-period .active {
  color: #ffffff;
  background: #626262;
  font-weight: 700;
}

.brand-footer {
  max-width: 650px;
  margin: 0;
  color: #c0c0c0;
  line-height: 1.6;
}

.form-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px;
  overflow-y: auto;
}

.register-form {
  width: 100%;
  max-width: 440px;
}

.form-heading {
  margin-bottom: 30px;
}

.form-heading h2 {
  margin: 0 0 8px;
  color: #171717;
  font-size: 28px;
}

.form-heading p {
  margin: 0;
  color: #737373;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #171717;
  font-size: 14px;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border: 1px solid #dedede;
  border-radius: 9px;
  color: #171717;
  background: #ffffff;
  font-size: 14px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.form-group input:focus {
  border-color: #171717;
  box-shadow: 0 0 0 3px rgb(23 23 23 / 8%);
}

.form-group input.invalid {
  border-color: #dc2626;
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  padding-right: 100px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 12px;
  padding: 5px;
  border: none;
  color: #737373;
  background: transparent;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transform: translateY(-50%);
}

.field-error {
  display: block;
  margin-top: 6px;
  color: #dc2626;
}

.alert {
  margin-bottom: 20px;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 14px;
}

.alert-error {
  color: #b42318;
  border: 1px solid #fecdca;
  background: #fef3f2;
}

.alert-success {
  color: #027a48;
  border: 1px solid #abefc6;
  background: #ecfdf3;
}

.register-button {
  width: 100%;
  height: 46px;
  margin-top: 6px;
  border: none;
  border-radius: 9px;
  color: #ffffff;
  background: #171717;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.register-button:hover:not(:disabled) {
  opacity: 0.9;
}

.register-button:active:not(:disabled) {
  transform: scale(0.99);
}

.register-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.login-link {
  margin-top: 20px;
  color: #737373;
  text-align: center;
  font-size: 14px;
}

.login-link a {
  color: #171717;
  font-weight: 600;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}

@media (max-width: 900px) {
  .register-page {
    display: block;
  }

  .brand-section {
    display: none;
  }

  .form-section {
    padding: 32px 22px;
  }
}

@media (max-height: 720px) {
  .form-section {
    align-items: flex-start;
  }
}
</style>