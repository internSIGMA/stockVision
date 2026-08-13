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