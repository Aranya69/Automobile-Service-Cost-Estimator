export interface Vehicle {
  id: number
  make: string
  model: string
  year: number
  engine_cc: number
  odometer_km: number
  label: string
  created_at: string
  updated_at: string
}

export interface VehicleInput {
  model: string
  year: number | null
  engine_cc: number | null
  odometer_km: number | null
}

export interface VehicleOptions {
  make: string
  models: { name: string; engines: number[] }[]
  first_year: number
  last_year: number
  odometer_max: number
}

export function formatKm(km: number) {
  return `${km.toLocaleString('en-IN')} km`
}

export function formatCc(cc: number) {
  return `${(cc / 1000).toFixed(1)} L`
}
