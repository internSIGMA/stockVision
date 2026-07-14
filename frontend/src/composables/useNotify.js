import { toast } from 'vue-sonner'

const DURATION = 4000

export function useNotify() {
  return {
    success: (message, description) => toast.success(message, { description, duration: DURATION }),
    error: (message, description) => toast.error(message, { description, duration: DURATION }),
    info: (message, description) => toast(message, { description, duration: DURATION }),
  }
}
