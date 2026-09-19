import assert from 'node:assert/strict'
import { launchBrowser, baseUrl } from './p0-helpers.mjs'

const browser = await launchBrowser()
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, locale: 'zh-CN' })
  await page.goto(`${baseUrl}/settings`, { waitUntil: 'networkidle' })
  await page.getByText('本地管理员').waitFor({ state: 'visible', timeout: 10000 })
  assert.ok((await page.locator('.settings-user').innerText()).includes('admin'))

  await page.getByRole('button', { name: /3D 显示/ }).click()
  const gridRow = page.locator('.toggle-row').filter({ hasText: '工程网格' })
  const gridToggle = gridRow.locator('input[type="checkbox"]')
  const original = await gridToggle.isChecked()
  await gridToggle.setChecked(!original)
  await page.getByRole('button', { name: '保存设置', exact: true }).click()
  await page.getByText('已保存').waitFor({ state: 'visible', timeout: 5000 })

  await page.reload({ waitUntil: 'networkidle' })
  await page.getByRole('button', { name: /3D 显示/ }).click()
  const persisted = page.locator('.toggle-row').filter({ hasText: '工程网格' }).locator('input[type="checkbox"]')
  assert.equal(await persisted.isChecked(), !original, '3D setting must persist after reload')

  // Restore the previous value so the test is repeatable.
  await persisted.setChecked(original)
  await page.getByRole('button', { name: '保存设置', exact: true }).click()
  await page.getByText('已保存').waitFor({ state: 'visible', timeout: 5000 })

  await page.getByRole('button', { name: /账户与密码/ }).click()
  assert.equal(await page.locator('input[disabled]').inputValue(), 'admin')
  assert.equal(await page.locator('input[type="password"]').count(), 3)

  console.log('E2E PASS: settings persistence and admin password UI')
} finally {
  await browser.close()
}
