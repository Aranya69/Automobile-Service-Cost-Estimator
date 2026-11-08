<script setup lang="ts">
const POINTS = [
  'Save your cars once, estimate any time',
  'Itemised price ranges in taka',
  'Keep a history of every estimate',
]
</script>

<template>
  <div class="split">
    <aside class="side">
      <div class="blob" aria-hidden="true" />
      <BrandMark inverted />
      <div class="side-body">
        <h1>Know the repair bill before you reach the garage.</h1>
        <CarArt class="art" dark />
        <ul class="points">
          <li v-for="point in POINTS" :key="point">
            <span class="tick"><AppIcon name="check" :size="16" :stroke="2.25" /></span>
            {{ point }}
          </li>
        </ul>
      </div>
    </aside>

    <main class="form-side">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.split {
  min-height: 100vh;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 440px), 1fr));
}

.side {
  position: relative;
  overflow: hidden;
  background: var(--ink);
  color: #fff;
  padding: 40px 48px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.blob {
  position: absolute;
  right: -160px;
  bottom: -160px;
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: var(--signal);
  opacity: 0.16;
}

.side-body {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 32px;
  max-width: 480px;
}

.side-body h1 {
  margin: 0;
  font-stretch: 110%;
  font-size: 40px;
  line-height: 1.08;
  text-wrap: balance;
}

.art {
  width: 100%;
  max-width: 420px;
  height: auto;
}

.points {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 14px;
  font-size: 16px;
}

.points li {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tick {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--signal);
  color: var(--ink);
  display: grid;
  place-items: center;
  flex: none;
}

.form-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}

@media (max-width: 900px) {
  .side {
    padding: 28px 24px;
  }

  .side-body h1 {
    font-size: 30px;
  }

  .art,
  .points {
    display: none;
  }
}
</style>
