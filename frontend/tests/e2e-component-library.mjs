import assert from 'node:assert/strict'
import { launchBrowser, baseUrl, loginAsAdmin } from './p0-helpers.mjs'

const browser = await launchBrowser()
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, locale: 'zh-CN' })
  await loginAsAdmin(page)
  await page.goto(`${baseUrl}/components`, { waitUntil: 'networkidle' })
  await page.locator('.library-card').first().waitFor({ state: 'visible', timeout: 10000 })

  assert.ok(await page.locator('.library-card').count() >= 10, 'component library should show seeded components')
  await page.getByRole('button', { name: /电机/ }).first().click()
  await page.waitForTimeout(200)
  const motorCards = page.locator('.library-card')
  assert.ok(await motorCards.count() >= 2, 'motor category should show multiple motors')

  await motorCards.first().click()
  await page.getByRole('button', { name: '3D资产', exact: true }).click()
  await page.locator('.component-preview canvas').waitFor({ state: 'visible', timeout: 10000 })

  await page.getByRole('button', { name: '适配关系', exact: true }).click()
  await page.locator('.compat-group').first().waitFor({ state: 'visible', timeout: 5000 })

  const search = page.locator('.library-search')
  await search.fill('5010')
  await page.waitForTimeout(350)
  assert.equal(await page.locator('.library-card').count(), 1, 'search should narrow to the 5010 component')
  assert.ok((await page.locator('.library-card').first().innerText()).includes('5010'))

  console.log('E2E PASS: component library browse, filter, detail, 3D preview and compatibility')
} finally {
  await browser.close()
}
