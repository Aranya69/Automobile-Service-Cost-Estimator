<script setup lang="ts">
// Line icons from the ASCE design, 24×24 stroke paths.
const ICONS = {
  logo: 'M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5zM14.7 8.3a2.6 2.6 0 0 0-3.4 3.4L8.5 14.5l1 1 2.8-2.8a2.6 2.6 0 0 0 3.4-3.4l-1.4 1.4-1-1z',
  shieldCheck: 'M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5zM9 12l2 2 4-4',
  language: 'M5 8h8M9 4v4M7 8c0 4 3 7 6 8M11 8c0 3-3 7-6 8M13 20l4-10 4 10M14.5 17h5',
  arrowRight: 'M5 12h14M13 5l7 7-7 7',
  chevronRight: 'M9 6l6 6-6 6',
  chevronDown: 'M6 9l6 6 6-6',
  check: 'M20 6 9 17l-5-5',
  plus: 'M12 5v14M5 12h14',
  close: 'M18 6 6 18M6 6l12 12',
  edit: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z',
  trash: 'M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8v4M12 16h.01',
  warning: 'M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01',
  sparkle: 'M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  printer: 'M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v7H6z',
  database: 'M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6',
  noEntry: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM5.6 5.6l12.8 12.8',
  brake: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 3v3M21 12h-3',
  ac: 'M12 2v20M2 12h20M5 5l14 14M19 5L5 19M9 4l3 2 3-2M9 20l3-2 3 2',
  battery: 'M4 7h14a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2zM22 11v2M6 12h4M8 10v4M13 12h3',
  suspension: 'M12 2v3M12 19v3M7 5h10M7 19h10M8 8l8 2-8 2 8 2-8 2',
  oil: 'M12 2.7s-6 6.6-6 11.3a6 6 0 0 0 12 0c0-4.7-6-11.3-6-11.3z',
  thermometer: 'M14 14.8V4a2 2 0 0 0-4 0v10.8a4 4 0 1 0 4 0zM12 9v7',
} as const

export type IconName = keyof typeof ICONS

const props = withDefaults(
  defineProps<{ name: IconName; size?: number; stroke?: number }>(),
  { size: 20, stroke: 1.75 },
)
</script>

<template>
  <svg
    :width="props.size"
    :height="props.size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="props.stroke"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="ICONS[props.name]" />
  </svg>
</template>
