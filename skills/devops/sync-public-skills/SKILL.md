---
name: sync-public-skills
description: Sync selected skills from ~/.hermes-openrouter/skills/ to github-repos/skills/ using a whitelist. Includes security scanning to prevent accidental secret exposure.
version: 1.0.0
author: hermclaw
license: MIT
dependencies: []
metadata:
  hermes:
    tags: ["skills", "sync", "github", "publishing", "security"]
---

# Sync Public Skills

Sync selected Hermes skills to a public GitHub repository while keeping private state separate.

## How It Works

Reads `~/.hermes-openrouter/public-skills.txt` as a whitelist of skills to sync.
Scans each skill for secrets before copying to `~/.hermes-openrouter/github-repos/skills/`.

## Configuration

Edit `~/.hermes-openrouter/public-skills.txt`:

```text
# One skill per line
```

## Usage

```bash
# Preview (dry run)
~/.hermes-openrouter/skills/devops/sync-public-skills/scripts/sync-public-skills --dry-run

# Actually sync
~/.hermes-openrouter/skills/devops/sync-public-skills/scripts/sync-public-skills

# Sync even with security warnings (not recommended)
~/.hermes-openrouter/skills/devops/sync-public-skills/scripts/sync-public-skills --force
```

## Security

Scans for:
- API keys, tokens, secrets (regex patterns)
- AWS keys, GitHub tokens, OpenAI keys
- Private keys, bearer tokens
- High-entropy base64 blobs

If secrets are found, the skill is blocked from syncing.

## Repo Structure

```
github-repos/skills/
└── skills/
    ├── devops/
    │   └── sync-public-skills/
    └── productivity/
        └── train-report/
```

All scripts live **inside skills** — no standalone scripts directory.

## First-Time Setup

If the GitHub repo doesn't exist yet:

```bash
cd ~/.hermes-openrouter/github-repos/skills

# Initialize repo
git init
git branch -m main
git config user.name "hermclaw"
git config user.email "hermclaw@users.noreply.github.com"

# Create GitHub repo via gh CLI
gh repo create hermes-skills --public --description "Public Hermes skills"

# Add remote and push
git remote add origin https://github.com/hermclaw/hermes-skills.git
git add . && git commit -m "Initial sync"
git push -u origin main
```

## Meta-Recursive Nature

This skill publishes itself! Once synced to your public repo, it can clone and sync your other skills, including future versions of itself.
