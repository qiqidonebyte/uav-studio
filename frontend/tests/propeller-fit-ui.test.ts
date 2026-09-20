import { describe, expect, it } from 'vitest'
import type {
  AircraftDefinition,
  AssemblyValidationResult,
} from '../src/types/aircraft'
import {
  ASSEMBLY_STEPS,
  getStepStatus,
} from '../src/utils/assembly'

const aircraft: AircraftDefinition = {
  id: 1,
  name: 'EduQuad-450',
  frame_id: 2,
  motor_id: 10,
  esc_id: 20,
  propeller_id: 31,
  battery_id: 40,
  power_module_id: 50,
  flight_controller_id: 60,
}

describe('propeller/frame visual fit mapping', () => {
  it('marks the propeller assembly step as error for rotor-disc overlap', () => {
    const validation: AssemblyValidationResult = {
      passed: false,
      blocking_errors: [
        {
          code: 'PROPELLER_FRAME_OVERLAP',
          severity: 'error',
          message: '旋翼盘重叠',
          affected_slots: ['frame', 'propeller'],
          affected_mounts: ['M1', 'M2', 'M3', 'M4'],
        },
      ],
      warnings: [],
    }

    expect(getStepStatus(ASSEMBLY_STEPS[5], aircraft, validation)).toBe('error')
    expect(getStepStatus(ASSEMBLY_STEPS[6], aircraft, validation)).toBe('error')
  })
})
