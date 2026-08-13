<script setup>
import {
  computed,
  onMounted,
  onUnmounted,
  reactive,
  ref,
} from 'vue'

import { useAuthStore } from '@/stores/auth'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

import {
  createAdminUser,
  getAdminUsers,
  getUserActivity,
  updateAdminUser,
} from '@/api/admin'


// Sejalan dengan Auto Scheduler yang juga menyegarkan tiap 5 detik.
const REFRESH_MS = 5000

const auth = useAuthStore()

const activeTab = ref('users')

const loading = ref(false)
const error = ref('')

const users = ref([])
const activities = ref([])


// Header X-Access-Role untuk API admin. Pakai auth.isAdmin,
// sumber yang sama dengan penjaga rute adminOnly, supaya yang
// lolos ke halaman ini pasti lolos juga di backend.
// (auth.user memakai camelCase accessRole, bukan access_role.)
const accessRole = computed(() => {
  return auth.isAdmin ? 'admin' : 'user'
})


// ========================================
// USER FORM
// ========================================

const showUserModal = ref(false)
const editingUser = ref(null)

const userForm = reactive({
  name: '',
  username: '',
  email: '',
  password: '',
  access_role: 'user',
  is_active: true,
})


function resetUserForm() {
  editingUser.value = null

  userForm.name = ''
  userForm.username = ''
  userForm.email = ''
  userForm.password = ''
  userForm.access_role = 'user'
  userForm.is_active = true
}


function openAddUser() {
  resetUserForm()
  showUserModal.value = true
}


function openEditUser(user) {
  editingUser.value = user

  userForm.name = user.name || ''
  userForm.username = user.username || ''
  userForm.email = user.email || ''
  userForm.password = ''
  userForm.access_role =
    user.access_role || 'user'

  userForm.is_active =
    user.is_active !== false

  showUserModal.value = true
}


async function saveUser() {
  if (!userForm.email.trim()) {
    alert('Email wajib diisi.')
    return
  }

  if (!userForm.username.trim()) {
    alert('Username wajib diisi.')
    return
  }

  if (
    !editingUser.value &&
    userForm.password.length < 6
  ) {
    alert(
      'Password minimal 6 karakter.'
    )
    return
  }

  try {
    const payload = {
      name: userForm.name.trim(),
      username:
        userForm.username.trim(),

      email:
        userForm.email
          .trim()
          .toLowerCase(),

      access_role:
        userForm.access_role,

      is_active:
        userForm.is_active,
    }

    if (userForm.password) {
      payload.password =
        userForm.password
    }

    if (editingUser.value) {
      await updateAdminUser(
        editingUser.value.id,
        payload,
        accessRole.value
      )
    } else {
      await createAdminUser(
        payload,
        accessRole.value
      )
    }

    showUserModal.value = false

    await loadUsers()

  } catch (err) {
    alert(
      err.message ||
      'Gagal menyimpan user.'
    )
  }
}


async function toggleUser(user) {
  try {
    await updateAdminUser(
      user.id,
      {
        is_active: !user.is_active,
      },
      accessRole.value
    )

    await loadUsers()

  } catch (err) {
    alert(
      err.message ||
      'Gagal mengubah status user.'
    )
  }
}


// ========================================
// ROLE MANAGEMENT
// ========================================

// Admin tidak boleh menurunkan akunnya sendiri, karena
// setelah tersimpan dia langsung kehilangan akses halaman ini.
function akunSendiri(user) {
  return (
    auth.user?.id === user.id ||
    auth.user?.email === user.email
  )
}


async function changeAccessRole(user, value) {
  if (value === user.access_role) return

  const confirmed = confirm(
    `Ubah access role ${user.email} ` +
    `dari "${user.access_role || 'user'}" ` +
    `menjadi "${value}"?`
  )

  if (!confirmed) {
    // Kembalikan select ke nilai semula.
    await loadUsers()
    return
  }

  try {
    await updateAdminUser(
      user.id,
      { access_role: value },
      accessRole.value
    )

  } catch (err) {
    alert(
      err.message ||
      'Access role gagal diubah.'
    )
  }

  await loadUsers()
}


// ========================================
// LOAD DATA
// ========================================

// Interceptor di api/index.js sudah mengembalikan response.data,
// jadi fungsi API di sini langsung memberi array-nya.
async function loadUsers() {
  users.value =
    await getAdminUsers(
      accessRole.value
    ) || []
}


async function loadActivities() {
  activities.value =
    await getUserActivity(
      accessRole.value
    ) || []
}


/**
 * @param {boolean} diamDiam penyegaran berkala: jangan tampilkan skeleton
 *   "Memuat data...", kalau tidak tabel akan berkedip tiap 5 detik.
 */
async function loadAll({ diamDiam = false } = {}) {
  if (!diamDiam) loading.value = true

  try {
    await Promise.all([
      loadUsers(),
      loadActivities(),
    ])

    error.value = ''

  } catch (err) {
    console.error(err)

    error.value =
      err.message ||
      'Data admin gagal dimuat.'

  } finally {
    loading.value = false
  }
}


// ========================================
// REAL-TIME
// ========================================

/*
 * Ketiga tab (User Management, Role Management, User Activity) memakai
 * `users` dan `activities` yang sama, jadi satu polling menghidupkan
 * ketiganya. Tanpa indikator apa pun di layar — datanya saja yang berjalan.
 *
 * Aktivitas login dicatat backend saat /users/login berhasil, jadi begitu
 * ada yang masuk, barisnya muncul sendiri di tab User Activity.
 *
 * Polling dijeda saat modal terbuka supaya daftar tidak berubah di bawah
 * admin yang sedang mengisi form, dan saat tab browser tidak terlihat
 * supaya tidak memanggil API terus-menerus di latar belakang.
 */
const bolehSegar = ref(!document.hidden)

function pantauVisibilitas() {
  bolehSegar.value = !document.hidden
}

const autoAktif = computed(
  () => bolehSegar.value && !showUserModal.value
)

useAutoRefresh(
  () => loadAll({ diamDiam: true }),
  REFRESH_MS,
  autoAktif
)


function formatDate(value) {
  if (!value) return '-'

  return new Date(
    value
  ).toLocaleString('id-ID')
}


onMounted(() => {
  document.addEventListener(
    'visibilitychange',
    pantauVisibilitas
  )

  loadAll()
})

onUnmounted(() => {
  document.removeEventListener(
    'visibilitychange',
    pantauVisibilitas
  )
})
</script>


<template>
  <main class="admin-page">

    <!-- HEADER -->

    <div class="page-header">

      <div>
        <h1>Admin Management</h1>

        <p>
          Kelola pengguna, role,
          dan aktivitas user.
        </p>
      </div>

      <button
        v-if="activeTab === 'users'"
        class="btn primary"
        @click="openAddUser"
      >
        + Tambah User
      </button>

    </div>


    <!-- TABS -->

    <nav class="tabs">

      <button
        :class="{
          active:
            activeTab === 'users'
        }"
        @click="activeTab = 'users'"
      >
        User Management
      </button>

      <button
        :class="{
          active:
            activeTab === 'roles'
        }"
        @click="activeTab = 'roles'"
      >
        Role Management
      </button>

      <button
        :class="{
          active:
            activeTab === 'activity'
        }"
        @click="activeTab = 'activity'"
      >
        User Activity
      </button>

    </nav>


    <div
      v-if="error"
      class="error-message"
    >
      {{ error }}
    </div>


    <div
      v-if="loading"
      class="card loading"
    >
      Memuat data...
    </div>


    <!-- USER MANAGEMENT -->

    <section
      v-else-if="
        activeTab === 'users'
      "
      class="card"
    >

      <div class="table-wrapper">

        <table>

          <thead>
            <tr>
              <th>Nama</th>
              <th>Email</th>
              <th>Username</th>
              <th>Access</th>
              <th>Status</th>
              <th>Aksi</th>
            </tr>
          </thead>

          <tbody>

            <tr
              v-for="user in users"
              :key="user.id"
            >

              <td>
                {{ user.name || '-' }}
              </td>

              <td>
                {{ user.email }}
              </td>

              <td>
                {{ user.username }}
              </td>

              <td>
                <span
                  class="badge"
                  :class="user.access_role"
                >
                  {{
                    user.access_role
                    || 'user'
                  }}
                </span>
              </td>

              <td>
                <span
                  class="status"
                  :class="{
                    inactive:
                      !user.is_active
                  }"
                >
                  {{
                    user.is_active
                      ? 'Aktif'
                      : 'Nonaktif'
                  }}
                </span>
              </td>

              <td class="actions">

                <button
                  class="btn small"
                  @click="
                    openEditUser(user)
                  "
                >
                  Edit
                </button>

                <button
                  class="btn small danger"
                  @click="
                    toggleUser(user)
                  "
                >
                  {{
                    user.is_active
                      ? 'Nonaktifkan'
                      : 'Aktifkan'
                  }}
                </button>

              </td>

            </tr>

          </tbody>

        </table>

      </div>

    </section>


    <!-- ROLE MANAGEMENT -->

    <section
      v-else-if="
        activeTab === 'roles'
      "
      class="card"
    >

      <div class="section-heading">

        <h2>
          Access Role
        </h2>

        <p>
          Atur hak akses tiap akun
          yang terdaftar. Admin dapat
          membuka seluruh menu,
          user hanya menu biasa.
        </p>

      </div>


      <div class="table-wrapper">

        <table>

          <thead>
            <tr>
              <th>Nama</th>
              <th>Email</th>
              <th>Username</th>
              <th>Status</th>
              <th>Access Role</th>
            </tr>
          </thead>

          <tbody>

            <tr
              v-for="user in users"
              :key="user.id"
            >

              <td>
                {{ user.name || '-' }}
              </td>

              <td>
                {{ user.email }}
              </td>

              <td>
                {{ user.username }}
              </td>

              <td>
                <span
                  class="status"
                  :class="{
                    inactive:
                      !user.is_active
                  }"
                >
                  {{
                    user.is_active
                      ? 'Aktif'
                      : 'Nonaktif'
                  }}
                </span>
              </td>

              <td>

                <select
                  :value="
                    user.access_role
                    || 'user'
                  "
                  :disabled="
                    akunSendiri(user)
                  "
                  :title="
                    akunSendiri(user)
                      ? 'Tidak bisa mengubah '
                        + 'access role akun sendiri'
                      : ''
                  "
                  @change="
                    changeAccessRole(
                      user,
                      $event.target.value
                    )
                  "
                >
                  <option value="user">
                    User
                  </option>

                  <option value="admin">
                    Admin
                  </option>
                </select>

              </td>

            </tr>

            <tr v-if="!users.length">
              <td
                colspan="5"
                class="empty-row"
              >
                Belum ada akun terdaftar.
              </td>
            </tr>

          </tbody>

        </table>

      </div>

    </section>


    <!-- USER ACTIVITY -->

    <section
      v-else-if="
        activeTab === 'activity'
      "
      class="card"
    >

      <div class="section-heading">

        <h2>
          User Activity
        </h2>

        <button
          class="btn small"
          @click="loadActivities"
        >
          Refresh
        </button>

      </div>


      <div class="table-wrapper">

        <table>

          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Activity</th>
              <th>Description</th>
              <th>Waktu</th>
            </tr>
          </thead>

          <tbody>

            <tr
              v-for="
                activity in activities
              "
              :key="activity.id"
            >

              <td>
                {{
                  activity.name ||
                  'Unknown'
                }}
              </td>

              <td>
                {{
                  activity.email ||
                  '-'
                }}
              </td>

              <td>
                <span class="activity">
                  {{ activity.activity }}
                </span>
              </td>

              <td>
                {{
                  activity.description
                  || '-'
                }}
              </td>

              <td>
                {{
                  formatDate(
                    activity.created_at
                  )
                }}
              </td>

            </tr>

          </tbody>

        </table>

      </div>

    </section>


    <!-- USER MODAL -->

    <div
      v-if="showUserModal"
      class="overlay"
      @click.self="
        showUserModal = false
      "
    >

      <div class="modal">

        <h2>
          {{
            editingUser
              ? 'Edit User'
              : 'Tambah User'
          }}
        </h2>

        <label>Nama</label>

        <input
          v-model="userForm.name"
          placeholder="Nama lengkap"
        />


        <label>Username</label>

        <input
          v-model="
            userForm.username
          "
          placeholder="username"
        />


        <label>Email</label>

        <input
          v-model="userForm.email"
          type="email"
          placeholder="user@email.com"
        />


        <label>
          {{
            editingUser
              ? 'Password Baru (opsional)'
              : 'Password'
          }}
        </label>

        <input
          v-model="
            userForm.password
          "
          type="password"
          placeholder="Minimal 6 karakter"
        />


        <label>
          Access Role
        </label>

        <select
          v-model="
            userForm.access_role
          "
        >
          <option value="user">
            User
          </option>

          <option value="admin">
            Admin
          </option>
        </select>


        <label
          v-if="editingUser"
          class="checkbox-row"
        >
          <input
            v-model="
              userForm.is_active
            "
            type="checkbox"
          />

          Akun aktif
        </label>


        <div class="modal-actions">

          <button
            class="btn"
            @click="
              showUserModal = false
            "
          >
            Batal
          </button>

          <button
            class="btn primary"
            @click="saveUser"
          >
            Simpan
          </button>

        </div>

      </div>

    </div>


  </main>
</template>


<style scoped>
.admin-page {
  padding: 28px;
  min-height: 100vh;
  background: var(--background);
  color: var(--foreground);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 26px;
}

.page-header p {
  margin-top: 6px;
  color: var(--muted-foreground);
}

.tabs {
  display: flex;
  gap: 26px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}

.tabs button {
  border: none;
  background: none;
  padding: 13px 2px;
  cursor: pointer;
  color: var(--muted-foreground);
}

.tabs button.active {
  color: var(--foreground);
  border-bottom:
    2px solid var(--primary);
}

.card {
  background: var(--card);
  border:
    1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}

.loading {
  padding: 30px;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 14px 16px;
  text-align: left;
  border-bottom:
    1px solid var(--border);
}

th {
  font-size: 12px;
  color: var(--muted-foreground);
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 6px;
}

.btn {
  border:
    1px solid var(--border);
  background: var(--background);
  color: var(--foreground);
  border-radius: 7px;
  padding: 9px 14px;
  cursor: pointer;
}

.btn.primary {
  color:
    var(--primary-foreground);
  background: var(--primary);
  border-color: var(--primary);
}

.btn.small {
  padding: 6px 10px;
  font-size: 12px;
}

.btn.danger {
  color: #dc2626;
}

.badge {
  display: inline-block;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 12px;
  background: var(--muted);
}

.badge.admin {
  font-weight: 600;
}

.status {
  color: #16a34a;
}

.status.inactive {
  color: #dc2626;
}

.empty-row {
  text-align: center;
  padding: 24px;
  color: var(--muted-foreground);
}

.section-heading {
  padding: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-heading h2 {
  margin: 0;
  font-size: 16px;
}

.section-heading p {
  color: var(--muted-foreground);
}

.activity {
  font-size: 12px;
  font-weight: 600;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background:
    rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  width: min(
    460px,
    calc(100vw - 32px)
  );
  max-height: 90vh;
  overflow-y: auto;
  padding: 24px;
  background: var(--card);
  border:
    1px solid var(--border);
  border-radius: 14px;
}

.modal h2 {
  margin-top: 0;
}

.modal label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin:
    15px 0 6px;
}

.modal input,
.modal select,
.modal textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 11px;
  border:
    1px solid var(--border);
  border-radius: 7px;
  background: var(--background);
  color: var(--foreground);
}

.checkbox-row {
  display: flex !important;
  align-items: center;
  gap: 8px;
}

.checkbox-row input {
  width: auto;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
}

.error-message {
  margin-bottom: 16px;
  padding: 12px;
  background: #fee2e2;
  color: #b91c1c;
  border-radius: 8px;
}

@media (
  max-width: 768px
) {
  .admin-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
  }

  .tabs {
    overflow-x: auto;
  }

  .tabs button {
    white-space: nowrap;
  }
}
</style>