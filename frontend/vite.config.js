import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    open: false,
    allowedHosts: true,
    // Bind mount Docker di Windows tidak meneruskan event file-watcher,
    // jadi HMR tidak pernah jalan dan browser terus memakai kode lama.
    // Polling memaksa Vite mengecek perubahan sendiri.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
