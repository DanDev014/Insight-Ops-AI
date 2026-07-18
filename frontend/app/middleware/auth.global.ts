export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  const isPublicRoute = to.path === '/'

  if (isPublicRoute && authStore.isAuthenticated) {
    return navigateTo('/dashboard')
  }

  if (!isPublicRoute && !authStore.isAuthenticated) {
    return navigateTo('/')
  }
})