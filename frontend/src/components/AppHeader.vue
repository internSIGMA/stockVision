<script setup>
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { TrendingUp, ListChecks, Clock, Sun, Moon, Menu, X } from 'lucide-vue-next';
import { useMarketStore } from '../store/market.js';
import { useAuthStore } from '../store/auth.js';
import AccountMenu from './AccountMenu.vue';

const route = useRoute();
const router = useRouter();
const market = useMarketStore();
const auth = useAuthStore();

const tabs = [
  { name: 'stream', label: 'Stream', icon: TrendingUp },
  { name: 'crawl-logs', label: 'Crawl Logs', icon: ListChecks },
  { name: 'auto-scheduler', label: 'Auto Scheduler', icon: Clock },
];

const dark = ref(false);
const mobileOpen = ref(false);

watch(
  dark,
  (v) => document.documentElement.classList.toggle('dark', v),
  { immediate: true }
);

function goTo(name) {
  mobileOpen.value = false;
  router.push({ name });
}
</script>

<template>
  <header class="app-header">
    <div class="app-header-inner">
      <div class="brand"><span class="brand-mark"></span> SahamScope</div>

      <nav class="nav-tabs" aria-label="Menu utama">
        <button
          v-for="t in tabs"
          :key="t.name"
          type="button"
          class="nav-tab"
          :class="{ active: route.name === t.name }"
          @click="goTo(t.name)"
        >
          <component :is="t.icon" :size="15" />
          {{ t.label }}
        </button>
      </nav>

      <div class="header-actions">
        <button class="icon-btn" :title="dark ? 'Mode terang' : 'Mode gelap'" @click="dark = !dark">
          <Sun v-if="dark" :size="15" />
          <Moon v-else :size="15" />
        </button>
        <button class="icon-btn hamburger" @click="mobileOpen = true" aria-label="Buka menu">
          <Menu :size="15" />
        </button>
      </div>
    </div>
  </header>

  <transition name="fade">
    <div v-if="mobileOpen" class="mobile-scrim" @click.self="mobileOpen = false">
      <div class="mobile-sheet">
        <div class="mobile-sheet-head">
          <div class="brand" style="font-size:15px;"><span class="brand-mark"></span> SahamScope</div>
          <button class="icon-btn" @click="mobileOpen = false" aria-label="Tutup menu"><X :size="15" /></button>
        </div>

        <label class="mobile-label" for="mobile-ticker-select">Pilih Emiten</label>
        <select id="mobile-ticker-select" v-model="market.selectedTicker" class="mobile-select">
          <option v-for="t in auth.user.watchlist" :key="t" :value="t">{{ t }}</option>
        </select>

        <button
          v-for="t in tabs"
          :key="t.name"
          type="button"
          class="nav-tab mobile-tab"
          :class="{ active: route.name === t.name }"
          @click="goTo(t.name)"
        >
          <component :is="t.icon" :size="15" />
          {{ t.label }}
        </button>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.app-header {
  position: sticky; top: 0; z-index: 40;
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
}
.app-header-inner { max-width: 1400px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; gap: 28px; height: 58px; }
.brand { display: flex; align-items: center; gap: 8px; font-weight: 800; letter-spacing: -.01em; font-size: 17px; white-space: nowrap; }
.brand-mark { width: 22px; height: 22px; border-radius: 5px; background: var(--ink); position: relative; flex: none; }
.brand-mark::after {
  content: ''; position: absolute; left: 4px; right: 4px; bottom: 4px; height: 8px;
  background: linear-gradient(180deg, var(--primary), transparent);
  clip-path: polygon(0 100%, 20% 40%, 40% 65%, 60% 20%, 80% 45%, 100% 0, 100% 100%);
}
.nav-tabs { display: flex; gap: 2px; flex: 1; }
.nav-tab {
  display: flex; align-items: center; gap: 7px; padding: 8px 14px; border-radius: 8px;
  font-size: 13.5px; font-weight: 600; color: var(--ink-muted); cursor: pointer; border: 1px solid transparent;
  background: none; font-family: inherit; transition: all .15s ease;
}
.nav-tab:hover { color: var(--ink); background: var(--surface-sunken); }
.nav-tab.active { color: var(--primary); background: var(--primary-bg); border-color: color-mix(in srgb, var(--primary) 25%, transparent); }
.header-actions { display: flex; align-items: center; gap: 10px; }
.hamburger { display: none; }
@media (max-width: 900px) {
  .nav-tabs { display: none; }
  .hamburger { display: flex; }
}

.mobile-scrim { position: fixed; inset: 0; z-index: 90; background: rgba(0, 0, 0, .35); }
.mobile-sheet { width: 260px; max-width: 88vw; height: 100%; background: var(--surface); border-right: 1px solid var(--border); padding: 16px; }
.mobile-sheet-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.mobile-label { font-size: 11px; font-weight: 700; color: var(--ink-muted); text-transform: uppercase; letter-spacing: .05em; }
.mobile-select {
  width: 100%; margin: 6px 0 16px; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--paper); color: var(--ink); font-family: var(--font-mono);
}
.mobile-tab { width: 100%; margin-bottom: 4px; justify-content: flex-start; }
</style>
