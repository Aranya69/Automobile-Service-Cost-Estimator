<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useHead({ title: 'My account · ASCE' })

const { user } = useAuth()

const joined = computed(() =>
  user.value
    ? new Date(user.value.created_at).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : '',
)
</script>

<template>
  <div v-if="user" class="page">
    <div class="page-head">
      <div>
        <h1>My account</h1>
        <p class="lead">Your login details.</p>
      </div>
    </div>

    <dl class="panel details">
      <dt>Name</dt>
      <dd>{{ user.name }}</dd>
      <dt>Email</dt>
      <dd>{{ user.email }}</dd>
      <dt>Member since</dt>
      <dd>{{ joined }}</dd>
    </dl>
  </div>
</template>

<style scoped>
.details {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 10px 24px;
  margin: 0;
  max-width: 520px;
}

dt {
  color: var(--ink-soft);
  font-weight: 500;
}

dd {
  margin: 0;
  word-break: break-word;
}
</style>
