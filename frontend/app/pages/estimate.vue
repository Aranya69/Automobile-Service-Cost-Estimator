<script setup lang="ts">
import { ApiError } from '~/composables/useApi'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'New estimate · ASCE' })

type Step = 'setup' | 'problem' | 'waiting' | 'question' | 'manual'

interface Turn {
  question: string
  answer: string
}

const route = useRoute()
const api = useApi()
const draftStore = useDraft()

const { data: vehicleData } = await useAsyncData('estimate-vehicles', () =>
  api.get<{ vehicles: Vehicle[] }>('/vehicles'),
)
const vehicles = computed(() => vehicleData.value?.vehicles ?? [])

const requested = Number(route.query.vehicle)
const form = reactive({
  vehicle_id: vehicles.value.find((v) => v.id === requested)?.id ?? vehicles.value[0]?.id ?? null,
  garage_tier: 'local' as GarageTier,
  problem_text: '',
})

const step = ref<Step>(requested && form.vehicle_id === requested ? 'problem' : 'setup')
const turns = ref<Turn[]>([])
const pendingQuestion = ref('')
const maxQuestions = ref(3)
const answer = ref('')
const notice = ref('')
const formError = ref('')
const fieldErrors = ref<Record<string, string>>({})

// Manual job choice
const jobs = ref<JobOption[]>([])
const chosen = ref<string[]>([])

const CHIPS = ['ব্রেক এ আওয়াজ করে', 'AC thanda hoy na', 'Car is slow to start', 'Engine overheats']
const LOAD_STEPS = ['Reading your description', 'Matching repair jobs', 'Looking up part prices', 'Working out labour']

const selectedVehicle = computed(() => vehicles.value.find((v) => v.id === form.vehicle_id))
const carLabel = computed(() => (selectedVehicle.value ? `${selectedVehicle.value.model} ${selectedVehicle.value.year}` : '—'))

// Prefill what the visitor typed on the landing page.
onMounted(() => {
  const draft = draftStore.load()
  if (draft?.problem && !form.problem_text) form.problem_text = draft.problem
})

// Progress steps while waiting for the server (cosmetic, advances every 900 ms).
const loadIdx = ref(0)
let timer: ReturnType<typeof setInterval> | undefined
watch(step, (now) => {
  clearInterval(timer)
  if (now === 'waiting') {
    loadIdx.value = 0
    timer = setInterval(() => {
      if (loadIdx.value < LOAD_STEPS.length - 1) loadIdx.value++
    }, 900)
  }
})
onBeforeUnmount(() => clearInterval(timer))

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
  formError.value = ''
  fieldErrors.value = {}
  const returnTo = step.value
  step.value = 'waiting'
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
      draftStore.clear()
      await navigateTo(`/history/${res.estimate.id}?new=1`)
    }
  } catch (err) {
    if (err instanceof ApiError && err.data?.status === 'ai_unavailable') {
      await openManual(err.data.suggested ?? [], err.message)
      return
    }
    step.value = returnTo
    if (err instanceof ApiError) {
      formError.value = err.message
      fieldErrors.value = err.fields
    } else {
      formError.value = 'Something went wrong. Please try again.'
    }
  }
}

function sendProblem() {
  if (form.problem_text.trim().length < 5) {
    fieldErrors.value = { problem_text: 'Describe what is wrong in a few words.' }
    return
  }
  turns.value = []
  send()
}

function reply(text = answer.value) {
  if (!text.trim()) return
  turns.value = [...turns.value, { question: pendingQuestion.value, answer: text.trim() }]
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
  step.value = 'setup'
  turns.value = []
  pendingQuestion.value = ''
  notice.value = ''
  formError.value = ''
  fieldErrors.value = {}
}

const pastSetup = computed(() => step.value !== 'setup')
const pastProblem = computed(() => !['setup', 'problem'].includes(step.value))
</script>

<template>
  <div class="page">
    <div v-if="!vehicles.length" class="empty">
      <p>Add your car first, so the estimate uses the right parts prices.</p>
      <NuxtLink to="/vehicles/new" class="btn btn-primary">Add a car</NuxtLink>
    </div>

    <div v-else class="layout">
      <div class="chat">
        <div class="chat-head">
          <h1>New estimate</h1>
          <button v-if="pastSetup" type="button" class="btn btn-quiet" @click="startOver">Start over</button>
        </div>

        <!-- 1. Car and garage -->
        <div class="ai">
          <span class="avatar"><AppIcon name="sparkle" :size="18" /></span>
          <div class="bubble">
            <span class="q">Which car is it, and where will you take it?</span>
            <template v-if="!pastSetup">
              <div class="car-chips">
                <button
                  v-for="v in vehicles"
                  :key="v.id"
                  type="button"
                  class="car-chip"
                  :class="{ on: form.vehicle_id === v.id }"
                  @click="form.vehicle_id = v.id"
                >
                  <svg width="22" height="14" viewBox="0 0 34 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round" aria-hidden="true"><path d="M2 15v-4l3-5h18l5 5h2a2 2 0 0 1 2 2v2z" /><circle cx="9" cy="16" r="2.5" fill="#FFFFFF" /><circle cx="25" cy="16" r="2.5" fill="#FFFFFF" /></svg>
                  {{ v.model }} {{ v.year }}
                </button>
              </div>
              <div class="garages" role="radiogroup" aria-label="Garage type">
                <button
                  v-for="g in GARAGE_TIERS"
                  :key="g.value"
                  type="button"
                  role="radio"
                  class="garage"
                  :class="{ on: form.garage_tier === g.value }"
                  :aria-checked="form.garage_tier === g.value"
                  @click="form.garage_tier = g.value"
                >
                  <b>{{ g.label }}</b>
                  <span class="small muted">{{ g.hint }}</span>
                </button>
              </div>
              <button type="button" class="btn btn-primary self-start" @click="step = 'problem'">Continue</button>
            </template>
          </div>
        </div>

        <!-- 2. Problem -->
        <template v-if="pastSetup">
          <div class="me">{{ carLabel }} · {{ tierLabel(form.garage_tier) }}</div>
          <div class="ai">
            <span class="avatar"><AppIcon name="sparkle" :size="18" /></span>
            <div class="bubble">
              <span class="q">What is wrong with the car? Write it the way you would tell a mechanic.</span>
              <form v-if="step === 'problem'" class="stack" novalidate @submit.prevent="sendProblem">
                <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>
                <textarea
                  v-model="form.problem_text"
                  class="input"
                  :class="{ 'has-error': fieldErrors.problem_text }"
                  maxlength="1000"
                  aria-label="Describe the problem"
                  placeholder="যেমন: ব্রেক চাপলে আওয়াজ হয় / e.g. Noise when I brake"
                />
                <span v-if="fieldErrors.problem_text" class="field-error">
                  <AppIcon name="info" :size="16" :stroke="2" />{{ fieldErrors.problem_text }}
                </span>
                <div class="chips">
                  <button v-for="c in CHIPS" :key="c" type="button" class="chip" @click="form.problem_text = c">
                    {{ c }}
                  </button>
                </div>
                <button type="submit" class="btn btn-primary self-start">Send</button>
              </form>
            </div>
          </div>
        </template>

        <template v-if="pastProblem">
          <div class="me">{{ form.problem_text }}</div>

          <!-- 3. Clarifying questions -->
          <template v-for="(t, i) in turns" :key="i">
            <div class="ai">
              <span class="avatar"><AppIcon name="sparkle" :size="18" /></span>
              <div class="bubble">
                <span class="tag-ai">AI assistant ({{ i + 1 }}/{{ maxQuestions }})</span>
                <span class="q">{{ t.question }}</span>
              </div>
            </div>
            <div class="me">{{ t.answer }}</div>
          </template>

          <div v-if="step === 'question'" class="ai">
            <span class="avatar"><AppIcon name="sparkle" :size="18" /></span>
            <div class="bubble">
              <span class="tag-ai">AI assistant ({{ turns.length + 1 }}/{{ maxQuestions }})</span>
              <span class="q">{{ pendingQuestion }}</span>
              <form class="answer" @submit.prevent="reply()">
                <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>
                <input v-model="answer" class="input" maxlength="300" autocomplete="off" aria-label="Your answer" />
                <div class="answer-actions">
                  <button type="button" class="chip" @click="reply('Not sure')">Not sure</button>
                  <button type="submit" class="btn btn-primary" :disabled="!answer.trim()">Answer</button>
                </div>
              </form>
            </div>
          </div>

          <!-- Waiting -->
          <div v-if="step === 'waiting'" class="panel loading" aria-live="polite">
            <div
              v-for="(label, i) in LOAD_STEPS"
              :key="label"
              class="load-step"
              :class="{ done: i < loadIdx, active: i === loadIdx }"
            >
              <span class="load-dot">
                <AppIcon v-if="i < loadIdx" name="check" :size="14" :stroke="3" />
                <span v-else-if="i === loadIdx" class="spinner" />
              </span>
              {{ label }}
            </div>
          </div>

          <!-- Manual choice -->
          <div v-if="step === 'manual'" class="ai">
            <span class="avatar"><AppIcon name="sparkle" :size="18" /></span>
            <form class="bubble" @submit.prevent="submitManual">
              <p class="alert alert-warn"><AppIcon name="info" :size="18" :stroke="2" />{{ notice }}</p>
              <p v-if="formError" class="alert alert-error" role="alert">{{ formError }}</p>
              <span class="q">Tick the repair jobs you want priced. Suggestions are ticked already.</span>
              <div class="jobs">
                <label v-for="job in jobs" :key="job.code" class="job" :class="{ on: chosen.includes(job.code) }">
                  <input v-model="chosen" type="checkbox" :value="job.code" />
                  <span class="job-text">
                    {{ job.name_en }}
                    <span class="small muted">{{ job.name_bn }}</span>
                  </span>
                  <span v-if="job.safety_critical" class="tag low">Safety</span>
                </label>
              </div>
              <button class="btn btn-primary self-start" type="submit">
                Price {{ chosen.length || '' }} job{{ chosen.length === 1 ? '' : 's' }}
              </button>
            </form>
          </div>
        </template>
      </div>

      <aside class="panel summary">
        <div class="eyebrow">Your estimate so far</div>
        <div class="sum-row"><span class="muted">Car</span><b>{{ carLabel }}</b></div>
        <div class="sum-row dashed"><span class="muted">Garage</span><b>{{ tierLabel(form.garage_tier) }}</b></div>
        <div class="sum-col dashed">
          <span class="muted">Problem</span>
          <b>{{ pastProblem && form.problem_text ? form.problem_text : '—' }}</b>
        </div>
        <div class="sum-col dashed">
          <span class="muted">Your answers</span>
          <span v-for="(t, i) in turns" :key="i" class="sum-answer">
            <span>{{ t.question }}</span><b>{{ t.answer }}</b>
          </span>
          <span v-if="!turns.length" class="muted">None yet</span>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  align-items: flex-start;
}

.chat {
  flex: 3 1 480px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chat-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.chat-head h1 {
  margin: 0;
  font-size: 36px;
}

.ai {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.avatar {
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--signal);
  display: grid;
  place-items: center;
}

.bubble {
  flex: 1;
  min-width: 0;
  background: var(--card);
  border-radius: 4px 12px 12px 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 1px 2px rgba(22, 24, 29, 0.06);
}

.q {
  font-size: 16px;
  font-weight: 600;
}

.tag-ai {
  font-size: 13px;
  font-weight: 600;
  color: var(--signal-dark);
}

.me {
  align-self: flex-end;
  max-width: 80%;
  background: var(--ink);
  color: #fff;
  border-radius: 12px 4px 12px 12px;
  padding: 12px 16px;
  font-size: 16px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.self-start {
  align-self: flex-start;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.car-chips,
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.car-chip {
  border: 1.5px solid var(--line);
  background: var(--card);
  border-radius: 999px;
  padding: 8px 14px;
  min-height: 44px;
  font: inherit;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.car-chip.on {
  border-color: var(--signal);
  background: var(--signal-soft);
}

.garages {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background: var(--paper);
  border-radius: var(--radius);
  padding: 4px;
  gap: 4px;
}

.garage {
  border: 0;
  background: transparent;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 2px;
  font: inherit;
}

.garage b {
  font-size: 15px;
}

.garage .small {
  font-size: 13px;
  line-height: 1.35;
}

.garage.on {
  background: var(--card);
  box-shadow: 0 1px 3px rgba(22, 24, 29, 0.15);
}

.answer {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.answer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.loading {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.load-step {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  color: var(--ink-soft);
}

.load-step.done,
.load-step.active {
  color: var(--ink);
}

.load-step.active {
  font-weight: 600;
}

.load-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--line);
  color: #fff;
  flex: none;
}

.load-step.done .load-dot {
  background: var(--fair);
}

.load-step.active .load-dot {
  background: var(--signal);
}

.jobs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 8px;
}

.job {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 12px;
  cursor: pointer;
}

.job.on {
  border-color: var(--signal);
  background: var(--signal-soft);
}

.job input {
  margin-top: 5px;
  accent-color: var(--ink);
}

.job-text {
  flex: 1;
  display: grid;
}

.summary {
  position: sticky;
  top: 92px;
  flex: 2 1 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary + .summary {
  margin-top: 0;
}

.sum-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 15px;
}

.sum-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 15px;
}

.dashed {
  padding-top: 14px;
}

.sum-col b {
  font-weight: 600;
  overflow-wrap: anywhere;
}

.sum-answer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 600px) {
  .garages {
    grid-template-columns: 1fr;
  }

  .chat-head h1 {
    font-size: 30px;
  }

  .summary {
    position: static;
  }
}
</style>
