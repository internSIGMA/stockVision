<script setup>
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import AccountSettingsModal from './AccountSettingsModal.vue'
import LogoutConfirmDialog from './LogoutConfirmDialog.vue'

const router = useRouter()
const authStore = useAuthStore()
const { user } = storeToRefs(authStore)
const { isDark } = useTheme()

const accountElement = ref(null)
const menuOpen = ref(false)
const settingsOpen = ref(false)
const showLogoutDialog = ref(false)

const displayName = computed(() => {
  return (
    user.value?.name ||
    user.value?.username ||
    'User'
  )
})

const initials = computed(() => {
  return displayName.value
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0))
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function openAdminManagement() {
  menuOpen.value = false
  router.push('/admin')
}

function openSettings() {
  menuOpen.value = false
  settingsOpen.value = true
}

function logout() {
  menuOpen.value = false
  showLogoutDialog.value = true
}

function performLogout() {
  authStore.logout()
  router.push('/')
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
  document.addEventListener(
    'click',
    closeMenuWhenClickOutside,
  )
})

onBeforeUnmount(() => {
  document.removeEventListener(
    'click',
    closeMenuWhenClickOutside,
  )
})
</script>

<template>
  <div
    ref="accountElement"
    class="account-menu"
  >
    <!-- Tombol akun pada header -->
    <button
      type="button"
      class="account-trigger"
      :class="{
        active: menuOpen,
        'account-trigger--dark': isDark,
      }"
      aria-label="Buka menu akun"
      :aria-expanded="menuOpen"
      @click.stop="toggleMenu"
    >
      <div
        class="account-avatar"
        :class="{
          'account-avatar--dark': isDark,
        }"
      >
        <img
          v-if="user?.avatar"
          :src="user.avatar"
          alt="Foto profil"
        />

        <span v-else>
          {{ initials }}
        </span>
      </div>

      <span
        class="account-name"
        :class="{
          'account-name--dark': isDark,
        }"
      >
        {{ displayName }}
      </span>

      <span
        class="account-arrow"
        :class="{
          rotate: menuOpen,
          'account-arrow--dark': isDark,
        }"
        aria-hidden="true"
      >
        ▾
      </span>
    </button>

    <!-- Dropdown akun -->
    <Transition name="menu">
      <div
        v-if="menuOpen"
        class="account-dropdown"
        :class="{
          'account-dropdown--dark': isDark,
        }"
        @click.stop
      >
        <div class="dropdown-profile">
          <div
            class="dropdown-avatar"
            :class="{
              'dropdown-avatar--dark': isDark,
            }"
          >
            <img
              v-if="user?.avatar"
              :src="user.avatar"
              alt="Foto profil"
            />

            <span v-else>
              {{ initials }}
            </span>
          </div>

          <div class="dropdown-profile-info">
            <strong>
              {{ displayName }}
            </strong>

            <p>
              {{
                user?.email ||
                'Email belum ditambahkan'
              }}
            </p>
          </div>
        </div>

        <div class="dropdown-divider"></div>

      <!-- Admin Management -->
      <button
        type="button"
        class="dropdown-item"
        @click="openAdminManagement"
      >
        <span
          class="dropdown-icon"
          aria-hidden="true"
        >
          🛡
        </span>

        <div>
          <strong>Admin Management</strong>
          <small>Kelola user, role, menu, dan aktivitas</small>
        </div>
      </button>

      <!-- Kelola Akun -->
      <button
        type="button"
        class="dropdown-item"
        @click="openSettings"
      >
        <span
          class="dropdown-icon"
          aria-hidden="true"
        >
          ⚙
        </span>

        <div>
          <strong>Kelola akun</strong>
          <small>Profil dan preferensi</small>
        </div>
      </button>

      <!-- Keluar -->
      <button
        type="button"
        class="dropdown-item logout-item"
        @click="logout"
      >
        <span
          class="dropdown-icon"
          aria-hidden="true"
        >
          ↪
        </span>

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

    <LogoutConfirmDialog
      v-model:open="showLogoutDialog"
      @confirm="performLogout"
    />
  </div>
</template>

<style scoped>
.account-menu {
  position: relative;
}

/* Tombol akun */
.account-trigger {
  display: flex;
  align-items: center;
  gap: 9px;

  min-height: 44px;
  padding: 5px 8px;

  appearance: none;
  border: 1px solid transparent;
  border-radius: 10px;
  outline: none;

  background: transparent;
  color: var(--foreground);

  font-family: inherit;
  cursor: pointer;

  box-shadow: none;
  -webkit-tap-highlight-color: transparent;

  transition:
    color 0.15s ease,
    opacity 0.15s ease;
}

.account-trigger:hover {
  border-color: transparent;
  background: transparent;
  color: var(--foreground);
  opacity: 0.85;
}

.account-trigger.active,
.account-trigger:active,
.account-trigger:focus,
.account-trigger:focus-visible {
  border-color: transparent;
  outline: none;
  background: transparent;
  color: var(--foreground);
  box-shadow: none;
}

/* Tombol akun dark mode */
.account-trigger--dark {
  color: var(--foreground) !important;
}

.account-trigger--dark:hover,
.account-trigger--dark.active,
.account-trigger--dark:active,
.account-trigger--dark:focus,
.account-trigger--dark:focus-visible {
  border-color: transparent !important;
  background: transparent !important;
  color: var(--foreground) !important;
  box-shadow: none !important;
}

/* Avatar */
.account-avatar,
.dropdown-avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;

  overflow: hidden;

  border: 1px solid var(--border);
  border-radius: 50%;

  background: var(--card-hover);
  color: var(--foreground);

  font-weight: 600;
}

.account-avatar {
  width: 32px;
  height: 32px;
  font-size: 13px;
}

.dropdown-avatar {
  width: 44px;
  height: 44px;
  font-size: 14px;
}

.account-avatar--dark,
.dropdown-avatar--dark {
  border-color: var(--border) !important;
  background: var(--card-hover) !important;
  color: var(--foreground) !important;
}

.account-avatar img,
.dropdown-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Nama */
.account-name {
  display: inline-block;

  color: var(--foreground);
  font-size: 13px;
  font-weight: 600;
  line-height: 1;

  opacity: 1;
  visibility: visible;
  white-space: nowrap;
}

.account-name--dark {
  color: var(--foreground) !important;
  opacity: 1 !important;
  visibility: visible !important;
}

/* Panah */
.account-arrow {
  color: var(--muted-foreground);
  font-size: 11px;
  line-height: 1;

  transition: transform 0.2s ease;
}

.account-arrow--dark {
  color: var(--muted-foreground) !important;
}

.account-arrow.rotate {
  transform: rotate(180deg);
}

/* Dropdown akun */
.account-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 99999;

  width: 280px;
  padding: 10px;

  border: 1px solid var(--border);
  border-radius: 14px;

  background: var(--card);
  color: var(--foreground);

  opacity: 1;
  isolation: isolate;
  overflow: hidden;

  box-shadow:
    0 18px 45px rgba(15, 23, 42, 0.2);
}

.account-dropdown--dark {
  border-color: var(--border) !important;
  background: var(--card) !important;
  color: var(--foreground) !important;
  opacity: 1 !important;

  box-shadow:
    0 18px 45px rgba(0, 0, 0, 0.5) !important;
}

/* Profil dalam dropdown */
.dropdown-profile {
  display: flex;
  align-items: center;
  gap: 12px;

  padding: 10px;
}

.dropdown-profile-info {
  min-width: 0;
  flex: 1;
}

.dropdown-profile strong {
  display: block;

  color: var(--foreground);
  font-size: 14px;
  font-weight: 700;
}

.dropdown-profile p {
  max-width: 180px;
  margin: 4px 0 0;

  overflow: hidden;

  color: var(--muted-foreground);
  font-size: 12px;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-dropdown--dark .dropdown-profile strong {
  color: var(--foreground) !important;
}

.account-dropdown--dark .dropdown-profile p {
  color: var(--muted-foreground) !important;
}

/* Garis pemisah */
.dropdown-divider {
  height: 1px;
  margin: 7px 0;

  background: var(--border);
}

.account-dropdown--dark .dropdown-divider {
  background: var(--border) !important;
}

/* Item menu */
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 13px;

  width: 100%;
  padding: 11px;

  appearance: none;
  border: none;
  border-radius: 9px;
  outline: none;

  background: transparent;
  color: var(--foreground);

  font-family: inherit;
  text-align: left;

  cursor: pointer;

  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.dropdown-item:hover,
.dropdown-item:focus-visible {
  background: var(--card-hover);
}

.account-dropdown--dark .dropdown-item {
  color: var(--foreground) !important;
}

.account-dropdown--dark .dropdown-item:hover,
.account-dropdown--dark .dropdown-item:focus-visible {
  background: var(--card-hover) !important;
}

.dropdown-icon {
  flex-shrink: 0;

  width: 18px;

  color: var(--muted-foreground);
  font-size: 15px;
  text-align: center;
}

.account-dropdown--dark .dropdown-icon {
  color: var(--muted-foreground) !important;
}

.dropdown-item > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dropdown-item strong {
  color: var(--foreground);
  font-size: 13px;
  font-weight: 600;
}

.dropdown-item small {
  color: var(--muted-foreground);
  font-size: 11px;
}

.account-dropdown--dark .dropdown-item strong {
  color: var(--foreground) !important;
}

.account-dropdown--dark .dropdown-item small {
  color: var(--muted-foreground) !important;
}

/* Tombol keluar */
.logout-item strong,
.logout-item .dropdown-icon {
  color: var(--destructive);
}

.logout-item:hover,
.logout-item:focus-visible {
  background: var(--down-bg);
}

.account-dropdown--dark .logout-item strong,
.account-dropdown--dark .logout-item .dropdown-icon {
  color: var(--destructive) !important;
}

.account-dropdown--dark .logout-item:hover,
.account-dropdown--dark .logout-item:focus-visible {
  background: color-mix(in srgb, var(--destructive) 12%, transparent) !important;
}

/* Animasi dropdown */
.menu-enter-active,
.menu-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>