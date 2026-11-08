<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const api = useApi()
const id = Number(route.params.id)
// Arrived straight from the estimate page.
const justSaved = computed(() => route.query.new === '1')

const { data, error } = await useAsyncData(`estimate-${id}`, () =>
  api.get<{ estimate: EstimateDetail }>(`/estimates/${id}`),
)
const estimate = computed(() => data.value?.estimate)

useHead(() => ({
  title: estimate.value
    ? `${estimateNo(estimate.value.id)} ${estimate.value.vehicle_label} · ASCE`
    : 'Estimate · ASCE',
}))

const confirming = ref(false)
const deleting = ref(false)
const deleteError = ref('')

async function remove() {
  deleting.value = true
  deleteError.value = ''
  try {
    await api.del(`/estimates/${id}`)
    await navigateTo('/history')
  } catch (err) {
    deleteError.value = err instanceof ApiError ? err.message : 'Could not delete. Try again.'
    deleting.value = false
  }
}

function print() {
  window.print()
}
</script>

<template>
  <div class="page detail">
    <div v-if="error" class="panel failed">
      <span class="fail-icon"><AppIcon name="info" :size="24" :stroke="2" /></span>
      <b>We could not load this estimate</b>
      <span class="muted">It may have been deleted. Your other estimates are safe.</span>
      <NuxtLink to="/history" class="btn">Back to history</NuxtLink>
    </div>

    <template v-else-if="estimate">
      <div class="toolbar no-print">
        <span v-if="justSaved" class="saved">
          <AppIcon name="check" :size="16" :stroke="2.25" />Saved to your history
        </span>
        <NuxtLink v-else to="/history" class="back">← All estimates</NuxtLink>
        <div class="tools">
          <button type="button" class="btn" @click="print"><AppIcon name="printer" :size="16" />Print</button>
          <button type="button" class="btn btn-icon danger" aria-label="Delete estimate" @click="confirming = true">
            <AppIcon name="trash" :size="18" />
          </button>
          <NuxtLink
            :to="estimate.vehicle_id ? `/estimate?vehicle=${estimate.vehicle_id}` : '/estimate'"
            class="btn btn-primary"
          >
            New estimate
          </NuxtLink>
        </div>
      </div>

      <EstimateReceipt :estimate="estimate" />
    </template>

    <ConfirmDialog
      v-if="confirming && estimate"
      title="Delete this estimate?"
      :text="`${estimateNo(estimate.id)} for the ${estimate.vehicle_label} will be removed. This cannot be undone.`"
      :busy="deleting"
      :error="deleteError"
      @confirm="remove"
      @cancel="confirming = false; deleteError = ''"
    />
  </div>
</template>

<style scoped>
.detail {
  max-width: 880px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.saved {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--fair);
}

.back {
  font-size: 15px;
  font-weight: 600;
}

.tools {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.failed {
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
}

.failed b {
  font-size: 18px;
}

.fail-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--alert-bg);
  color: var(--alert);
  display: grid;
  place-items: center;
}
</style>
