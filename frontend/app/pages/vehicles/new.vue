<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useHead({ title: 'Add a car · ASCE' })

const api = useApi()

async function save(input: VehicleInput) {
  const res = await api.post<{ vehicle: Vehicle }>('/vehicles', input)
  // Came from the landing page with a problem typed in: go straight to the estimate.
  const draft = useDraft().load()
  await navigateTo(draft?.problem ? `/estimate?vehicle=${res.vehicle.id}` : '/vehicles')
}
</script>

<template>
  <div class="page">
    <VehicleForm title="Add a car" submit-label="Save car" :save="save" from-draft />
  </div>
</template>
