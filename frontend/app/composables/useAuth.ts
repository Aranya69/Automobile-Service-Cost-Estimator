export interface User {
  id: number
  name: string
  email: string
  role: string
  created_at: string
}

export interface RegisterForm {
  name: string
  email: string
  password: string
  confirm_password: string
}

export function useAuth() {
  const user = useState<User | null>('auth-user', () => null)
  const checked = useState<boolean>('auth-checked', () => false)
  const api = useApi()

  async function fetchUser() {
    try {
      const res = await api.get<{ user: User }>('/auth/me')
      user.value = res.user
    } catch {
      user.value = null
    } finally {
      checked.value = true
    }
    return user.value
  }

  async function login(email: string, password: string) {
    const res = await api.post<{ user: User }>('/auth/login', { email, password })
    user.value = res.user
    checked.value = true
  }

  async function register(form: RegisterForm) {
    const res = await api.post<{ user: User }>('/auth/register', form)
    user.value = res.user
    checked.value = true
  }

  return {
    user,
    checked,
    isLoggedIn: computed(() => user.value !== null),
    fetchUser,
    login,
    register,
  }
}

// Only allow redirects to our own pages, never to another site.
export function safeRedirect(value: unknown, fallback = '/') {
  if (typeof value !== 'string') return fallback
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) return fallback
  return value
}
