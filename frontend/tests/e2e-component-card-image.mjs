import assert from 'node:assert/strict'
import { baseUrl, launchBrowser, loginAsAdmin } from './p0-helpers.mjs'

const browser = await launchBrowser()

try {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } })
  await loginAsAdmin(page)
  await page.goto(`${baseUrl}/assembly`, { waitUntil: 'networkidle' })
  await page.getByText('机架 · 组件选择').waitFor({ state: 'visible' })

  const card = page.locator('[data-testid="component-card"][data-component-type="frame"]').first()
  const media = card.getByTestId('component-media')
  const image = card.getByTestId('component-thumbnail')
  await image.waitFor({ state: 'visible' })

  const geometry = await image.evaluate(img => {
    const media = img.parentElement
    const imageRect = img.getBoundingClientRect()
    const mediaRect = media?.getBoundingClientRect()
    const style = getComputedStyle(img)
    return {
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      imageWidth: imageRect.width,
      imageHeight: imageRect.height,
      mediaWidth: mediaRect?.width ?? 0,
      mediaHeight: mediaRect?.height ?? 0,
      objectFit: style.objectFit,
      objectPosition: style.objectPosition,
    }
  })

  assert.equal(geometry.complete, true)
  assert.ok(geometry.naturalWidth > 0 && geometry.naturalHeight > 0)
  assert.equal(geometry.objectFit, 'contain')
  assert.ok(geometry.imageWidth <= geometry.mediaWidth)
  assert.ok(geometry.imageHeight <= geometry.mediaHeight)
  assert.ok(geometry.imageWidth > 60, `rendered image too small: ${geometry.imageWidth}px`)
  assert.ok(geometry.imageHeight > 60, `rendered image too small: ${geometry.imageHeight}px`)

  // The media viewport itself must be large enough to show the full frame thumbnail.
  const mediaBox = await media.boundingBox()
  assert.ok(mediaBox)
  assert.ok(mediaBox.height >= 128, `media height=${mediaBox.height}px`)

  console.log('E2E PASS: frame component thumbnail is fully contained and visible')
} finally {
  await browser.close()
}
