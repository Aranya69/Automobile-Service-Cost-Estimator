<script setup lang="ts">
withDefaults(defineProps<{ inverted?: boolean; to?: string }>(), { inverted: false, to: '/' })
</script>

<template>
  <NuxtLink :to="to" class="brand" :class="{ inverted }" aria-label="ASCE home">
    <span class="mark"><AppIcon name="logo" /></span>
    <span class="word">ASCE</span>
  </NuxtLink>
</template>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--ink);
}

.mark {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--ink);
  color: var(--signal);
  display: grid;
  place-items: center;
}

.word {
  font-family: var(--font-head);
  font-weight: 800;
  font-size: 22px;
  letter-spacing: 0.02em;
}

.inverted { color: #fff; }
.inverted:hover { color: #fff; }

.inverted .mark {
  background: var(--signal);
  color: var(--ink);
}
</style>
