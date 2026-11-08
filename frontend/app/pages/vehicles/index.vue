<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'My cars · ASCE' })

const api = useApi()

const { data, error, refresh } = await useAsyncData('my-cars', async () => {
  const [cars, recent] = await Promise.all([
    api.get<{ vehicles: Vehicle[] }>('/vehicles'),
    api.get<{ estimates: EstimateSummary[]; total: number }>('/estimates?per_page=50'),
  ])
  return { vehicles: cars.vehicles, estimates: recent.estimates, total: recent.total }
})

const vehicles = computed(() => data.value?.vehicles ?? [])
const latest = computed(() => data.value?.estimates[0])

// Newest estimate per car (the list is already newest first).
const lastByCar = computed(() => {
  const map = new Map<number, EstimateSummary>()
  for (const e of data.value?.estimates ?? []) {
    if (e.vehicle_id && !map.has(e.vehicle_id)) map.set(e.vehicle_id, e)
  }
  return map
})

const deleting = ref<Vehicle | null>(null)
const busy = ref(false)
const deleteError = ref('')

async function confirmDelete() {
  if (!deleting.value) return
  busy.value = true
  deleteError.value = ''
  try {
    await api.del(`/vehicles/${deleting.value.id}`)
    deleting.value = null
    await refresh()
  } catch (err) {
    deleteError.value = err instanceof ApiError ? err.message : 'Could not delete. Try again.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>My cars</h1>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">
        <AppIcon name="plus" :size="18" :stroke="2" />Add a car
      </NuxtLink>
    </div>

    <p v-if="error" class="alert alert-error">
      <AppIcon name="info" :size="18" :stroke="2" />Could not load your cars. Please refresh the page.
    </p>

    <div v-else-if="!vehicles.length" class="empty">
      <svg width="96" height="64" viewBox="0 0 96 64" fill="none" stroke="#16181D" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M8 46V36l8-14h52l12 14h6a4 4 0 0 1 4 4v6z" />
        <circle cx="26" cy="48" r="7" fill="#F6F4EF" />
        <circle cx="72" cy="48" r="7" fill="#F6F4EF" />
        <path d="M44 30a5 5 0 1 1 6 5v3M50 42h.01" stroke="#C99600" stroke-width="2.25" />
      </svg>
      <p>No cars yet. Add your first car to get an estimate.</p>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">Add a car</NuxtLink>
    </div>

    <template v-else>
      <div class="stats">
        <div class="stat">
          <span class="muted small">Cars</span>
          <span class="mono big">{{ vehicles.length }}</span>
        </div>
        <div class="stat">
          <span class="muted small">Estimates</span>
          <span class="mono big">{{ data?.total ?? 0 }}</span>
        </div>
        <div class="stat">
          <span class="muted small">Last estimate</span>
          <NuxtLink v-if="latest" :to="`/history/${latest.id}`" class="last">
            {{ latest.vehicle_label.replace('Toyota ', '') }} · {{ formatDate(latest.created_at) }}
          </NuxtLink>
          <span v-else class="last muted">None yet</span>
        </div>
      </div>

      <div class="cars">
        <article v-for="car in vehicles" :key="car.id" class="car">
          <div class="car-art">
            <CarArt :van="car.model === 'Noah'" />
          </div>
          <div class="car-body">
            <div class="car-top">
              <div>
                <h2 class="car-name">{{ car.model }} {{ car.year }}</h2>
                <span class="muted small">{{ car.engine_cc }} cc</span>
              </div>
              <div class="car-actions">
                <NuxtLink :to="`/vehicles/${car.id}/edit`" class="btn btn-icon" :aria-label="`Edit ${car.label}`">
                  <AppIcon name="edit" :size="18" />
                </NuxtLink>
                <button
                  type="button"
                  class="btn btn-icon danger"
                  :aria-label="`Delete ${car.label}`"
                  @click="deleting = car"
                >
                  <AppIcon name="trash" :size="18" />
                </button>
              </div>
            </div>
            <div class="car-facts dashed">
              <div>
                <div class="muted">Odometer</div>
                <div class="mono">{{ formatKm(car.odometer_km) }}</div>
              </div>
              <div>
                <div class="muted">Last estimate</div>
                <NuxtLink v-if="lastByCar.get(car.id)" :to="`/history/${lastByCar.get(car.id)!.id}`" class="fact-link">
                  {{ formatDate(lastByCar.get(car.id)!.created_at) }}
                </NuxtLink>
                <div v-else class="fact-none">—</div>
              </div>
            </div>
            <NuxtLink :to="`/estimate?vehicle=${car.id}`" class="btn">Get estimate</NuxtLink>
          </div>
        </article>
      </div>
    </template>

    <ConfirmDialog
      v-if="deleting"
      :title="`Delete ${deleting.model} ${deleting.year}?`"
      text="The car is removed from your list. Past estimates for it stay in your history."
      :busy="busy"
      :error="deleteError"
      @confirm="confirmDelete"
      @cancel="deleting = null; deleteError = ''"
    />
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  margin-bottom: 32px;
}

.stat {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat + .stat {
  border-left: 1px solid var(--line);
}

.big {
  font-size: 28px;
}

.last {
  font-weight: 600;
  font-size: 17px;
  margin-top: 6px;
}

.cars {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  gap: 20px;
}

.car {
  background: var(--card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.car-art {
  height: 150px;
  background: var(--signal-soft);
  display: grid;
  place-items: center;
  padding: 16px 32px 8px;
}

.car-art svg {
  width: 100%;
  max-width: 240px;
  height: auto;
}

.car-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.car-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.car-name {
  margin: 0;
  font-size: 22px;
}

.car-actions {
  display: flex;
}

.car-facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding-top: 14px;
  font-size: 14px;
}

.fact-link,
.fact-none {
  font-weight: 600;
}

@media (max-width: 600px) {
  .stat + .stat {
    border-left: 0;
    border-top: 1px solid var(--line);
  }
}
</style>
