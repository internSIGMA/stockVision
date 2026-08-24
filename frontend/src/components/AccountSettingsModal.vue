<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  reactive,
  ref,
  watch,
} from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const authStore = useAuthStore()
const { user, isAdmin } = storeToRefs(authStore)

const modalBody = ref(null)
const saving = ref(false)

const form = reactive({
  name: '',
  username: '',
  email: '',
  phone: '',
  defaultTicker: '',
  avatar: '',
  emailNotification: true,
})

const initials = computed(() => {
  const name =
    form.name ||
    form.username ||
    'User'

  return name
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0))
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

function fillForm() {
  form.name =
    user.value?.name ?? 'User'

  form.username =
    user.value?.username ?? 'user'

  form.email =
    user.value?.email ?? ''

  form.phone =
    user.value?.phone ?? ''

  form.defaultTicker =
    user.value?.defaultTicker ?? 'BJBR'

  form.avatar =
    user.value?.avatar ?? ''

  form.emailNotification =
    user.value?.emailNotification ?? true
}

function closeModal() {
  if (saving.value) return

  emit('close')
}

/*
 * Menangkap scroll mouse dan touchpad pada seluruh modal,
 * lalu mengarahkannya ke bagian isi modal.
 */
function handleModalWheel(event) {
  const element = modalBody.value

  if (!element) return

  /*
   * Abaikan gerakan horizontal touchpad.
   */
  if (
    Math.abs(event.deltaX) >
    Math.abs(event.deltaY)
  ) {
    return
  }

  const canScroll =
    element.scrollHeight >
    element.clientHeight

  if (!canScroll) return

  event.preventDefault()
  event.stopPropagation()

  element.scrollTop += event.deltaY
}

function handleAvatar(event) {
  const file = event.target.files?.[0]

  if (!file) return

  if (!file.type.startsWith('image/')) {
    alert('File harus berupa gambar.')
    event.target.value = ''
    return
  }

  if (file.size > 2 * 1024 * 1024) {
    alert('Ukuran foto maksimal 2 MB.')
    event.target.value = ''
    return
  }

  const reader = new FileReader()

  reader.onload = () => {
    form.avatar = reader.result
  }

  reader.onerror = () => {
    alert('Foto gagal dibaca.')
  }

  reader.readAsDataURL(file)
}

async function saveProfile() {
  if (!form.name.trim()) {
    alert('Nama tidak boleh kosong.')
    return
  }

  if (!form.username.trim()) {
    alert('Username tidak boleh kosong.')
    return
  }

  if (!form.email.trim()) {
    alert('Email tidak boleh kosong.')
    return
  }



  saving.value = true

  try {
    await authStore.updateProfile({
      name: form.name.trim(),

      username:
        form.username.trim(),

      email:
        form.email.trim(),

      phone:
        form.phone.trim(),

      defaultTicker:
        form.defaultTicker
          .trim()
          .toUpperCase(),

      avatar:
        form.avatar,

      emailNotification:
        form.emailNotification,
    })

    emit('close')
  } catch (error) {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error?.message ||
      'Gagal menyimpan perubahan akun.'

    alert(message)
  } finally {
    saving.value = false
  }
}

/*
 * Menyimpan pengaturan overflow halaman sebelum modal dibuka.
 */
let previousBodyOverflow = ''
let previousHtmlOverflow = ''

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      fillForm()

      previousBodyOverflow =
        document.body.style.overflow

      previousHtmlOverflow =
        document.documentElement.style.overflow

      /*
       * Mencegah dashboard di belakang ikut bergerak.
       */
      document.body.style.overflow = 'hidden'
      document.documentElement.style.overflow = 'hidden'

      await nextTick()

      if (modalBody.value) {
        modalBody.value.scrollTop = 0

        /*
         * Membuat area modal menerima scroll keyboard.
         */
        modalBody.value.focus({
          preventScroll: true,
        })
      }
    } else {
      document.body.style.overflow =
        previousBodyOverflow

      document.documentElement.style.overflow =
        previousHtmlOverflow
    }
  },
  {
    immediate: true,
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow =
    previousBodyOverflow

  document.documentElement.style.overflow =
    previousHtmlOverflow
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="modal-overlay"
      data-lenis-prevent
      data-lenis-prevent-wheel
      data-lenis-prevent-touch
      @click.self="closeModal"
    >
      <section
        class="settings-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-settings-title"
        data-lenis-prevent
        data-lenis-prevent-wheel
        data-lenis-prevent-touch
        @wheel.capture="handleModalWheel"
      >
        <!-- Header tetap berada di atas -->
        <header class="modal-header">
          <div>
            <h2 id="account-settings-title">
              Kelola Akun
            </h2>

            <p>
              Perbarui informasi akun dan preferensi
              pengguna.
            </p>
          </div>

          <button
            type="button"
            class="close-button"
            aria-label="Tutup"
            :disabled="saving"
            @click="closeModal"
          >
            ×
          </button>
        </header>

        <!-- Bagian ini yang dapat di-scroll -->
        <main
          ref="modalBody"
          class="modal-body"
          tabindex="0"
          data-lenis-prevent
          data-lenis-prevent-wheel
          data-lenis-prevent-touch
        >
          <section class="avatar-section">
            <div class="avatar-preview">
              <img
                v-if="form.avatar"
                :src="form.avatar"
                alt="Foto profil"
              />

              <span v-else>
                {{ initials }}
              </span>
            </div>

            <div>
              <label class="upload-button">
                Ganti foto

                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  hidden
                  @change="handleAvatar"
                />
              </label>

              <p class="input-hint">
                JPG, PNG, atau WEBP, maksimal 2 MB.
              </p>
            </div>
          </section>

          <section class="form-grid">
            <div class="form-group">
              <label for="account-name">
                Nama lengkap
              </label>

              <input
                id="account-name"
                v-model="form.name"
                type="text"
                autocomplete="name"
                placeholder="Masukkan nama lengkap"
              />
            </div>

            <div class="form-group">
              <label for="account-username">
                Username
              </label>

              <input
                id="account-username"
                v-model="form.username"
                type="text"
                autocomplete="username"
                placeholder="Masukkan username"
              />
            </div>

            <div class="form-group">
              <label for="account-email">
                Email
              </label>

              <input
                id="account-email"
                v-model="form.email"
                type="email"
                autocomplete="email"
                placeholder="nama@email.com"
              />
            </div>

            <div class="form-group">
              <label for="account-phone">
                Nomor telepon
              </label>

              <input
                id="account-phone"
                v-model="form.phone"
                type="tel"
                autocomplete="tel"
                placeholder="08xxxxxxxxxx"
              />
            </div>


          </section>

          <!-- Memberi ruang pada bagian paling bawah -->
          <div class="modal-bottom-space"></div>
        </main>

        <!-- Footer tetap berada di bawah -->
        <footer class="modal-footer">
          <button
            type="button"
            class="cancel-button"
            :disabled="saving"
            @click="closeModal"
          >
            Batal
          </button>

          <button
            type="button"
            class="save-button"
            :disabled="saving"
            @click="saveProfile"
          >
            {{
              saving
                ? 'Menyimpan...'
                : 'Simpan perubahan'
            }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;

  display: flex;
  align-items: center;
  justify-content: center;

  padding: 16px;

  overflow: hidden;

  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(4px);

  pointer-events: auto;
  overscroll-behavior: none;
}

/*
 * Tinggi modal dibuat pasti agar bagian tengah
 * mempunyai area scroll yang jelas.
 */
.settings-modal {
  width: min(680px, calc(100vw - 32px));

  height: calc(100vh - 32px);
  height: calc(100dvh - 32px);

  max-height: 760px;

  display: grid;

  grid-template-rows:
    auto
    minmax(0, 1fr)
    auto;

  overflow: hidden;

  color: var(--foreground);
  background: var(--card);

  border: 1px solid var(--border);
  border-radius: 18px;

  box-shadow:
    0 24px 70px rgba(15, 23, 42, 0.24);

  pointer-events: auto;
  overscroll-behavior: none;
}

/* HEADER */

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;

  gap: 20px;

  padding: 24px 28px;

  border-bottom: 1px solid var(--border);
  background: var(--card);
}

.modal-header h2 {
  margin: 0;

  font-size: 22px;
  font-weight: 700;
}

.modal-header p {
  margin: 6px 0 0;

  color: var(--muted-foreground);
  font-size: 14px;
}

.close-button {
  width: 36px;
  height: 36px;
  flex-shrink: 0;

  display: grid;
  place-items: center;

  padding: 0;

  border: none;
  border-radius: 10px;

  color: var(--foreground);
  background: var(--card-hover);

  font-size: 24px;
  line-height: 1;

  cursor: pointer;
}

.close-button:hover {
  background: var(--border);
}

.close-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* AREA SCROLL */

.modal-body {
  width: 100%;
  min-width: 0;
  min-height: 0;

  box-sizing: border-box;

  padding: 28px;

  /*
   * scroll, bukan auto, agar area scroll selalu
   * dikenali browser dan touchpad.
   */
  overflow-x: hidden;
  overflow-y: scroll;

  overscroll-behavior: contain;
  touch-action: pan-y;

  pointer-events: auto;

  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: var(--disabled) transparent;

  -webkit-overflow-scrolling: touch;
}

.modal-body:focus {
  outline: none;
}

.modal-body::-webkit-scrollbar {
  width: 10px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  border: 3px solid transparent;
  border-radius: 999px;

  background: var(--disabled);
  background-clip: padding-box;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: var(--muted-foreground);
  background-clip: padding-box;
}

/* AVATAR */

.avatar-section {
  display: flex;
  align-items: center;

  gap: 18px;

  margin-bottom: 28px;
}

.avatar-preview {
  width: 76px;
  height: 76px;
  flex-shrink: 0;

  display: grid;
  place-items: center;

  overflow: hidden;

  border-radius: 50%;

  background: var(--card-hover);

  font-size: 24px;
  font-weight: 700;
}

.avatar-preview img {
  width: 100%;
  height: 100%;

  object-fit: cover;
}

.upload-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  padding: 9px 14px;

  border: 1px solid var(--border);
  border-radius: 9px;

  background: var(--card);

  font-size: 14px;
  font-weight: 600;

  cursor: pointer;
}

.upload-button:hover {
  background: var(--card-hover);
}

/* FORM */

.form-grid {
  display: grid;

  grid-template-columns:
    repeat(2, minmax(0, 1fr));

  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;

  gap: 8px;

  min-width: 0;
}

.form-group-full {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
}

.form-group input {
  width: 100%;

  box-sizing: border-box;

  padding: 11px 13px;

  border: 1px solid var(--border);
  border-radius: 9px;

  outline: none;

  color: var(--foreground);
  background: var(--card);

  font-size: 14px;
}

.form-group input:focus {
  border-color: var(--ring);

  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent);
}

.input-hint {
  margin: 7px 0 0;

  color: var(--disabled);
  font-size: 12px;
}

/* PREFERENSI DAN PASSWORD */

.preference-section,
.password-section {
  display: flex;
  align-items: center;
  justify-content: space-between;

  gap: 20px;

  margin-top: 26px;
  padding: 17px;

  border: 1px solid var(--border);
  border-radius: 12px;
}

.preference-section p,
.password-section p {
  margin: 5px 0 0;

  color: var(--muted-foreground);
  font-size: 13px;
}

/* SWITCH */

.switch {
  position: relative;

  width: 46px;
  height: 25px;

  flex-shrink: 0;
}

.switch input {
  position: absolute;

  width: 1px;
  height: 1px;

  opacity: 0;
}

.slider {
  position: absolute;
  inset: 0;

  border-radius: 999px;

  background: var(--disabled);

  cursor: pointer;

  transition: 0.2s;
}

.slider::before {
  content: "";

  position: absolute;

  top: 3px;
  left: 3px;

  width: 19px;
  height: 19px;

  border-radius: 50%;

  background: var(--card);

  transition: 0.2s;
}

.switch input:checked + .slider {
  background: var(--primary);
}

.switch input:checked + .slider::before {
  transform: translateX(21px);
}

.switch input:focus-visible + .slider {
  outline: 3px solid color-mix(in srgb, var(--ring) 30%, transparent);
  outline-offset: 2px;
}

/* FOOTER */

.modal-footer {
  display: flex;
  justify-content: flex-end;

  gap: 12px;

  padding: 20px 28px;

  border-top: 1px solid var(--border);
  background: var(--card);
}

.cancel-button,
.save-button,
.secondary-button {
  padding: 10px 17px;

  border-radius: 9px;

  font-weight: 600;

  cursor: pointer;
}

.cancel-button,
.secondary-button {
  border: 1px solid var(--border);

  color: var(--foreground);
  background: var(--card);
}

.cancel-button:hover {
  background: var(--card-hover);
}

.save-button {
  border: 1px solid var(--primary);

  color: var(--primary-foreground);
  background: var(--primary);
}

.save-button:hover {
  background: var(--primary-hover);
}

.cancel-button:disabled,
.save-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.secondary-button:disabled {
  color: var(--disabled);
  cursor: not-allowed;
}

.modal-bottom-space {
  height: 12px;
}

/* MOBILE */

@media (max-width: 640px) {
  .modal-overlay {
    align-items: flex-end;

    padding: 0;
  }

  .settings-modal {
    width: 100%;

    height: 92vh;
    height: 92dvh;

    max-height: 92vh;
    max-height: 92dvh;

    border-radius: 18px 18px 0 0;
  }

  .modal-header {
    padding: 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .modal-footer {
    padding: 16px 20px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-group-full {
    grid-column: auto;
  }

  .preference-section {
    align-items: center;
  }

  .password-section {
    align-items: flex-start;
    flex-direction: column;
  }

  .secondary-button {
    width: 100%;
  }
}
</style>