<script setup lang="ts">
// Line drawing of a Toyota-style sedan (or a minivan for the Noah), side view.
const props = withDefaults(defineProps<{ van?: boolean; dark?: boolean }>(), { van: false, dark: false })
const body = computed(() =>
  props.van
    ? 'M24 118V72c0-10 6-18 16-22l26-14c6-3 12-4 18-4h150c10 0 18 6 22 15l12 33 22 6c10 3 16 10 16 20v12z'
    : 'M20 118v-18c0-9 6-15 15-17l38-8 34-26c8-6 16-9 26-9h70c10 0 18 3 25 9l32 26 34 6c10 2 16 9 16 18v19z',
)
const windows = computed(() =>
  props.van
    ? 'M70 50l20-10h46v34H62zM146 40h50v34h-50zM206 40h22c6 0 10 3 12 8l9 26h-43z'
    : 'M112 72l26-22c5-4 11-6 17-6h17v28zM182 44h22c7 0 13 2 18 6l26 22h-66z',
)
</script>

<template>
  <svg viewBox="0 0 320 150" fill="none" role="img" :aria-label="van ? 'Minivan illustration' : 'Sedan illustration'">
    <ellipse cx="160" cy="134" rx="140" ry="8" :fill="dark ? 'rgba(255,255,255,.08)' : 'rgba(22,24,29,.08)'" />
    <path :d="body" :fill="dark ? '#20232a' : '#fff'" :stroke="dark ? '#fff' : '#16181D'" stroke-width="3" stroke-linejoin="round" />
    <path :d="windows" fill="#FDF3D2" :stroke="dark ? '#fff' : '#16181D'" stroke-width="2.5" stroke-linejoin="round" />
    <path d="M276 96h18M24 100h14" stroke="#F2B705" stroke-width="5" stroke-linecap="round" />
    <circle cx="82" cy="118" r="20" :fill="dark ? '#16181D' : '#fff'" :stroke="dark ? '#fff' : '#16181D'" stroke-width="3" />
    <circle cx="82" cy="118" r="8" fill="#F2B705" />
    <circle cx="246" cy="118" r="20" :fill="dark ? '#16181D' : '#fff'" :stroke="dark ? '#fff' : '#16181D'" stroke-width="3" />
    <circle cx="246" cy="118" r="8" fill="#F2B705" />
  </svg>
</template>
