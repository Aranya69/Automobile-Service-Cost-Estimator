<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'guest' })
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
  busy.value = true
  try {
    await login(form.email, form.password)
    await navigateTo(safeRedirect(route.query.redirect))
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
  <div class="page">
    <div class="narrow auth-box">
      <h1>Log in</h1>
      <p class="lead">Welcome back. Your cars and past estimates are waiting.</p>

      <form class="panel form" @submit.prevent="submit">
        <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>

        <div class="field">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            class="input"
            :class="{ 'has-error': fieldErrors.email }"
            type="email"
            autocomplete="email"
            required
          />
          <span v-if="fieldErrors.email" class="field-error">{{ fieldErrors.email }}</span>
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="form.password"
            class="input"
            :class="{ 'has-error': fieldErrors.password }"
            type="password"
            autocomplete="current-password"
            required
          />
          <span v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</span>
        </div>

        <button class="btn btn-primary btn-block" type="submit" :disabled="busy">
          {{ busy ? 'Logging in…' : 'Log in' }}
        </button>
      </form>

      <p class="switch small">
        New here? <NuxtLink to="/register">Create an account</NuxtLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-box {
  margin: 16px auto 0;
}

.switch {
  margin-top: 16px;
  text-align: center;
}
</style>
