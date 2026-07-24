<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Clock, ListChecks, LogOut, Menu, Moon, Sun, TrendingUp } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import UserMenu from '@/components/layout/UserMenu.vue'

const auth = useAuthStore()
const router = useRouter()
const { isDark, toggle } = useTheme()

const TABS = [
  { label: 'Stream', to: '/stream', icon: TrendingUp },
  { label: 'Crawl Logs', to: '/crawl-logs', icon: ListChecks },
  { label: 'Auto Scheduler', to: '/auto-scheduler', icon: Clock },
]

const menuTerbuka = ref(false)

function keluar() {
  menuTerbuka.value = false
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="flex h-[68px] items-center gap-5 border-b-[0.5px] border-border bg-card px-6">
    <RouterLink to="/stream" class="shrink-0 text-[16px] font-semibold">◆ StockVision</RouterLink>

    <!-- Tiga tab muat di layar lebar; di mobile diganti hamburger. -->
    <nav class="hidden flex-1 md:flex" aria-label="Navigasi utama">
      <RouterLink
        v-for="tab in TABS"
        :key="tab.to"
        :to="tab.to"
        class="flex h-[68px] shrink-0 items-center gap-2 whitespace-nowrap border-b-2 border-transparent px-4 text-[14px] text-muted-foreground transition-colors duration-150 hover:text-foreground"
        active-class="!border-foreground text-foreground"
      >
        <component :is="tab.icon" class="size-4" aria-hidden="true" />
        {{ tab.label }}
      </RouterLink>
    </nav>

    <div class="ml-auto flex shrink-0 items-center gap-2">
      <UserMenu v-if="auth.user" />

      <span class="hidden text-border sm:inline" aria-hidden="true">│</span>

      <Button
        variant="ghost"
        :aria-label="isDark ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'"
        @click="toggle"
      >
        <Sun v-if="isDark" class="size-[18px]" />
        <Moon v-else class="size-[18px]" />
      </Button>

      <Button variant="ghost" class="hidden text-[14px] md:inline-flex" @click="keluar">
        <LogOut class="size-[18px]" />
        Keluar
      </Button>

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

    <!-- Mobile: hanya 3 item, jadi menunya pendek. -->
    <Sheet v-model:open="menuTerbuka">
      <SheetContent side="right" class="w-[260px]">
        <SheetHeader>
          <SheetTitle>Navigasi</SheetTitle>
        </SheetHeader>

        <nav class="flex flex-col gap-0.5 p-3" aria-label="Navigasi utama (mobile)">
          <RouterLink
            v-for="tab in TABS"
            :key="tab.to"
            :to="tab.to"
            class="flex items-center gap-2.5 rounded-md px-2.5 py-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            active-class="bg-accent !text-foreground font-medium"
            @click="menuTerbuka = false"
          >
            <component :is="tab.icon" class="size-4" aria-hidden="true" />
            {{ tab.label }}
          </RouterLink>

          <Button variant="ghost" size="sm" class="mt-2 justify-start" @click="keluar">
            <LogOut class="size-4" />
            Keluar
          </Button>
        </nav>
      </SheetContent>
    </Sheet>
  </header>
</template>
