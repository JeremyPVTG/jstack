# Classify a failing check before acting

Run `git fetch origin` first. Read the failed job's log for the current head (`gh run view <id> --log-failed`) and place the failure in one class. Only the base branch's required checks block (`gh api repos/<owner>/<repo>/rules/branches/<base>` lists them); report a failing optional or cancelled check, but do not classify it as a flake or fix it.

| Class | Signs | Action |
|---|---|---|
| **In the change** | The error points at lines or behaviour the diff touches. | Fix it with the smallest change, a test where it is behaviour, in the next push wave. |
| **Base already fixes it** | The failure is in code the diff never touches, the base has moved (`git merge-base --is-ancestor origin/<base> HEAD` is false), and the base's latest run passes. | Bring the branch up to date the way the build file allows (merge the base), never by rebasing or force-pushing. Do not patch the base's code on the branch. |
| **Base is red too** | The same failure shows on the base's latest run. | Not this PR's defect: report it and change nothing on the branch. |
| **Flake or infrastructure** | Timeouts, network errors, runner or service outages, a test known to be intermittent, or the same check passing on an earlier identical commit. | One fresh run of the whole workflow, never a job-level retry loop. An identical second failure means it is not a flake: classify it again. |
| **Budget or policy** | A size budget, coverage floor, ratchet or policy check. | Fix the code to meet it. Changing the budget or baseline is the owner's decision; flag it. |
| **Approval gate** | The check fails only because an approval it names is missing (a risk tier, a release manager's sign-off). | Not a defect: change nothing and report the exact approval needed and the head it must cover. |
| **Environment** | It only fails because a tool or credential is missing where you ran it. | Not a defect in the change; run it where the build file says, or report what is missing. |

Many CI systems test the PR merged with the current base, so a failure in untouched code there often means the base itself is red. Check the base's own run before changing anything. If the log does not settle the class, say which classes remain and what would tell them apart.

Adapted from pstack's [babysit playbook](https://github.com/cursor/plugins/blob/ab1f702ce8e8b6557edb56b09f52cde8bfb83f17/pstack/skills/poteto-mode/playbooks/babysit.md) (classify before retrigger, one fresh build, identical second failure is real, untouched code means a stale base).
