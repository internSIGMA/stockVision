import { computed, onUnmounted, ref } from 'vue'
import { requestResetCode, verifyResetCode, resetPassword } from '@/api/StockVision'

/** Detik sebelum "Kirim ulang kode" bisa ditekan lagi. */
export const JEDA_KIRIM_ULANG = 60

export const PANJANG_KODE = 6

/** Backend menolak password < 6 karakter (user.py). Samakan supaya tidak bentrok. */
export const MIN_PASSWORD = 6

/** Cukup untuk menangkap salah ketik; validasi sesungguhnya tetap di backend. */
const POLA_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Backend belum pasti mengembalikan token — dan kalaupun iya, namanya bisa
 * bermacam-macam. Ambil yang pertama ketemu; null berarti backend stateless
 * dan langkah terakhir cukup mengirim ulang kodenya.
 */
function ambilToken(res) {
  if (!res || typeof res !== 'object') return null
  return res.reset_token ?? res.resetToken ?? res.token ?? res.data?.reset_token ?? null
}

/**
 * Alur lupa password: email → kode → password baru.
 *
 * Semua kegagalan mendarat di `error` sebagai teks siap tampil (inline, bukan
 * toast) — pesan dari backend dipakai apa adanya supaya alasan sebenarnya
 * ("email tidak terdaftar", "kode kedaluwarsa") tidak tertimpa tebakan kita.
 */
export function useAuthReset() {
  const step = ref(1)
  const email = ref('')
  const code = ref('')
  const password = ref('')
  const konfirmasi = ref('')
  const token = ref(null)

  const loading = ref(false)
  const error = ref('')

  /**
   * Kode yang dititipkan backend saat SMTP belum dikonfigurasi (simulated).
   * Null berarti email sungguhan terkirim dan kodenya tidak boleh ada di layar.
   */
  const kodeSimulasi = ref(null)

  const sisaJeda = ref(0)
  let timer = null

  const emailValid = computed(() => POLA_EMAIL.test(email.value.trim()))
  const kodeValid = computed(() => code.value.length === PANJANG_KODE)
  const bisaKirimUlang = computed(() => sisaJeda.value === 0 && !loading.value)

  /** Password baru harus lolos SEMUA syarat sebelum tombol simpan hidup. */
  const passwordValid = computed(
    () => password.value.length >= MIN_PASSWORD && password.value === konfirmasi.value,
  )

  function hentikanJeda() {
    if (timer) clearInterval(timer)
    timer = null
  }

  function mulaiJeda() {
    hentikanJeda()
    sisaJeda.value = JEDA_KIRIM_ULANG
    timer = setInterval(() => {
      sisaJeda.value -= 1
      if (sisaJeda.value <= 0) hentikanJeda()
    }, 1000)
  }

  // Timer hidup lebih lama dari komponen kalau tidak dimatikan di sini.
  onUnmounted(hentikanJeda)

  /** Hanya A-Z dan 0-9, dipotong di 6 — mencegah spasi ikut terkirim saat paste. */
  function setKode(raw) {
    code.value = String(raw || '')
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .slice(0, PANJANG_KODE)
  }

  async function jalankan(fn) {
    loading.value = true
    error.value = ''
    try {
      return await fn()
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  /** Step 1 → 2. Dipakai juga oleh "Kirim ulang kode", karena payload-nya sama. */
  async function kirimKode({ lanjutStep = true } = {}) {
    if (!emailValid.value) {
      error.value = 'Format email tidak valid.'
      return false
    }

    const res = await jalankan(() => requestResetCode(email.value.trim()))
    if (res === null) return false

    // Hanya tampilkan kode kalau backend memang sedang mensimulasikan pengiriman.
    kodeSimulasi.value = res?.simulated ? (res.debug_code ?? null) : null

    mulaiJeda()
    if (lanjutStep) step.value = 2
    return true
  }

  /** Step 2 → 3. */
  async function verifikasiKode() {
    if (!kodeValid.value) {
      error.value = `Kode harus ${PANJANG_KODE} karakter.`
      return false
    }

    const res = await jalankan(() => verifyResetCode(email.value.trim(), code.value))
    if (res === null) return false

    token.value = ambilToken(res)
    step.value = 3
    return true
  }

  /** Step 3 → selesai. */
  async function simpanPassword() {
    if (password.value.length < MIN_PASSWORD) {
      error.value = `Password minimal ${MIN_PASSWORD} karakter.`
      return false
    }
    if (password.value !== konfirmasi.value) {
      error.value = 'Konfirmasi password tidak sama.'
      return false
    }

    const res = await jalankan(() => resetPassword({ token: token.value, password: password.value }))
    return res !== null
  }

  /** Kembali ke Step 1 — kode lama sudah tidak relevan, buang. */
  function kembaliKeStep1() {
    step.value = 1
    code.value = ''
    token.value = null
    kodeSimulasi.value = null
    error.value = ''
    hentikanJeda()
    sisaJeda.value = 0
  }

  return {
    step,
    email,
    code,
    password,
    konfirmasi,
    loading,
    error,
    kodeSimulasi,
    sisaJeda,
    emailValid,
    kodeValid,
    passwordValid,
    bisaKirimUlang,
    setKode,
    kirimKode,
    verifikasiKode,
    simpanPassword,
    kembaliKeStep1,
  }
}
