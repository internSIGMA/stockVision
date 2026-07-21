<script setup>
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref
} from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AccountSettingsModal from './AccountSettingsModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const { user } = storeToRefs(authStore)

const accountElement = ref(null)
const menuOpen = ref(false)
const settingsOpen = ref(false)

const displayName = computed(() => {
  return user.value?.name ?? 'Fariz'
})

const defaultTicker = computed(() => {
  return user.value?.defaultTicker ?? 'BJBR'
})

const initials = computed(() => {
  return displayName.value
    .split(' ')
    .map((word) => word.charAt(0))
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function openSettings() {
  menuOpen.value = false
  settingsOpen.value = true
}

function logout() {
  authStore.logout()
  router.push('/login')
}

function closeMenuWhenClickOutside(event) {
  if (
    accountElement.value &&
    !accountElement.value.contains(event.target)
  ) {
    menuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeMenuWhenClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeMenuWhenClickOutside)
})
</script>

<template>
  <div
    ref="accountElement"
    class="account-menu"
  >
    <button
      type="button"
      class="account-trigger"
      :class="{ active: menuOpen }"
      @click.stop="toggleMenu"
    >
      <div class="account-avatar">
        <img
          v-if="user?.avatar"
          :src="user.avatar"
          alt="Foto profil"
        />

        <span v-else>
          {{ initials }}
        </span>
      </div>

      <div class="account-info">
        <span class="account-name">
          {{ displayName }}
        </span>

        <span class="account-separator">·</span>

        <span class="account-ticker">
          {{ defaultTicker }}
        </span>
      </div>

      <span
        class="account-arrow"
        :class="{ rotate: menuOpen }"
      >
        ▾
      </span>
    </button>

    <Transition name="menu">
      <div
        v-if="menuOpen"
        class="account-dropdown"
        @click.stop
      >
        <div class="dropdown-profile">
          <div class="dropdown-avatar">
            <img
              v-if="user?.avatar"
              :src="user.avatar"
              alt="Foto profil"
            />

            <span v-else>
              {{ initials }}
            </span>
          </div>

          <div>
            <strong>{{ displayName }}</strong>
            <p>{{ user?.email || 'Email belum ditambahkan' }}</p>
          </div>
        </div>

        <div class="dropdown-divider"></div>

        <button
          type="button"
          class="dropdown-item"
          @click="openSettings"
        >
          <span>⚙</span>

          <div>
            <strong>Kelola akun</strong>
            <small>Profil dan preferensi</small>
          </div>
        </button>

        <button
          type="button"
          class="dropdown-item logout-item"
          @click="logout"
        >
          <span>↪</span>

          <div>
            <strong>Keluar</strong>
            <small>Keluar dari StockVision</small>
          </div>
        </button>
      </div>
    </Transition>

    <AccountSettingsModal
      :open="settingsOpen"
      @close="settingsOpen = false"
    />
  </div>
</template>

<style scoped>
.account-menu {
  position: relative;
}

.account-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  transition: 0.2s;
}

.account-trigger:hover,
.account-trigger.active {
  border-color: #e5e7eb;
  background: #f8fafc;
}

.account-avatar,
.dropdown-avatar {
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 50%;
  background: #f3f4f6;
  font-weight: 600;
}

.account-avatar {
  width: 32px;
  height: 32px;
}

.dropdown-avatar {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.account-avatar img,
.dropdown-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.account-info {
  display: flex;
  align-items: center;
  gap: 7px;
}

.account-name {
  color: #111827;
  font-weight: 600;
}

.account-separator,
.account-ticker {
  color: #6b7280;
}

.account-arrow {
  color: #6b7280;
  transition: transform 0.2s;
}

.account-arrow.rotate {
  transform: rotate(180deg);
}

.account-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 1000;
  width: 280px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.14);
}

.dropdown-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
}

.dropdown-profile strong {
  font-size: 14px;
}

.dropdown-profile p {
  max-width: 180px;
  margin: 4px 0 0;
  overflow: hidden;
  color: #6b7280;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  margin: 7px 0;
  background: #e5e7eb;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 11px;
  border: none;
  border-radius: 9px;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.dropdown-item div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dropdown-item strong {
  color: #111827;
  font-size: 13px;
}

.dropdown-item small {
  color: #6b7280;
  font-size: 11px;
}

.logout-item:hover {
  background: #fef2f2;
}

.logout-item strong {
  color: #dc2626;
}

.menu-enter-active,
.menu-leave-active {
  transition: 0.15s ease;
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>