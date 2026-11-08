<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Estimate history · ASCE' })

interface Page {
  estimates: EstimateSummary[]
  total: number
  page: number
  per_page: number
}

const api = useApi()
const route = useRoute()
const router = useRouter()

const DATE_OPTIONS = [
  { value: '', label: 'All time' },
  { value: '30', label: 'Last 30 days' },
  { value: '180', label: 'Last 6 months' },
]

const page = computed(() => Math.max(1, Number(route.query.page) || 1))
const vehicleFilter = computed(() => String(route.query.vehicle ?? ''))
const daysFilter = computed(() => String(route.query.days ?? ''))
const sort = computed(() => (route.query.sort === 'cost' ? 'cost' : 'newest'))

const { data: vehicleData } = await useAsyncData('history-vehicles', () =>
  api.get<{ vehicles: Vehicle[] }>('/vehicles'),
)

const { data, error, refresh } = await useAsyncData(
  'history',
  () => {
    const params = new URLSearchParams({ page: String(page.value), per_page: '10', sort: sort.value })
    if (vehicleFilter.value) params.set('vehicle_id', vehicleFilter.value)
    if (daysFilter.value) params.set('days', daysFilter.value)
    return api.get<Page>(`/estimates?${params}`)
  },
  { watch: [page, vehicleFilter, daysFilter, sort] },
)

const estimates = computed(() => data.value?.estimates ?? [])
const pages = computed(() =>
  data.value ? Math.max(1, Math.ceil(data.value.total / data.value.per_page)) : 1,
)
const filtered = computed(() => Boolean(vehicleFilter.value || daysFilter.value))

function setQuery(changes: Record<string, string | undefined>) {
  const query: Record<string, string> = {}
  for (const [k, v] of Object.entries({ ...route.query, ...changes, page: changes.page })) {
    if (typeof v === 'string' && v) query[k] = v
  }
  router.push({ query })
}

const deleting = ref<EstimateSummary | null>(null)
const busy = ref(false)
const deleteError = ref('')

async function confirmDelete() {
  if (!deleting.value) return
  busy.value = true
  deleteError.value = ''
  try {
    await api.del(`/estimates/${deleting.value.id}`)
    deleting.value = null
    // Deleted the last row on this page: step back one page.
    if (estimates.value.length === 1 && page.value > 1) setQuery({ page: String(page.value - 1) })
    else await refresh()
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
      <h1>Estimate history</h1>
      <NuxtLink to="/estimate" class="btn btn-primary">New estimate</NuxtLink>
    </div>

    <div class="filters">
      <label class="field">
        Car
        <select class="input" :value="vehicleFilter" @change="setQuery({ vehicle: ($event.target as HTMLSelectElement).value })">
          <option value="">All cars</option>
          <option v-for="v in vehicleData?.vehicles" :key="v.id" :value="String(v.id)">
            {{ v.model }} {{ v.year }}
          </option>
        </select>
      </label>
      <label class="field">
        Date
        <select class="input" :value="daysFilter" @change="setQuery({ days: ($event.target as HTMLSelectElement).value })">
          <option v-for="d in DATE_OPTIONS" :key="d.value" :value="d.value">{{ d.label }}</option>
        </select>
      </label>
      <div class="sort" role="radiogroup" aria-label="Sort">
        <button
          type="button"
          role="radio"
          :aria-checked="sort === 'newest'"
          :class="{ on: sort === 'newest' }"
          @click="setQuery({ sort: undefined })"
        >
          Newest
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="sort === 'cost'"
          :class="{ on: sort === 'cost' }"
          @click="setQuery({ sort: 'cost' })"
        >
          Highest cost
        </button>
      </div>
    </div>

    <p v-if="error" class="alert alert-error">
      <AppIcon name="info" :size="18" :stroke="2" />Could not load your estimates. Please refresh the page.
    </p>

    <div v-else-if="!estimates.length" class="empty">
      <svg width="64" height="76" viewBox="0 0 64 76" fill="none" stroke="#16181D" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="6" y="10" width="52" height="62" rx="6" />
        <rect x="20" y="4" width="24" height="12" rx="3" fill="#F2B705" />
        <path d="M18 32h28M18 44h28M18 56h16" stroke-dasharray="3 4" />
      </svg>
      <p>{{ filtered ? 'No estimates match these filters' : 'No estimates yet' }}</p>
      <NuxtLink v-if="!filtered" to="/estimate" class="btn btn-primary">Get your first estimate</NuxtLink>
      <button v-else type="button" class="btn" @click="router.push({ query: {} })">Clear filters</button>
    </div>

    <div v-else class="panel table">
      <div class="row head" aria-hidden="true">
        <span>Date</span><span>Car</span><span>Problem</span><span>Range</span><span>Confidence</span><span />
      </div>
      <div v-for="e in estimates" :key="e.id" class="row">
        <span class="muted date">{{ formatDate(e.created_at) }}</span>
        <b class="car">{{ e.vehicle_label.replace('Toyota ', '') }}</b>
        <NuxtLink :to="`/history/${e.id}`" class="problem">{{ e.problem_text }}</NuxtLink>
        <span class="mono range">{{ formatTaka(e.total_min) }}–{{ formatTaka(e.total_max).replace('৳', '') }}</span>
        <span class="conf"><span class="tag" :class="e.confidence">{{ CONFIDENCE_TEXT[e.confidence].replace(' confidence', '') }}</span></span>
        <span class="actions">
          <button type="button" class="btn btn-icon danger" :aria-label="`Delete estimate from ${formatDate(e.created_at)}`" @click="deleting = e">
            <AppIcon name="trash" :size="16" />
          </button>
          <NuxtLink :to="`/history/${e.id}`" class="btn btn-icon" aria-label="Open estimate">
            <AppIcon name="chevronRight" :size="18" :stroke="2" />
          </NuxtLink>
        </span>
      </div>
    </div>

    <nav v-if="pages > 1" class="pager" aria-label="Pages">
      <button class="btn" type="button" :disabled="page <= 1" @click="setQuery({ page: String(page - 1) })">Newer</button>
      <span class="small muted">Page {{ page }} of {{ pages }}</span>
      <button class="btn" type="button" :disabled="page >= pages" @click="setQuery({ page: String(page + 1) })">Older</button>
    </nav>

    <ConfirmDialog
      v-if="deleting"
      title="Delete this estimate?"
      :text="`The ${deleting.vehicle_label} estimate from ${formatDate(deleting.created_at)} will be removed. This cannot be undone.`"
      :busy="busy"
      :error="deleteError"
      @confirm="confirmDelete"
      @cancel="deleting = null; deleteError = ''"
    />
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 24px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  margin-bottom: 24px;
}

.filters .field {
  min-width: 180px;
}

.filters .input {
  height: 44px;
  font-size: 15px;
}

.sort {
  display: flex;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 3px;
  gap: 3px;
  margin-left: auto;
}

.sort button {
  border: 0;
  background: none;
  padding: 9px 14px;
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.sort button.on {
  background: var(--ink);
  color: #fff;
}

.table {
  padding: 0;
  overflow: hidden;
}

.row {
  display: grid;
  grid-template-columns: 120px 140px minmax(0, 1fr) 190px 110px 88px;
  gap: 16px;
  padding: 14px 24px;
  align-items: center;
  border-bottom: 1px solid var(--line);
  font-size: 15px;
}

.row:last-child {
  border-bottom: 0;
}

.row:not(.head):hover {
  background: var(--hover-row);
}

.row.head {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-soft);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.car {
  font-weight: 600;
}

.problem {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conf .tag {
  justify-self: start;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 2px;
}

.actions .btn-icon {
  width: 40px;
  height: 40px;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

@media (max-width: 900px) {
  .row.head {
    display: none;
  }

  .row {
    grid-template-columns: 1fr auto;
    gap: 4px 12px;
    padding: 16px;
  }

  .date {
    grid-column: 1;
    font-size: 14px;
  }

  .car {
    grid-column: 1;
  }

  .problem {
    grid-column: 1 / -1;
  }

  .range {
    grid-column: 1;
  }

  .conf {
    grid-column: 2;
    grid-row: 1;
  }

  .actions {
    grid-column: 2;
    grid-row: 4;
  }

  .sort {
    margin-left: 0;
  }
}
</style>
