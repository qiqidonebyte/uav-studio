import { spawn } from 'node:child_process'

// Run only functional browser checks. Visual capture remains a review artifact,
// not a pass/fail release gate. Start backend (8000) and Vite (5174) first.
const suites = [
  'e2e-auth.mjs',
  'e2e-aircraft-library.mjs',
  'e2e-assembly.mjs',
  'e2e-digital-assembly.mjs',
  'e2e-component-card-image.mjs',
  'e2e-component-library.mjs',
  'e2e-flight-controls.mjs',
  'e2e-flight.mjs',
  'e2e-settings.mjs',
  'e2e-teacher-workbench.mjs',
  'p0-ui-contract.mjs',
  'p0-scene-contract.mjs',
]

for (const suite of suites) {
  console.log(`\n=== Browser regression: ${suite} ===`)
  const exitCode = await new Promise(resolve => {
    const child = spawn(process.execPath, [`tests/${suite}`], {
      stdio: 'inherit',
      env: process.env,
    })
    child.on('exit', code => resolve(code ?? 1))
    child.on('error', () => resolve(1))
  })
  if (exitCode !== 0) process.exit(exitCode)
}

console.log('\nBrowser regression PASS: all functional E2E and P0 contracts')
