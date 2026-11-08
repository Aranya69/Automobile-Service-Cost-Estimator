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
    <div v-if="error" class="empty">
      <p>This car could not be found.</p>
      <NuxtLink to="/vehicles" class="btn btn-primary">Back to my cars</NuxtLink>
    </div>

    <VehicleForm
      v-else-if="vehicle"
      :title="`Edit ${vehicle.model} ${vehicle.year}`"
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
</template>
