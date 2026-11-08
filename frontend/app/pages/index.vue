<script setup lang="ts">
const { user } = useAuth()
const api = useApi()

// Only fetched for logged-in visitors; the landing page needs no data.
const { data: dash } = await useAsyncData(
  'dashboard',
  async () => {
    if (!user.value) return null
    const [cars, recent] = await Promise.all([
      api.get<{ vehicles: Vehicle[] }>('/vehicles'),
      api.get<{ estimates: EstimateSummary[]; total: number }>('/estimates?per_page=3'),
    ])
    return { vehicles: cars.vehicles, recent: recent.estimates, total: recent.total }
  },
  { watch: [user] },
)

const firstName = computed(() => user.value?.name.split(' ')[0] ?? '')
</script>

<template>
  <!-- Logged in: dashboard -->
  <div v-if="user" class="page">
    <div class="page-head">
      <div>
        <h1>Hello, {{ firstName }}</h1>
        <p class="lead">What is the car doing today?</p>
      </div>
      <NuxtLink to="/estimate" class="btn btn-primary">New estimate</NuxtLink>
    </div>

    <div v-if="dash && !dash.vehicles.length" class="panel start">
      <h2>Start by adding your car</h2>
      <p class="muted">Prices differ between an Axio and a Noah, so we need to know which one you drive.</p>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">Add a car</NuxtLink>
    </div>

    <div v-else-if="dash" class="grid">
      <section class="panel">
        <div class="section-head">
          <h2>Recent estimates</h2>
          <NuxtLink v-if="dash.total" to="/history" class="small">See all {{ dash.total }}</NuxtLink>
        </div>
        <p v-if="!dash.recent.length" class="muted">No estimates yet.</p>
        <ul v-else class="list">
          <li v-for="e in dash.recent" :key="e.id">
            <NuxtLink :to="`/history/${e.id}`">
              <span class="problem">“{{ e.problem_text }}”</span>
              <span class="small muted">{{ e.vehicle_label }} · {{ formatDate(e.created_at) }}</span>
            </NuxtLink>
            <span class="mono amount">{{ formatTaka(e.total_likely) }}</span>
          </li>
        </ul>
      </section>

      <section class="panel">
        <div class="section-head">
          <h2>My cars</h2>
          <NuxtLink to="/vehicles" class="small">Manage</NuxtLink>
        </div>
        <ul class="list">
          <li v-for="car in dash.vehicles" :key="car.id">
            <span>
              <strong>{{ car.model }}</strong> {{ car.year }}
              <span class="small muted">· {{ formatKm(car.odometer_km) }}</span>
            </span>
            <NuxtLink :to="`/estimate?vehicle=${car.id}`" class="small">Estimate</NuxtLink>
          </li>
        </ul>
      </section>
    </div>
  </div>

  <!-- Visitors: landing -->
  <div v-else class="page">
    <section class="intro">
      <p class="eyebrow">For Toyota Axio, Premio, Allion, Corolla and Noah</p>
      <h1>Know the repair bill before you reach the garage.</h1>
      <p class="lead">
        Describe the problem in Bangla, Banglish or English. ASCE picks the likely repair jobs and
        prices them from parts market and garage data, in taka.
      </p>
      <div class="actions">
        <NuxtLink to="/register" class="btn btn-primary">Create an account</NuxtLink>
        <NuxtLink to="/login" class="btn">I already have one</NuxtLink>
      </div>
    </section>

    <ol class="steps">
      <li>
        <strong>Add your car</strong>
        <span>Model, year and odometer reading.</span>
      </li>
      <li>
        <strong>Describe the problem</strong>
        <span>"brake e awaj kore", "AC thanda hoy na", or plain English.</span>
      </li>
      <li>
        <strong>Get a range</strong>
        <span>Minimum, likely and maximum cost, part by part.</span>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.intro {
  max-width: 640px;
  padding: 24px 0 8px;
}

.eyebrow {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--red-600);
  margin-bottom: 8px;
}

.intro h1 {
  font-size: 2.1rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.steps {
  list-style: none;
  counter-reset: step;
  padding: 0;
  margin: 40px 0 0;
  display: grid;
  gap: 0;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  border-top: 1px solid var(--line);
}

.steps li {
  counter-increment: step;
  padding: 18px 16px 18px 0;
  display: grid;
  gap: 2px;
}

.steps li::before {
  content: counter(step, decimal-leading-zero);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--red-500);
}

.steps span {
  color: var(--ink-soft);
  font-size: 0.95rem;
}

.start {
  max-width: 560px;
}

.grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 16px;
  align-items: start;
}

.grid .panel + .panel {
  margin-top: 0;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}

.section-head h2 {
  margin: 0;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}

.list li:last-child {
  border-bottom: 0;
}

.list a:not(.small) {
  display: grid;
  min-width: 0;
  color: var(--ink);
  text-decoration: none;
}

.list a:not(.small):hover .problem {
  color: var(--red-700);
}

.problem {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.amount {
  color: var(--red-700);
  white-space: nowrap;
}

@media (max-width: 760px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .intro h1 {
    font-size: 1.6rem;
  }
}
</style>
