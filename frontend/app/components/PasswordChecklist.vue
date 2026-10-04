<script setup lang="ts">
const props = defineProps<{ password: string }>()
const checks = computed(() => passwordChecks(props.password))
</script>

<template>
  <ul class="checklist" aria-live="polite">
    <li v-for="check in checks" :key="check.label" :class="{ ok: check.ok }">
      <span class="mark" aria-hidden="true">{{ check.ok ? '✓' : '·' }}</span>
      {{ check.label }}
      <span class="sr-only">{{ check.ok ? '(done)' : '(not yet)' }}</span>
    </li>
  </ul>
</template>

<style scoped>
.checklist {
  list-style: none;
  margin: 4px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 2px 16px;
  font-size: 0.85rem;
  color: var(--ink-soft);
}

.checklist li.ok {
  color: var(--ok);
}

.mark {
  display: inline-block;
  width: 1em;
  font-weight: 700;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>
