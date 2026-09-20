import { describe, expect, it } from 'vitest'
import type { AircraftDefinition, AssemblyValidationResult } from '../src/types/aircraft'
import { ASSEMBLY_STEPS, getStepStatus } from '../src/utils/assembly'

const aircraft: AircraftDefinition = {
  name: 'EduQuad-650',
  frame_id: 1,
  motor_id: 10,
  esc_id: 20,
  propeller_id: 30,
  battery_id: 40,
  power_module_id: 50,
  flight_controller_id: 60,
}

describe('digital assembly issue routing', () => {
  it('marks only the affected step when a physical mount is incomplete', () => {
    const validation: AssemblyValidationResult = {
      passed: false,
      blocking_errors: [{
        code: 'ASSEMBLY_MOUNT_INCOMPLETE',
        severity: 'error',
        message: 'motor:M2 pending',
        affected_slots: ['motor'],
        affected_mount_ids: ['motor:M2'],
      }],
      warnings: [],
    }

    expect(getStepStatus(ASSEMBLY_STEPS[1], aircraft, validation)).toBe('error')
    expect(getStepStatus(ASSEMBLY_STEPS[2], aircraft, validation)).toBe('done')
    expect(getStepStatus(ASSEMBLY_STEPS[6], aircraft, validation)).toBe('error')
  })
})
