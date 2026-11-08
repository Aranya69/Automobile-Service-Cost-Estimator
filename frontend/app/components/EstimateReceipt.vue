<script setup lang="ts">
const props = defineProps<{ estimate: EstimateDetail }>()

// Group the lines by repair job, keeping the order the estimator returned.
const groups = computed(() => {
  const byJob = new Map<string, EstimateItem[]>()
  for (const item of props.estimate.items) {
    if (!byJob.has(item.job_code)) byJob.set(item.job_code, [])
    byJob.get(item.job_code)!.push(item)
  }
  const names = new Map((props.estimate.jobs ?? []).map((j) => [j.code, j]))
  return [...byJob.entries()].map(([code, items]) => ({
    code,
    title: names.get(code)?.name_en ?? jobNameFromLabour(items) ?? code,
    titleBn: names.get(code)?.name_bn ?? '',
    items,
  }))
})

// Saved estimates have no job list; the labour line reads "Labour: <job name> (1.5 h)".
function jobNameFromLabour(items: EstimateItem[]) {
  const labour = items.find((i) => i.kind === 'labour')
  return labour?.description.replace(/^Labour: /, '').replace(/ \([\d.]+ h\)$/, '')
}

const hasLikely = computed(() => props.estimate.items.some((i) => i.price_likely != null))

function qty(item: EstimateItem) {
  return item.kind === 'labour' ? `${item.quantity} h` : `× ${item.quantity}`
}
</script>

<template>
  <article class="receipt">
    <header class="receipt-head">
      <div>
        <p class="label">Estimate for</p>
        <h2>{{ estimate.vehicle_label }}</h2>
        <p class="meta small">
          {{ tierLabel(estimate.garage_tier) }} · {{ formatDate(estimate.created_at) }}
          <template v-if="estimate.method === 'manual'"> · jobs chosen by hand</template>
        </p>
      </div>
      <span class="tag" :class="`conf-${estimate.confidence}`">
        {{ CONFIDENCE_TEXT[estimate.confidence] }}
      </span>
    </header>

    <section class="totals">
      <div>
        <p class="label">Likely cost</p>
        <p class="likely mono">{{ formatTaka(estimate.total_likely) }}</p>
      </div>
      <div class="range">
        <p class="label">Range</p>
        <p class="mono">{{ formatTaka(estimate.total_min) }} – {{ formatTaka(estimate.total_max) }}</p>
      </div>
    </section>

    <div v-if="estimate.warnings.length" class="warnings">
      <p v-for="(w, i) in estimate.warnings" :key="i" class="alert alert-warn">{{ w }}</p>
    </div>

    <p class="problem small">
      <span class="label">Problem:</span> “{{ estimate.problem_text }}”
    </p>
    <p v-if="estimate.explanation" class="explanation">{{ estimate.explanation }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th class="num">Qty</th>
            <th class="num">Min</th>
            <th v-if="hasLikely" class="num">Likely</th>
            <th class="num">Max</th>
          </tr>
        </thead>
        <tbody v-for="group in groups" :key="group.code">
          <tr class="job-row">
            <td :colspan="hasLikely ? 5 : 4">
              <strong>{{ group.title }}</strong>
              <span v-if="group.titleBn" class="bn"> · {{ group.titleBn }}</span>
            </td>
          </tr>
          <tr v-for="item in group.items" :key="item.id" :class="{ missing: item.price_min === null }">
            <td class="item-name">
              {{ item.kind === 'labour' ? 'Labour' : item.description }}
              <span v-if="item.kind === 'part' && item.price_count" class="count small">
                {{ item.price_count }} price{{ item.price_count === 1 ? '' : 's' }}
              </span>
              <span v-if="item.price_min === null" class="count small">no price data</span>
            </td>
            <td class="num">{{ qty(item) }}</td>
            <td class="num">{{ formatTaka(item.price_min) }}</td>
            <td v-if="hasLikely" class="num">{{ formatTaka(item.price_likely) }}</td>
            <td class="num">{{ formatTaka(item.price_max) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="2"><strong>Total</strong></td>
            <td class="num">{{ formatTaka(estimate.total_min) }}</td>
            <td v-if="hasLikely" class="num">{{ formatTaka(estimate.total_likely) }}</td>
            <td class="num">{{ formatTaka(estimate.total_max) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>

    <p class="fine small muted">
      Parts prices come from market listings and garage price sheets for this model. Labour is
      standard hours × the hourly rate for the garage type. The final bill depends on the
      garage and what they find.
    </p>
  </article>
</template>

<style scoped>
.receipt {
  background: var(--surface);
  border: 1px solid var(--line);
  border-top: 4px solid var(--red-500);
  border-radius: var(--radius);
  padding: 24px;
}

.receipt-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.receipt-head h2 {
  margin: 0;
}

.label {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-soft);
}

.meta {
  margin: 2px 0 0;
  color: var(--ink-soft);
}

.conf-high { background: var(--ok-bg); color: var(--ok); }
.conf-medium { background: var(--warn-bg); color: var(--warn); }
.conf-low { background: var(--red-100); color: var(--red-700); }
.conf-insufficient { background: var(--red-100); color: var(--red-700); }

.totals {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 48px;
  margin: 20px 0;
  padding: 16px 0;
  border-top: 1px dashed var(--line-strong);
  border-bottom: 1px dashed var(--line-strong);
}

.totals p {
  margin: 0;
}

.likely {
  font-size: 2rem;
  font-weight: 500;
  color: var(--red-700);
  line-height: 1.1;
}

.range .mono {
  font-size: 1.15rem;
  margin-top: 6px;
}

.warnings {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.warnings .alert {
  margin: 0;
}

.problem {
  margin-bottom: 6px;
}

.problem .label {
  display: inline;
}

.explanation {
  margin-bottom: 16px;
}

.job-row td {
  background: var(--red-50);
  border-bottom-color: var(--line);
  padding-top: 8px;
  padding-bottom: 8px;
}

.bn {
  color: var(--ink-soft);
  font-weight: 400;
}

.item-name {
  padding-left: 20px;
}

.count {
  display: block;
  color: var(--ink-soft);
}

tr.missing td {
  color: var(--red-700);
}

tfoot td {
  border-top: 2px solid var(--ink);
  border-bottom: 0;
  font-weight: 600;
}

.fine {
  margin: 16px 0 0;
}

@media (max-width: 600px) {
  .receipt {
    padding: 16px;
  }

  .likely {
    font-size: 1.6rem;
  }

  th,
  td {
    padding: 8px 6px;
  }

  .item-name {
    padding-left: 10px;
  }
}
</style>
