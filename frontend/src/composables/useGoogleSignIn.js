import { ref } from 'vue'

/**
 * Harus sama persis dengan expected_client_id di backend/user.py — backend
 * menolak token yang audience-nya berbeda dengan HTTP 400.
 */
const CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ||
  '984699715154-avv957f6q8sncnjglfe00d4ksrg01ifl.apps.googleusercontent.com'

const SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

/** Satu promise dipakai bersama supaya script tidak dipasang dua kali. */
let pemuatan = null

// Script Google dimuat saat dibutuhkan, bukan lewat index.html: hanya halaman
// login yang memakainya, dan halaman lain tidak perlu ikut menunggu.
function muatScript() {
  if (window.google?.accounts?.id) return Promise.resolve()
  if (pemuatan) return pemuatan

  pemuatan = new Promise((resolve, reject) => {
    const el = document.createElement('script')
    el.src = SCRIPT_SRC
    el.async = true
    el.onload = () => resolve()
    el.onerror = () => {
      pemuatan = null
      reject(new Error('Tidak dapat memuat Google Sign-In.'))
    }
    document.head.appendChild(el)
  })

  return pemuatan
}

/**
 * Merender tombol resmi Google ke dalam `wadah`. Pemanggil menaruh wadah itu
 * transparan di atas tombol bergayanya sendiri — One Tap dan prompt() kerap
 * diblokir browser, sedangkan tombol asli Google selalu boleh membuka popup.
 */
export function useGoogleSignIn(onCredential) {
  const siap = ref(false)
  const error = ref('')

  async function pasang(wadah, lebar) {
    if (!wadah) return

    try {
      await muatScript()

      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: (res) => onCredential(res.credential),
      })

      // renderButton menolak lebar di atas 400px.
      window.google.accounts.id.renderButton(wadah, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        width: Math.min(Math.round(lebar) || 320, 400),
      })

      siap.value = true
    } catch (err) {
      error.value = err.message
    }
  }

  return { siap, error, pasang }
}
