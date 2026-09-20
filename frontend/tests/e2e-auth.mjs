import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const baseUrl = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5174'
const edgePath =
  process.env.EDGE_PATH ??
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

const username = 'e2e_auth_student'
const password = 'uavstudio-e2e-2026'

const browser = await chromium.launch({
  executablePath: edgePath,
  headless: true,
})

try {
  const context = await browser.newContext({
    viewport: { width: 1500, height: 960 },
    locale: 'zh-CN',
  })
  const page = await context.newPage()

  // Anonymous users are sent to login.
  await page.goto(`${baseUrl}/aircraft`, { waitUntil: 'networkidle' })
  await page.waitForURL('**/login**')
  await page.getByTestId('login-form').waitFor()

  // Try the stable E2E account first. Register it on the first run only.
  await page.getByTestId('login-username').fill(username)
  await page.getByTestId('login-password').fill(password)
  await page.getByTestId('login-submit').click()

  const loggedIn = await page
    .waitForURL('**/aircraft', { timeout: 2500 })
    .then(() => true)
    .catch(() => false)

  if (!loggedIn) {
    await page.goto(`${baseUrl}/register`, { waitUntil: 'networkidle' })
    await page.getByTestId('register-form').waitFor()
    await page.getByTestId('register-username').fill(username)
    await page.getByTestId('register-display-name').fill('E2E 学生')
    await page.getByTestId('register-password').fill(password)
    await page.getByTestId('register-confirm').fill(password)
    await page.getByTestId('register-submit').click()
    await page.waitForURL('**/aircraft', { timeout: 10000 })
  }

  // New accounts receive an isolated workspace and the first reference design.
  await page.getByTestId('aircraft-library-grid').waitFor({ timeout: 15000 })
  const bodyText = await page.locator('body').innerText()
  assert.match(bodyText, /我的飞机/)
  assert.match(bodyText, /\/ 10/)
  assert.match(bodyText, /E2E 学生|e2e_auth_student/)

  // Server session cookie must be HttpOnly; JS cannot read it.
  const cookies = await context.cookies()
  const sessionCookie = cookies.find(cookie => cookie.name === 'uav_session')
  assert.ok(sessionCookie, 'uav_session cookie missing')
  assert.equal(sessionCookie.httpOnly, true)
  assert.match(sessionCookie.sameSite, /Lax/i)
  const documentCookie = await page.evaluate(() => document.cookie)
  assert.ok(!documentCookie.includes('uav_session='))

  // Logout returns to login and protected routes stay protected.
  await page.getByRole('button', { name: '退出' }).click()
  await page.waitForURL('**/login', { timeout: 10000 })
  await page.goto(`${baseUrl}/assembly`, { waitUntil: 'networkidle' })
  await page.waitForURL('**/login**')

  // Log back in and verify the same saved workspace returns.
  await page.getByTestId('login-username').fill(username)
  await page.getByTestId('login-password').fill(password)
  await page.getByTestId('login-submit').click()
  await page.waitForURL('**/aircraft', { timeout: 10000 })
  await page.getByTestId('aircraft-library-grid').waitFor({ timeout: 15000 })
  assert.ok(
    (await page.getByTestId('aircraft-design-card').count()) >= 1,
    'saved aircraft workspace did not return after login',
  )

  console.log('E2E PASS: register/login/logout/session cookie/workspace restore/10-aircraft quota UI')
} finally {
  await browser.close()
}
