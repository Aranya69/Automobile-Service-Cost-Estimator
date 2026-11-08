<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()
const { user } = useAuth()

const notFound = computed(() => props.error.statusCode === 404)
useHead({ title: notFound.value ? 'Page not found · ASCE' : 'Something went wrong · ASCE' })

function back() {
  clearError({ redirect: user.value ? '/vehicles' : '/' })
}
</script>

<template>
  <NuxtLayout name="default">
    <div class="page">
      <div class="panel lost">
        <svg width="180" height="110" viewBox="0 0 180 110" fill="none" stroke="#16181D" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <g transform="rotate(-8 90 50)">
            <path d="M24 62V48l12-20h76l18 20h10a6 6 0 0 1 6 6v8z" />
            <circle cx="50" cy="64" r="10" fill="#FFFFFF" />
            <circle cx="120" cy="64" r="10" fill="#FFFFFF" />
            <path d="M60 30v18M86 30v18" />
          </g>
          <path d="M126 70v24M114 94h24M120 70h12" stroke="#C99600" stroke-width="2.25" />
          <path d="M10 100h160" stroke="#E3DFD6" />
        </svg>
        <h1>{{ notFound ? 'This page is up on the jack' : 'Something went wrong' }}</h1>
        <p class="muted">
          {{ notFound ? 'We could not find what you were looking for.' : 'Please try again in a moment. Your data is safe.' }}
        </p>
        <button class="btn btn-primary" type="button" @click="back">
          {{ user ? 'Back to my cars' : 'Back to the home page' }}
        </button>
      </div>
    </div>
  </NuxtLayout>
</template>

<style scoped>
.lost {
  padding: 56px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 14px;
}

.lost h1 {
  font-size: 28px;
  margin: 0;
}

.lost p {
  margin: 0;
}
</style>
