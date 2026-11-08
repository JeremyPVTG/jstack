export const meta = {
  name: 'j-build-review',
  description: 'j-build review stage: three fresh lenses on the branch diff, findings merged by root cause, each refuted independently, survivors fixed, checks re-run, verdict',
  whenToUse: 'After the build stage of j-build, on a branch with committed or staged changes against the base the repository build file names',
  phases: [
    { title: 'Review', detail: 'correctness, repo rules, tests' },
    { title: 'Merge', detail: 'group findings by root cause' },
    { title: 'Verify', detail: 'one independent refuter per merged finding' },
    { title: 'Fix', detail: 'apply confirmed findings and re-run the checks' },
  ],
}

// args: { goal: string, base: string, buildFile?: string, checks?: string[] }
// goal is one neutral sentence; base, buildFile and checks come from the repository's build file.
// Fails closed: CLEAN only when every lens ran and every finding was refuted or fixed; when something was fixed,
// every check must pass afterwards. With nothing fixed the code is unchanged, and j-build's Verify stage runs the checks.
const goal = (args && args.goal) || 'the change on this branch'
const base = (args && args.base) || 'origin/main'
const checks = (args && args.checks) || []
const buildFile = (args && args.buildFile) || 'the build file AGENTS.md (or CLAUDE.md) names for building'

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          line: { type: 'integer' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          claim: { type: 'string' },
          failure: { type: 'string' },
        },
        required: ['file', 'severity', 'claim', 'failure'],
      },
    },
  },
  required: ['findings'],
}

const GROUPS = {
  type: 'object',
  properties: {
    groups: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          members: { type: 'array', items: { type: 'integer' } },
          representative: { type: 'integer' },
          rootCause: { type: 'string' },
        },
        required: ['members', 'representative', 'rootCause'],
      },
    },
  },
  required: ['groups'],
}

const VERDICT = {
  type: 'object',
  properties: { refuted: { type: 'boolean' }, reason: { type: 'string' } },
  required: ['refuted', 'reason'],
}

const FIXED = {
  type: 'object',
  properties: {
    fixed: { type: 'array', items: { type: 'integer' } },
    notFixed: { type: 'array', items: { type: 'string' } },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: { command: { type: 'string' }, passed: { type: 'boolean' }, tail: { type: 'string' } },
        required: ['command', 'passed'],
      },
    },
  },
  required: ['fixed', 'notFixed', 'checks'],
}

const skill = (mode) => `Load the j-review skill and follow it in ${mode} mode. The repository's build file is ${buildFile}; read it.`
const scope = `${skill('assess')}\n\nThe change under review, in the current directory: \`git diff ${base}...HEAD\` (committed), \`git diff HEAD\` (staged and unstaged), and every untracked file \`git status --short\` lists (read those directly; plain git diff skips them). Its goal: ${goal}. Read the changed files and whatever they call. Report only defects with a concrete failure path; no style or formatting notes. Return an empty list when you find nothing real.`

const LENSES = [
  { key: 'correctness', prompt: `${scope}\n\nLens: correctness. Wrong results, crashes, resource leaks, races, error paths that leave state behind, contract mismatches with the caller (read the caller's code, not just the docs).` },
  { key: 'rules', prompt: `${scope}\n\nLens: the repository's own rules. Read AGENTS.md (or CLAUDE.md), the build file, and any principles or decision records they point to. Report changes that break those rules, or that contradict a recorded decision without adding a new decision record.` },
  { key: 'tests', prompt: `${scope}\n\nLens: tests. Behaviour the change adds that no test exercises, tests that pass for the wrong reason, timing races in tests, fakes that diverge from the real interface they stand in for.` },
]

const describe = (f, i) => `${i}. (${f.severity}) ${f.file}:${f.line || '?'}: ${f.claim}. Failure: ${f.failure}`

phase('Review')
const reviews = await parallel(LENSES.map((lens) => () => agent(lens.prompt, { label: `review:${lens.key}`, phase: 'Review', schema: FINDINGS })))
const failedLenses = LENSES.filter((_, i) => !reviews[i]).map((l) => l.key)
if (failedLenses.length) log(`Lens(es) that returned nothing: ${failedLenses.join(', ')}. The verdict cannot be CLEAN.`)
const all = reviews.filter(Boolean).flatMap((r) => r.findings)
if (all.length === 0) {
  return { verdict: failedLenses.length ? 'FINDINGS' : 'CLEAN', failedLenses, confirmed: [], refuted: [], unverified: [], fix: null }
}

phase('Merge')
const order = { high: 0, medium: 1, low: 2 }
let merged = all.map((f, i) => ({ ...f, members: [i] }))
if (all.length > 1) {
  const grouping = await agent(
    `These review findings came from separate reviewers of one change. Group the ones that share a root cause, meaning one fix would resolve them all, even when worded or located differently. Every index appears in exactly one group; a finding with no duplicate is its own group. For each group pick the representative with the clearest failure path.\n\n${all.map(describe).join('\n')}`,
    { label: 'merge', phase: 'Merge', schema: GROUPS },
  )
  // Accept the grouping only if it is an exact partition of every index with a representative inside each group.
  const groups = grouping && grouping.groups ? grouping.groups : []
  const seen = groups.flatMap((g) => g.members)
  const exact = seen.length === all.length && new Set(seen).size === all.length && seen.every((i) => all[i]) &&
    groups.every((g) => g.members.includes(g.representative))
  if (exact) {
    merged = groups.map((g) => {
      const top = g.members.map((i) => all[i]).sort((a, b) => order[a.severity] - order[b.severity])[0]
      return { ...all[g.representative], severity: top.severity, rootCause: g.rootCause, members: g.members }
    })
  } else {
    log('Merge did not cover every finding exactly once; verifying each finding on its own.')
  }
}
if (all.length > merged.length) log(`${all.length} findings merged into ${merged.length} by root cause.`)
merged.sort((a, b) => order[a.severity] - order[b.severity])

phase('Verify')
const judged = await parallel(
  merged.map((f, i) => () =>
    agent(
      `${skill('confirm')}\n\nTry to refute this review finding about the change in the current directory (diff against ${base}). Read the code yourself. Set refuted=true unless you can trace the failure path in the code; also refute it if it is already handled or lies outside the change.\n\nFinding (${f.severity}) at ${f.file}:${f.line || '?'}: ${f.claim}\nClaimed failure: ${f.failure}`,
      { label: `verify:${i + 1}`, phase: 'Verify', schema: VERDICT },
    ).then((v) => (v ? { ...f, verdict: v } : null)),
  ),
)
const decided = merged.map((f, i) => judged[i] || { ...f, verdict: null })
const confirmed = decided.filter((f) => f.verdict && !f.verdict.refuted)
const refuted = decided.filter((f) => f.verdict && f.verdict.refuted)
const unverified = decided.filter((f) => !f.verdict)
if (unverified.length) log(`${unverified.length} finding(s) got no refuter verdict. The verdict cannot be CLEAN.`)
const incomplete = failedLenses.length > 0 || unverified.length > 0
if (confirmed.length === 0) {
  return { verdict: incomplete ? 'FINDINGS' : 'CLEAN', failedLenses, confirmed, refuted, unverified, fix: null }
}

phase('Fix')
const checkLines = checks.length ? checks.map((c) => `- ${c}`).join('\n') : '- (none given: run the tests for the files you change, one suite at a time)'
const fix = await agent(
  `${skill('fix')}\n\nFix these confirmed review findings in the current directory, with the smallest change each, and add or adjust a test for each where practical. In \`fixed\`, list the number of each finding you fixed; put any you could not fix in \`notFixed\` with the reason. Do not commit or push. Follow the build file's rules for where and how to run checks.\n\nFindings:\n${confirmed.map((f, i) => describe(f, i + 1)).join('\n')}\n\nThen run these checks and report each result with the last lines of its output, using the exact command text below. Read each command's exit status; do not pipe output through tail or head without set -o pipefail:\n${checkLines}`,
  { label: 'fix', phase: 'Fix', schema: FIXED },
)
// Every requested check needs a passing result; with none requested, at least one check must have run and passed.
const ran = fix ? fix.checks : []
const checksPass = ran.length > 0 && ran.every((c) => c.passed) &&
  checks.every((cmd) => ran.some((c) => c.command.trim() === cmd.trim() && c.passed))
const allFixed = Boolean(fix) && confirmed.every((_, i) => fix.fixed.includes(i + 1)) && fix.notFixed.length === 0
const clean = !incomplete && allFixed && checksPass
return { verdict: clean ? 'CLEAN' : 'FINDINGS', failedLenses, confirmed, refuted, unverified, fix }
