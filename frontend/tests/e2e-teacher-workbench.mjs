import assert from 'node:assert/strict'
import { baseUrl, launchBrowser, loginAsAdmin } from './p0-helpers.mjs'

const browser = await launchBrowser()

try {
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    locale: 'zh-CN',
  })
  await loginAsAdmin(page)
  await page.goto(`${baseUrl}/teacher`, { waitUntil: 'networkidle' })
  await page.getByRole('heading', { name: '教师工作台' }).waitFor({ timeout: 10000 })
  assert.match(await page.locator('.teacher-identity').innerText(), /管理员/)

  const tabs = [
    ['班级管理', '班级管理'],
    ['实训任务', '实训任务'],
    ['实训记录', '实训记录'],
    ['学生情况', '学生情况'],
    ['课程成绩', '课程成绩与班级分析'],
    ['用户角色', '用户角色'],
  ]
  for (const [tab, heading] of tabs) {
    await page.getByRole('button', { name: new RegExp(tab) }).click()
    await page.getByRole('heading', { name: heading }).waitFor({ timeout: 10000 })
  }

  console.log('E2E PASS: teacher/admin workbench tabs and role-scoped management views')
} finally {
  await browser.close()
}
