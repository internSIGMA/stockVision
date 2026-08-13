<script setup>
import {
  computed,
  onMounted,
  reactive,
  ref,
} from 'vue'

import { useAuthStore } from '@/stores/auth'

import {
  createAdminUser,
  createRole,
  deleteRole,
  getAdminUsers,
  getMenuPermissions,
  getRoles,
  getUserActivity,
  updateAdminUser,
  updateMenuPermission,
  updateRole,
} from '@/api/admin'


const auth = useAuthStore()

const activeTab = ref('users')

const loading = ref(false)
const error = ref('')

const users = ref([])
const roles = ref([])
const menus = ref([])
const activities = ref([])


// Karena halaman ini adminOnly,
// fallback admin aman untuk project sekarang.
const accessRole = computed(() => {
  return (
    auth.user?.access_role ||
    (auth.isAdmin ? 'admin' : 'user')
  )
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
  role: '',
  access_role: 'user',
  is_active: true,
})


function resetUserForm() {
  editingUser.value = null

  userForm.name = ''
  userForm.username = ''
  userForm.email = ''
  userForm.password = ''
  userForm.role = ''
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
  userForm.role = user.role || ''
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

      role: userForm.role,
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
      err.response?.data?.error ||
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
      err.response?.data?.error ||
      'Gagal mengubah status user.'
    )
  }
}


// ========================================
// ROLE FORM
// ========================================

const showRoleModal = ref(false)
const editingRole = ref(null)

const roleForm = reactive({
  name: '',
  description: '',
})


function openAddRole() {
  editingRole.value = null

  roleForm.name = ''
  roleForm.description = ''

  showRoleModal.value = true
}


function openEditRole(role) {
  editingRole.value = role

  roleForm.name = role.name
  roleForm.description =
    role.description || ''

  showRoleModal.value = true
}


async function saveRole() {
  if (!roleForm.name.trim()) {
    alert('Nama role wajib diisi.')
    return
  }

  try {
    const payload = {
      name:
        roleForm.name.trim(),

      description:
        roleForm.description.trim(),
    }

    if (editingRole.value) {
      await updateRole(
        editingRole.value.id,
        payload,
        accessRole.value
      )
    } else {
      await createRole(
        payload,
        accessRole.value
      )
    }

    showRoleModal.value = false

    await Promise.all([
      loadRoles(),
      loadUsers(),
    ])

  } catch (err) {
    alert(
      err.response?.data?.error ||
      'Gagal menyimpan role.'
    )
  }
}


async function removeRole(role) {
  const confirmed = confirm(
    `Hapus role "${role.name}"?`
  )

  if (!confirmed) return

  try {
    await deleteRole(
      role.id,
      accessRole.value
    )

    await loadRoles()

  } catch (err) {
    alert(
      err.response?.data?.error ||
      'Role gagal dihapus.'
    )
  }
}


// ========================================
// MENU
// ========================================

async function changePermission(
  menu,
  role,
  value
) {
  try {
    await updateMenuPermission(
      {
        menu_key: menu.menu_key,
        access_role: role,
        enabled: value,
      },
      accessRole.value
    )

    await loadMenus()

  } catch (err) {
    alert(
      err.response?.data?.error ||
      'Permission gagal diperbarui.'
    )

    await loadMenus()
  }
}


// ========================================
// LOAD DATA
// ========================================

async function loadUsers() {
  const response =
    await getAdminUsers(
      accessRole.value
    )

  users.value = response.data
}


async function loadRoles() {
  const response =
    await getRoles(
      accessRole.value
    )

  roles.value = response.data
}


async function loadMenus() {
  const response =
    await getMenuPermissions(
      accessRole.value
    )

  menus.value = response.data
}


async function loadActivities() {
  const response =
    await getUserActivity(
      accessRole.value
    )

  activities.value =
    response.data
}


async function loadAll() {
  loading.value = true
  error.value = ''

  try {
    await Promise.all([
      loadUsers(),
      loadRoles(),
      loadMenus(),
      loadActivities(),
    ])

  } catch (err) {
    console.error(err)

    error.value =
      err.response?.data?.error ||
      'Data admin gagal dimuat.'

  } finally {
    loading.value = false
  }
}


function formatDate(value) {
  if (!value) return '-'

  return new Date(
    value
  ).toLocaleString('id-ID')
}


onMounted(loadAll)
</script>


<template>
  <main class="admin-page">

    <!-- HEADER -->

    <div class="page-header">

      <div>
        <h1>Admin Management</h1>

        <p>
          Kelola pengguna, role,
          menu dan aktivitas user.
        </p>
      </div>

      <button
        v-if="activeTab === 'users'"
        class="btn primary"
        @click="openAddUser"
      >
        + Tambah User
      </button>

      <button
        v-if="activeTab === 'roles'"
        class="btn primary"
        @click="openAddRole"
      >
        + Tambah Role
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
            activeTab === 'menus'
        }"
        @click="activeTab = 'menus'"
      >
        Menu Management
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
              <th>Role</th>
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
                {{ user.role || '-' }}
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
      class="role-grid"
    >

      <article
        v-for="role in roles"
        :key="role.id"
        class="role-card"
      >

        <h3>
          {{ role.name }}
        </h3>

        <p>
          {{
            role.description ||
            'Belum ada deskripsi.'
          }}
        </p>

        <div class="role-actions">

          <button
            class="btn small"
            @click="
              openEditRole(role)
            "
          >
            Edit
          </button>

          <button
            class="btn small danger"
            @click="
              removeRole(role)
            "
          >
            Hapus
          </button>

        </div>

      </article>

    </section>


    <!-- MENU MANAGEMENT -->

    <section
      v-else-if="
        activeTab === 'menus'
      "
      class="card"
    >

      <div class="section-heading">

        <h2>
          Menu Permission
        </h2>

        <p>
          Atur menu yang dapat
          diakses berdasarkan
          access role.
        </p>

      </div>


      <div class="table-wrapper">

        <table>

          <thead>
            <tr>
              <th>Menu</th>
              <th>Route</th>
              <th>Admin</th>
              <th>User</th>
            </tr>
          </thead>

          <tbody>

            <tr
              v-for="menu in menus"
              :key="menu.menu_key"
            >

              <td>
                {{ menu.name }}
              </td>

              <td>
                <code>
                  {{ menu.route }}
                </code>
              </td>

              <td>

                <input
                  type="checkbox"
                  :checked="
                    menu.admin_enabled
                  "
                  @change="
                    changePermission(
                      menu,
                      'admin',
                      $event.target.checked
                    )
                  "
                />

              </td>

              <td>

                <input
                  type="checkbox"
                  :checked="
                    menu.user_enabled
                  "
                  @change="
                    changePermission(
                      menu,
                      'user',
                      $event.target.checked
                    )
                  "
                />

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


        <label>Role / Jabatan</label>

        <select
          v-model="userForm.role"
        >

          <option value="">
            Pilih role
          </option>

          <option
            v-for="role in roles"
            :key="role.id"
            :value="role.name"
          >
            {{ role.name }}
          </option>

        </select>


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


    <!-- ROLE MODAL -->

    <div
      v-if="showRoleModal"
      class="overlay"
      @click.self="
        showRoleModal = false
      "
    >

      <div class="modal">

        <h2>
          {{
            editingRole
              ? 'Edit Role'
              : 'Tambah Role'
          }}
        </h2>


        <label>
          Nama Role
        </label>

        <input
          v-model="roleForm.name"
          placeholder="
            Contoh: Trader — Perbankan
          "
        />


        <label>
          Deskripsi Role
        </label>

        <textarea
          v-model="
            roleForm.description
          "
          rows="4"
          placeholder="
            Jelaskan fungsi role ini
          "
        />


        <div class="modal-actions">

          <button
            class="btn"
            @click="
              showRoleModal = false
            "
          >
            Batal
          </button>

          <button
            class="btn primary"
            @click="saveRole"
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

.role-grid {
  display: grid;
  grid-template-columns:
    repeat(
      auto-fill,
      minmax(270px, 1fr)
    );
  gap: 16px;
}

.role-card {
  padding: 18px;
  border:
    1px solid var(--border);
  border-radius: 12px;
  background: var(--card);
}

.role-card h3 {
  margin-top: 0;
}

.role-card p {
  color: var(--muted-foreground);
  min-height: 42px;
}

.role-actions {
  display: flex;
  gap: 8px;
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