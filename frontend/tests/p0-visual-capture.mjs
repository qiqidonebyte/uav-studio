import path from 'node:path'
import { launchBrowser, openAssembly, outputDir, baseUrl } from './p0-helpers.mjs'

const browser = await launchBrowser()
const dir = outputDir('p0-visual-candidates')

async function shot(page, name) {
  const file = path.join(dir, `${name}.png`)
  await page.screenshot({ path: file, fullPage: false })
  console.log(`CAPTURE ${file}`)
}

try {
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    locale: 'zh-CN',
  })

  await openAssembly(page)
  await page.waitForTimeout(500)
  await shot(page, '01-assembly-current')

  await page.locator('.assembly-step').nth(1).click()
  await page.waitForTimeout(250)
  await shot(page, '02-assembly-motor-step-current')

  await page.goto(`${baseUrl}/flight`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  await shot(page, '03-flight-3d-current')

  const mapButton = page.getByRole('button', { name: '基础地图', exact: true })
  if (await mapButton.count()) {
    await mapButton.click()
    await page.waitForTimeout(200)
    await shot(page, '04-flight-map-current')
  }

  const splitButton = page.getByRole('button', { name: '分屏', exact: true })
  if (await splitButton.count()) {
    await splitButton.click()
    await page.waitForTimeout(200)
    await shot(page, '05-flight-split-current')
  }

  await page.goto(`${baseUrl}/history`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(250)
  await shot(page, '06-history-current')

  console.log('\nThese are review candidates only. They are NOT Golden Screenshots.')
} finally {
  await browser.close()
}
