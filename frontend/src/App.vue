<script setup>
import { onMounted, onBeforeUnmount } from 'vue';
import Lenis from 'lenis';
import AppHeader from './components/AppHeader.vue';
import TrendingStocksStrip from './components/TrendingStocksStrip.vue';
import ToastStack from './components/ToastStack.vue';

// Lenis smooth scroll — Stream is a single long scrolling page, so this
// keeps navigation between its sections pleasant across all 3 top-level
// pages (per the design carryover from earlier phases).
let lenis = null;
onMounted(() => {
  lenis = new Lenis({ duration: 1.1, smoothWheel: true });
  function raf(time) {
    lenis.raf(time);
    requestAnimationFrame(raf);
  }
  requestAnimationFrame(raf);
});
onBeforeUnmount(() => lenis && lenis.destroy());
</script>

<template>
  <div>
    <AppHeader />
    <!-- Trending Stocks strip is shared across all 3 top-level pages,
         mounted once here rather than per-page. -->
    <TrendingStocksStrip />

    <div class="page-shell">
      <router-view v-slot="{ Component, route }">
        <transition name="fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </div>

    <ToastStack />
  </div>
</template>
