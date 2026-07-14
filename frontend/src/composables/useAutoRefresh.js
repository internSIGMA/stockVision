import { onUnmounted, unref, watch } from 'vue'

/**
 * Jalankan fetchFn setiap intervalMs selama `enabled` bernilai true.
 *
 * @param {Function} fetchFn   fungsi yang dipanggil tiap tick
 * @param {number}   intervalMs jeda antar pemanggilan
 * @param {import('vue').Ref<boolean>} enabled saklar on/off
 */
export function useAutoRefresh(fetchFn, intervalMs, enabled) {
  let timer = null

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function start() {
    stop()
    timer = setInterval(() => fetchFn(), intervalMs)
  }

  watch(
    () => unref(enabled),
    (on) => (on ? start() : stop()),
    { immediate: true },
  )

  onUnmounted(stop)

  return { start, stop }
}
