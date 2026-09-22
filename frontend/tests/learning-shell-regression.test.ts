import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

function source(relative: string): string {
  return readFileSync(new URL(relative, import.meta.url), 'utf8')
}

describe('Learning Guide V1 页面收口', () => {
  it('preserves the active training task in page-local navigation', () => {
    expect(source('../src/views/Assembly.vue')).toContain(":to=\"debuggingRoute\"")
    expect(source('../src/views/FlightLab.vue')).toContain(":to=\"assemblyRoute\"")
    expect(source('../src/views/FlightLab.vue')).toContain(":to=\"debuggingRoute\"")
  })

  it('does not mistake visited-looking stages for completed evidence', () => {
    const nav = source('../src/components/LearningTaskNav.vue')
    expect(nav).not.toContain('index < currentIndex')
    expect(nav).not.toContain('completed:')
  })

  it('lets the app shell allocate space for both navigation rows', () => {
    const app = source('../src/App.vue')
    const workbench = source('../src/styles/workbench.css')
    const safeTheme = source('../src/styles/tech-theme-safe.css')
    expect(app).toContain('class="app-content"')
    expect(workbench).toContain('grid-template-rows: 56px auto minmax(0, 1fr)')
    expect(`${workbench}\n${safeTheme}`).not.toContain('calc(100vh - 56px)')
  })
})
