<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import AccountSettingsModal from '@/components/AccountSettingsModal.vue'

const router = useRouter()
const auth = useAuthStore()
const market = useMarketStore()

const menuOpen = ref(false)
const settingsOpen = ref(false)

const initials = computed(() => {
  const name = auth.user?.name || auth.user?.username || 'User'
  return name.charAt(0).toUpperCase()
})

function openSettings() {
  menuOpen.value = false
  settingsOpen.value = true
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="topbar">
    <RouterLink to="/" class="brand">
      <span class="mark">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#04211e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l5-6 4 3 4-6 5 4" /></svg>
      </span>
      <span class="name">SahamScope TEST</span>
    </RouterLink>

    <div class="right">
      <div class="ticker-select">
        <label>Emiten</label>
        <select :value="market.selected" @change="market.select($event.target.value)">
          <option v-for="e in market.universe" :key="e.code" :value="e.code">
            {{ e.code }} — {{ e.name }}
          </option>
        </select>
      </div>

      <button class="icon" aria-label="Notifikasi">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        <span class="badge-dot"></span>
      </button>

    <div class="profile-wrapper">
  <button
    type="button"
    class="profile"
    @click.stop="menuOpen = !menuOpen"
  >
    <img
      v-if="auth.user?.avatar"
      :src="auth.user.avatar"
      :alt="auth.user?.name || 'Foto profil'"
    />

    <span v-else class="avatar-placeholder">
      {{ initials }}
    </span>

    <div class="who-inline">
      <strong>
        {{ auth.user?.name || auth.user?.username || 'User' }}
      </strong>

      <span>
        {{ auth.user?.defaultTicker || 'BBCA' }}
      </span>
    </div>

    <span
      class="profile-arrow"
      :class="{ rotate: menuOpen }"
    >
      ▾
    </span>
  </button>

  <transition name="pop">
    <div
      v-if="menuOpen"
      class="dropdown"
      @click.stop
    >
      <div class="who">
        <strong>
          {{ auth.user?.name || auth.user?.username || 'User' }}
        </strong>

        <span>
          {{ auth.user?.email || 'Email belum tersedia' }}
        </span>
      </div>

      <button
        type="button"
        class="manage-button"
        @click="openSettings"
      >
        <span>⚙</span>

        <div>
          <strong>Kelola akun</strong>
          <small>Profil dan pengaturan user</small>
        </div>
      </button>

      <button
        type="button"
        class="logout-button"
        @click="logout"
      >
        <span>↪</span>

        <div>
          <strong>Keluar</strong>
          <small>Keluar dari StockVision</small>
        </div>
      </button>
    </div>
  </transition>
</div>
    </div>
    <AccountSettingsModal
  :open="settingsOpen"
  @close="settingsOpen = false"
/>
  </header>
</template>

<style scoped>
.topbar {
  height: 60px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 30;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: -0.02em;
  color: var(--text);
}
.mark {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: var(--brand);
  display: grid;
  place-items: center;
}
.right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.ticker-select {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ticker-select label {
  font-size: 12px;
  color: var(--text-faint);
  font-weight: 600;
}
.ticker-select select {
  border: 1px solid var(--border);
  background: var(--surface-2);
  border-radius: 9px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  max-width: 240px;
}
.ticker-select select:focus {
  outline: none;
  border-color: var(--brand);
}
.icon {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border);
  display: grid;
  place-items: center;
  color: var(--text-muted);
}
.icon:hover {
  background: var(--surface-2);
}
.badge-dot {
  position: absolute;
  top: 9px;
  right: 10px;
  width: 7px;
  height: 7px;
  background: var(--down);
  border-radius: 50%;
  border: 1.5px solid var(--surface);
}
.profile {
  position: relative;
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  padding-left: 4px;
}
.profile img {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border);
}
.who-inline {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}
.who-inline strong {
  font-size: 13.5px;
}
.who-inline span {
  font-size: 11.5px;
  color: var(--text-muted);
}
.dropdown {
  position: absolute;
  right: 0;
  top: 50px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  min-width: 210px;
  padding: 8px;
  z-index: 50;
}
.who {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.who span {
  font-size: 12.5px;
  color: var(--text-muted);
}
.dropdown button {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 500;
  color: var(--down);
}
.dropdown button:hover {
  background: var(--down-bg);
}
.pop-enter-active,
.pop-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
@media (max-width: 900px) {
  .topbar {
    height: 56px;
    padding: 0 14px;
  }
  .who-inline {
    display: none;
  }
  .ticker-select label {
    display: none;
  }
}
</style>
