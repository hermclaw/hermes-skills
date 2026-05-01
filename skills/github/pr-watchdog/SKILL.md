---
name: pr-watchdog
description: Monitor open PRs by the authenticated user for CI failures and merge conflicts, and attempt automated fixes. Use when the user asks to check PR health, fix CI failures, resolve merge conflicts on PRs, triage open PRs, or any variation of "are my PRs green". Works as a manual check or scheduled cron job.
version: 1.0.0
author: hermclaw
license: MIT
metadata:
  hermes:
    tags: [github, pull-requests, ci, automation, merge-conflicts, cron]
    related_skills: [github-pr-workflow, github-actions-debug, fork-first-pr]
---

# PR Watchdog

Automated health monitor for open PRs. Detects CI failures and merge conflicts, then attempts to fix them.

## Prerequisites

- `gh` CLI with auth configured (`gh auth status`)
- `git` with push access to PR branches

## How It Works

1. Discover all open PRs by the authenticated user
2. For each PR, check mergeability and CI status
3. Attempt automated fixes for issues found
4. Report results

---

## Step 1: Discover Open PRs

```bash
# Get authenticated username dynamically
AUTH_USER=$(gh api user --jq .login)

# Search for open PRs authored by the authenticated user across all repos
gh search prs --author="$AUTH_USER" --state=open --json number,repository,title,url,headRefName,baseRefName,isDraft
```

**Optional:** Scope to a specific repo:

```bash
gh pr list --author="@me" --repo OWNER/REPO --state=open --json number,title,headRefName,baseRefName,isDraft,url
```

**Filter out drafts** — drafts typically don't run CI and rebasing them is noisy:

```bash
gh search prs --author="$AUTH_USER" --state=open --json number,repository,title,url,headRefName,baseRefName,isDraft \
  --jq '.[] | select(.isDraft == false)'
```

---

## Step 2: Check Mergeability and CI Status

For each PR, run these checks in parallel:

### Merge Conflicts

```bash
gh pr view PR_NUMBER --repo OWNER/REPO --json mergeable,mergeStateStatus,baseRefName,headRefName
```

- `mergeable: false` + `mergeStateStatus: "DIRTY"` → **merge conflict**
- `mergeable: true` → clean
- `mergeable: null` → GitHub hasn't finished checking yet; wait and retry

### CI Status

```bash
# Check check runs on the PR's HEAD commit
gh pr checks PR_NUMBER --repo OWNER/REPO
```

Or via API for structured output:

```bash
gh api repos/OWNER/REPO/commits/BRANCH/status --jq '{state: .state, statuses: [.statuses[] | {context: .context, state: .state}]}'
```

And GitHub Actions check runs:

```bash
gh api repos/OWNER/REPO/commits/BRANCH/check-runs \
  --jq '.check_runs[] | select(.conclusion == "failure") | {name: .name, id: .id}'
```

**Classify the PR:**

| Mergeable | CI | Status | Action |
|-----------|-----|--------|--------|
| ✅ clean | ✅ passing | Healthy | None |
| ✅ clean | ❌ failing | CI failure | Fix CI |
| ❌ conflict | ✅ passing | Conflict | Rebase |
| ❌ conflict | ❌ failing | Both | Rebase first, then fix CI |
| ⏳ null | — | Unknown | Wait, retry in 30s |

---

## Step 3: Fix Merge Conflicts (Rebase)

When a PR has merge conflicts, rebase it onto the base branch:

```bash
# Clone/update the repo
cd /path/to/local/repo
git fetch origin

# Checkout the PR branch
git checkout HEAD_BRANCH

# Rebase onto the base branch
git rebase origin/BASE_BRANCH
```

### After Rebase: Push

**If the branch only exists in the target repo (direct push access):**

```bash
git push --force-with-lease origin HEAD_BRANCH
```

**If the PR is from a fork (no direct push access to target repo):**

```bash
# Push to fork remote
git push --force-with-lease fork HEAD_BRANCH
```

> **Safety:** Always use `--force-with-lease`, never `--force`. This prevents overwriting commits pushed by others.

### Rebase Conflicts

If rebase itself has conflicts:

```bash
git rebase --abort
```

Mark the PR as "manual intervention needed" and report to the user. Do NOT attempt automatic conflict resolution — semantic conflicts require human judgment.

---

## Step 4: Fix CI Failures

### 4a. Identify the Failure

```bash
# Find failed workflow runs on the branch
gh run list --repo OWNER/REPO --branch HEAD_BRANCH --limit 5

# Get failed run details
RUN_ID=<run_id>
gh api repos/OWNER/REPO/actions/runs/$RUN_ID/jobs \
  --jq '.jobs[] | select(.conclusion == "failure") | {name: .name, steps: [.steps[] | select(.conclusion == "failure") | .name]}'
```

### 4b. Download and Analyze Failed Logs

```bash
gh run download $RUN_ID --repo OWNER/REPO --dir /tmp/ci-logs-PR_NUMBER
```

Extract and read the **last portion** of failed step logs — errors are always at the end:

```python
import zipfile, os

logs_dir = '/tmp/ci-logs-PR_NUMBER'
for f in sorted(os.listdir(logs_dir)):
    if f.endswith('.zip'):
        with zipfile.ZipFile(os.path.join(logs_dir, f), 'r') as z:
            for name in z.namelist():
                if name.endswith('.txt'):
                    content = z.read(name).decode('utf-8', errors='replace')
                    # Only show last 3000 chars — errors are at the end
                    print(f"=== {name} ===")
                    print(content[-3000:])
```

### 4c. Diagnose and Fix

Common fixable CI failures:

| Failure Type | Diagnosis | Fix |
|-------------|-----------|-----|
| Lint errors (rubocop, eslint, ruff, etc.) | Annotations show exact file:line | Fix the lint violation |
| Outdated lockfile | "Lockfile out of sync" or "Regenerate lockfile" | Run lockfile update command, commit |
| Test failure | Specific test name + assertion | Fix the test or the code |
| Type errors (mypy, tsc, etc.) | File + line + expected vs actual | Fix the type annotation |
| Build failure (missing dep) | "Cannot find module" or version mismatch | Add/update dependency |
| Docker build failure | Dockerfile line number in error | Fix the Dockerfile line |

### 4d. Apply Fix, Commit, and Push

```bash
# Make the fix (using file editing tools)

# Commit with descriptive message
git add <changed_files>
git commit -m "fix: resolve CI failure in <check_name>

<brief explanation of what was wrong and how it was fixed>"

# Push
git push origin HEAD_BRANCH
# or: git push fork HEAD_BRANCH (for fork PRs)
```

### 4e. Verify CI Passes

After pushing the fix, wait for the new CI run and check:

```bash
# Wait for new run to start (poll every 15s, up to 2 min)
for i in $(seq 1 8); do
  RUN_ID=$(gh run list --repo OWNER/REPO --branch HEAD_BRANCH --limit 1 --json databaseId --jq '.[0].databaseId')
  if [ -n "$RUN_ID" ]; then break; fi
  sleep 15
done

# Watch until complete
gh run watch $RUN_ID --repo OWNER/REPO --exit-status
```

If CI still fails after the fix, **do NOT keep iterating**. Report the remaining failure to the user with the error details. Max 2 fix attempts per PR per run.

---

## Step 5: Report Results

After processing all PRs, produce a summary:

```
## PR Watchdog Report

| Repo | PR | Title | Status | Action Taken |
|------|-----|-------|--------|-------------|
| owner/repo | #42 | Fix login bug | ✅ Healthy | — |
| owner/repo | #43 | Add auth | 🔧 Fixed CI | Rebased + fixed lint error |
| owner/repo | #44 | Update deps | ⚠️ Manual needed | Rebase conflict (unresolved) |

**Fixed:** 1 | **Healthy:** 1 | **Needs attention:** 1
```

## Cron Job Setup

To run this as a scheduled cron job:

```yaml
# enabled_toolsets: ["terminal", "file", "web"]
# skills: ["github/pr-watchdog"]
# schedule: "0 */2 * * 1-5"  # every 2 hours, weekdays
# deliver: "origin"
```

The prompt for the cron job:

```
Run the pr-watchdog skill. Check all open PRs by the authenticated user for merge conflicts and CI failures. Fix what you can, report what you can't.
```

**Important:** The cron job needs `terminal` toolset (for git/gh commands) and `file` toolset (for editing files to fix CI issues).

---

## Pitfalls

- **`mergeable: null`**: GitHub computes mergeability asynchronously. If null, wait 30s and retry. Don't assume conflict.
- **Draft PRs**: Skip drafts — they typically don't run required CI checks and rebasing them creates noise.
- **Protected branches**: Some repos require status checks to pass before merge. A rebase won't help if the base branch itself is broken.
- **Fork PRs**: The PR head branch lives in the fork. Push to the fork remote, not origin. See fork-first-pr skill.
- **Force push safety**: Always use `--force-with-lease`. Never `--force`.
- **Infinite fix loops**: Max 2 fix attempts per PR per watchdog run. If CI keeps failing, escalate to user.
- **Concurrent runs**: If two watchdog runs overlap, they may race on the same branch. Use a lock file or deduplicate by checking recent commit timestamps.
- **Large repos**: `gh search prs` may be slow. Scope to specific repos if the user has many.
- **Rebase breaks commit SHA**: After rebase, the HEAD commit SHA changes. Any existing CI run becomes invalid. Always wait for the new CI run after rebasing.
