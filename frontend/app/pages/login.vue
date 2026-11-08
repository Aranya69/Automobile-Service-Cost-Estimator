<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Log in · ASCE' })

const route = useRoute()
const { login } = useAuth()

const form = reactive({ email: '', password: '' })
const fieldErrors = ref<Record<string, string>>({})
const formError = ref('')
const busy = ref(false)

async function submit() {
  formError.value = ''
  fieldErrors.value = {}
  if (!form.email.trim()) fieldErrors.value.email = 'Email is required.'
  if (!form.password) fieldErrors.value.password = 'Password is required.'
  if (Object.keys(fieldErrors.value).length) return

  busy.value = true
  try {
    await login(form.email, form.password)
    await navigateTo(safeRedirect(route.query.redirect, '/vehicles'))
  } catch (err) {
    if (err instanceof ApiError) {
      formError.value = err.message
      fieldErrors.value = err.fields
    } else {
      formError.value = 'Something went wrong. Please try again.'
    }
    form.password = ''
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="auth-form" novalidate @submit.prevent="submit">
    <h2>Welcome back</h2>

    <p v-if="formError" class="alert alert-error" role="alert">
      <AppIcon name="info" :size="18" :stroke="2" />{{ formError }}
    </p>

    <label class="field">
      Email
      <input
        v-model="form.email"
        class="input"
        :class="{ 'has-error': fieldErrors.email }"
        type="email"
        autocomplete="email"
      />
      <span v-if="fieldErrors.email" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.email }}
      </span>
    </label>

    <label class="field">
      Password
      <input
        v-model="form.password"
        class="input"
        :class="{ 'has-error': fieldErrors.password }"
        type="password"
        autocomplete="current-password"
      />
      <span v-if="fieldErrors.password" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.password }}
      </span>
    </label>

    <button class="btn btn-primary btn-lg" type="submit" :disabled="busy">
      <span v-if="busy" class="spinner" />Log in
    </button>

    <p class="switch">
      New to ASCE? <NuxtLink to="/register">Create an account</NuxtLink>
    </p>
  </form>
</template>

<style scoped>
.auth-form {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.auth-form h2 {
  margin: 0;
}

.switch {
  margin: 0;
  text-align: center;
  font-size: 15px;
  color: var(--ink-soft);
}

.switch a {
  font-weight: 600;
  text-decoration: underline;
}
</style>
