import { describe, expect, it } from 'vitest'
import type {
  AircraftDefinition,
  AssemblyValidationResult,
  Component,
} from '../src/types/aircraft'
import {
  ASSEMBLY_STEPS,
  assemblySlotFromScenePart,
  componentFitsSlot,
  getStepStatus,
  slotComponents,
} from '../src/utils/assembly'
import { motorPositionsToThree } from '../src/three/coordinates'

const aircraft: AircraftDefinition = {
  id: 1,
  name: 'EduQuad-650',
  frame_id: 1,
  motor_id: 10,
  esc_id: 20,
  propeller_id: 30,
  battery_id: 40,
  power_module_id: 50,
  flight_controller_id: 60,
  gnss_id: 70,
  payload_id: 80,
  gnss_position_m: { x: -0.16, y: 0, z: 0.08 },
  payload_position_m: { x: 0.08, y: 0, z: -0.12 },
}

const passedValidation: AssemblyValidationResult = {
  passed: true,
  blocking_errors: [],
  warnings: [],
}

describe('assembly workflow', () => {
  it('defines all seven frozen assembly steps', () => {
    expect(ASSEMBLY_STEPS.map(step => step.title)).toEqual([
      '机架',
      '动力系统',
      '供电系统',
      '飞控与导航',
      '任务载荷',
      '螺旋桨',
      '装配检查',
    ])
    expect(ASSEMBLY_STEPS[5].detail).toContain('顺时针/逆时针')
  })

  it('marks configured steps as complete and the final check as passed', () => {
    expect(getStepStatus(ASSEMBLY_STEPS[0], aircraft, passedValidation)).toBe('done')
    expect(getStepStatus(ASSEMBLY_STEPS[6], aircraft, passedValidation)).toBe('done')
  })

  it('marks missing required components as pending and the check as failed', () => {
    const incomplete = { ...aircraft, motor_id: null }
    const validation: AssemblyValidationResult = {
      passed: false,
      blocking_errors: [
        {
          code: 'REQUIRED_COMPONENT_MISSING',
          severity: 'error',
          message: '必需组件缺失或不可用：motor',
        },
      ],
      warnings: [],
    }

    expect(getStepStatus(ASSEMBLY_STEPS[1], incomplete, validation)).toBe('pending')
    expect(getStepStatus(ASSEMBLY_STEPS[6], incomplete, validation)).toBe('error')
  })

  it('shows backend electrical failures on the matching assembly step', () => {
    const validation: AssemblyValidationResult = {
      passed: false,
      blocking_errors: [
        {
          code: 'VOLTAGE_INCOMPATIBLE',
          severity: 'error',
          message: '电池电压范围与电调不兼容',
        },
      ],
      warnings: [],
    }

    expect(getStepStatus(ASSEMBLY_STEPS[2], aircraft, validation)).toBe('error')
  })

  it('maps scene parts to their installation slot', () => {
    expect(assemblySlotFromScenePart('motor_1')).toBe('motor')
    expect(assemblySlotFromScenePart('esc_4')).toBe('esc')
    expect(assemblySlotFromScenePart('propeller_3')).toBe('propeller')
    expect(assemblySlotFromScenePart('battery')).toBe('battery')
    expect(assemblySlotFromScenePart('unknown')).toBeNull()
  })

  it('filters catalog components by slot type', () => {
    const components: Component[] = [
      {
        id: 10,
        name: 'EduMotor-5010',
        type: 'motor',
        mass_kg: 0.18,
        parameters_json: {},
      },
      {
        id: 30,
        name: 'EduProp-15x5',
        type: 'propeller',
        mass_kg: 0.025,
        parameters_json: {},
      },
    ]

    expect(slotComponents(components, 'motor').map(component => component.id)).toEqual([10])
    expect(componentFitsSlot(components[1], 'propeller')).toBe(true)
    expect(componentFitsSlot(components[1], 'motor')).toBe(false)
  })
})

describe('3D coordinate conversion', () => {
  it('maps simulator X/Y/Z and frozen motor order into Three.js coordinates', () => {
    const positions = motorPositionsToThree(0.65)

    expect(positions.M1.x).toBeGreaterThan(0)
    expect(positions.M1.z).toBeLessThan(0)
    expect(positions.M2.x).toBeGreaterThan(0)
    expect(positions.M2.z).toBeGreaterThan(0)
    expect(positions.M3.x).toBeLessThan(0)
    expect(positions.M3.z).toBeGreaterThan(0)
    expect(positions.M4.x).toBeLessThan(0)
    expect(positions.M4.z).toBeLessThan(0)
  })
})
