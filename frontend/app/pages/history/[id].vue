<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const api = useApi()
const id = Number(route.params.id)

const { data, error } = await useAsyncData(`estimate-${id}`, () =>
  api.get<{ estimate: EstimateDetail }>(`/estimates/${id}`),
)
const estimate = computed(() => data.value?.estimate)

useHead(() => ({
  title: estimate.value ? `${estimate.value.vehicle_label} estimate · ASCE` : 'Estimate · ASCE',
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
    deleteError.value = err instanceof ApiError ? err.message : 'Could not delete the estimate.'
    deleting.value = false
  }
}
</script>

<template>
  <div class="page">
    <p class="back small"><NuxtLink to="/history">← All estimates</NuxtLink></p>

    <div v-if="error" class="panel empty">
      <p>This estimate could not be found. It may have been deleted.</p>
      <NuxtLink to="/history" class="btn">Back to history</NuxtLink>
    </div>

    <template v-else-if="estimate">
      <EstimateReceipt :estimate="estimate" />

      <p v-if="deleteError" class="alert alert-error">{{ deleteError }}</p>
      <div class="actions">
        <NuxtLink
          v-if="estimate.vehicle_id"
          :to="`/estimate?vehicle=${estimate.vehicle_id}`"
          class="btn"
        >
          New estimate for this car
        </NuxtLink>
        <template v-if="confirming">
          <span class="small confirm">Delete this estimate?</span>
          <button class="btn btn-danger" type="button" :disabled="deleting" @click="remove">
            {{ deleting ? 'Deleting…' : 'Yes, delete' }}
          </button>
          <button class="btn btn-quiet" type="button" @click="confirming = false">Keep</button>
        </template>
        <button v-else class="btn btn-quiet btn-danger" type="button" @click="confirming = true">
          Delete estimate
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.back {
  margin: 0 0 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.confirm {
  color: var(--red-700);
  font-weight: 600;
}
</style>
