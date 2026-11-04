<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

const props = defineProps<{
  initial?: VehicleInput
  submitLabel: string
  save: (input: VehicleInput) => Promise<void>
}>()

const api = useApi()
const { data: options } = await useAsyncData('vehicle-options', () =>
  api.get<VehicleOptions>('/vehicles/options'),
)

const form = reactive<VehicleInput>({
  model: props.initial?.model ?? '',
  year: props.initial?.year ?? null,
  engine_cc: props.initial?.engine_cc ?? null,
  odometer_km: props.initial?.odometer_km ?? null,
})

const fieldErrors = ref<Record<string, string>>({})
const formError = ref('')
const busy = ref(false)

const engines = computed(
  () => options.value?.models.find((m) => m.name === form.model)?.engines ?? [],
)

const years = computed(() => {
  if (!options.value) return []
  const list: number[] = []
  for (let y = options.value.last_year; y >= options.value.first_year; y--) list.push(y)
  return list
})

// Picking another model can make the chosen engine size impossible.
watch(
  () => form.model,
  () => {
    if (form.engine_cc && !engines.value.includes(form.engine_cc)) form.engine_cc = null
    if (engines.value.length === 1) form.engine_cc = engines.value[0]!
  },
)

function localErrors() {
  const errors: Record<string, string> = {}
  const max = options.value?.odometer_max ?? 999999
  if (!form.model) errors.model = 'Choose a model.'
  if (!form.year) errors.year = 'Choose the year.'
  if (!form.engine_cc) errors.engine_cc = 'Choose the engine size.'
  const km = form.odometer_km
  if (km === null || Number.isNaN(km) || !Number.isInteger(km) || km < 0 || km > max) {
    errors.odometer_km = `Enter a whole number from 0 to ${max.toLocaleString('en-IN')}.`
  }
  return errors
}

async function submit() {
  formError.value = ''
  fieldErrors.value = localErrors()
  if (Object.keys(fieldErrors.value).length) return

  busy.value = true
  try {
    await props.save({ ...form })
  } catch (err) {
    if (err instanceof ApiError) {
      formError.value = err.message
      fieldErrors.value = err.fields
    } else {
      formError.value = 'Could not save the car. Please try again.'
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="panel form" novalidate @submit.prevent="submit">
    <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>

    <div class="form-row">
      <div class="field">
        <label for="model">Model</label>
        <select id="model" v-model="form.model" class="input" :class="{ 'has-error': fieldErrors.model }">
          <option value="" disabled>Choose…</option>
          <option v-for="m in options?.models" :key="m.name" :value="m.name">
            {{ options?.make }} {{ m.name }}
          </option>
        </select>
        <span v-if="fieldErrors.model" class="field-error">{{ fieldErrors.model }}</span>
      </div>

      <div class="field">
        <label for="year">Year</label>
        <select id="year" v-model.number="form.year" class="input" :class="{ 'has-error': fieldErrors.year }">
          <option :value="null" disabled>Choose…</option>
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <span v-if="fieldErrors.year" class="field-error">{{ fieldErrors.year }}</span>
      </div>
    </div>

    <div class="form-row">
      <div class="field">
        <label for="engine">Engine</label>
        <select
          id="engine"
          v-model.number="form.engine_cc"
          class="input"
          :class="{ 'has-error': fieldErrors.engine_cc }"
          :disabled="!form.model"
        >
          <option :value="null" disabled>{{ form.model ? 'Choose…' : 'Pick a model first' }}</option>
          <option v-for="cc in engines" :key="cc" :value="cc">{{ cc }} cc ({{ formatCc(cc) }})</option>
        </select>
        <span v-if="fieldErrors.engine_cc" class="field-error">{{ fieldErrors.engine_cc }}</span>
      </div>

      <div class="field">
        <label for="odometer">Odometer</label>
        <div class="with-unit">
          <input
            id="odometer"
            v-model.number="form.odometer_km"
            class="input"
            :class="{ 'has-error': fieldErrors.odometer_km }"
            type="number"
            inputmode="numeric"
            min="0"
            step="1"
            placeholder="e.g. 85000"
          />
          <span class="unit">km</span>
        </div>
        <span v-if="fieldErrors.odometer_km" class="field-error">{{ fieldErrors.odometer_km }}</span>
      </div>
    </div>

    <div class="buttons">
      <button class="btn btn-primary" type="submit" :disabled="busy">
        {{ busy ? 'Saving…' : submitLabel }}
      </button>
      <NuxtLink to="/vehicles" class="btn btn-quiet">Cancel</NuxtLink>
    </div>
  </form>
</template>

<style scoped>
.with-unit {
  position: relative;
}

.with-unit .input {
  padding-right: 44px;
}

.unit {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-soft);
  font-size: 0.9rem;
  pointer-events: none;
}

.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
