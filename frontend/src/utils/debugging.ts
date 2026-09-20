import type { MotorName } from '../types/aircraft'

export type DebugScenario = 'standard' | 'mapping' | 'compass' | 'failsafe'

export function resolveMotorResponse(
  scenario: DebugScenario,
  mappingRepaired: boolean,
  command: MotorName,
): MotorName {
  if (scenario === 'mapping' && !mappingRepaired && command === 'M1') return 'M3'
  return command
}

export function calculateDebugScore(
  scenario: DebugScenario,
  mappingRepaired: boolean,
  assemblyPassed: boolean,
  compassRepaired = false,
  failsafeRepaired = false,
): number {
  let value = 100
  if (scenario === 'mapping' && !mappingRepaired) value -= 22
  if (scenario === 'compass' && !compassRepaired) value -= 18
  if (scenario === 'failsafe' && !failsafeRepaired) value -= 16
  if (!assemblyPassed) value -= 20
  return Math.max(0, value)
}
