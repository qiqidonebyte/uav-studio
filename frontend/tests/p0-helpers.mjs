import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright-core'

export const baseUrl = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5174'

function browserCandidates() {
  const values = [
    process.env.P0_BROWSER_PATH,
    process.env.EDGE_PATH,
  ]

  if (process.platform === 'win32') {
    values.push(
      'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
      'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    )
  } else if (process.platform === 'darwin') {
    values.push(
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    )
  } else {
    values.push(
      '/usr/bin/microsoft-edge',
      '/usr/bin/google-chrome',
      '/usr/bin/chromium',
      '/usr/bin/chromium-browser',
    )
  }

  return values.filter(Boolean)
}

export async function launchBrowser() {
  let lastError = null

  for (const candidate of browserCandidates()) {
    if (!fs.existsSync(candidate)) continue
    try {
      return await chromium.launch({ executablePath: candidate, headless: true })
    } catch (error) {
      lastError = error
    }
  }

  try {
    return await chromium.launch({ headless: true })
  } catch (error) {
    lastError = error
  }

  throw new Error(
    [
      '无法启动 Chromium/Edge。',
      '可设置 P0_BROWSER_PATH 指向本机 Edge/Chrome。',
      `最后错误：${lastError?.message ?? 'unknown'}`,
    ].join('\n'),
  )
}

export function createRunner(label) {
  const results = []

  async function run(id, name, fn) {
    try {
      await fn()
      results.push({ id, name, status: 'PASS' })
      console.log(`PASS ${id} ${name}`)
    } catch (error) {
      results.push({
        id,
        name,
        status: 'FAIL',
        message: error?.message ?? String(error),
      })
      console.error(`FAIL ${id} ${name}`)
      console.error(`  ${error?.message ?? error}`)
    }
  }

  function finish() {
    const passed = results.filter(item => item.status === 'PASS').length
    const failed = results.length - passed
    console.log(`\n${label}: ${passed} PASS / ${failed} FAIL / ${results.length} TOTAL`)
    if (failed > 0) process.exitCode = 1
    return { results, passed, failed }
  }

  return { run, finish, assert }
}

export async function openAssembly(page) {
  await page.goto(`${baseUrl}/assembly`, { waitUntil: 'networkidle' })
  await page.locator('.assembly-step').first().waitFor({ state: 'visible', timeout: 10000 })
}

export function outputDir(name) {
  const dir = path.resolve(process.cwd(), 'test-results', name)
  fs.mkdirSync(dir, { recursive: true })
  return dir
}
