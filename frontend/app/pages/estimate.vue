<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'New estimate · ASCE' })

type Step = 'describe' | 'question' | 'manual' | 'result'

interface Turn {
  question: string
  answer: string
}

const route = useRoute()
const api = useApi()

const { data: vehicleData } = await useAsyncData('estimate-vehicles', () =>
  api.get<{ vehicles: Vehicle[] }>('/vehicles'),
)
const vehicles = computed(() => vehicleData.value?.vehicles ?? [])

const requested = Number(route.query.vehicle)
const form = reactive({
  vehicle_id: vehicles.value.find((v) => v.id === requested)?.id ?? vehicles.value[0]?.id ?? null,
  garage_tier: 'workshop' as GarageTier,
  problem_text: '',
})

const step = ref<Step>('describe')
const turns = ref<Turn[]>([])
const pendingQuestion = ref('')
const maxQuestions = ref(3)
const answer = ref('')
const notice = ref('')
const formError = ref('')
const fieldErrors = ref<Record<string, string>>({})
const busy = ref(false)
const result = ref<EstimateDetail | null>(null)

// Manual job choice
const jobs = ref<JobOption[]>([])
const chosen = ref<string[]>([])

const EXAMPLES = ['brake chaple awaj kore', 'AC thanda hoy na', 'ইঞ্জিন গরম হয়ে যায়', 'khot khot sound over speed breakers']

const selectedVehicle = computed(() => vehicles.value.find((v) => v.id === form.vehicle_id))

function resetMessages() {
  formError.value = ''
  fieldErrors.value = {}
}

async function openManual(suggested: string[], message: string) {
  notice.value = message
  if (!jobs.value.length) {
    const res = await api.get<{ jobs: JobOption[] }>('/estimates/jobs')
    jobs.value = res.jobs
  }
  chosen.value = [...suggested]
  step.value = 'manual'
}

async function send(extra: Record<string, unknown> = {}) {
  resetMessages()
  busy.value = true
  try {
    const res = await api.post<any>('/estimates', {
      vehicle_id: form.vehicle_id,
      garage_tier: form.garage_tier,
      problem_text: form.problem_text,
      answers: turns.value,
      ...extra,
    })

    if (res.status === 'question') {
      pendingQuestion.value = res.question
      maxQuestions.value = res.max_questions
      answer.value = ''
      step.value = 'question'
    } else if (res.status === 'no_match') {
      await openManual(res.suggested ?? [], res.explanation)
    } else {
      result.value = res.estimate
      step.value = 'result'
    }
  } catch (err) {
    if (err instanceof ApiError && err.data?.status === 'ai_unavailable') {
      await openManual(err.data.suggested ?? [], err.message)
    } else if (err instanceof ApiError) {
      formError.value = err.message
      fieldErrors.value = err.fields
    } else {
      formError.value = 'Something went wrong. Please try again.'
    }
  } finally {
    busy.value = false
  }
}

function start() {
  if (!form.problem_text.trim()) {
    fieldErrors.value = { problem_text: 'Describe what is wrong with the car.' }
    return
  }
  turns.value = []
  send()
}

function reply() {
  if (!answer.value.trim()) return
  turns.value = [...turns.value, { question: pendingQuestion.value, answer: answer.value.trim() }]
  pendingQuestion.value = ''
  send()
}

function submitManual() {
  if (!chosen.value.length) {
    formError.value = 'Tick at least one repair job.'
    return
  }
  send({ job_codes: chosen.value })
}

function startOver() {
  step.value = 'describe'
  turns.value = []
  pendingQuestion.value = ''
  result.value = null
  notice.value = ''
  resetMessages()
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>New estimate</h1>
        <p class="lead">Describe the problem the way you would tell a mechanic.</p>
      </div>
      <button v-if="step !== 'describe'" class="btn" type="button" @click="startOver">
        Start over
      </button>
    </div>

    <!-- No cars yet -->
    <div v-if="!vehicles.length" class="panel empty">
      <p>Add your car first, so the estimate uses the right parts prices.</p>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">Add a car</NuxtLink>
    </div>

    <template v-else>
      <!-- Step 1: describe -->
      <form v-if="step === 'describe'" class="panel form" novalidate @submit.prevent="start">
        <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>

        <div class="form-row">
          <div class="field">
            <label for="vehicle">Car</label>
            <select id="vehicle" v-model.number="form.vehicle_id" class="input">
              <option v-for="v in vehicles" :key="v.id" :value="v.id">
                {{ v.label }} · {{ formatKm(v.odometer_km) }}
              </option>
            </select>
          </div>
        </div>

        <fieldset class="field tiers">
          <legend>Where will you get it fixed?</legend>
          <label v-for="t in GARAGE_TIERS" :key="t.value" class="tier" :class="{ on: form.garage_tier === t.value }">
            <input v-model="form.garage_tier" type="radio" name="tier" :value="t.value" />
            <span>
              <strong>{{ t.label }}</strong>
              <span class="small muted">{{ t.hint }}</span>
            </span>
          </label>
        </fieldset>

        <div class="field">
          <label for="problem">What is wrong?</label>
          <textarea
            id="problem"
            v-model="form.problem_text"
            class="input"
            :class="{ 'has-error': fieldErrors.problem_text }"
            maxlength="1000"
            placeholder="Bangla, Banglish or English. For example: brake chaple samner chaka theke awaj ase"
          />
          <span v-if="fieldErrors.problem_text" class="field-error">{{ fieldErrors.problem_text }}</span>
          <div class="examples small">
            <span class="muted">Try:</span>
            <button
              v-for="ex in EXAMPLES"
              :key="ex"
              type="button"
              class="chip"
              @click="form.problem_text = ex"
            >
              {{ ex }}
            </button>
          </div>
        </div>

        <div>
          <button class="btn btn-primary" type="submit" :disabled="busy">
            {{ busy ? 'Thinking…' : 'Get estimate' }}
          </button>
        </div>
      </form>

      <!-- Step 2: clarifying questions -->
      <div v-else-if="step === 'question'" class="panel chat">
        <p class="label small muted">{{ selectedVehicle?.label }}</p>
        <p class="bubble you">{{ form.problem_text }}</p>
        <template v-for="(t, i) in turns" :key="i">
          <p class="bubble asce">{{ t.question }}</p>
          <p class="bubble you">{{ t.answer }}</p>
        </template>
        <p class="bubble asce">{{ pendingQuestion }}</p>

        <form class="answer" @submit.prevent="reply">
          <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>
          <label for="answer" class="small muted">
            Question {{ turns.length + 1 }} of up to {{ maxQuestions }}
          </label>
          <div class="answer-row">
            <input id="answer" v-model="answer" class="input" maxlength="300" autocomplete="off" />
            <button class="btn btn-primary" type="submit" :disabled="busy || !answer.trim()">
              {{ busy ? 'Thinking…' : 'Answer' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Manual choice: AI unavailable or no match -->
      <form v-else-if="step === 'manual'" class="panel form" @submit.prevent="submitManual">
        <p v-if="notice" class="alert alert-warn">{{ notice }}</p>
        <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>
        <p class="muted">Tick the repair jobs you want priced. Suggestions are ticked already.</p>

        <div class="jobs">
          <label v-for="job in jobs" :key="job.code" class="job" :class="{ on: chosen.includes(job.code) }">
            <input v-model="chosen" type="checkbox" :value="job.code" />
            <span>
              {{ job.name_en }}
              <span class="small muted">{{ job.name_bn }}</span>
            </span>
            <span v-if="job.safety_critical" class="tag">safety</span>
          </label>
        </div>

        <div>
          <button class="btn btn-primary" type="submit" :disabled="busy">
            {{ busy ? 'Pricing…' : `Price ${chosen.length || ''} job${chosen.length === 1 ? '' : 's'}` }}
          </button>
        </div>
      </form>

      <!-- Result -->
      <div v-else-if="step === 'result' && result">
        <EstimateReceipt :estimate="result" />
        <div class="after">
          <NuxtLink :to="`/history/${result.id}`" class="btn">Saved to history</NuxtLink>
          <button class="btn btn-primary" type="button" @click="startOver">Estimate another problem</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.panel {
  max-width: 760px;
}

fieldset {
  border: 0;
  margin: 0;
  padding: 0;
}

legend {
  font-weight: 600;
  font-size: 0.925rem;
  margin-bottom: 6px;
}

.tiers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 8px;
}

.tier,
.job {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 10px 12px;
  cursor: pointer;
  background: var(--surface);
}

.tier.on,
.job.on {
  border-color: var(--red-400);
  background: var(--red-50);
}

.tier input,
.job input {
  margin-top: 5px;
  accent-color: var(--red-500);
}

.tier > span {
  display: grid;
}

.examples {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.chip {
  font: inherit;
  border: 1px solid var(--line-strong);
  background: var(--paper);
  border-radius: 999px;
  padding: 2px 10px;
  cursor: pointer;
  color: var(--ink);
}

.chip:hover {
  border-color: var(--red-400);
  color: var(--red-700);
}

.chat {
  display: grid;
  gap: 10px;
}

.bubble {
  margin: 0;
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 10px;
  white-space: pre-wrap;
}

.bubble.you {
  justify-self: end;
  background: var(--red-500);
  color: #fff;
  border-bottom-right-radius: 2px;
}

.bubble.asce {
  justify-self: start;
  background: var(--paper);
  border: 1px solid var(--line);
  border-bottom-left-radius: 2px;
}

.answer {
  margin-top: 8px;
  display: grid;
  gap: 6px;
}

.answer-row {
  display: flex;
  gap: 8px;
}

.answer-row .input {
  flex: 1;
  min-width: 0;
}

.jobs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 8px;
}

.job > span:not(.tag) {
  flex: 1;
  display: grid;
}

.after {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
</style>
