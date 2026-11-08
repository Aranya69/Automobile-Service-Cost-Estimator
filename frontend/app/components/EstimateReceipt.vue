<script setup lang="ts">
// The estimate as a garage job card.
const props = defineProps<{ estimate: EstimateDetail }>()

// Saved estimates have no job list; the labour line reads "Labour: <job name> (1.5 h)".
function jobNameFromLabour(item: EstimateItem) {
  return item.description.replace(/^Labour: /, '').replace(/ \([\d.]+ h\)$/, '')
}

const jobNames = computed(() => {
  if (props.estimate.jobs?.length) return props.estimate.jobs.map((j) => j.name_en)
  return props.estimate.items.filter((i) => i.kind === 'labour').map(jobNameFromLabour)
})

const lines = computed(() =>
  props.estimate.items.map((item) => ({
    ...item,
    name: item.kind === 'labour' ? `Labour · ${jobNameFromLabour(item)}` : item.description,
    detail: item.kind === 'labour' ? `${item.quantity} h` : `× ${item.quantity}`,
    missing: item.price_min === null,
  })),
)

function sum(kind: 'part' | 'labour', key: 'price_min' | 'price_max') {
  return props.estimate.items
    .filter((i) => i.kind === kind && i[key] !== null)
    .reduce((total, i) => total + (i[key] as number), 0)
}

const split = computed(() => {
  const parts = { min: sum('part', 'price_min'), max: sum('part', 'price_max') }
  const labour = { min: sum('labour', 'price_min'), max: sum('labour', 'price_max') }
  const mid = (r: { min: number; max: number }) => (r.min + r.max) / 2
  const total = mid(parts) + mid(labour)
  return { parts, labour, partsShare: total ? Math.round((100 * mid(parts)) / total) : 0 }
})

// Where "likely" sits between the lowest and highest total, for the marker.
const likelyAt = computed(() => {
  const { total_min: lo, total_max: hi, total_likely: likely } = props.estimate
  if (hi <= lo) return 50
  return Math.min(100, Math.max(0, ((likely - lo) / (hi - lo)) * 100))
})

const safetyWarnings = computed(() =>
  props.estimate.warnings.filter((w) => !w.startsWith('Not enough price data')),
)
const dataWarnings = computed(() =>
  props.estimate.warnings.filter((w) => w.startsWith('Not enough price data')),
)

// "Got a quote from the garage?"
const quote = ref<number | null>(null)
const verdict = computed(() => {
  const q = quote.value
  if (!q || q <= 0) return null
  const { total_min: lo, total_max: hi } = props.estimate
  if (q < lo) return { cls: 'medium', text: 'Below usual range – ask what is included' }
  if (q <= hi) return { cls: 'high', text: 'Within usual range' }
  if (q <= hi * 1.25) return { cls: 'medium', text: 'Above usual range – ask why' }
  return { cls: 'low', text: 'Well above usual range – get a second quote' }
})
</script>

<template>
  <div class="receipt-stack">
    <article class="panel ticket job-card">
      <header class="meta">
        <div>
          <div class="muted">Car</div>
          <div class="meta-value">{{ estimate.vehicle_label }}</div>
        </div>
        <div>
          <div class="muted">Garage type</div>
          <div class="meta-value">{{ tierLabel(estimate.garage_tier) }}</div>
        </div>
        <div>
          <div class="muted">Date</div>
          <div class="meta-value">{{ formatDate(estimate.created_at) }}</div>
        </div>
        <div>
          <div class="muted">Estimate no.</div>
          <div class="meta-value mono">{{ estimateNo(estimate.id) }}</div>
        </div>
      </header>

      <section class="block total">
        <div class="total-top">
          <div>
            <div class="muted">{{ jobNames.join(' + ') || 'Repair' }} · estimated total</div>
            <div class="range mono">{{ formatTaka(estimate.total_min) }} – {{ formatTaka(estimate.total_max) }}</div>
            <div class="likely">Most likely <b class="mono">{{ formatTaka(estimate.total_likely) }}</b></div>
          </div>
          <div class="conf">
            <span class="tag" :class="estimate.confidence">
              <span class="dot" />{{ CONFIDENCE_TEXT[estimate.confidence] }}
            </span>
            <span class="small muted">{{ CONFIDENCE_NOTE[estimate.confidence] }}</span>
          </div>
        </div>

        <div class="range-bar" :style="{ '--at': `${likelyAt}%` }">
          <span class="marker" />
        </div>
        <div class="range-labels mono">
          <span>{{ formatTaka(estimate.total_min) }}<small>Lowest</small></span>
          <span class="mid">{{ formatTaka(estimate.total_likely) }}<small>Likely</small></span>
          <span class="end">{{ formatTaka(estimate.total_max) }}<small>Highest</small></span>
        </div>

        <div v-for="(w, i) in safetyWarnings" :key="`s${i}`" class="alert alert-safety" role="alert">
          <AppIcon name="warning" :size="22" :stroke="2" class="alert-icon" />
          <span>{{ w }}</span>
        </div>
        <p v-for="(w, i) in dataWarnings" :key="`d${i}`" class="alert alert-warn">
          <AppIcon name="info" :size="18" :stroke="2" />{{ w }}
        </p>
      </section>

      <section v-if="estimate.explanation" class="block">
        <h3>What this means</h3>
        <p class="explanation">{{ estimate.explanation }}</p>
        <p class="small muted problem">You wrote: “{{ estimate.problem_text }}”</p>
      </section>

      <section class="block">
        <h3>Itemised estimate</h3>
        <div v-for="line in lines" :key="line.id" class="line" :class="{ missing: line.missing }">
          <div class="line-main">
            <span class="line-name">{{ line.name }}</span>
            <span class="line-meta small">
              <span class="kind"><i :class="line.kind" />{{ line.kind === 'part' ? 'Parts' : 'Labour' }}</span>
              <span class="pill">{{ line.detail }}</span>
            </span>
          </div>
          <div class="line-price">
            <span v-if="line.missing" class="mono">No data</span>
            <span v-else class="mono">{{ formatTaka(line.price_min) }} – {{ formatTaka(line.price_max) }}</span>
            <span class="small" :class="line.missing ? 'warn-text' : 'muted'">
              <template v-if="line.missing">Ask the garage for 2 quotes</template>
              <template v-else-if="line.kind === 'part'">
                {{ line.price_count }} price{{ line.price_count === 1 ? '' : 's' }}
              </template>
              <template v-else>Standard hours × rate</template>
            </span>
          </div>
        </div>

        <div class="split">
          <div class="split-bar">
            <span class="parts" :style="{ width: `${split.partsShare}%` }" />
          </div>
          <div class="split-legend small">
            <span><i class="part" />Parts <b class="mono">{{ formatTaka(split.parts.min) }}–{{ formatTaka(split.parts.max).replace('৳', '') }}</b></span>
            <span><i class="labour" />Labour <b class="mono">{{ formatTaka(split.labour.min) }}–{{ formatTaka(split.labour.max).replace('৳', '') }}</b></span>
          </div>
        </div>
      </section>
    </article>

    <div class="panel-flat quote no-print">
      <label for="quote" class="quote-label">Got a quote from the garage?</label>
      <div class="quote-input">
        <span class="mono">৳</span>
        <input id="quote" v-model.number="quote" type="number" inputmode="numeric" min="0" placeholder="8500" />
      </div>
      <span v-if="verdict" class="tag" :class="verdict.cls">{{ verdict.text }}</span>
    </div>
  </div>
</template>

<style scoped>
.receipt-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.job-card {
  padding: 10px 0 0;
}

.meta {
  padding: 24px 32px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  border-bottom: 1.5px dashed var(--line);
  font-size: 14px;
}

.meta-value {
  font-weight: 700;
  font-size: 16px;
}

.block {
  padding: 28px 32px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.block + .block {
  border-top: 1.5px dashed var(--line);
}

.block h3 {
  margin: 0;
}

.total-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.range {
  font-size: clamp(30px, 5vw, 44px);
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin-top: 4px;
}

.likely {
  margin-top: 6px;
}

.conf {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.conf .tag {
  font-size: 14px;
  padding: 5px 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.range-bar {
  position: relative;
  height: 12px;
  margin-top: 16px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--signal-soft), var(--signal) var(--at), var(--signal-soft));
}

.marker {
  position: absolute;
  left: var(--at);
  top: -8px;
  width: 4px;
  height: 28px;
  border-radius: 2px;
  background: var(--ink);
  transform: translateX(-2px);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  margin-top: 4px;
}

.range-labels small {
  display: block;
  font-family: var(--font-body);
  font-weight: 400;
  color: var(--ink-soft);
  font-size: 13px;
}

.range-labels .mid {
  text-align: center;
}

.range-labels .end {
  text-align: right;
}

.alert-icon {
  color: var(--alert);
  flex: none;
}

.explanation {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
}

.problem {
  margin: 0;
}

.line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 4px 16px;
  padding: 16px 0;
  border-bottom: 1.5px dashed var(--line);
}

.line-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.line-name {
  font-size: 16px;
  font-weight: 600;
}

.line-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--ink-soft);
}

.kind {
  display: flex;
  align-items: center;
  gap: 6px;
}

.kind i,
.split-legend i {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

i.part {
  background: var(--parts);
}

i.labour {
  background: var(--labour);
}

.pill {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0 8px;
}

.line-price {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.line-price .mono {
  font-size: 16px;
}

.line.missing .line-name,
.line.missing .line-price .mono,
.warn-text {
  color: var(--alert);
}

.split {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.split-bar {
  display: flex;
  height: 14px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--labour);
}

.split-bar .parts {
  background: var(--parts);
}

.split-legend {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.split-legend span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quote {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 20px;
}

.quote-label {
  font-weight: 600;
  font-size: 16px;
}

.quote-input {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 44px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
}

.quote-input input {
  border: 0;
  outline: none;
  width: 120px;
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 700;
  background: transparent;
}

.quote .tag {
  font-size: 14px;
  padding: 6px 14px;
}

@media (max-width: 600px) {
  .meta,
  .block {
    padding-left: 18px;
    padding-right: 18px;
  }

  .conf {
    align-items: flex-start;
  }
}
</style>
