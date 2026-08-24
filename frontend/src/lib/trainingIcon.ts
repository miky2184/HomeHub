import { Activity, Bike, Dumbbell, Footprints, Waves } from 'lucide-react'
import type { ComponentType } from 'react'

/** Icona per tipo di sport (da dieta.allenamento o dal piano Garmin — vedi
 * TrainingSession.sport_type). Euristica su parole chiave: i valori reali
 * variano ("running", "open_water_swimming", "strength_training", ...) e non
 * vale la pena mappare ogni typeKey esatto di Garmin uno per uno. */
export function iconForSportType(sportType: string | null): ComponentType<{ size?: number }> {
  if (!sportType) return Activity
  const key = sportType.toLowerCase()
  if (key.includes('run') || key.includes('walk')) return Footprints
  if (key.includes('swim')) return Waves
  if (key.includes('cycl') || key.includes('bike')) return Bike
  if (key.includes('strength') || key.includes('cardio') || key.includes('gym') || key.includes('training')) {
    return Dumbbell
  }
  return Activity
}
