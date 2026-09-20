import { describe, expect, it } from 'vitest'
import {
  applyDebuggingScenario,
  defaultDebuggingBenchState,
  evaluateDebugging,
} from '../src/utils/debugging'
import type { DebuggingContext } from '../src/types/debugging'

const context: DebuggingContext = {
  validationPassed: true,
  blockingErrorCount: 0,
  warningCount: 0,
  engineeringAvailable: true,
  thrustWeightRatio: 2.1,
  cgHorizontalM: 0.01,
  escCurrentMarginA: 18,
  batteryContinuousMarginA: 40,
  powerModuleCurrentMarginA: 25,
  batteryMinVoltageV: 19.8,
  batteryNominalVoltageV: 22.2,
  batteryMaxVoltageV: 25.2,
}

describe('debugging workbench evaluation', () => {
  it('marks the normal teaching preset ready', () => {
    const result = evaluateDebugging(defaultDebuggingBenchState(22.2), context)
    expect(result.readiness).toBe('READY')
    expect(result.errorCount).toBe(0)
    expect(result.score).toBe(100)
  })

  it('blocks a motor fault scenario', () => {
    const normal = defaultDebuggingBenchState(22.2)
    const result = evaluateDebugging(applyDebuggingScenario('motor', normal), context)
    expect(result.readiness).toBe('BLOCKED')
    expect(result.checks.find(item => item.key === 'motor-M2')?.severity).toBe('error')
    expect(result.checks.find(item => item.key === 'motor-M4')?.severity).toBe('error')
  })

  it('blocks an aircraft with assembly errors regardless of bench state', () => {
    const result = evaluateDebugging(defaultDebuggingBenchState(22.2), {
      ...context,
      validationPassed: false,
      blockingErrorCount: 2,
    })
    expect(result.readiness).toBe('BLOCKED')
    expect(result.checks.find(item => item.key === 'assembly')?.severity).toBe('error')
  })
})
