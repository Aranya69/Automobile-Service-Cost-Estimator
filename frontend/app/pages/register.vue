<script setup lang="ts">
import { ApiError } from '~/composables/useApi'
import type { RegisterForm } from '~/composables/useAuth'
import type { Draft } from '~/composables/useDraft'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Create account · ASCE' })

const { register } = useAuth()
const draftStore = useDraft()

// Filled in on the client: what the visitor typed on the landing page.
const draft = ref<Draft | null>(null)
onMounted(() => {
  draft.value = draftStore.load()
})

const form = reactive<RegisterForm>({
  name: '',
  email: '',
  password: '',
  confirm_password: '',
})
const showPassword = ref(false)
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

const emailTaken = computed(() => fieldErrors.value.email?.includes('already exists'))

async function submit() {
  formError.value = ''
  const fields: Field[] = ['name', 'email', 'password', 'confirm_password']
  if (fields.map(checkField).includes(false)) {
    formError.value = 'Please fix the highlighted fields.'
    return
  }

  busy.value = true
  try {
    await register({ ...form })
    // Came from the landing page: add that car next, then estimate.
    await navigateTo(draft.value ? '/vehicles/new' : '/vehicles')
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
  <form class="auth-form" novalidate @submit.prevent="submit">
    <div>
      <h2>Create your account</h2>
      <p v-if="draft" class="muted intro">
        Your {{ draft.model }} {{ draft.year }}
        <template v-if="draft.problem">and problem description are</template>
        <template v-else>is</template>
        saved. Finish signing up to see the estimate.
      </p>
      <p v-else class="muted intro">It takes a minute. We only use your email to log you in.</p>
    </div>

    <p v-if="formError && !emailTaken" class="alert alert-error" role="alert">
      <AppIcon name="info" :size="18" :stroke="2" />{{ formError }}
    </p>

    <label class="field">
      Full name
      <input
        v-model="form.name"
        class="input"
        :class="{ 'has-error': fieldErrors.name }"
        autocomplete="name"
        maxlength="60"
        @blur="onBlur('name')"
        @input="onInput('name')"
      />
      <span v-if="fieldErrors.name" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.name }}
      </span>
    </label>

    <label class="field">
      Email
      <input
        v-model="form.email"
        class="input"
        :class="{ 'has-error': fieldErrors.email }"
        type="email"
        autocomplete="email"
        @blur="onBlur('email')"
        @input="onInput('email')"
      />
      <span v-if="emailTaken" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />This email is already registered.
        <NuxtLink to="/login" class="inline-link">Log in instead</NuxtLink>
      </span>
      <span v-else-if="fieldErrors.email" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.email }}
      </span>
    </label>

    <div class="field">
      <label for="password">Password</label>
      <div class="with-toggle">
        <input
          id="password"
          v-model="form.password"
          class="input"
          :class="{ 'has-error': fieldErrors.password }"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="At least 8 characters"
          maxlength="128"
          @blur="onBlur('password')"
          @input="onInput('password')"
        />
        <button
          type="button"
          class="toggle"
          :aria-label="showPassword ? 'Hide password' : 'Show password'"
          :aria-pressed="showPassword"
          @click="showPassword = !showPassword"
        >
          <AppIcon name="eye" />
        </button>
      </div>
      <PasswordChecklist :password="form.password" />
      <span v-if="fieldErrors.password" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.password }}
      </span>
    </div>

    <label class="field">
      Confirm password
      <input
        v-model="form.confirm_password"
        class="input"
        :class="{ 'has-error': fieldErrors.confirm_password }"
        :type="showPassword ? 'text' : 'password'"
        autocomplete="new-password"
        @blur="onBlur('confirm_password')"
        @input="onInput('confirm_password')"
      />
      <span v-if="fieldErrors.confirm_password" class="field-error">
        <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.confirm_password }}
      </span>
    </label>

    <button class="btn btn-primary btn-lg" type="submit" :disabled="busy">
      <span v-if="busy" class="spinner" />Create account
    </button>

    <p class="switch">
      Already have an account? <NuxtLink to="/login">Log in</NuxtLink>
    </p>
  </form>
</template>

<style scoped>
.auth-form {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.auth-form h2 {
  margin: 0 0 6px;
}

.intro {
  margin: 0;
}

.with-toggle {
  position: relative;
}

.with-toggle .input {
  padding-right: 48px;
}

.toggle {
  position: absolute;
  right: 2px;
  top: 2px;
  width: 44px;
  height: 44px;
  border: 0;
  background: none;
  cursor: pointer;
  color: var(--ink-soft);
  display: grid;
  place-items: center;
}

.inline-link {
  color: var(--alert);
  text-decoration: underline;
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
