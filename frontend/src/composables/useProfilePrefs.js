import { ref, watch } from 'vue'

/**
 * Preferensi profil yang TIDAK punya kolom di backend: nomor telepon, foto,
 * dan notifikasi email. Backend hanya menyimpan name/username/email/role/
 * default_ticker (lihat update_user di backend/user.py), jadi ketiga field ini
 * disimpan lokal per pengguna supaya tetap fungsional — bukan sekadar hiasan.
 *
 * Disimpan per user id agar tidak tercampur saat berganti akun di browser sama.
 */
const PREFIX = 'stockvision.profile.'

function baca(userId) {
  try {
    const raw = localStorage.getItem(PREFIX + userId)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function useProfilePrefs(userId) {
  const tersimpan = baca(userId)

  const phone = ref(tersimpan.phone ?? '')
  const emailNotif = ref(tersimpan.emailNotif ?? true)
  const photo = ref(tersimpan.photo ?? '') // data URL, atau '' kalau memakai inisial

  function simpan() {
    localStorage.setItem(
      PREFIX + userId,
      JSON.stringify({ phone: phone.value, emailNotif: emailNotif.value, photo: photo.value }),
    )
  }

  return { phone, emailNotif, photo, simpan }
}

/** Dipakai komponen di luar modal (mis. avatar header) untuk membaca foto saja. */
export function bacaFotoProfil(userId) {
  return baca(userId).photo ?? ''
}
