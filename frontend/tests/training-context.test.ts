import { describe, expect, it } from 'vitest'
import {
  activeTrainingContext,
  clearTrainingContext,
  loadTrainingContext,
  trainingAwareTarget,
  trainingContextFromQuery,
} from '../src/utils/trainingContext'

function memoryStorage(): Storage {
  const values = new Map<string, string>()
  return {
    get length() { return values.size },
    clear: () => values.clear(),
    getItem: key => values.get(key) ?? null,
    key: index => [...values.keys()][index] ?? null,
    removeItem: key => { values.delete(key) },
    setItem: (key, value) => { values.set(key, value) },
  }
}

describe('训练任务上下文', () => {
  it('accepts only positive run and assignment identifiers', () => {
    expect(trainingContextFromQuery({ run: '12', assignment: '8', scenario: 'F06' })).toEqual({
      run: '12', assignment: '8', scenario: 'F06',
    })
    expect(trainingContextFromQuery({ run: '0', scenario: 'F06' })).toBeNull()
    expect(trainingContextFromQuery({ run: 'abc' })).toBeNull()
  })

  it('keeps one task across assembly, debugging and flight navigation', () => {
    const storage = memoryStorage()
    expect(activeTrainingContext({ run: '12', assignment: '8', scenario: 'F06' }, storage)).toEqual({
      run: '12', assignment: '8', scenario: 'F06',
    })
    expect(trainingAwareTarget('/debugging', {}, storage)).toEqual({
      path: '/debugging',
      query: { run: '12', assignment: '8', scenario: 'F06' },
    })
    expect(trainingAwareTarget('/flight', { run: '12' }, storage)).toEqual({
      path: '/flight',
      query: { run: '12', assignment: '8', scenario: 'F06' },
    })
  })

  it('does not leak a previous scenario into a different run', () => {
    const storage = memoryStorage()
    activeTrainingContext({ run: '12', scenario: 'F06' }, storage)
    expect(activeTrainingContext({ run: '13' }, storage)).toEqual({ run: '13' })
    expect(loadTrainingContext(storage)).toEqual({ run: '13' })
    clearTrainingContext(storage)
    expect(loadTrainingContext(storage)).toBeNull()
  })
})
