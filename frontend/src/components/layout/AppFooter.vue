<script setup>
import { 
  Mail, 
  Phone, 
  MapPin, 
  Activity 
} from '@lucide/vue'
</script>

<template>
  <footer class="mt-auto w-full border-t-[0.5px] border-border bg-card">
    <!-- Main Footer Content -->
    <div class="mx-auto w-full max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-4">
        
        <!-- Brand & Description -->
        <div class="flex flex-col gap-4">
          <div class="flex items-center gap-2">
            <Activity class="size-6 text-[var(--primary)]" />
            <span class="text-xl font-bold tracking-tight text-foreground">StockVision</span>
          </div>
          <p class="text-sm leading-relaxed text-muted-foreground">
            Platform analisis saham cerdas dengan rekomendasi preskriptif berbasis AI untuk membantu setiap keputusan investasi Anda.
          </p>
          <div class="mt-2 flex items-center gap-4">
            <a href="#" aria-label="Facebook" class="text-muted-foreground transition-colors hover:text-[var(--primary)]">
              <svg class="size-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.879V14.89h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.989C18.343 21.129 22 16.99 22 12c0-5.523-4.477-10-10-10z"/></svg>
            </a>
            <a href="#" aria-label="Twitter" class="text-muted-foreground transition-colors hover:text-[var(--primary)]">
              <svg class="size-5" fill="currentColor" viewBox="0 0 24 24"><path d="M22.46 6c-.77.35-1.6.58-2.46.69.88-.53 1.56-1.37 1.88-2.38-.83.5-1.75.85-2.72 1.05C18.37 4.5 17.26 4 16 4c-2.35 0-4.27 1.92-4.27 4.29 0 .34.04.67.11.98C8.28 9.09 5.11 7.38 3 4.79c-.37.63-.58 1.37-.58 2.15 0 1.49.75 2.81 1.91 3.56-.71 0-1.37-.2-1.95-.5v.05c0 2.08 1.48 3.82 3.44 4.21a4.22 4.22 0 0 1-1.93.07 4.28 4.28 0 0 0 4 2.98 8.521 8.521 0 0 1-5.33 1.84c-.34 0-.68-.02-1.02-.06C3.44 20.29 5.7 21 8.12 21 16 21 20.33 14.46 20.33 8.79c0-.19 0-.37-.01-.56.84-.6 1.56-1.36 2.14-2.23z"/></svg>
            </a>
            <a href="#" aria-label="Instagram" class="text-muted-foreground transition-colors hover:text-[var(--primary)]">
              <svg class="size-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg>
            </a>
            <a href="#" aria-label="LinkedIn" class="text-muted-foreground transition-colors hover:text-[var(--primary)]">
              <svg class="size-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
          </div>
        </div>

        <!-- Perusahaan -->
        <div class="flex flex-col gap-4">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-foreground">Perusahaan</h3>
          <ul class="flex flex-col gap-3">
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Tentang Kami</a></li>
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Karir</a></li>
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Blog & Berita</a></li>
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Pusat Bantuan</a></li>
          </ul>
        </div>

        <!-- Layanan -->
        <div class="flex flex-col gap-4">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-foreground">Layanan</h3>
          <ul class="flex flex-col gap-3">
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Analisis Prediktif</a></li>
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Data Historis</a></li>
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Sinyal Trading AI</a></li>
            <li><a href="#" class="text-sm text-muted-foreground transition-colors hover:text-[var(--primary)]">Integrasi API</a></li>
          </ul>
        </div>

        <!-- Kontak -->
        <div class="flex flex-col gap-4">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-foreground">Hubungi Kami</h3>
          <div class="flex flex-col gap-3">
            <div class="flex items-start gap-3 text-sm text-muted-foreground">
              <MapPin class="mt-0.5 size-4 shrink-0 text-[var(--primary)]" />
              <span class="leading-relaxed">
                Graha Teknologi Jl. Sudirman No. 123<br />
                Bandung, 12190
              </span>
            </div>
            <div class="flex items-center gap-3 text-sm text-muted-foreground">
              <Phone class="size-4 shrink-0 text-[var(--primary)]" />
              <a href="tel:+6281122334455" class="transition-colors hover:text-[var(--primary)]">+62 811 2233 4455</a>
            </div>
            <div class="flex items-center gap-3 text-sm text-muted-foreground">
              <Mail class="size-4 shrink-0 text-[var(--primary)]" />
              <a href="mailto:support@stockvision.id" class="transition-colors hover:text-[var(--primary)]">support@stockvision.id</a>
            </div>
          </div>
        </div>
        
      </div>
    </div>

    <!-- Copyright Bar -->
    <div class="border-t-[0.5px] border-border bg-muted/40">
      <div class="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-4 px-4 py-6 sm:flex-row sm:px-6 lg:px-8 text-xs text-muted-foreground">
        <div>
          &copy; {{ new Date().getFullYear() }} StockVision. Hak Cipta Dilindungi.
        </div>
        <div class="flex items-center gap-6">
          <a href="#" class="transition-colors hover:text-foreground">Kebijakan Privasi</a>
          <a href="#" class="transition-colors hover:text-foreground">Syarat & Ketentuan</a>
        </div>
      </div>
    </div>
  </footer>
</template>
