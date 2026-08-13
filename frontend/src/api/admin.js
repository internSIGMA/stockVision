import api from './index'

function adminConfig(accessRole = 'admin') {
  return {
    headers: {
      'X-Access-Role': accessRole,
    },
  }
}


// ==============================
// USER MANAGEMENT
// ==============================

export function getAdminUsers(accessRole) {
  return api.get(
    '/admin/users',
    adminConfig(accessRole)
  )
}

export function createAdminUser(
  data,
  accessRole
) {
  return api.post(
    '/admin/users',
    data,
    adminConfig(accessRole)
  )
}

export function updateAdminUser(
  id,
  data,
  accessRole
) {
  return api.put(
    `/admin/users/${id}`,
    data,
    adminConfig(accessRole)
  )
}


// ==============================
// ROLE MANAGEMENT
// ==============================

export function getRoles(accessRole) {
  return api.get(
    '/admin/roles',
    adminConfig(accessRole)
  )
}

export function createRole(
  data,
  accessRole
) {
  return api.post(
    '/admin/roles',
    data,
    adminConfig(accessRole)
  )
}

export function updateRole(
  id,
  data,
  accessRole
) {
  return api.put(
    `/admin/roles/${id}`,
    data,
    adminConfig(accessRole)
  )
}

export function deleteRole(
  id,
  accessRole
) {
  return api.delete(
    `/admin/roles/${id}`,
    adminConfig(accessRole)
  )
}


// ==============================
// MENU MANAGEMENT
// ==============================

export function getMenuPermissions(
  accessRole
) {
  return api.get(
    '/admin/menu-permissions',
    adminConfig(accessRole)
  )
}

export function updateMenuPermission(
  data,
  accessRole
) {
  return api.put(
    '/admin/menu-permissions',
    data,
    adminConfig(accessRole)
  )
}

export function getUserPermissions(
  accessRole
) {
  return api.get(
    `/admin/permissions/${accessRole}`
  )
}


// ==============================
// ACTIVITY
// ==============================

export function getUserActivity(
  accessRole
) {
  return api.get(
    '/admin/activity',
    adminConfig(accessRole)
  )
}