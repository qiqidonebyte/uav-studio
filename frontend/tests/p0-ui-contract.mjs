import { baseUrl, createRunner, launchBrowser, openAssembly } from './p0-helpers.mjs'

const { run, finish, assert } = createRunner('P0 UI Contract')
const browser = await launchBrowser()

try {
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    locale: 'zh-CN',
  })

  await openAssembly(page)

  await run('P0-UI-001', 'Topbar remains 56px', async () => {
    const h = await page.locator('.topbar').evaluate(el => el.getBoundingClientRect().height)
    assert.ok(Math.abs(h - 56) <= 1, `topbar=${h}`)
  })

  await run('P0-UI-002', 'assembly keeps left / stage / inspector three-column workbench', async () => {
    for (const selector of ['.left-panel', '.assembly-stage', '.inspector-panel']) {
      assert.equal(await page.locator(selector).isVisible(), true, `${selector} not visible`)
    }
    const boxes = await page.evaluate(() => {
      const rect = selector => document.querySelector(selector)?.getBoundingClientRect()
      const left = rect('.left-panel')
      const stage = rect('.assembly-stage')
      const right = rect('.inspector-panel')
      return {
        left: left ? { x: left.x, width: left.width } : null,
        stage: stage ? { x: stage.x, width: stage.width } : null,
        right: right ? { x: right.x, width: right.width } : null,
      }
    })
    assert.ok(boxes.left && boxes.stage && boxes.right)
    assert.ok(boxes.left.x < boxes.stage.x && boxes.stage.x < boxes.right.x)
  })

  await run('P0-UI-003', 'left and right panel widths stay in frozen ranges', async () => {
    const sizes = await page.evaluate(() => ({
      left: document.querySelector('.left-panel')?.getBoundingClientRect().width ?? 0,
      right: document.querySelector('.inspector-panel')?.getBoundingClientRect().width ?? 0,
    }))
    assert.ok(sizes.left >= 240 && sizes.left <= 300, `left=${sizes.left}`)
    assert.ok(sizes.right >= 280 && sizes.right <= 360, `right=${sizes.right}`)
  })

  await run('P0-UI-004', 'central stage occupies at least 45 percent of workbench content width', async () => {
    const sizes = await page.evaluate(() => {
      const workbench = document.querySelector('.workbench-grid')?.getBoundingClientRect()
      const stage = document.querySelector('.assembly-stage')?.getBoundingClientRect()
      return {
        workbench: workbench?.width ?? 0,
        stage: stage?.width ?? 0,
      }
    })
    assert.ok(sizes.workbench > 0)
    assert.ok(sizes.stage / sizes.workbench >= 0.45, `ratio=${sizes.stage / sizes.workbench}`)
  })

  await run('P0-UI-005', 'page has no horizontal overflow', async () => {
    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }))
    assert.ok(overflow.scrollWidth <= overflow.clientWidth + 1, JSON.stringify(overflow))
  })

  await run('P0-UI-006', 'assembly has exactly seven workflow steps', async () => {
    assert.equal(await page.locator('.assembly-step').count(), 7)
  })

  await run('P0-UI-007', '3D canvas remains a large central engineering viewport', async () => {
    const canvas = page.locator('.drone-scene canvas')
    await canvas.waitFor({ state: 'visible' })
    const box = await canvas.boundingBox()
    assert.ok(box)
    assert.ok(box.width >= 500, `canvas width=${box.width}`)
    assert.ok(box.height >= 400, `canvas height=${box.height}`)
  })

  await run('P0-UI-008', 'inspector does not horizontally overflow', async () => {
    const value = await page.locator('.inspector-panel').evaluate(el => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
    }))
    assert.ok(value.scrollWidth <= value.clientWidth + 1, JSON.stringify(value))
  })

  await run('P0-UI-009', 'component selection primary UI is no longer a native select list', async () => {
    await page.locator('.assembly-step').nth(1).click()
    assert.equal(
      await page.locator('.component-picker select').count(),
      0,
      'P0 requires Component Cards; native select is still the primary selector',
    )
  })

  await run('P0-UI-010', 'motor step renders at least two Component Cards', async () => {
    await page.locator('.assembly-step').nth(1).click()
    const cards = page.locator('[data-testid="component-card"][data-component-type="motor"]')
    assert.ok(await cards.count() >= 2, `motor cards=${await cards.count()}`)
  })

  await run('P0-UI-011', 'Component Card contains a visible thumbnail', async () => {
    const card = page.locator('[data-testid="component-card"]').first()
    await card.waitFor({ state: 'visible', timeout: 1000 })
    assert.equal(await card.locator('img').isVisible(), true)
  })

  await run('P0-UI-012', 'Component Card exposes name and mass with stable test ids', async () => {
    const card = page.locator('[data-testid="component-card"]').first()
    await card.waitFor({ state: 'visible', timeout: 1000 })
    assert.equal(await card.getByTestId('component-name').isVisible(), true)
    assert.equal(await card.getByTestId('component-mass').isVisible(), true)
  })

  await run('P0-UI-013', 'Component Card exposes at least one primary engineering spec', async () => {
    const card = page.locator('[data-testid="component-card"]').first()
    await card.waitFor({ state: 'visible', timeout: 1000 })
    assert.equal(await card.getByTestId('component-primary-spec').isVisible(), true)
  })

  await run('P0-UI-014', 'main assembly workbench stays inside 1600x1000 viewport', async () => {
    const bounds = await page.evaluate(() => {
      const bottom = document.querySelector('.assembly-bottom')?.getBoundingClientRect()
      return {
        viewportHeight: window.innerHeight,
        bottom: bottom?.bottom ?? Number.POSITIVE_INFINITY,
      }
    })
    assert.ok(bounds.bottom <= bounds.viewportHeight + 1, JSON.stringify(bounds))
  })

  await run('P0-UI-015', 'debugging workbench stays inside a 1366x768 classroom viewport', async () => {
    await page.setViewportSize({ width: 1366, height: 768 })
    await page.goto(`${baseUrl}/debugging?section=preflight`, { waitUntil: 'networkidle' })
    await page.locator('.debug-page').waitFor({ state: 'visible', timeout: 10000 })
    const bounds = await page.locator('.debug-page').evaluate(el => {
      const rect = el.getBoundingClientRect()
      return { top: rect.top, bottom: rect.bottom, viewportHeight: window.innerHeight }
    })
    assert.ok(bounds.top >= 0, JSON.stringify(bounds))
    assert.ok(bounds.bottom <= bounds.viewportHeight + 1, JSON.stringify(bounds))
  })

  await run('P0-UI-016', 'learning review can scroll to its return action', async () => {
    await page.goto(`${baseUrl}/review`, { waitUntil: 'networkidle' })
    const review = page.locator('.review-page')
    await review.waitFor({ state: 'visible', timeout: 10000 })
    const returnAction = page.locator('.transfer-card a')
    await returnAction.scrollIntoViewIfNeeded()
    assert.equal(await returnAction.isVisible(), true)
    const layout = await review.evaluate(el => ({ clientHeight: el.clientHeight, scrollHeight: el.scrollHeight }))
    assert.ok(layout.clientHeight > 0 && layout.scrollHeight >= layout.clientHeight, JSON.stringify(layout))
  })

  await run('P0-UI-017', 'Mode 2 virtual transmitter follows drag and springs the right stick to center', async () => {
    await page.goto(`${baseUrl}/debugging?section=rc`, { waitUntil: 'networkidle' })
    await page.locator('.virtual-transmitter').waitFor({ state: 'visible', timeout: 10000 })
    await page.locator('.virtual-rc-controls summary').click()
    const rightStick = page.locator('.stick-pad').nth(1)
    const box = await rightStick.boundingBox()
    assert.ok(box)
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
    await page.mouse.down()
    await page.mouse.move(box.x + box.width * .85, box.y + box.height * .15)
    const precisionInputs = page.locator('.virtual-rc-controls input')
    assert.ok(Number(await precisionInputs.nth(0).inputValue()) > 1750, 'roll did not follow right drag')
    assert.ok(Number(await precisionInputs.nth(1).inputValue()) > 1750, 'pitch did not follow upward drag')
    await page.mouse.up()
    assert.equal(await precisionInputs.nth(0).inputValue(), '1500')
    assert.equal(await precisionInputs.nth(1).inputValue(), '1500')

    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
    await page.mouse.down()
    await page.mouse.move(box.x + box.width * .8, box.y + box.height * .2)
    await page.evaluate(() => window.dispatchEvent(new Event('blur')))
    assert.equal(await precisionInputs.nth(0).inputValue(), '1500')
    assert.equal(await precisionInputs.nth(1).inputValue(), '1500')
    await page.mouse.up()
  })

  finish()
} finally {
  await browser.close()
}
