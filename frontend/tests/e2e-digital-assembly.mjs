import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const baseUrl = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5174'
const edgePath =
  process.env.EDGE_PATH ??
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

const browser = await chromium.launch({
  executablePath: edgePath,
  headless: true,
})

async function waitScene(page) {
  await page.waitForFunction(
    () => window.__UAV_VISUAL_TEST__?.sceneReady === true,
    undefined,
    { timeout: 15000 },
  )
}

async function probe(page) {
  return page.evaluate(() => window.__UAV_VISUAL_TEST__)
}

async function card(page, id) {
  const value = page.locator(`[data-testid="component-card"][data-component-id="${id}"]`)
  await value.waitFor({ state: 'visible' })
  return value
}

try {
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    locale: 'zh-CN',
  })
  await page.goto(`${baseUrl}/assembly`, { waitUntil: 'networkidle' })
  await waitScene(page)

  // Motor step: enter constrained physical assembly instead of quick configure.
  await page.locator('.assembly-step').nth(1).click()
  const motor = await card(page, 10)
  await motor.getByTestId('component-3d-assemble').click()

  await page.getByTestId('assembly-session-card').waitFor()
  await page.waitForFunction(
    () =>
      window.__UAV_VISUAL_TEST__?.pendingInstall?.slot === 'motor' &&
      document.querySelectorAll('[data-testid="assembly-mount-hotspot"]').length === 4,
    undefined,
    { timeout: 10000 },
  )

  let value = await probe(page)
  assert.ok(value)
  assert.equal(value.pendingInstall.slot, 'motor')
  assert.equal(value.partInstances.filter(item => item.slot === 'motor' && item.installed).length, 0)

  for (const mountId of ['motor:M1', 'motor:M2', 'motor:M3', 'motor:M4']) {
    const hotspot = page.locator(
      `[data-testid="assembly-mount-hotspot"][data-mount-id="${mountId}"]`,
    )
    await hotspot.hover()
    await page.waitForFunction(
      id => window.__UAV_VISUAL_TEST__?.hoveredMountId === id,
      mountId,
    )
    await hotspot.click()
    await page.waitForFunction(
      id => window.__UAV_VISUAL_TEST__?.partInstances.some(
        item => item.mountId === id && item.installed,
      ),
      mountId,
      { timeout: 10000 },
    )
  }

  await page.waitForFunction(
    () =>
      window.__UAV_VISUAL_TEST__?.pendingInstall === null &&
      window.__UAV_VISUAL_TEST__?.partInstances.filter(
        item => item.slot === 'motor' && item.installed,
      ).length === 4,
    undefined,
    { timeout: 10000 },
  )
  assert.match(await page.getByTestId('mount-inspector').innerText(), /motor:M4/)

  // Remove one independent instance: backend validation must block the aircraft.
  await page.getByTestId('remove-selected-mount').click()
  await page.waitForFunction(
    () =>
      window.__UAV_VISUAL_TEST__?.partInstances.filter(
        item => item.slot === 'motor' && item.installed,
      ).length === 3,
    undefined,
    { timeout: 10000 },
  )
  assert.match(await page.locator('.inspector-panel').innerText(), /物理装配尚未完成/)

  // Restore reference state through the compatibility quick-config path.
  await page.locator('.assembly-step').nth(1).click()
  const restoreMotor = await card(page, 10)
  await restoreMotor.getByTestId('component-install').click()
  await page.waitForFunction(
    () =>
      window.__UAV_VISUAL_TEST__?.partInstances.filter(
        item => item.slot === 'motor' && item.installed,
      ).length === 4,
    undefined,
    { timeout: 10000 },
  )

  // Visual envelope: the larger 16 Ah battery must trigger a teaching warning.
  await page.locator('.assembly-step').nth(2).click()
  const largeBattery = await card(page, 41)
  await largeBattery.getByTestId('component-install').click()
  await page.waitForFunction(
    () => window.__UAV_VISUAL_TEST__?.spatialDiagnostics.some(
      item => item.code === 'BATTERY_ENVELOPE_EXCEEDED',
    ),
    undefined,
    { timeout: 10000 },
  )

  // Restore 10 Ah reference battery for subsequent suites.
  const referenceBattery = await card(page, 40)
  await referenceBattery.getByTestId('component-install').click()
  await page.waitForFunction(
    () => !window.__UAV_VISUAL_TEST__?.spatialDiagnostics.some(
      item => item.code === 'BATTERY_ENVELOPE_EXCEEDED',
    ),
    undefined,
    { timeout: 10000 },
  )

  console.log('E2E PASS: mount anchors, Ghost/Snap assembly, per-mount removal, spatial envelope')
} finally {
  await browser.close()
}
