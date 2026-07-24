import { onBeforeUnmount, onMounted, ref } from 'vue'

/** Ambang subpiksel: scrollLeft kerap meleset pecahan piksel setelah smooth scroll. */
const TOLERANSI = 2

/**
 * Carousel horizontal di atas scroll native. Tombol hanya memanggil scrollBy,
 * jadi roda mouse, drag trackpad, dan swipe di ponsel tetap jalan tanpa kode
 * tambahan — dan posisi tombol selalu konsisten dengan posisi scroll asli.
 *
 * Pemanggil memasang `track` sebagai ref elemen yang punya overflow-x, lalu
 * memanggil `ukur()` setiap kali jumlah item berubah: ResizeObserver hanya
 * bereaksi pada perubahan ukuran kontainer, bukan pada isinya.
 */
export function useCarousel({ lebarKartu = 240, jarak = 12, langkah = 2 } = {}) {
  const track = ref(null)
  const bisaMundur = ref(false)
  const bisaMaju = ref(false)

  let pengamatUkuran = null

  function ukur() {
    const el = track.value
    if (!el) return

    const sisaKanan = el.scrollWidth - el.clientWidth - el.scrollLeft
    bisaMundur.value = el.scrollLeft > TOLERANSI
    bisaMaju.value = sisaKanan > TOLERANSI
  }

  function geser(arah) {
    const el = track.value
    if (!el) return

    // Di viewport sempit satu langkah tidak boleh melompati lebih dari satu layar.
    const jarakGeser = Math.min((lebarKartu + jarak) * langkah, el.clientWidth)
    const halus = !window.matchMedia('(prefers-reduced-motion: reduce)').matches

    el.scrollBy({ left: arah * jarakGeser, behavior: halus ? 'smooth' : 'auto' })
  }

  onMounted(() => {
    const el = track.value
    if (!el) return

    el.addEventListener('scroll', ukur, { passive: true })
    pengamatUkuran = new ResizeObserver(ukur)
    pengamatUkuran.observe(el)
    ukur()
  })

  onBeforeUnmount(() => {
    track.value?.removeEventListener('scroll', ukur)
    pengamatUkuran?.disconnect()
    pengamatUkuran = null
  })

  return {
    track,
    bisaMundur,
    bisaMaju,
    ukur,
    maju: () => geser(1),
    mundur: () => geser(-1),
  }
}
