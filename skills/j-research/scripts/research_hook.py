#!/usr/bin/env python3
"""UserPromptSubmit hook: remind the agent to use j-research when a prompt needs current facts.

A skill's description is only a hint, and some models skip it for questions that
sound like design advice ("how would you build X for us?"). This hook asks
TypeSafe's Jev four yes/no questions about the prompt and decides in code whether
to add a one-line reminder. It never blocks a prompt: on any error it adds
nothing and notes the error on stderr.

Chosen over a Haiku call after a comparison on 71 labelled prompts (jstack-evals
experiments/2026-11-08-trigger-classifier): Jev fired on 40/40 research prompts
and 0/31 others, at a median of about 165 ms; Haiku 39/40 and 0/31 at about 710 ms.

Every classified prompt is appended to a local JSON Lines log (scores, decision, first 300
characters of the prompt) so false fires can be labelled before anyone tunes the questions:
~/.local/state/jstack/research-hook.jsonl, or JSTACK_HOOK_LOG; set it to "off" to disable.
Summarise with `research_hook.py --report`.

Key: TYPESAFE_API_KEY (or EVAL_TYPESAFE_API_KEY under `claude plugin eval`) from the environment, else the macOS keychain item
`jstack-typesafe` (security add-generic-password -s jstack-typesafe -a "$USER" -w).
"""
import json
import os
import time
from pathlib import Path
import subprocess
import sys
import urllib.request

MODEL = "jev-1.14.0"
URL = os.environ.get("TYPESAFE_ENDPOINT", "https://api.typesafe.ai") + "/v1/systemone"
TIMEOUT = 3.0  # seconds; a slow call adds nothing rather than holding up the prompt
YES, NO = 0.70, 0.30
# Hosts deliver some messages through UserPromptSubmit that the user did not type: T3 delegated-task
# results and background notices. A research-shaped result would otherwise trigger a pointless reminder.
NOT_USER = ("Delegated task ", "<task-notification", "[SYSTEM NOTIFICATION", "<system-reminder>")
REMINDER = (
    "This request depends on current outside facts or on how to build, set up or choose something. "
    "Use the j-research skill before answering: check the vault, then current sources, and cite them."
)

# Wording and thresholds tested in the comparison above; change them together and re-run it.
QUESTIONS = {
    "changing_facts": {"type": "noul", "instructions": "Would a good answer to `message` rely on current facts about products or services outside the person's own project?",
        "criteria": {"true": "The answer depends on current versions, prices, limits, recent releases, or which outside products and services exist.",
                     "false": "The answer depends only on the person's own code, files, tests or text, or on stable knowledge, such as how a language feature works."}},
    "build_or_choose": {"type": "noul", "instructions": "Does `message` ask how to build, set up, or choose a tool, service, or approach?",
        "criteria": {"true": "The person wants a recommendation on how to build or set something up, or which option to pick.",
                     "false": "The person wants existing code or text changed, written, run, or explained."}},
    "reliance": {"type": "noul", "instructions": "Does `message` ask whether a claim, product, or release can be relied on?",
        "criteria": {"true": "The person asks if something is safe, ready, true, or dependable before acting on it.",
                     "false": "The person does not ask whether anything can be trusted."}},
    "self_contained": {"type": "noul", "instructions": "Can `message` be answered fully from the message itself and the person's own files?",
        "criteria": {"true": "Everything needed is in the message or the project, such as fixing a given error or rewriting given text.",
                     "false": "Answering well needs information from outside sources."}},
}


def decide(a: dict) -> bool:
    """A clear research signal fires; an unsettled one fires only if the task is not clearly self-contained."""
    signal = max(a["changing_facts"], a["build_or_choose"], a["reliance"])
    if signal > YES:
        return True
    if signal > NO:
        return a["self_contained"] < YES
    return False


def api_key() -> str | None:
    for name in ("TYPESAFE_API_KEY", "EVAL_TYPESAFE_API_KEY"):  # plugin evals pass only EVAL_* variables
        if os.environ.get(name):
            return os.environ[name]
    try:
        out = subprocess.run(["security", "find-generic-password", "-s", "jstack-typesafe", "-w"], capture_output=True, text=True, timeout=2)
        return out.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def judge(message: str, key: str) -> dict:
    body = json.dumps({"model": MODEL, "state": {"message": message[:4000]}, "questions": QUESTIONS}).encode()
    request = urllib.request.Request(URL, data=body, method="POST", headers={"authorization": f"Bearer {key}", "content-type": "application/json", "user-agent": "jstack-research-hook"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        result = json.loads(response.read())
    return {name: result["answers"][name]["noul"] for name in QUESTIONS}


def log_path() -> Path | None:
    setting = os.environ.get("JSTACK_HOOK_LOG", "")
    if setting == "off":
        return None
    return Path(setting) if setting else Path.home() / ".local/state/jstack/research-hook.jsonl"


def record(prompt: str, scores: dict, fire: bool) -> None:
    """Append one line for later labelling; a logging failure never affects the hook."""
    path = log_path()
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "fire": fire, "scores": scores, "prompt": prompt[:300], "label": None}
        with path.open("a") as handle:
            handle.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def report(path: Path) -> int:
    """Print fire rate and, for labelled lines (label true = needed research), false fires and misses."""
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    labelled = [r for r in rows if r.get("label") is not None]
    print(json.dumps({
        "prompts": len(rows), "fired": sum(r["fire"] for r in rows), "labelled": len(labelled),
        "false_fires": sum(r["fire"] and not r["label"] for r in labelled),
        "misses": sum(r["label"] and not r["fire"] for r in labelled),
    }))
    return 0


def main() -> int:
    if "--report" in sys.argv:
        path = log_path()
        return report(path) if path else 0
    try:
        prompt = str(json.load(sys.stdin).get("prompt", "")).strip()
    except (ValueError, AttributeError):
        return 0
    if len(prompt) < 12 or prompt.startswith("/"):  # slash commands and one-word replies
        return 0
    if prompt.startswith(NOT_USER):  # results and notices the host delivers as prompts, not questions
        return 0
    key = api_key()
    if not key:
        print("research hook: no TYPESAFE_API_KEY; skipped", file=sys.stderr)
        return 0
    try:
        scores = judge(prompt, key)
        fire = decide(scores)
    except Exception as error:  # never block or alter a prompt because the classifier failed
        print(f"research hook: classifier failed ({type(error).__name__}); skipped", file=sys.stderr)
        return 0
    record(prompt, scores, fire)
    if fire:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
