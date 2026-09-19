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
  await page.goto(`${baseUrl}/flight`, { waitUntil: 'networkidle' })
  await page.waitForFunction(() => {
    const button = Array.from(document.querySelectorAll('button')).find(
      item => item.textContent?.trim() === '开始',
    )
    return button instanceof HTMLButtonElement && !button.disabled
  })

  await page.getByRole('button', { name: '开始' }).click()
  await waitForText(page, '.command-state', '运行中')
  await waitForText(page, '.aircraft-summary', '已连接')

  await page.getByRole('button', { name: '解锁' }).click()
  await waitForText(page, '.inspector-panel', '已解锁')

  const targetInput = page.locator('.control-block').nth(1).locator('input').first()
  await targetInput.fill('5')
  await page.getByRole('button', { name: '起飞' }).click()
  await waitForText(page, '.inspector-panel', '悬停', 30000)
  await waitForCondition(
    page,
    () => {
      const altitude = document
        .querySelector('.inspector-panel')
        ?.textContent?.match(/高度\s*([0-9.]+)\s*m/)
      return altitude ? Number(altitude[1]) >= 4.5 : false
    },
    15000,
  )

  const environment = page.locator('.control-block').nth(2)
  await environment.locator('input').nth(0).fill('5')
  await environment.locator('input').nth(1).fill('90')
  await page.getByRole('button', { name: '应用风场' }).click()

  await waitForCondition(
    page,
    () => {
      const outputTexts = Array.from(
        document.querySelectorAll('.motor-section tbody tr td:nth-child(2)'),
      ).map(cell => Number.parseFloat(cell.textContent ?? '0'))
      return Math.max(...outputTexts) - Math.min(...outputTexts) > 0.5
    },
    10000,
  )
  await waitForCondition(
    page,
    () => {
      const row = Array.from(document.querySelectorAll('.inspector-panel dl > div'))
        .find(item => item.textContent?.includes('X / Y'))
      const text = row?.querySelector('dd')?.textContent ?? ''
      const match = text.match(/[-\d.]+\s*\/\s*([-\d.]+)/)
      return match ? Math.abs(Number(match[1])) > 0.1 : false
    },
    10000,
  )

  await page.getByRole('button', { name: '基础地图' }).click()
  const map = page.locator('.local-map svg')
  const mapBox = await map.boundingBox()
  assert.ok(mapBox)
  await page.mouse.click(
    mapBox.x + mapBox.width * 0.62,
    mapBox.y + mapBox.height * 0.42,
  )
  await page.getByRole('button', { name: '设为目标点' }).click()
  await page.getByRole('button', { name: '添加航点' }).click()
  await page.waitForSelector('.target-label')
  await page.waitForSelector('.waypoint-label')

  assert.equal(await page.locator('.chart-box canvas').count(), 4)

  await page.getByRole('button', { name: '降落' }).click()
  await waitForText(page, '.inspector-panel', '待机', 30000)
  await waitForCondition(
    page,
    () => {
      const altitude = document
        .querySelector('.inspector-panel')
        ?.textContent?.match(/高度\s*([0-9.]+)\s*m/)
      return altitude ? Number(altitude[1]) < 0.1 : false
    },
    10000,
  )

  await page.getByRole('button', { name: '停止' }).click()
  await waitForText(page, '.command-state', '已停止')

  await page.getByRole('link', { name: '实验记录' }).click()
  await page.waitForSelector('.history-row a')
  await page.locator('.history-row a').first().click()
  await page.waitForSelector('.replay-grid')
  await page.waitForFunction(
    () => document.querySelectorAll('.chart-box canvas').length === 4,
  )
  await waitForCondition(
    page,
    () => document.querySelector('.replay-slider span')?.textContent?.includes('s'),
  )

  const replayTimeBefore = await page.locator('.replay-slider span').innerText()
  await page.getByRole('button', { name: '播放' }).click()
  await page.waitForTimeout(500)
  await page.getByRole('button', { name: '暂停' }).click()
  const replayTimeAfter = await page.locator('.replay-slider span').innerText()
  assert.notEqual(replayTimeAfter, replayTimeBefore)

  await page.getByRole('button', { name: '复位' }).click()
  await waitForCondition(
    page,
    () => document.querySelector('.replay-slider span')?.textContent?.startsWith('0.0 s'),
  )

  await page.getByRole('button', { name: '轨迹回放' }).click()
  await page.waitForSelector('.target-label')
  await page.waitForSelector('.waypoint-label')

  console.log('E2E PASS: full V1 flight, map, experiment and replay chain')
} finally {
  await browser.close()
}

async function waitForText(page, selector, text, timeout = 10000) {
  await page.waitForFunction(
    ({ selector, text }) =>
      document.querySelector(selector)?.textContent?.includes(text),
    { selector, text },
    { timeout },
  )
}

async function waitForCondition(page, predicate, timeout = 10000) {
  await page.waitForFunction(predicate, undefined, { timeout })
}
