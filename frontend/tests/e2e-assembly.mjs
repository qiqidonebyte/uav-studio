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

  await page.locator('.assembly-step').nth(0).click()
  const frameSelect = page.locator('.slot-picker select').first()
  await frameSelect.selectOption('2')
  await page.getByRole('button', { name: '更换组件' }).click()
  await page.waitForFunction(
    () => document.querySelector('.inspector-panel')?.textContent?.includes('2.770 kg'),
  )

  await frameSelect.selectOption('1')
  await page.getByRole('button', { name: '更换组件' }).click()
  await page.waitForFunction(
    () => document.querySelector('.inspector-panel')?.textContent?.includes('2.920 kg'),
  )

  await page.locator('.assembly-step').nth(1).click()
  await page.locator('.slot-picker-head').first().click()
  const selectedPartLabel = page.locator(
    '.inspector-panel > .inspector-section:first-child .inspector-heading p',
  )
  await page.waitForFunction(
    () =>
      document.querySelector(
        '.inspector-panel > .inspector-section:first-child .inspector-heading p',
      )?.textContent === '电机',
  )

  const canvas = page.locator('.drone-scene canvas')
  const box = await canvas.boundingBox()
  assert.ok(box)
  for (const ratio of [0.5, 0.58, 0.64, 0.7]) {
    await page.mouse.click(
      box.x + box.width / 2,
      box.y + box.height * ratio,
    )
    await page.waitForTimeout(100)
    const selected = await selectedPartLabel.innerText()
    if (selected === '机架') break
  }
  await page.waitForFunction(
    () =>
      document.querySelector(
        '.inspector-panel > .inspector-section:first-child .inspector-heading p',
      )?.textContent === '机架',
  )

  console.log('E2E PASS: assembly workflow, engineering refresh and 3D selection')
} finally {
  await browser.close()
}
