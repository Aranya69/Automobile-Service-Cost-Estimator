<script setup lang="ts">
// Strength meter and live rules under the password field.
const props = defineProps<{ password: string }>()

const checks = computed(() => passwordChecks(props.password))

const score = computed(() => {
  if (!props.password) return 0
  return checks.value.filter((c) => c.ok).length + (props.password.length >= 12 ? 1 : 0)
})

const LABELS = ['Too short', 'Weak', 'Fair', 'Good', 'Strong']
const COLORS = ['var(--line)', 'var(--alert)', '#D9822B', 'var(--fair)', 'var(--fair)']
</script>

<template>
  <div class="strength" aria-live="polite">
    <div class="bars">
      <span v-for="i in 4" :key="i" :style="{ background: i <= score ? COLORS[score] : 'var(--line)' }" />
    </div>
    <span class="label">Strength: <b>{{ password ? LABELS[score] : '—' }}</b></span>
    <ul class="rules">
      <li v-for="check in checks" :key="check.label" :class="{ ok: check.ok }">
        <AppIcon :name="check.ok ? 'check' : 'close'" :size="16" :stroke="2.25" />
        {{ check.label }}
        <span class="sr-only">{{ check.ok ? '(done)' : '(not yet)' }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.strength {
  display: grid;
  gap: 6px;
  margin-top: 4px;
}

.bars {
  display: flex;
  gap: 4px;
}

.bars span {
  flex: 1;
  height: 4px;
  border-radius: 2px;
}

.label {
  font-size: 13px;
  font-weight: 400;
  color: var(--ink-soft);
}

.label b {
  color: var(--ink);
}

.rules {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  font-size: 14px;
  font-weight: 400;
  color: var(--ink-soft);
}

.rules li {
  display: flex;
  align-items: center;
  gap: 6px;
}

.rules li.ok {
  color: var(--fair);
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
