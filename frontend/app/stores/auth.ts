interface AuthUser {
  id: number
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = useCookie<AuthUser | null>('auth_user', {
    default: () => null,
    maxAge: 60 * 60 * 24 * 7, // 7 days
    sameSite: 'lax',
  })

  const isAuthenticated = computed(() => !!user.value)

  async function login(email: string, password: string) {
    const response = await $fetch<{ message: string; user: AuthUser }>('/api/login', {
      method: 'POST',
      body: { email, password },
    })

    user.value = response.user
  }

  function logout() {
    user.value = null
  }

  return { user, isAuthenticated, login, logout }
})