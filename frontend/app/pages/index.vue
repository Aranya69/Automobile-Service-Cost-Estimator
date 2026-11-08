<script setup lang="ts">
import type { IconName } from '~/components/AppIcon.vue'

definePageMeta({
  layout: false,
  // Logged-in users start on their cars.
  middleware: () => {
    const { user } = useAuth()
    if (user.value) return navigateTo('/vehicles')
  },
})
useHead({ title: 'ASCE · Know the repair bill before you reach the garage' })

interface Highlights {
  tiles: { key: string; name: string; job_code: string; from: number }[]
  samples: {
    car: string
    job: string
    garage_tier: string
    total_min: number
    total_likely: number
    total_max: number
    parts_share: number
    labour_share: number
  }[]
}

const api = useApi()
const draft = useDraft()

const { data: highlights } = await useAsyncData('highlights', () =>
  api.get<Highlights>('/estimates/highlights').catch(() => ({ tiles: [], samples: [] })),
)

const MODELS = ['Axio', 'Premio', 'Allion', 'Corolla', 'Noah']
const thisYear = new Date().getFullYear()
const YEARS = Array.from({ length: thisYear - 1995 + 1 }, (_, i) => thisYear - i)
const CHIPS = ['ব্রেক এ আওয়াজ করে', 'AC thanda hoy na', 'Car is slow to start']

const start = reactive({ model: 'Axio', year: 2016, problem: '' })

function getEstimate() {
  draft.save({ model: start.model, year: start.year, problem: start.problem.trim() })
  navigateTo('/register')
}

const TILE_ICONS: Record<string, IconName> = {
  brakes: 'brake',
  ac: 'ac',
  battery: 'battery',
  suspension: 'suspension',
  servicing: 'oil',
  cooling: 'thermometer',
}
const ROTATIONS = ['-2.5deg', '1.5deg', '-1deg']

const STEPS = [
  {
    title: 'Add your car',
    text: 'Pick your Toyota model, year and odometer. Save it once, use it for every estimate.',
  },
  {
    title: 'Describe the problem',
    text: 'Write it the way you would tell a mechanic, in Bangla or English. The assistant asks up to 3 short questions.',
  },
  {
    title: 'Get an itemised range',
    text: 'See each part and labour line with a price range, saved to your history.',
  },
]
const step = ref(0)

const phoneSample = computed(() => highlights.value?.samples[0])

const TRUST: { icon: IconName; title: string; text: string }[] = [
  {
    icon: 'database',
    title: 'Market and garage prices',
    text: 'Parts listings and price sheets from local garages, each one dated and stored.',
  },
  {
    icon: 'shieldCheck',
    title: 'Garage-checked prices',
    text: 'Prices from garage sheets are marked as verified and raise the confidence of an estimate.',
  },
  {
    icon: 'noEntry',
    title: 'No invented prices',
    text: 'If we do not have enough data for a part, we say so and tell you to ask for quotes.',
  },
  {
    icon: 'language',
    title: 'Bangla support',
    text: 'Write the problem in Bangla, English or Banglish. The assistant answers the same way.',
  },
]

const FAQS = [
  {
    q: 'Is the price final?',
    a: 'No. ASCE gives a price range based on recorded prices. The final bill depends on the garage, the parts they use and what they find when they open the car.',
  },
  {
    q: 'Where do prices come from?',
    a: 'From parts listings and price sheets collected from garages in Dhaka. Every price is dated, and garage prices are marked as verified.',
  },
  {
    q: 'Does the AI decide the price?',
    a: 'No. The assistant only works out which repair jobs fit your problem. Every taka figure comes from our price database.',
  },
  {
    q: 'Which cars are supported?',
    a: 'Toyota Axio, Premio, Allion, Corolla and Noah. More models will follow.',
  },
]
const openFaq = ref(0)
</script>

<template>
  <div class="landing">
    <header class="topbar">
      <div class="container bar">
        <BrandMark />
        <nav class="links" aria-label="Sections">
          <a href="#how">How it works</a>
          <a href="#repairs">Common repairs</a>
          <a href="#trust">About</a>
        </nav>
        <div class="auth">
          <NuxtLink to="/login" class="login-link">Log in</NuxtLink>
          <NuxtLink to="/register" class="btn btn-primary">Register</NuxtLink>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <section class="hero">
      <div class="blob blob-1" aria-hidden="true" />
      <div class="blob blob-2" aria-hidden="true" />
      <div class="container hero-grid">
        <div class="hero-copy">
          <span class="pill">For Toyota Axio, Premio, Allion, Corolla and Noah</span>
          <h1>Know the repair bill before you reach the garage.</h1>
          <p class="hero-lead">
            Describe the problem in Bangla or English. Get an itemised price range for parts and
            labour, based on Dhaka market and garage prices.
          </p>
          <div class="facts">
            <span><b class="taka">৳</b>Prices in taka</span>
            <span><AppIcon name="language" :size="18" class="gold" />Bangla &amp; English</span>
            <span><AppIcon name="shieldCheck" :size="18" class="gold" />Market and garage data</span>
          </div>
          <CarArt class="hero-car" />
        </div>

        <form class="start-card" @submit.prevent="getEstimate">
          <div class="start-head">
            <h2>Start your estimate</h2>
            <span class="small muted">Free · 2 minutes</span>
          </div>
          <div class="start-row">
            <label class="field">
              Car model
              <select v-model="start.model" class="input">
                <option v-for="m in MODELS" :key="m" :value="m">Toyota {{ m }}</option>
              </select>
            </label>
            <label class="field">
              Year
              <select v-model.number="start.year" class="input">
                <option v-for="y in YEARS" :key="y" :value="y">{{ y }}</option>
              </select>
            </label>
          </div>
          <label class="field">
            What is wrong with the car?
            <textarea
              v-model="start.problem"
              class="input"
              maxlength="1000"
              placeholder="যেমন: ব্রেক চাপলে আওয়াজ হয় / e.g. Noise when I brake"
            />
          </label>
          <div class="chips">
            <button v-for="c in CHIPS" :key="c" type="button" class="chip" @click="start.problem = c">
              {{ c }}
            </button>
          </div>
          <button type="submit" class="btn btn-primary btn-lg btn-block">
            Get my estimate <AppIcon name="arrowRight" :size="18" :stroke="2" />
          </button>
          <p class="small muted center">You will create a free account next. We keep what you typed.</p>
        </form>
      </div>
    </section>

    <!-- Sample job cards -->
    <section v-if="highlights?.samples.length" class="dark">
      <div class="container section">
        <div class="section-head">
          <div>
            <div class="kicker">Sample estimates</div>
            <h2>Every estimate is a clear job card</h2>
          </div>
          <p class="section-note">
            A price range, the most likely total, and how much goes to parts and to labour.
          </p>
        </div>
        <div class="samples">
          <article
            v-for="(s, i) in highlights.samples"
            :key="s.car"
            class="sample"
            :style="{ transform: `rotate(${ROTATIONS[i]})` }"
          >
            <div class="sample-top small muted">
              <span>{{ s.car }}</span>
              <span>{{ tierLabel(s.garage_tier) }}</span>
            </div>
            <h3>{{ s.job }}</h3>
            <div class="dashed" />
            <div class="sample-range mono">{{ formatTaka(s.total_min) }} – {{ formatTaka(s.total_max) }}</div>
            <div class="split-bar">
              <span class="parts" :style="{ width: `${s.parts_share}%` }" />
              <span class="labour" />
            </div>
            <div class="legend small muted">
              <span><i class="sw parts" />Parts {{ s.parts_share }}%</span>
              <span><i class="sw labour" />Labour {{ s.labour_share }}%</span>
            </div>
          </article>
        </div>
      </div>
    </section>

    <!-- Common repairs -->
    <section v-if="highlights?.tiles.length" id="repairs" class="container section">
      <div class="section-head">
        <h2>Common repairs</h2>
        <span class="muted">Starting prices at local garages in Dhaka</span>
      </div>
      <div class="tiles">
        <NuxtLink v-for="t in highlights.tiles" :key="t.key" to="/register" class="tile">
          <span class="tile-icon"><AppIcon :name="TILE_ICONS[t.key] ?? 'brake'" :size="24" /></span>
          <span class="tile-text">
            <span class="tile-name">{{ t.name }}</span>
            <span class="small muted">from <b class="mono ink">{{ formatTaka(t.from) }}</b></span>
          </span>
        </NuxtLink>
      </div>
    </section>

    <!-- How it works -->
    <section id="how" class="container section how">
      <div class="steps">
        <h2>How it works</h2>
        <button
          v-for="(s, i) in STEPS"
          :key="s.title"
          type="button"
          class="step"
          :class="{ on: step === i }"
          @click="step = i"
        >
          <span class="step-n mono">{{ i + 1 }}</span>
          <span class="step-text">
            <span class="step-title">{{ s.title }}</span>
            <span class="muted">{{ s.text }}</span>
          </span>
        </button>
      </div>

      <div class="phone-wrap" aria-hidden="true">
        <div class="phone-blob" />
        <div class="phone">
          <div class="screen">
            <div class="notch"><span /></div>
            <div class="screen-head">ASCE <span>Step {{ step + 1 }} of 3</span></div>

            <div v-if="step === 0" class="screen-body">
              <div class="screen-title">Add your car</div>
              <div class="models">
                <span class="on">Axio</span><span>Premio</span><span>Allion</span><span>Corolla</span>
              </div>
              <div class="row"><span class="muted">Year</span><b>2016</b></div>
              <div class="row"><span class="muted">Odometer</span><b class="mono">84,200 km</b></div>
              <div class="fake-btn">Save car</div>
            </div>

            <div v-else-if="step === 1" class="screen-body">
              <div class="screen-title">Describe the problem</div>
              <div class="fake-input">ব্রেক চাপলে সামনের চাকা থেকে ঘষার আওয়াজ হয়</div>
              <div class="bubble">
                <span class="gold-text">AI assistant (1/3)</span><br />When do you hear the noise?
              </div>
              <div class="mini-chips">
                <span class="on">Only when braking</span><span>Always</span><span>Not sure</span>
              </div>
            </div>

            <div v-else class="screen-body">
              <div class="mini-card">
                <span class="muted">{{ phoneSample?.car.replace('Toyota ', '') ?? 'Axio 2016' }} · Local garage</span>
                <span class="mono big">
                  {{ formatTaka(phoneSample?.total_min) }} – {{ formatTaka(phoneSample?.total_max) }}
                </span>
                <span class="muted">Most likely <b class="ink">{{ formatTaka(phoneSample?.total_likely) }}</b></span>
                <span class="tag high">High confidence</span>
              </div>
              <div class="mini-lines">
                <div><span>{{ phoneSample?.job ?? 'Front brake pads' }}</span><b class="mono">{{ phoneSample?.parts_share ?? '—' }}%</b></div>
                <div><span>Labour</span><b class="mono">{{ phoneSample?.labour_share ?? '—' }}%</b></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Trust -->
    <section id="trust" class="container section">
      <h2>Why trust ASCE</h2>
      <div class="trust">
        <div v-for="t in TRUST" :key="t.title" class="panel trust-card">
          <AppIcon :name="t.icon" :size="28" class="gold" />
          <span class="trust-title">{{ t.title }}</span>
          <span class="muted">{{ t.text }}</span>
        </div>
      </div>
    </section>

    <!-- FAQ -->
    <section class="container section faq">
      <h2>Questions</h2>
      <div class="faq-list">
        <div v-for="(f, i) in FAQS" :key="f.q" class="faq-item">
          <button
            type="button"
            class="faq-q"
            :aria-expanded="openFaq === i"
            @click="openFaq = openFaq === i ? -1 : i"
          >
            {{ f.q }}<span class="mono gold">{{ openFaq === i ? '−' : '+' }}</span>
          </button>
          <p v-if="openFaq === i" class="faq-a muted">{{ f.a }}</p>
        </div>
      </div>
    </section>

    <footer class="footer">
      <div class="container foot-grid">
        <div class="foot-brand">
          <span class="foot-word">ASCE</span>
          <span>Prices are estimates; the final cost depends on the garage.</span>
        </div>
        <nav class="foot-links" aria-label="Footer">
          <a href="#how">How it works</a>
          <a href="#repairs">Common repairs</a>
          <a href="#trust">About</a>
          <NuxtLink to="/login">Log in</NuxtLink>
        </nav>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  background: var(--paper);
}

.gold { color: var(--signal-dark); }
.gold-text { color: var(--signal-dark); font-weight: 600; }
.ink { color: var(--ink); }
.center { text-align: center; margin: 0; }

/* Header */
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--card);
  border-bottom: 1px solid var(--line);
}

.bar {
  min-height: 68px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 32px;
}

.links {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  flex: 1;
  font-size: 15px;
  font-weight: 500;
}

.auth {
  display: flex;
  align-items: center;
  gap: 12px;
}

.login-link {
  font-weight: 600;
  font-size: 15px;
  padding: 10px 12px;
}

/* Hero */
.hero {
  position: relative;
  overflow: hidden;
}

.blob {
  position: absolute;
  background: var(--signal);
  pointer-events: none;
}

.blob-1 {
  right: -180px;
  top: -140px;
  width: 780px;
  height: 780px;
  border-radius: 44% 56% 52% 48%;
  opacity: 0.22;
}

.blob-2 {
  right: 120px;
  bottom: -220px;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  opacity: 0.14;
}

.hero-grid {
  position: relative;
  padding-top: 72px;
  padding-bottom: 96px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr));
  gap: 56px;
  align-items: center;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.pill {
  align-self: flex-start;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-soft);
}

.hero h1 {
  margin: 0;
  font-stretch: 112%;
  font-size: clamp(38px, 5vw, 56px);
  line-height: 1.04;
  letter-spacing: -0.015em;
  text-wrap: balance;
}

.hero-lead {
  margin: 0;
  font-size: 19px;
  color: var(--ink-soft);
  max-width: 500px;
  text-wrap: pretty;
}

.facts {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  font-size: 15px;
  font-weight: 500;
}

.facts span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.taka {
  font-family: var(--font-mono);
  color: var(--signal-dark);
}

.hero-car {
  width: 100%;
  max-width: 460px;
  height: auto;
  margin-top: 8px;
}

.start-card {
  background: var(--card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  border-top: 6px solid var(--signal);
  padding: 28px;
  max-width: 480px;
  width: 100%;
  justify-self: end;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.start-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.start-head h2 {
  margin: 0;
  font-size: 24px;
}

.start-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 12px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Sections */
.section {
  padding-top: 96px;
}

.section-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 32px;
}

.section-head h2 {
  margin: 0;
}

.dark {
  background: var(--ink);
  color: #fff;
  overflow: hidden;
  margin-top: 0;
}

.dark .section {
  padding-bottom: 96px;
}

.kicker {
  color: var(--signal);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.section-note {
  margin: 0;
  max-width: 380px;
  color: #c9cbd1;
}

.samples {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
  gap: 28px;
  padding: 12px 0;
}

.sample {
  position: relative;
  background: var(--card);
  color: var(--ink);
  border-radius: var(--radius-lg);
  padding: 30px 24px 24px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sample::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 8px;
  background: radial-gradient(circle at 8px 0, var(--ink) 5px, transparent 5.5px) repeat-x;
  background-size: 16px 8px;
}

.sample-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.sample h3 {
  margin: 0;
  font-size: 20px;
}

.sample-range {
  font-size: 28px;
  letter-spacing: -0.02em;
}

.split-bar {
  display: flex;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--labour);
}

.split-bar .parts {
  background: var(--parts);
}

.legend {
  display: flex;
  justify-content: space-between;
}

.legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sw {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.sw.parts { background: var(--parts); }
.sw.labour { background: var(--labour); }

.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 170px), 1fr));
  gap: 16px;
}

.tile {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.tile:hover {
  color: var(--ink);
  border-color: var(--signal);
  box-shadow: 0 8px 24px rgba(22, 24, 29, 0.08);
}

.tile-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius);
  background: var(--signal-soft);
  display: grid;
  place-items: center;
}

.tile-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tile-name {
  font-weight: 600;
  font-size: 17px;
}

/* How it works */
.how {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr));
  gap: 56px;
  align-items: center;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.steps h2 {
  margin-bottom: 20px;
}

.step {
  text-align: left;
  border: 1px solid var(--line);
  background: transparent;
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  font-size: 15px;
}

.step.on {
  background: var(--card);
  border-color: var(--signal);
}

.step-n {
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--line);
  display: grid;
  place-items: center;
}

.step.on .step-n {
  background: var(--signal);
}

.step-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-title {
  font-family: var(--font-head);
  font-weight: 700;
  font-size: 20px;
}

.phone-wrap {
  display: grid;
  place-items: center;
  position: relative;
  padding: 24px 0;
}

.phone-blob {
  position: absolute;
  width: 360px;
  height: 360px;
  max-width: 100%;
  border-radius: 50%;
  background: var(--signal);
  opacity: 0.25;
}

.phone {
  position: relative;
  width: 290px;
  height: 580px;
  border-radius: 44px;
  background: var(--ink);
  padding: 12px;
  box-shadow: 0 24px 48px rgba(22, 24, 29, 0.25);
}

.screen {
  width: 100%;
  height: 100%;
  border-radius: 34px;
  background: var(--paper);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-size: 13px;
}

.notch {
  height: 44px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.notch span {
  width: 84px;
  height: 22px;
  border-radius: 999px;
  background: var(--ink);
}

.screen-head {
  padding: 8px 18px;
  display: flex;
  align-items: center;
  font-family: var(--font-head);
  font-weight: 800;
  font-size: 15px;
}

.screen-head span {
  margin-left: auto;
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 12px;
  color: var(--ink-soft);
}

.screen-body {
  padding: 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.screen-title {
  font-family: var(--font-head);
  font-weight: 700;
  font-size: 18px;
}

.models {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.models span {
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: var(--radius);
  padding: 12px 8px;
  text-align: center;
}

.models span.on {
  border: 2px solid var(--signal);
  font-weight: 600;
}

.row,
.fake-input {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 12px;
}

.row {
  display: flex;
  justify-content: space-between;
}

.fake-input {
  min-height: 90px;
  font-size: 14px;
  line-height: 1.5;
}

.fake-btn {
  margin-top: 8px;
  height: 42px;
  border-radius: var(--radius);
  background: var(--signal);
  font-weight: 700;
  font-size: 14px;
  display: grid;
  place-items: center;
}

.bubble {
  align-self: flex-start;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px 12px 12px 4px;
  padding: 10px 12px;
  line-height: 1.45;
}

.mini-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mini-chips span {
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
}

.mini-chips span.on {
  background: var(--ink);
  border-color: var(--ink);
  color: #fff;
}

.mini-card {
  background: var(--card);
  border-radius: var(--radius-lg);
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: var(--shadow);
  font-size: 12px;
}

.mini-card .big {
  font-size: 21px;
}

.mini-card .tag {
  align-self: flex-start;
  font-size: 11px;
}

.mini-lines {
  background: var(--card);
  border-radius: var(--radius-lg);
  padding: 6px 14px;
  font-size: 12px;
}

.mini-lines div {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.mini-lines div + div {
  border-top: 1.5px dashed var(--line);
}

/* Trust */
.trust {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 16px;
}

.trust-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trust-card + .trust-card {
  margin-top: 0;
}

.trust-title {
  font-family: var(--font-head);
  font-weight: 700;
  font-size: 20px;
}

/* FAQ */
.faq {
  max-width: 800px;
  padding-bottom: 96px;
}

.faq-list {
  border-top: 1px solid var(--line);
}

.faq-item {
  border-bottom: 1px solid var(--line);
}

.faq-q {
  width: 100%;
  background: none;
  border: 0;
  padding: 22px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  text-align: left;
}

.faq-q .mono {
  font-size: 22px;
}

.faq-a {
  margin: 0 0 22px;
  max-width: 640px;
}

/* Footer */
.footer {
  background: var(--ink);
  color: #fff;
}

.foot-grid {
  padding-top: 56px;
  padding-bottom: 56px;
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  justify-content: space-between;
  align-items: flex-start;
}

.foot-brand {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 360px;
  color: #c9cbd1;
  font-size: 15px;
}

.foot-word {
  font-family: var(--font-head);
  font-weight: 800;
  font-size: 22px;
  color: var(--signal);
}

.foot-links {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  font-size: 15px;
}

.foot-links a {
  color: #fff;
}

.foot-links a:hover {
  color: var(--signal);
}

@media (max-width: 720px) {
  .links {
    display: none;
  }

  .auth {
    margin-left: auto;
  }

  .hero-grid {
    padding-top: 40px;
    padding-bottom: 56px;
    gap: 32px;
  }

  .start-card {
    justify-self: stretch;
    padding: 20px;
  }

  .section {
    padding-top: 64px;
  }

  .sample {
    transform: none !important;
  }
}

@media (max-width: 420px) {
  .start-row {
    grid-template-columns: 1fr;
  }

  .phone {
    transform: scale(0.9);
  }
}
</style>
