<script setup lang="ts">
import { ApiError } from '~/composables/useApi'
import type { RegisterForm } from '~/composables/useAuth'

definePageMeta({ middleware: 'guest' })
useHead({ title: 'Create account · ASCE' })

const { register } = useAuth()

const form = reactive<RegisterForm>({
  name: '',
  email: '',
  password: '',
  confirm_password: '',
})
const fieldErrors = ref<Record<string, string>>({})
const formError = ref('')
const busy = ref(false)

type Field = keyof RegisterForm

function checkField(field: Field) {
  const rules: Record<Field, () => string> = {
    name: () => nameError(form.name),
    email: () => emailError(form.email),
    password: () => passwordError(form.password, form.email),
    confirm_password: () => confirmError(form.password, form.confirm_password),
  }
  const message = rules[field]()
  const next = { ...fieldErrors.value }
  if (message) next[field] = message
  else delete next[field]
  fieldErrors.value = next
  return !message
}

// Check a field when the user leaves it, and re-check while they fix it.
function onBlur(field: Field) {
  if (form[field]) checkField(field)
}

function onInput(field: Field) {
  if (fieldErrors.value[field]) checkField(field)
}

async function submit() {
  formError.value = ''
  const fields: Field[] = ['name', 'email', 'password', 'confirm_password']
  const results = fields.map(checkField)
  if (results.includes(false)) {
    formError.value = 'Please fix the highlighted fields.'
    return
  }

  busy.value = true
  try {
    await register({ ...form })
    await navigateTo('/')
  } catch (err) {
    if (err instanceof ApiError) {
      formError.value = err.message
      fieldErrors.value = err.fields
    } else {
      formError.value = 'Something went wrong. Please try again.'
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="narrow auth-box">
      <h1>Create an account</h1>
      <p class="lead">It takes a minute. We only use your email to log you in.</p>

      <form class="panel form" novalidate @submit.prevent="submit">
        <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>

        <div class="field">
          <label for="name">Full name</label>
          <input
            id="name"
            v-model="form.name"
            @blur="onBlur('name')"
            @input="onInput('name')"
            class="input"
            :class="{ 'has-error': fieldErrors.name }"
            autocomplete="name"
            maxlength="60"
            required
          />
          <span v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</span>
        </div>

        <div class="field">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            @blur="onBlur('email')"
            @input="onInput('email')"
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
            @blur="onBlur('password')"
            @input="onInput('password')"
            class="input"
            :class="{ 'has-error': fieldErrors.password }"
            type="password"
            autocomplete="new-password"
            minlength="8"
            maxlength="128"
            required
          />
          <PasswordChecklist :password="form.password" />
          <span v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</span>
        </div>

        <div class="field">
          <label for="confirm_password">Confirm password</label>
          <input
            id="confirm_password"
            v-model="form.confirm_password"
            @blur="onBlur('confirm_password')"
            @input="onInput('confirm_password')"
            class="input"
            :class="{ 'has-error': fieldErrors.confirm_password }"
            type="password"
            autocomplete="new-password"
            required
          />
          <span v-if="fieldErrors.confirm_password" class="field-error">
            {{ fieldErrors.confirm_password }}
          </span>
        </div>

        <button class="btn btn-primary btn-block" type="submit" :disabled="busy">
          {{ busy ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <p class="switch small">
        Already registered? <NuxtLink to="/login">Log in</NuxtLink>
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
