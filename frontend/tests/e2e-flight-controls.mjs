import assert from 'node:assert/strict'
import { baseUrl, launchBrowser, loginAsAdmin } from './p0-helpers.mjs'

const browser = await launchBrowser()

async function disabled(page, testId) {
  return page.getByTestId(testId).isDisabled()
}

try {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } })
  await loginAsAdmin(page)
  await page.goto(`${baseUrl}/flight`, { waitUntil: 'networkidle' })
  await page.getByTestId('flight-start').waitFor({ state: 'visible' })

  // Initial state: only Start may be used.
  assert.equal(await disabled(page, 'flight-start'), false)
  assert.equal(await disabled(page, 'flight-arm'), true)
  assert.equal(await disabled(page, 'flight-takeoff'), true)
  assert.equal(await disabled(page, 'flight-land'), true)

  await page.getByTestId('flight-start').click()
  await page.waitForFunction(() =>
    document.querySelector('.command-state')?.textContent?.includes('运行中'),
  )

  // Running but still locked: Arm enabled, Takeoff still gray/disabled.
  assert.equal(await disabled(page, 'flight-start'), true)
  assert.equal(await disabled(page, 'flight-arm'), false)
  assert.equal(await disabled(page, 'flight-takeoff'), true)
  assert.equal(await disabled(page, 'flight-land'), true)

  await page.getByTestId('flight-arm').click()
  await page.waitForFunction(() =>
    document.querySelector('.inspector-panel')?.textContent?.includes('已解锁'),
  )

  // Armed: only Takeoff is valid.
  assert.equal(await disabled(page, 'flight-arm'), true)
  assert.equal(await disabled(page, 'flight-takeoff'), false)
  assert.equal(await disabled(page, 'flight-land'), true)

  await page.getByTestId('flight-takeoff').click()
  await page.waitForFunction(() => {
    const text = document.querySelector('.inspector-panel')?.textContent ?? ''
    return text.includes('起飞中') || text.includes('悬停')
  })

  // Once takeoff starts, repeated takeoff is locked and Land becomes valid.
  assert.equal(await disabled(page, 'flight-takeoff'), true)
  assert.equal(await disabled(page, 'flight-land'), false)

  console.log('E2E PASS: Start -> Arm -> Takeoff -> Land gating is preserved')
} finally {
  await browser.close()
}
