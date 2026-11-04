<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'My cars · ASCE' })

const api = useApi()
const { data, error, refresh } = await useAsyncData('vehicles', () =>
  api.get<{ vehicles: Vehicle[] }>('/vehicles'),
)
const vehicles = computed(() => data.value?.vehicles ?? [])

const confirmingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const deleteError = ref('')

async function remove(id: number) {
  deleteError.value = ''
  deletingId.value = id
  try {
    await api.del(`/vehicles/${id}`)
    confirmingId.value = null
    await refresh()
  } catch (err) {
    deleteError.value = err instanceof ApiError ? err.message : 'Could not delete the car.'
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>My cars</h1>
        <p class="lead">Estimates use the model, year and mileage of the car you pick.</p>
      </div>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">Add a car</NuxtLink>
    </div>

    <p v-if="error" class="alert alert-error">Could not load your cars. Please refresh the page.</p>
    <p v-if="deleteError" class="alert alert-error">{{ deleteError }}</p>

    <div v-if="!error && vehicles.length === 0" class="panel empty">
      <p>You have not added a car yet.</p>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">Add your first car</NuxtLink>
    </div>

    <ul v-else class="cars">
      <li v-for="car in vehicles" :key="car.id" class="car panel">
        <div class="car-main">
          <h2>{{ car.make }} {{ car.model }}</h2>
          <p class="specs">
            <span>{{ car.year }}</span>
            <span>{{ car.engine_cc }} cc</span>
            <span class="mono">{{ formatKm(car.odometer_km) }}</span>
          </p>
        </div>

        <div v-if="confirmingId === car.id" class="car-actions confirm">
          <span class="small">Delete this car?</span>
          <button
            class="btn btn-danger"
            type="button"
            :disabled="deletingId === car.id"
            @click="remove(car.id)"
          >
            {{ deletingId === car.id ? 'Deleting…' : 'Yes, delete' }}
          </button>
          <button class="btn btn-quiet" type="button" @click="confirmingId = null">Keep</button>
        </div>
        <div v-else class="car-actions">
          <NuxtLink :to="`/vehicles/${car.id}/edit`" class="btn">Edit</NuxtLink>
          <button class="btn btn-quiet btn-danger" type="button" @click="confirmingId = car.id">
            Delete
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.cars {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.car {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px 24px;
  padding: 16px 20px;
  border-left: 4px solid var(--red-400);
}

.car + .car {
  margin-top: 0;
}

.car h2 {
  margin: 0;
  font-size: 1.15rem;
}

.specs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  margin: 2px 0 0;
  color: var(--ink-soft);
  font-size: 0.95rem;
}

.car-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.confirm .small {
  color: var(--red-700);
  font-weight: 600;
}
</style>
