<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  Clock,
  ListChecks,
  LogOut,
  Menu,
  Moon,
  Sun,
  TrendingUp,
} from '@lucide/vue'

import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

import AccountMenu from '@/components/AccountMenu.vue'
import LogoutConfirmDialog from '@/components/LogoutConfirmDialog.vue'

const auth = useAuthStore()
const router = useRouter()
const { isDark, toggle } = useTheme()

const TABS = [
  {
    label: 'Stream',
    to: '/stream',
    icon: TrendingUp,
    adminOnly: false,
  },
  {
    label: 'Crawl Logs',
    to: '/crawl-logs',
    icon: ListChecks,
    adminOnly: true,
  },
  {
    label: 'Auto Scheduler',
    to: '/auto-scheduler',
    icon: Clock,
    adminOnly: true,
  },
]

/*
  Bernilai true saat aplikasi dijalankan dengan:
  npm run dev

  Bernilai false saat aplikasi di-build untuk production.
*/
const isDeveloperMode = import.meta.env.DEV

/*
  Hak akses penuh diberikan kepada:
  1. User dengan role admin.
  2. Developer ketika aplikasi berjalan di mode development.
*/
const hasAdminAccess = computed(() => {
  return auth.isAdmin
})

/*
  Developer lokal dan admin melihat semua menu.
  User biasa di production hanya melihat Stream.
*/
const visibleTabs = computed(() => {
  return TABS.filter((tab) => {
    return !tab.adminOnly || hasAdminAccess.value
  })
})

const menuTerbuka = ref(false)
const showLogoutDialog = ref(false)

function keluar() {
  menuTerbuka.value = false
  showLogoutDialog.value = true
}

function performLogout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <header
    class="sticky top-0 z-50 flex h-[52px] items-center gap-3 border-b-0 bg-card px-4 text-foreground shadow-sm"
  >
    <!-- Efek gradasi warna halus di latar -->
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-r from-[var(--primary)]/10 via-[var(--primary)]/5 to-transparent"></div>
    
    <!-- Garis neon tipis di batas bawah -->
    <div class="pointer-events-none absolute inset-x-0 bottom-0 h-[1px] bg-gradient-to-r from-[var(--primary)]/50 via-[var(--primary)]/20 to-border"></div>

    <!-- Konten perlu dibungkus relative z-10 agar berada di atas background glow -->
    <div class="relative z-10 flex w-full items-center gap-3">
    <!-- Logo dan nama aplikasi -->
    <RouterLink
      to="/stream"
      class="shrink-0 text-[16px] font-semibold text-foreground transition-colors hover:text-primary"
    >
      ◆ StockVision
    </RouterLink>

    <!-- Navigasi desktop -->
    <nav
      class="hidden flex-1 md:flex"
      aria-label="Navigasi utama"
    >
      <RouterLink
        v-for="tab in visibleTabs"
        :key="tab.to"
        :to="tab.to"
        class="flex h-[52px] shrink-0 items-center gap-2 whitespace-nowrap border-b-2 border-transparent px-4 text-[15px] text-muted-foreground transition-colors duration-150 hover:text-foreground"
        active-class="!border-primary !text-primary"
      >
        <component
          :is="tab.icon"
          class="size-4"
          aria-hidden="true"
        />

        {{ tab.label }}
      </RouterLink>
    </nav>

    <!-- Bagian kanan header -->
    <div class="ml-auto flex shrink-0 items-center gap-2">
      <!-- Menu akun hanya muncul jika ada user login -->
      <AccountMenu
        v-if="auth.user"
        class="hidden sm:block"
      />

      <span
        v-if="auth.user"
        class="hidden text-border sm:inline"
        aria-hidden="true"
      >
        │
      </span>

      <!-- Indikator mode developer -->
      <span
        v-if="isDeveloperMode && !auth.user"
        class="hidden rounded-md border border-border bg-muted/40 px-2 py-1 text-[11px] font-medium text-muted-foreground sm:inline"
      >
        Developer
      </span>

      <!-- Tombol dark/light mode -->
      <Button
        variant="ghost"
        size="sm"
        :aria-label="
          isDark
            ? 'Aktifkan mode terang'
            : 'Aktifkan mode gelap'
        "
        @click="toggle"
      >
        <Sun
          v-if="isDark"
          class="size-4"
        />

        <Moon
          v-else
          class="size-4"
        />
      </Button>

      <!-- Tombol keluar hanya muncul jika user login -->
      <Button
        v-if="auth.user"
        variant="ghost"
        size="sm"
        class="hidden md:inline-flex"
        @click="keluar"
      >
        <LogOut class="size-4" />
        Keluar
      </Button>

      <!-- Tombol menu mobile -->
      <Button
        variant="ghost"
        size="sm"
        class="md:hidden"
        aria-label="Buka menu navigasi"
        @click="menuTerbuka = true"
      >
        <Menu class="size-4" />
      </Button>
    </div>

    <!-- Navigasi mobile -->
    <Sheet v-model:open="menuTerbuka">
      <SheetContent
        side="right"
        class="w-[260px]"
      >
        <SheetHeader>
          <SheetTitle>Navigasi</SheetTitle>
        </SheetHeader>

        <!-- Informasi akun -->
        <div
          v-if="auth.user"
          class="mx-3 mt-3 rounded-lg border border-border bg-muted/30 p-3"
        >
          <div class="flex items-center gap-3">
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold"
            >
              {{
                (
                  auth.user?.name ||
                  auth.user?.username ||
                  'U'
                )
                  .charAt(0)
                  .toUpperCase()
              }}
            </span>

            <div class="min-w-0">
              <p class="truncate text-[13px] font-semibold">
                {{
                  auth.user?.name ||
                  auth.user?.username ||
                  'User'
                }}
              </p>

              <p class="truncate text-[11px] text-muted-foreground">
                {{ auth.user?.email || 'Email belum tersedia' }}
              </p>

              <p class="text-[11px] text-muted-foreground">
                Access:
                {{ auth.user?.accessRole || 'user' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Informasi developer tanpa login -->
        <div
          v-else-if="isDeveloperMode"
          class="mx-3 mt-3 rounded-lg border border-border bg-muted/30 p-3"
        >
          <p class="text-[13px] font-semibold">
            Developer Mode
          </p>

          <p class="mt-1 text-[11px] text-muted-foreground">
            Akses lokal tanpa login sedang aktif.
          </p>
        </div>

        <nav
          class="flex flex-col gap-0.5 p-3"
          aria-label="Navigasi utama mobile"
        >
          <RouterLink
            v-for="tab in visibleTabs"
            :key="tab.to"
            :to="tab.to"
            class="flex items-center gap-2.5 rounded-md px-2.5 py-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            active-class="bg-accent !text-foreground font-medium"
            @click="menuTerbuka = false"
          >
            <component
              :is="tab.icon"
              class="size-4"
              aria-hidden="true"
            />

            {{ tab.label }}
          </RouterLink>

          <Button
            v-if="auth.user"
            variant="ghost"
            size="sm"
            class="mt-2 justify-start"
            @click="keluar"
          >
            <LogOut class="size-4" />
            Keluar
          </Button>
        </nav>
      </SheetContent>
    </Sheet>

    <LogoutConfirmDialog
      v-model:open="showLogoutDialog"
      @confirm="performLogout"
    />
    </div>
  </header>
</template>