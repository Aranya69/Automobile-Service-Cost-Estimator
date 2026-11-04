<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useHead({ title: 'Edit car · ASCE' })

const route = useRoute()
const api = useApi()
const id = Number(route.params.id)

const { data, error } = await useAsyncData(`vehicle-${id}`, () =>
  api.get<{ vehicle: Vehicle }>(`/vehicles/${id}`),
)
const vehicle = computed(() => data.value?.vehicle)

async function save(input: VehicleInput) {
  await api.put(`/vehicles/${id}`, input)
  await navigateTo('/vehicles')
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>Edit car</h1>
        <p v-if="vehicle" class="lead">{{ vehicle.label }}</p>
      </div>
    </div>

    <div v-if="error" class="panel empty">
      <p>This car could not be found.</p>
      <NuxtLink to="/vehicles" class="btn">Back to my cars</NuxtLink>
    </div>

    <div v-else-if="vehicle" class="form-box">
      <VehicleForm
        submit-label="Save changes"
        :save="save"
        :initial="{
          model: vehicle.model,
          year: vehicle.year,
          engine_cc: vehicle.engine_cc,
          odometer_km: vehicle.odometer_km,
        }"
      />
    </div>
  </div>
</template>

<style scoped>
.form-box {
  max-width: 620px;
}
</style>
