import { ref, onBeforeUnmount } from 'vue';

/**
 * Runs `callback` on an interval. Used for things like Crawl Logs
 * auto-refresh or the Auto Scheduler's live clock.
 *
 *   const { active, start, stop, toggle } = useAutoRefresh(reload, 30000)
 */
export function useAutoRefresh(callback, intervalMs = 30000, { immediate = false } = {}) {
  const active = ref(false);
  let handle = null;

  function start() {
    if (active.value) return;
    active.value = true;
    if (immediate) callback();
    handle = setInterval(callback, intervalMs);
  }

  function stop() {
    active.value = false;
    if (handle) clearInterval(handle);
    handle = null;
  }

  function toggle() {
    active.value ? stop() : start();
  }

  onBeforeUnmount(stop);

  return { active, start, stop, toggle };
}
