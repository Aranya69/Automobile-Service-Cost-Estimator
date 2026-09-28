<template>
  <div class="shell">
    <header class="topbar">
      <div class="container topbar-inner">
        <NuxtLink to="/" class="brand">
          <span class="brand-mark">ASCE</span>
          <span class="brand-sub">Service Cost Estimator</span>
        </NuxtLink>

        <nav class="nav">
          <NuxtLink to="/login">Log in</NuxtLink>
          <NuxtLink to="/register" class="btn btn-primary">Register</NuxtLink>
        </nav>
      </div>
    </header>

    <main class="container">
      <slot />
    </main>

    <footer class="footer container small muted">
      Prices are estimates from local garage and market data. Final cost depends on the garage.
    </footer>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  background: var(--surface);
  border-bottom: 3px solid var(--red-500);
}

.topbar-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  min-height: 60px;
  padding-top: 8px;
  padding-bottom: 8px;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
  text-decoration: none;
  color: var(--ink);
}

.brand-mark {
  font-family: var(--font-head);
  font-weight: 700;
  font-size: 1.35rem;
  letter-spacing: 0.06em;
  color: var(--red-600);
}

.brand-sub {
  font-size: 0.85rem;
  color: var(--ink-soft);
}

.nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 18px;
}

.nav a:not(.btn) {
  color: var(--ink);
  text-decoration: none;
  font-weight: 500;
  padding: 4px 0;
  border-bottom: 2px solid transparent;
}

.nav a:not(.btn):hover,
.nav a.router-link-active:not(.btn) {
  border-bottom-color: var(--red-400);
}

main { flex: 1; }

.footer {
  padding-top: 20px;
  padding-bottom: 24px;
  border-top: 1px solid var(--line);
}

@media (max-width: 520px) {
  .brand-sub { display: none; }
}
</style>
