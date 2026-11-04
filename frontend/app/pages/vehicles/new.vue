<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useHead({ title: 'Add a car · ASCE' })

const api = useApi()

async function save(input: VehicleInput) {
  await api.post('/vehicles', input)
  await navigateTo('/vehicles')
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>Add a car</h1>
        <p class="lead">Only Toyota Axio, Premio, Allion, Corolla and Noah for now.</p>
      </div>
    </div>
    <div class="form-box">
      <VehicleForm submit-label="Add car" :save="save" />
    </div>
  </div>
</template>

<style scoped>
.form-box {
  max-width: 620px;
}
</style>
