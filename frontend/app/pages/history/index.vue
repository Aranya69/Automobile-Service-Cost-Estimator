<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Past estimates · ASCE' })

interface Page {
  estimates: EstimateSummary[]
  total: number
  page: number
  per_page: number
}

const api = useApi()
const route = useRoute()
const router = useRouter()

const page = computed(() => Math.max(1, Number(route.query.page) || 1))
const vehicleFilter = computed(() => (route.query.vehicle ? Number(route.query.vehicle) : null))

const { data: vehicleData } = await useAsyncData('history-vehicles', () =>
  api.get<{ vehicles: Vehicle[] }>('/vehicles'),
)

const { data, error, refresh } = await useAsyncData(
  'history',
  () => {
    const params = new URLSearchParams({ page: String(page.value), per_page: '10' })
    if (vehicleFilter.value) params.set('vehicle_id', String(vehicleFilter.value))
    return api.get<Page>(`/estimates?${params}`)
  },
  { watch: [page, vehicleFilter] },
)

const estimates = computed(() => data.value?.estimates ?? [])
const pages = computed(() =>
  data.value ? Math.max(1, Math.ceil(data.value.total / data.value.per_page)) : 1,
)

const confirmingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const deleteError = ref('')

function setFilter(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  router.push({ query: value ? { vehicle: value } : {} })
}

function goTo(p: number) {
  router.push({ query: { ...route.query, page: p > 1 ? String(p) : undefined } })
}

async function remove(id: number) {
  deleteError.value = ''
  deletingId.value = id
  try {
    await api.del(`/estimates/${id}`)
    confirmingId.value = null
    // Deleted the last row on this page: step back one page.
    if (estimates.value.length === 1 && page.value > 1) goTo(page.value - 1)
    else await refresh()
  } catch (err) {
    deleteError.value = err instanceof ApiError ? err.message : 'Could not delete the estimate.'
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>Past estimates</h1>
        <p class="lead">Every estimate you make is saved here.</p>
      </div>
      <NuxtLink to="/estimate" class="btn btn-primary">New estimate</NuxtLink>
    </div>

    <div v-if="vehicleData?.vehicles.length" class="filter">
      <label for="car-filter" class="small muted">Car</label>
      <select id="car-filter" class="input" :value="vehicleFilter ?? ''" @change="setFilter">
        <option value="">All cars</option>
        <option v-for="v in vehicleData.vehicles" :key="v.id" :value="v.id">{{ v.label }}</option>
      </select>
    </div>

    <p v-if="error" class="alert alert-error">Could not load your estimates. Please refresh the page.</p>
    <p v-if="deleteError" class="alert alert-error">{{ deleteError }}</p>

    <div v-if="!error && estimates.length === 0" class="panel empty">
      <p>{{ vehicleFilter ? 'No estimates for this car yet.' : 'You have no saved estimates yet.' }}</p>
      <NuxtLink to="/estimate" class="btn btn-primary">Make your first estimate</NuxtLink>
    </div>

    <ul v-else class="rows">
      <li v-for="e in estimates" :key="e.id" class="row">
        <NuxtLink :to="`/history/${e.id}`" class="row-link">
          <span class="when small muted">{{ formatDate(e.created_at) }}</span>
          <span class="what">
            <strong>{{ e.vehicle_label }}</strong>
            <span class="problem">“{{ e.problem_text }}”</span>
          </span>
          <span class="cost">
            <span class="mono likely">{{ formatTaka(e.total_likely) }}</span>
            <span class="mono small muted">
              {{ formatTaka(e.total_min) }} – {{ formatTaka(e.total_max) }}
            </span>
          </span>
        </NuxtLink>
        <div class="row-actions">
          <span class="tag" :class="`conf-${e.confidence}`">{{ CONFIDENCE_TEXT[e.confidence] }}</span>
          <template v-if="confirmingId === e.id">
            <button
              class="btn btn-danger"
              type="button"
              :disabled="deletingId === e.id"
              @click="remove(e.id)"
            >
              {{ deletingId === e.id ? 'Deleting…' : 'Delete' }}
            </button>
            <button class="btn btn-quiet" type="button" @click="confirmingId = null">Keep</button>
          </template>
          <button v-else class="btn btn-quiet btn-danger" type="button" @click="confirmingId = e.id">
            Delete
          </button>
        </div>
      </li>
    </ul>

    <nav v-if="pages > 1" class="pager">
      <button class="btn" type="button" :disabled="page <= 1" @click="goTo(page - 1)">Newer</button>
      <span class="small muted">Page {{ page }} of {{ pages }}</span>
      <button class="btn" type="button" :disabled="page >= pages" @click="goTo(page + 1)">
        Older
      </button>
    </nav>
  </div>
</template>

<style scoped>
.filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  max-width: 360px;
}

.rows {
  list-style: none;
  margin: 0;
  padding: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

.row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}

.row:last-child {
  border-bottom: 0;
}

.row-link {
  flex: 1 1 420px;
  display: grid;
  grid-template-columns: 96px 1fr auto;
  gap: 4px 16px;
  align-items: center;
  color: var(--ink);
  text-decoration: none;
  min-width: 0;
}

.row-link:hover strong {
  color: var(--red-700);
}

.what {
  display: grid;
  min-width: 0;
}

.problem {
  color: var(--ink-soft);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cost {
  display: grid;
  justify-items: end;
}

.likely {
  font-weight: 500;
  color: var(--red-700);
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.conf-high { background: var(--ok-bg); color: var(--ok); }
.conf-medium { background: var(--warn-bg); color: var(--warn); }

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}

@media (max-width: 600px) {
  .row-link {
    flex-basis: 100%;
    grid-template-columns: 1fr auto;
  }

  .when {
    grid-column: 1 / -1;
  }
}
</style>
