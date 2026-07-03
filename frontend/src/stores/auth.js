import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginRequest } from '@/services/authService'

const STORAGE_KEY = 'fullmoon.auth'

function loadPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const persisted = loadPersisted()

  const user = ref(persisted?.user ?? null)
  const token = ref(persisted?.token ?? null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials, remember = true) {
    loading.value = true
    try {
      const { token: t, user: u } = await loginRequest(credentials)
      token.value = t
      user.value = u
      if (remember) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: t, user: u }))
      }
      return u
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return { user, token, loading, isAuthenticated, login, logout }
})
