# Classify a failing check before acting

Read the failed job's log for the current head (`gh run view <id> --log-failed`) and place the failure in one class:

| Class | Signs | Action |
|---|---|---|
| **In the change** | The error points at lines or behaviour the diff touches. | Fix it with the smallest change, a test where it is behaviour, in the next push wave. |
| **Stale base** | The failure is in code the diff never touches, and the base has moved (`git merge-base --is-ancestor origin/<base> HEAD` is false). | Report it; update the branch only in the way the build file allows (merge the base or the forge's update button), never by force-pushing. |
| **Flake or infrastructure** | Timeouts, network errors, runner or service outages, a test known to be intermittent, or the same check passing on an earlier identical commit. | One fresh run of the whole workflow, never a job-level retry loop. An identical second failure means it is not a flake: treat it as in the change or stale base. |
| **Budget or policy** | A size budget, coverage floor, ratchet or policy check. | Fix the code to meet it. Changing the budget or baseline is the owner's decision; flag it. |
| **Environment** | It only fails because a tool or credential is missing where you ran it. | Not a defect in the change; run it where the build file says, or report what is missing. |

Do not guess. If the log does not settle the class, say which classes remain and what would tell them apart.

Adapted from pstack's [babysit playbook](https://github.com/cursor/plugins/tree/main/pstack/skills/poteto-mode) (classify before retrigger, one fresh build, identical second failure is real, untouched code means stale base).
