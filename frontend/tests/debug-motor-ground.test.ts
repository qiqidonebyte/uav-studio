import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

function source(relative: string): string {
  return readFileSync(new URL(relative, import.meta.url), 'utf8')
}

describe('动力系统地面测试视图', () => {
  it('locks the aircraft pose and drives rotors from ground-test outputs', () => {
    const wrapper = source('../src/components/DebugMotorScene.vue')
    const scene = source('../src/components/DroneScene.vue')

    expect(wrapper).toContain('grounded')
    expect(wrapper).toContain('地面动力测试')
    expect(scene).toContain('props.grounded')
    expect(scene).toContain('restAircraftOnGround')
    expect(scene).toContain('new THREE.Box3().setFromObject(aircraftRenderer.root)')
    expect(scene).toContain('? [...frame.motors.outputs]')
    expect(scene).toContain('flightSmoothing.renderedThrusts = [...flightSmoothing.targetThrusts]')
    expect(scene).toContain('if (props.grounded)')
    expect(scene).toContain('grounded-test-state')
  })

  it('stops local and PX4 outputs immediately and blocks armed motor tests', () => {
    const debugging = source('../src/views/Debugging.vue')
    const api = source('../src/api/px4.ts')

    expect(debugging).toContain(':disabled="motorTestBusy || px4Armed"')
    expect(debugging).toContain('motorOutputs.value = [0, 0, 0, 0]')
    expect(debugging).toContain('await px4Api.stopMotors()')
    expect(debugging).not.toContain('motorOutputs.value = telemetry.motors.outputs')
    expect(api).toContain("'/motors/stop', { method: 'POST' }")
  })
})
