// Login and register pages: send logged-in users back to the app.
export default defineNuxtRouteMiddleware(() => {
  const { user } = useAuth()
  if (user.value) return navigateTo('/')
})
