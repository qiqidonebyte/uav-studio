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
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    locale: 'zh-CN',
  })

  page.on('dialog', async dialog => {
    await dialog.accept()
  })

  await page.goto(`${baseUrl}/aircraft`, { waitUntil: 'networkidle' })
  await page.getByTestId('aircraft-library-grid').waitFor()

  const initialCount = await page.getByTestId('aircraft-design-card').count()
  assert.ok(initialCount >= 1)

  // Create a real independent design from a stable template.
  await page.getByTestId('new-aircraft').click()
  const dialog = page.getByTestId('new-aircraft-dialog')
  await dialog.waitFor()
  await dialog.locator('[data-template-key="blank-quad-x"]').click()
  await dialog.locator('input').fill('E2E Aircraft Library')
  await dialog.locator('textarea').fill('Temporary design created by the Aircraft Library E2E.')
  await dialog.getByTestId('create-aircraft-submit').click()
  await page.waitForURL('**/assembly')

  assert.match(await page.locator('.aircraft-chip').innerText(), /E2E Aircraft Library/)
  assert.match(await page.locator('.save-pill').innerText(), /已保存/)

  // Return to portfolio; created design must survive navigation and database reload.
  await page.goto(`${baseUrl}/aircraft`, { waitUntil: 'networkidle' })
  const createdCard = page.getByTestId('aircraft-design-card').filter({
    hasText: 'E2E Aircraft Library',
  })
  await createdCard.waitFor()
  assert.match(await createdCard.innerText(), /当前设计/)

  // Duplicate / Save As is a first-class design operation.
  await createdCard.getByTestId('duplicate-aircraft-design').click()
  const copyCard = page.getByTestId('aircraft-design-card').filter({
    hasText: 'E2E Aircraft Library - 副本',
  })
  await copyCard.waitFor()
  assert.equal(
    await page.getByTestId('aircraft-design-card').count(),
    initialCount + 2,
  )

  // Edit metadata on the copy.
  await copyCard.locator('.icon-button').click()
  const editDialog = page.getByTestId('edit-aircraft-dialog')
  await editDialog.waitFor()
  await editDialog.locator('input').fill('E2E Aircraft Library Copy')
  await editDialog.locator('textarea').fill('Renamed duplicate.')
  await editDialog.getByText('保存信息').click()
  await page.getByTestId('aircraft-design-card').filter({
    hasText: 'E2E Aircraft Library Copy',
  }).waitFor()

  // Clean up duplicate and original so the suite is repeatable.
  const renamedCopy = page.getByTestId('aircraft-design-card').filter({
    hasText: 'E2E Aircraft Library Copy',
  })
  await renamedCopy.locator('.icon-button').click()
  await page.getByTestId('edit-aircraft-dialog').getByTestId('delete-aircraft-design').click()
  await page.waitForFunction(
    () => !document.body.innerText.includes('E2E Aircraft Library Copy'),
  )

  const original = page.getByTestId('aircraft-design-card').filter({
    hasText: 'E2E Aircraft Library',
  })
  await original.locator('.icon-button').click()
  await page.getByTestId('edit-aircraft-dialog').getByTestId('delete-aircraft-design').click()
  await page.waitForFunction(
    () => !document.body.innerText.includes('E2E Aircraft Library'),
  )

  assert.equal(
    await page.getByTestId('aircraft-design-card').count(),
    initialCount,
  )

  console.log('E2E PASS: create, persist, duplicate, rename, delete and active-design save status')
} finally {
  await browser.close()
}
