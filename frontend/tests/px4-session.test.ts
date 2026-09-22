import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { Px4Status } from '../src/api/px4'
import { px4SessionPresentation } from '../src/utils/px4Session'

function status(overrides: Partial<Px4Status>): Px4Status {
  return {
    dependency_available: true,
    running: false,
    connected: false,
    connection_url: 'classroom-pool',
    heartbeat_age_s: null,
    system_id: null,
    component_id: null,
    mode: 'WAITING',
    armed: false,
    last_error: '',
    uptime_s: 0,
    ...overrides,
  }
}

describe('PX4 classroom session presentation', () => {
  it('shows an actionable FIFO queue position', () => {
    const view = px4SessionPresentation(status({ session_status: 'queued', queue_position: 3 }))
    expect(view.tone).toBe('queued')
    expect(view.title).toBe('PX4 资源排队中')
    expect(view.detail).toContain('第 3 位')
    expect(view.detail).toContain('自动连接')
  })

  it('shows the allocated slot while SIH starts', () => {
    const view = px4SessionPresentation(status({ session_status: 'starting', slot_id: 7 }))
    expect(view.tone).toBe('starting')
    expect(view.title).toContain('#7')
    expect(view.detail).toContain('等待 Heartbeat')
  })

  it('shows the active slot after connection', () => {
    const view = px4SessionPresentation(status({
      connected: true,
      session_status: 'active',
      slot_id: 4,
      system_id: 5,
    }))
    expect(view.tone).toBe('ready')
    expect(view.statusText).toBe('槽位 #4 · 已连接')
  })

  it('is wired into both PX4 student workspaces', () => {
    const flightLab = readFileSync(new URL('../src/views/FlightLab.vue', import.meta.url), 'utf8')
    const debugging = readFileSync(new URL('../src/views/Debugging.vue', import.meta.url), 'utf8')
    expect(flightLab).toContain('px4-session-status')
    expect(flightLab).toContain('px4SessionPresentation')
    expect(debugging).toContain('px4-debug-queue')
    expect(debugging).toContain('刷新排队状态')
  })
})
