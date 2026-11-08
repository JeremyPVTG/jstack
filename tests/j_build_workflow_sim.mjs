// Runs skills/j-build/references/workflow.js against stub agents and checks the verdict in each scenario.
// The review stage must fail closed: CLEAN only when every lens ran, every finding was refuted or fixed,
// and, after a fix, every requested check passed. Usage: node tests/j_build_workflow_sim.mjs (exit 1 on a mismatch).
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const file = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'skills/j-build/references/workflow.js')
const body = fs.readFileSync(file, 'utf8').replace(/^export const meta[\s\S]*?\n}\n/, '')

const run = (args, agent) => {
  const script = new Function('args', 'phase', 'parallel', 'agent', 'log', `return (async () => {${body}})()`)
  return script(args, () => {}, async (thunks) => Promise.all(thunks.map((t) => t())), agent, () => {})
}

const F = (claim, severity = 'medium') => ({ file: 'a.py', line: 1, severity, claim, failure: 'x' })
const stub = (s) => async (_prompt, { label }) => {
  if (label.startsWith('review:')) return label in s ? s[label] : { findings: [] }
  if (label === 'merge') return s.merge
  if (label.startsWith('verify:')) return s.verify ? s.verify(label) : { refuted: true, reason: '' }
  if (label === 'fix') return s.fix
}
const confirm = () => ({ refuted: false, reason: '' })
const pair = { 'review:tests': { findings: [F('a'), F('b')] }, merge: { groups: [{ members: [0], representative: 0, rootCause: 'r' }, { members: [1], representative: 1, rootCause: 's' }] } }

const cases = {
  'no findings': [{}, {}, 'CLEAN'],
  'a lens failed, no findings': [{}, { 'review:tests': null }, 'FINDINGS'],
  'a refuter returned nothing': [{}, { 'review:correctness': { findings: [F('a')] }, verify: () => null }, 'FINDINGS'],
  'all findings refuted': [{}, { 'review:correctness': { findings: [F('a'), F('b')] }, merge: { groups: [{ members: [0, 1], representative: 0, rootCause: 'r' }] } }, 'CLEAN'],
  'merge dropped an index, each verified alone': [{}, { 'review:correctness': { findings: [F('a'), F('b')] }, merge: { groups: [{ members: [0], representative: 0, rootCause: 'r' }] }, verify: (l) => (l === 'verify:2' ? confirm() : { refuted: true, reason: '' }), fix: { fixed: [1], notFixed: [], checks: [{ command: 'npm test', passed: true }] } }, 'CLEAN'],
  'confirmed and fixed, check passed': [{ checks: ['npm test'] }, { 'review:tests': { findings: [F('a')] }, verify: confirm, fix: { fixed: [1], notFixed: [], checks: [{ command: 'npm test', passed: true }] } }, 'CLEAN'],
  'a requested check is missing': [{ checks: ['npm test', 'ruff check'] }, { 'review:tests': { findings: [F('a')] }, verify: confirm, fix: { fixed: [1], notFixed: [], checks: [{ command: 'npm test', passed: true }] } }, 'FINDINGS'],
  'no checks ran after a fix': [{}, { 'review:tests': { findings: [F('a')] }, verify: confirm, fix: { fixed: [1], notFixed: [], checks: [] } }, 'FINDINGS'],
  'fixer fixed nothing': [{ checks: ['npm test'] }, { 'review:tests': { findings: [F('a')] }, verify: confirm, fix: { fixed: [], notFixed: [], checks: [{ command: 'npm test', passed: true }] } }, 'FINDINGS'],
  'fixer fixed one of two': [{}, { ...pair, verify: confirm, fix: { fixed: [1], notFixed: [], checks: [{ command: 't', passed: true }] } }, 'FINDINGS'],
  'fix agent returned nothing': [{}, { 'review:tests': { findings: [F('a')] }, verify: confirm, fix: null }, 'FINDINGS'],
}

let failures = 0
for (const [name, [args, scenario, want]] of Object.entries(cases)) {
  const result = await run(args, stub(scenario))
  if (result.verdict !== want) failures++
  console.log(`${result.verdict === want ? 'ok  ' : 'FAIL'} ${name}: ${result.verdict} (want ${want})`)
}
process.exit(failures ? 1 : 0)
