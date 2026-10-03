// Load the logged-in user once, on the server for the first page and then
// reused on the client, so the navbar and middleware know who is logged in.
export default defineNuxtPlugin(async () => {
  const { checked, fetchUser } = useAuth()
  if (!checked.value) await fetchUser()
})
