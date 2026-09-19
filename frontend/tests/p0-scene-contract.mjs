import { createRunner, launchBrowser, openAssembly } from './p0-helpers.mjs'

const { run, finish, assert } = createRunner('P0 Three.js Scene Contract')
const browser = await launchBrowser()

async function probe(page) {
  return page.evaluate(() => window.__UAV_VISUAL_TEST__ ?? null)
}

function requireProbe(value) {
  assert.ok(value, 'window.__UAV_VISUAL_TEST__ is not implemented')
  return value
}

async function waitSceneReady(page) {
  await page.waitForFunction(
    () => window.__UAV_VISUAL_TEST__?.sceneReady === true,
    undefined,
    { timeout: 15000 },
  )
}

async function installCard(page, componentId) {
  const card = page.locator(`[data-testid="component-card"][data-component-id="${componentId}"]`)
  await card.waitFor({ state: 'visible', timeout: 5000 })
  const button = card.getByTestId('component-install')
  if (await button.isEnabled()) await button.click()
  await page.waitForFunction(
    id => {
      const probe = window.__UAV_VISUAL_TEST__
      return Boolean(
        probe?.sceneReady &&
        probe.loadedAssets.some(asset => asset.componentId === id),
      )
    },
    componentId,
    { timeout: 15000 },
  )
}

try {
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    locale: 'zh-CN',
  })
  await openAssembly(page)
  await waitSceneReady(page)

  await run('P0-SCENE-001', 'visual test probe exists', async () => {
    requireProbe(await probe(page))
  })

  await run('P0-SCENE-002', 'probe reports version 1.0 and sceneReady=true', async () => {
    const value = requireProbe(await probe(page))
    assert.equal(value.version, '1.0')
    assert.equal(value.sceneReady, true)
  })

  await run('P0-SCENE-003', 'visual test mode fixes renderer pixel ratio to 1', async () => {
    const value = requireProbe(await probe(page))
    assert.equal(value.pixelRatio, 1)
  })

  await run('P0-SCENE-004', 'probe reports real GLB assets loaded for core installed parts', async () => {
    const value = requireProbe(await probe(page))
    const slots = new Set(value.loadedAssets.map(item => item.slot))
    for (const slot of ['frame', 'motor', 'esc', 'propeller', 'battery', 'flight_controller']) {
      assert.ok(slots.has(slot), `missing loaded asset slot ${slot}`)
    }
    for (const asset of value.loadedAssets) {
      assert.ok(asset.url.endsWith('.glb'), `not GLB: ${asset.url}`)
    }
  })

  await run('P0-SCENE-005', 'probe exposes positive aircraft bounds', async () => {
    const value = requireProbe(await probe(page))
    for (const axis of ['width', 'height', 'depth']) {
      assert.ok(value.aircraftBounds[axis] > 0, `${axis}=${value.aircraftBounds[axis]}`)
    }
  })

  await run('P0-SCENE-006', 'probe exposes M1-M4 mounts', async () => {
    const value = requireProbe(await probe(page))
    for (const motor of ['M1', 'M2', 'M3', 'M4']) {
      const p = value.mounts?.[motor]
      assert.ok(p, `missing ${motor}`)
      for (const axis of ['x', 'y', 'z']) assert.equal(typeof p[axis], 'number')
    }
  })

  await run('P0-SCENE-007', 'probe exposes battery part bounds for visual variant comparison', async () => {
    const value = requireProbe(await probe(page))
    const bounds = value.partBounds?.battery
    assert.ok(bounds, 'battery partBounds missing')
    assert.ok(bounds.width > 0 && bounds.height > 0 && bounds.depth > 0)
  })

  await run('P0-SCENE-008', 'camera button changes the real cameraMode observed by probe', async () => {
    await page.getByRole('button', { name: '跟随', exact: true }).click()
    await page.waitForTimeout(100)
    const value = requireProbe(await probe(page))
    assert.equal(value.cameraMode, 'follow')
  })

  await run('P0-SCENE-009', 'selected assembly category is reflected by scene probe', async () => {
    await page.locator('.assembly-step').nth(1).click()
    await page.waitForTimeout(50)
    const value = requireProbe(await probe(page))
    assert.equal(value.selectedSlot, 'motor')
  })

  await run('P0-SCENE-010', '650 to 450 frame switch changes loaded frame asset and whole-aircraft bounds', async () => {
    await page.locator('.assembly-step').nth(0).click()
    await installCard(page, 1) // normalize baseline first

    const before = requireProbe(await probe(page))
    const beforeFrame = before.loadedAssets.find(item => item.slot === 'frame')
    const beforeWidth = before.aircraftBounds.width

    await installCard(page, 2)
    const after = requireProbe(await probe(page))
    const afterFrame = after.loadedAssets.find(item => item.slot === 'frame')
    assert.ok(beforeFrame && afterFrame)
    assert.notEqual(afterFrame.url, beforeFrame.url)
    assert.ok(after.aircraftBounds.width < beforeWidth, `${after.aircraftBounds.width} !< ${beforeWidth}`)

    await installCard(page, 1) // restore reference configuration
  })

  await run('P0-SCENE-011', '10000 to 16000 battery switch changes loaded asset and battery bounds', async () => {
    await page.locator('.assembly-step').nth(2).click()
    await installCard(page, 40) // normalize baseline first

    const before = requireProbe(await probe(page))
    const beforeBattery = before.loadedAssets.find(item => item.slot === 'battery')
    const beforeBounds = before.partBounds?.battery
    assert.ok(beforeBattery && beforeBounds)

    await installCard(page, 41)
    const after = requireProbe(await probe(page))
    const afterBattery = after.loadedAssets.find(item => item.slot === 'battery')
    const afterBounds = after.partBounds?.battery
    assert.ok(afterBattery && afterBounds)
    assert.notEqual(afterBattery.url, beforeBattery.url)

    const beforeVolume = beforeBounds.width * beforeBounds.height * beforeBounds.depth
    const afterVolume = afterBounds.width * afterBounds.height * afterBounds.depth
    assert.ok(afterVolume > beforeVolume, `${afterVolume} !> ${beforeVolume}`)

    await installCard(page, 40) // restore reference configuration
  })

  finish()
} finally {
  await browser.close()
}
