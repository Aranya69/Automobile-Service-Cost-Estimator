<script setup lang="ts">
const props = withDefaults(
  defineProps<{ title: string; text: string; confirmLabel?: string; busy?: boolean; error?: string }>(),
  { confirmLabel: 'Delete', busy: false, error: '' },
)
const emit = defineEmits<{ confirm: []; cancel: [] }>()

const cancelButton = ref<HTMLButtonElement | null>(null)

function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape' && !props.busy) emit('cancel')
}

onMounted(() => {
  cancelButton.value?.focus()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div class="overlay" @click.self="!busy && emit('cancel')">
      <div class="dialog" role="dialog" aria-modal="true" :aria-label="title">
        <b class="title">{{ title }}</b>
        <span class="muted">{{ text }}</span>
        <p v-if="error" class="alert alert-error" role="alert">{{ error }}</p>
        <div class="buttons">
          <button ref="cancelButton" class="btn" type="button" :disabled="busy" @click="emit('cancel')">
            Cancel
          </button>
          <button class="btn btn-danger" type="button" :disabled="busy" @click="emit('confirm')">
            <span v-if="busy" class="spinner" />{{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.title {
  font-family: var(--font-head);
  font-size: 22px;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.spinner {
  border-color: var(--alert);
  border-right-color: transparent;
}
</style>
