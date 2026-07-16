<script setup>
import { RouterView } from 'vue-router'
import AppTopbar from './AppTopbar.vue'
</script>

<template>
  <div class="layout">
    <AppTopbar />
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.content {
  flex: 1;
  padding: 24px;
  max-width: 1500px;
  width: 100%;
  margin: 0 auto;
}
@media (max-width: 900px) {
  .content {
    padding: 16px;
  }
}
</style>
