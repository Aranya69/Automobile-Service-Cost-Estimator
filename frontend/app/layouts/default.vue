<script setup lang="ts">
const { user, logout } = useAuth()
const leaving = ref(false)

const NAV = [
  { to: '/estimate', label: 'New estimate' },
  { to: '/vehicles', label: 'My cars' },
  { to: '/history', label: 'History' },
]

const initials = computed(() =>
  (user.value?.name ?? '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join(''),
)

async function onLogout() {
  leaving.value = true
  await logout()
  leaving.value = false
  await navigateTo('/login')
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <div class="container bar">
        <BrandMark :to="user ? '/vehicles' : '/'" />

        <nav v-if="user" class="nav" aria-label="Main">
          <NuxtLink v-for="item in NAV" :key="item.to" :to="item.to" class="nav-item">
            {{ item.label }}
          </NuxtLink>
        </nav>
        <div v-else class="nav" />

        <div v-if="user" class="me">
          <NuxtLink to="/account" class="avatar" :title="`${user.name} · ${user.email}`">
            {{ initials }}
          </NuxtLink>
          <button class="btn btn-quiet" type="button" :disabled="leaving" @click="onLogout">
            Log out
          </button>
        </div>
        <div v-else class="me">
          <NuxtLink to="/login" class="login-link">Log in</NuxtLink>
          <NuxtLink to="/register" class="btn btn-primary">Register</NuxtLink>
        </div>
      </div>
    </header>

    <main class="container">
      <slot />
    </main>

    <footer class="foot container small muted">
      Prices are estimates; the final cost depends on the garage.
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
  padding-top: 8px;
  padding-bottom: 8px;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.nav-item {
  border-radius: var(--radius);
  padding: 10px 14px;
  font-size: 15px;
  font-weight: 600;
}

.nav-item:hover {
  background: var(--paper);
  color: var(--ink);
}

.nav-item.router-link-active {
  background: var(--signal-soft);
}

.me {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--signal);
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 15px;
}

.avatar:hover {
  color: var(--signal);
  outline: 3px solid var(--signal-soft);
}

.login-link {
  font-weight: 600;
  font-size: 15px;
  padding: 10px 12px;
}

main {
  flex: 1;
}

.foot {
  padding-top: 24px;
  padding-bottom: 32px;
  border-top: 1px solid var(--line);
}

@media (max-width: 720px) {
  .nav {
    order: 3;
    flex-basis: 100%;
  }

  .me {
    margin-left: auto;
  }
}
</style>
