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

  await run('P0-SCENE-012', 'assembly toolbar exposes assembled and exploded modes', async () => {
    assert.equal(await page.getByTestId('assembly-view-assembled').count(), 1)
    assert.equal(await page.getByTestId('assembly-view-exploded').count(), 1)

    const value = requireProbe(await probe(page))
    assert.equal(value.assemblyViewMode, 'assembled')
    assert.ok(value.explosionProgress <= 0.01)
  })

  await run('P0-SCENE-013', 'exploded view moves parts by hierarchy while frame remains fixed', async () => {
    await page.getByTestId('assembly-view-exploded').click()
    await page.waitForFunction(
      () =>
        window.__UAV_VISUAL_TEST__?.assemblyViewMode === 'exploded' &&
        (window.__UAV_VISUAL_TEST__?.explosionProgress ?? 0) > 0.98,
      undefined,
      { timeout: 4000 },
    )

    const value = requireProbe(await probe(page))
    const frame = value.explodedParts.find(item => item.slot === 'frame')
    const battery = value.explodedParts.find(item => item.slot === 'battery')
    const fc = value.explodedParts.find(item => item.slot === 'flight_controller')
    const motor = value.explodedParts.find(item => item.slot === 'motor')
    const propeller = value.explodedParts.find(item => item.slot === 'propeller')

    for (const part of [frame, battery, fc, motor, propeller]) {
      assert.ok(part, `missing exploded part ${part?.slot ?? 'unknown'}`)
    }

    assert.ok(Math.abs(frame.currentPosition.x - frame.basePosition.x) < 1e-4)
    assert.ok(Math.abs(frame.currentPosition.y - frame.basePosition.y) < 1e-4)
    assert.ok(Math.abs(frame.currentPosition.z - frame.basePosition.z) < 1e-4)

    assert.ok(battery.currentPosition.y < battery.basePosition.y)
    assert.ok(fc.currentPosition.y > fc.basePosition.y)

    const motorRadialBefore = Math.hypot(motor.basePosition.x, motor.basePosition.z)
    const motorRadialAfter = Math.hypot(motor.currentPosition.x, motor.currentPosition.z)
    assert.ok(motorRadialAfter > motorRadialBefore)

    const propVerticalTravel = propeller.currentPosition.y - propeller.basePosition.y
    const motorVerticalTravel = motor.currentPosition.y - motor.basePosition.y
    assert.ok(propVerticalTravel > motorVerticalTravel)
    assert.equal(await page.getByTestId('exploded-view-hint').isVisible(), true)
  })

  await run('P0-SCENE-014', 'general exploded view removes always-on CW/CCW teaching labels', async () => {
    const exploded = requireProbe(await probe(page))
    assert.equal(exploded.directionLabelsVisible, false)

    await page.getByTestId('assembly-view-assembled').click()
    await page.waitForFunction(
      () => (window.__UAV_VISUAL_TEST__?.explosionProgress ?? 1) < 0.02,
      undefined,
      { timeout: 4000 },
    )
    const assembled = requireProbe(await probe(page))
    assert.equal(assembled.assemblyViewMode, 'assembled')
    assert.equal(assembled.directionLabelsVisible, false)
  })

  await run('P0-SCENE-015', 'propeller step shows direction labels only when they are instructionally relevant', async () => {
    await page.locator('.assembly-step').nth(5).click()
    await page.waitForTimeout(50)
    let value = requireProbe(await probe(page))
    assert.equal(value.selectedSlot, 'propeller')
    assert.equal(value.directionLabelsVisible, true)

    await page.getByTestId('assembly-view-exploded').click()
    await page.waitForFunction(
      () => (window.__UAV_VISUAL_TEST__?.explosionProgress ?? 0) > 0.98,
      undefined,
      { timeout: 4000 },
    )
    value = requireProbe(await probe(page))
    assert.equal(value.directionLabelsVisible, false)
  })

  await run('P0-SCENE-017', 'exploded labels show real component names without duplicating repeated categories', async () => {
    await page.getByTestId('assembly-view-exploded').click()
    await page.waitForFunction(
      () =>
        (window.__UAV_VISUAL_TEST__?.explosionProgress ?? 0) > 0.98 &&
        (window.__UAV_VISUAL_TEST__?.explodedLabels?.length ?? 0) > 0,
      undefined,
      { timeout: 4000 },
    )

    const value = requireProbe(await probe(page))
    const labels = value.explodedLabels
    const slots = labels.map(label => label.slot)
    assert.equal(new Set(slots).size, slots.length, 'exploded labels contain duplicate categories')
    assert.ok(labels.some(label => label.slot === 'frame' && label.title.length > 0))
    const motor = labels.find(label => label.slot === 'motor')
    assert.ok(motor)
    assert.match(motor.meta, /×4/)
  })

  await run('P0-SCENE-018', 'exploded DOM labels are compact, inside scene and do not overlap each other', async () => {
    const labels = page.getByTestId('exploded-component-label')
    const count = await labels.count()
    assert.ok(count > 0)
    const sceneBox = await page.locator('.drone-scene').boundingBox()
    assert.ok(sceneBox)
    const boxes = []
    for (let index = 0; index < count; index += 1) {
      const box = await labels.nth(index).boundingBox()
      assert.ok(box)
      assert.ok(box.width <= 166, `label too wide: ${box.width}`)
      assert.ok(box.height <= 28, `label too tall: ${box.height}`)
      assert.ok(box.x >= sceneBox.x - 1)
      assert.ok(box.y >= sceneBox.y - 1)
      assert.ok(box.x + box.width <= sceneBox.x + sceneBox.width + 1)
      assert.ok(box.y + box.height <= sceneBox.y + sceneBox.height + 1)
      boxes.push(box)
    }
    for (let i = 0; i < boxes.length; i += 1) {
      for (let j = i + 1; j < boxes.length; j += 1) {
        const a = boxes[i]
        const b = boxes[j]
        const overlaps = !(
          a.x + a.width + 2 <= b.x ||
          b.x + b.width + 2 <= a.x ||
          a.y + a.height + 2 <= b.y ||
          b.y + b.height + 2 <= a.y
        )
        assert.equal(overlaps, false, `label ${i} overlaps ${j}`)
      }
    }
  })

  await run('P0-SCENE-019', 'obsolete GLB teaching-model badge is removed', async () => {
    assert.equal(await page.locator('.asset-badge').count(), 0)
    assert.equal((await page.locator('.drone-scene').innerText()).includes('GLB 教学模型'), false)
  })

  await run('P0-SCENE-016', 'returning to assembled view restores every part to its datum position', async () => {
    await page.getByTestId('assembly-view-assembled').click()
    await page.waitForFunction(
      () => (window.__UAV_VISUAL_TEST__?.explosionProgress ?? 1) < 0.02,
      undefined,
      { timeout: 4000 },
    )

    const value = requireProbe(await probe(page))
    for (const part of value.explodedParts) {
      assert.ok(Math.abs(part.currentPosition.x - part.basePosition.x) < 0.002)
      assert.ok(Math.abs(part.currentPosition.y - part.basePosition.y) < 0.002)
      assert.ok(Math.abs(part.currentPosition.z - part.basePosition.z) < 0.002)
    }
  })

  finish()
} finally {
  await browser.close()
}
