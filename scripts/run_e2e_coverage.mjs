import { spawn } from 'node:child_process'
import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'

const rootDir = process.cwd()
const reportDir = path.join(rootDir, 'coverage', 'e2e')
const bunxBin = process.platform === 'win32' ? 'bunx.cmd' : 'bunx'
const coverageThreshold = 85

function run(command, args, { env = {}, captureStdout = false } = {}) {
  return new Promise((resolve, reject) => {
    let stdout = ''
    const child = spawn(command, args, {
      stdio: captureStdout ? ['ignore', 'pipe', 'inherit'] : 'inherit',
      env: { ...process.env, ...env },
    })

    if (captureStdout) {
      child.stdout.on('data', (chunk) => {
        stdout += chunk.toString()
      })
    }

    child.on('error', reject)
    child.on('exit', (code) => {
      resolve({ code: code ?? 1, stdout })
    })
  })
}

await rm(reportDir, { recursive: true, force: true })
await mkdir(reportDir, { recursive: true })

const listResult = await run(bunxBin, ['playwright', 'test', '--list'], {
  captureStdout: true,
})
if (listResult.code !== 0) {
  throw new Error(`Failed to list Playwright tests (exit ${listResult.code})`)
}

const totalMatch = listResult.stdout.match(/Total:\s+(\d+)\s+tests/i)
const totalTests = totalMatch ? Number.parseInt(totalMatch[1], 10) : 0
if (!Number.isFinite(totalTests) || totalTests <= 0) {
  throw new Error('Unable to determine total e2e test count from Playwright --list output')
}

const runResult = await run(bunxBin, ['playwright', 'test'])
const passedTests = runResult.code === 0 ? totalTests : 0
const coveragePct = Number(((passedTests / totalTests) * 100).toFixed(2))

const report = {
  metric: 'e2e_journey_coverage',
  total_tests: totalTests,
  passed_tests: passedTests,
  coverage_percent: coveragePct,
  threshold_percent: coverageThreshold,
  threshold_met: coveragePct >= coverageThreshold,
}
await writeFile(
  path.join(reportDir, 'journey-coverage.json'),
  JSON.stringify(report, null, 2),
  'utf8'
)

console.log(
  `E2E journey coverage: ${coveragePct.toFixed(2)}% (${passedTests}/${totalTests}), threshold ${coverageThreshold}%`
)

if (coveragePct < coverageThreshold) {
  throw new Error(`E2E journey coverage threshold not met: ${coveragePct.toFixed(2)}% < ${coverageThreshold}%`)
}

if (runResult.code !== 0) {
  throw new Error(`Playwright tests failed with exit code ${runResult.code}`)
}
