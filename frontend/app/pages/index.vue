<template>
  <div class="page">
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

@media (max-width: 600px) {
  .intro h1 { font-size: 1.6rem; }
}
</style>
