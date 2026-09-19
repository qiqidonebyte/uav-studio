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

async function installCard(page, componentId) {
  const card = page.locator(`[data-testid="component-card"][data-component-id="${componentId}"]`)
  await card.waitFor({ state: 'visible' })
  const button = card.getByTestId('component-install')
  if (await button.isEnabled()) await button.click()
}

try {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } })
  page.on('console', message => {
    if (message.type() === 'error' || message.type() === 'warning') {
      console.error(`[browser:${message.type()}] ${message.text()}`)
    }
  })
  page.on('pageerror', error => {
    console.error(`[browser:pageerror] ${error.stack ?? error.message}`)
  })
  await page.goto(`${baseUrl}/assembly`, { waitUntil: 'networkidle' })
  await page.waitForFunction(
    () => document.querySelector('.aircraft-chip')?.textContent?.includes('EduQuad-650'),
  )

  assert.equal(await page.locator('.assembly-step').count(), 7)
  assert.match(await page.locator('.inspector-panel').innerText(), /2\.920 kg/)
  assert.match(await page.locator('.inspector-panel').innerText(), /3\.07/)

  const layout = await page.evaluate(() => {
    const canvas = document.querySelector('.drone-scene canvas')
    const bottom = document.querySelector('.assembly-bottom')
    return {
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      documentWidth: document.documentElement.scrollWidth,
      canvasWidth: canvas?.getBoundingClientRect().width ?? 0,
      canvasHeight: canvas?.getBoundingClientRect().height ?? 0,
      bottom: bottom?.getBoundingClientRect().bottom ?? Number.POSITIVE_INFINITY,
    }
  })
  assert.ok(layout.documentWidth <= layout.viewportWidth)
  assert.ok(layout.canvasWidth > 400)
  assert.ok(layout.canvasHeight > 300)
  assert.ok(layout.bottom <= layout.viewportHeight + 1)

  // Component Card replaces the old native select workflow.
  await page.locator('.assembly-step').nth(0).click()
  assert.equal(await page.locator('.component-picker select').count(), 0)
  assert.ok(await page.locator('[data-testid="component-card"]').count() >= 2)

  await installCard(page, 2)
  await page.waitForFunction(
    () => document.querySelector('.inspector-panel')?.textContent?.includes('2.770 kg'),
  )

  await installCard(page, 1)
  await page.waitForFunction(
    () => document.querySelector('.inspector-panel')?.textContent?.includes('2.920 kg'),
  )

  await page.locator('.assembly-step').nth(1).click()
  await page.waitForFunction(
    () =>
      document.querySelector(
        '.inspector-panel > .inspector-section:first-child .inspector-heading p',
      )?.textContent === '电机',
  )

  const motorCards = page.locator('[data-testid="component-card"][data-component-type="motor"]')
  assert.ok(await motorCards.count() >= 2)
  assert.equal(await motorCards.first().locator('img').isVisible(), true)

  await page.waitForFunction(
    () => window.__UAV_VISUAL_TEST__?.sceneReady === true,
    undefined,
    { timeout: 15000 },
  )
  const probe = await page.evaluate(() => window.__UAV_VISUAL_TEST__)
  assert.ok(probe)
  assert.equal(probe.selectedSlot, 'motor')
  assert.ok(probe.loadedAssets.some(asset => asset.slot === 'motor'))

  console.log('E2E PASS: component cards, engineering refresh and 3D visual probe')
} finally {
  await browser.close()
}
