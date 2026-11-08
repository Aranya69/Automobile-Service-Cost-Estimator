<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

const props = defineProps<{
  title: string
  initial?: VehicleInput
  submitLabel: string
  // Pre-fill model and year from what the visitor typed on the landing page.
  fromDraft?: boolean
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

onMounted(() => {
  if (!props.fromDraft || props.initial) return
  const draft = useDraft().load()
  if (draft && options.value?.models.some((m) => m.name === draft.model)) {
    form.model = draft.model
    form.year = draft.year
  }
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
    errors.odometer_km = 'Enter numbers only, for example 84200.'
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
  <form class="sheet" novalidate @submit.prevent="submit">
    <div class="sheet-head">
      <b>{{ title }}</b>
      <NuxtLink to="/vehicles" class="btn btn-icon" aria-label="Close"><AppIcon name="close" :stroke="2" /></NuxtLink>
    </div>

    <div class="sheet-body">
      <p v-if="formError" class="alert alert-error" role="alert">
        <AppIcon name="info" :size="18" :stroke="2" />{{ formError }}
      </p>

      <fieldset class="field">
        <legend>Model</legend>
        <div class="models">
          <button
            v-for="m in options?.models"
            :key="m.name"
            type="button"
            class="model"
            :class="{ on: form.model === m.name }"
            :aria-pressed="form.model === m.name"
            @click="form.model = m.name"
          >
            <CarArt :van="m.name === 'Noah'" class="model-art" />
            {{ m.name }}
          </button>
        </div>
        <span v-if="fieldErrors.model" class="field-error">
          <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.model }}
        </span>
      </fieldset>

      <div class="form-row">
        <label class="field">
          Year
          <select v-model.number="form.year" class="input" :class="{ 'has-error': fieldErrors.year }">
            <option :value="null" disabled>Choose…</option>
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
          <span v-if="fieldErrors.year" class="field-error">
            <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.year }}
          </span>
        </label>

        <label class="field">
          Engine (cc)
          <select
            v-model.number="form.engine_cc"
            class="input"
            :class="{ 'has-error': fieldErrors.engine_cc }"
            :disabled="!form.model"
          >
            <option :value="null" disabled>{{ form.model ? 'Choose…' : 'Pick a model first' }}</option>
            <option v-for="cc in engines" :key="cc" :value="cc">{{ cc }}</option>
          </select>
          <span v-if="fieldErrors.engine_cc" class="field-error">
            <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.engine_cc }}
          </span>
        </label>
      </div>

      <label class="field">
        Odometer (km)
        <input
          v-model.number="form.odometer_km"
          class="input mono-input"
          :class="{ 'has-error': fieldErrors.odometer_km }"
          type="number"
          inputmode="numeric"
          min="0"
          step="1"
          placeholder="e.g. 84200"
        />
        <span v-if="fieldErrors.odometer_km" class="field-error">
          <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.odometer_km }}
        </span>
        <span class="hint">Check the dashboard. Older cars often need different service items.</span>
      </label>
    </div>

    <div class="sheet-foot">
      <NuxtLink to="/vehicles" class="btn">Cancel</NuxtLink>
      <button class="btn btn-primary" type="submit" :disabled="busy">
        <span v-if="busy" class="spinner" />{{ submitLabel }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.sheet {
  background: var(--card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  max-width: 560px;
  display: flex;
  flex-direction: column;
}

.sheet-head {
  padding: 16px 16px 16px 24px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sheet-head b {
  font-family: var(--font-head);
  font-size: 22px;
}

.sheet-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sheet-foot {
  padding: 16px 24px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

fieldset {
  border: 0;
  margin: 0;
  padding: 0;
}

legend {
  margin-bottom: 8px;
}

.models {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 8px;
}

.model {
  border: 1.5px solid var(--line);
  background: var(--card);
  border-radius: var(--radius);
  padding: 12px 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font: inherit;
  font-size: 15px;
  font-weight: 600;
}

.model:hover {
  border-color: var(--ink);
}

.model.on {
  border-color: var(--signal);
  background: var(--signal-soft);
}

.model-art {
  width: 64px;
  height: auto;
}

.mono-input {
  font-family: var(--font-mono);
}
</style>
