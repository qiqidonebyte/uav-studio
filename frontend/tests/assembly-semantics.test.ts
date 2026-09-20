import { describe, expect, it } from 'vitest'
import type { AircraftDefinition, Component } from '../src/types/aircraft'
import {
  assemblyInstancesFor,
  batteryBayFit,
  buildMountPoints,
  clearSlotInstances,
  legacyAssemblyInstances,
  replaceSlotInstances,
  rotorDiscDiagnostics,
  slotCompletion,
} from '../src/three/assemblySemantics'

const frame650: Component = {
  id: 1,
  name: 'EduFrame-650',
  type: 'frame',
  mass_kg: 0.45,
  parameters_json: {
    motor_diagonal_m: 0.65,
    battery_position_m: { x: -0.03, y: 0, z: -0.10 },
    power_module_position_m: { x: 0, y: 0, z: 0.02 },
    flight_controller_position_m: { x: 0, y: 0, z: 0.05 },
    gnss_mount_position_m: { x: -0.16, y: 0, z: 0.08 },
  },
}
const frame450: Component = {
  ...frame650,
  id: 2,
  name: 'EduFrame-450',
  parameters_json: {
    ...frame650.parameters_json,
    motor_diagonal_m: 0.45,
  },
}
const prop15: Component = {
  id: 30,
  name: 'EduProp-15',
  type: 'propeller',
  mass_kg: 0.025,
  parameters_json: { diameter_in: 15, pitch_in: 5, direction: 'PAIR' },
}

function aircraft(frameId = 1): AircraftDefinition {
  return {
    id: 1,
    name: 'Test Quad',
    frame_id: frameId,
    motor_id: 10,
    esc_id: 20,
    propeller_id: 30,
    battery_id: 40,
    power_module_id: 50,
    flight_controller_id: 60,
    gnss_id: 70,
    payload_id: 80,
  }
}

describe('3D assembly semantic contract', () => {
  it('builds deterministic mount anchors for the complete Quad-X', () => {
    const mounts = buildMountPoints(aircraft(), [frame650, prop15])
    expect(mounts).toHaveLength(18)
    expect(mounts.filter(item => item.slot === 'motor')).toHaveLength(4)
    expect(mounts.filter(item => item.slot === 'esc')).toHaveLength(4)
    expect(mounts.filter(item => item.slot === 'propeller')).toHaveLength(4)

    const m1 = mounts.find(item => item.id === 'motor:M1')!
    const m3 = mounts.find(item => item.id === 'motor:M3')!
    expect(m1.position.x).toBeGreaterThan(0)
    expect(m1.position.y).toBeGreaterThan(0)
    expect(m3.position.x).toBeLessThan(0)
    expect(m3.position.y).toBeLessThan(0)
    expect(m1.position.z).toBeGreaterThan(0)
  })

  it('expands a legacy slot-level aircraft to mount-scoped instances', () => {
    const current = aircraft()
    const instances = legacyAssemblyInstances(current)
    expect(instances).toHaveLength(18)
    expect(assemblyInstancesFor(current)).toHaveLength(18)
  })

  it('clears and re-populates one repeated slot without touching other slots', () => {
    const current = aircraft()
    const mounts = buildMountPoints(current, [frame650, prop15])
    const explicit: AircraftDefinition = {
      ...current,
      assembly_instances: legacyAssemblyInstances(current),
    }
    const cleared: AircraftDefinition = {
      ...explicit,
      assembly_instances: clearSlotInstances(explicit, 'motor'),
    }
    expect(slotCompletion(cleared, 'motor')).toEqual({ installed: 0, total: 4 })
    expect(slotCompletion(cleared, 'esc')).toEqual({ installed: 4, total: 4 })

    const replaced = replaceSlotInstances(cleared, mounts, 'motor', 11)
    expect(replaced.filter(item => item.slot === 'motor')).toHaveLength(4)
    expect(replaced.filter(item => item.slot === 'motor').every(item => item.component_id === 11)).toBe(true)
  })

  it('detects 450 + 15 inch rotor-disc collision but keeps 650 clear', () => {
    const a650: AircraftDefinition = {
      ...aircraft(1),
      assembly_instances: legacyAssemblyInstances(aircraft(1)),
    }
    const a450: AircraftDefinition = {
      ...aircraft(2),
      assembly_instances: legacyAssemblyInstances(aircraft(2)),
    }
    expect(rotorDiscDiagnostics(a650, [frame650, frame450, prop15], buildMountPoints(a650, [frame650, frame450, prop15]))).toHaveLength(0)

    const bad = rotorDiscDiagnostics(
      a450,
      [frame650, frame450, prop15],
      buildMountPoints(a450, [frame650, frame450, prop15]),
    )
    expect(bad).toHaveLength(1)
    expect(bad[0].code).toBe('ROTOR_DISC_COLLISION')
    expect(bad[0].mountIds.length).toBeGreaterThan(1)
  })

  it('uses a scale-aware teaching battery bay envelope', () => {
    expect(
      batteryBayFit(0.65, { x: 0.2259, y: 0.0678, z: 0.0797 }).fits,
    ).toBe(true)
    const large = batteryBayFit(0.65, { x: 0.2637, y: 0.0786, z: 0.09182 })
    expect(large.fits).toBe(false)
    expect(Math.max(large.excess.x, large.excess.y, large.excess.z)).toBeGreaterThan(0)
  })
})
