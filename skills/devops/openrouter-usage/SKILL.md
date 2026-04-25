---
name: openrouter-usage
description: Check OpenRouter API key usage, credits, and cost statistics. Reports daily/weekly/monthly usage, remaining credits, and spending trends.
version: 1.0.0
author: hermclaw
license: MIT
dependencies: []
metadata:
  hermes:
    tags: ["openrouter", "usage", "cost", "monitoring", "api"]
    related_skills: ["image-gen"]
---

# OpenRouter Usage Skill

Check your OpenRouter API key usage, remaining credits, and spending statistics.

## How It Works

Retrieves usage data from OpenRouter's `/auth/key` and `/credits` endpoints and displays formatted spending information. Works without external dependencies using only Python stdlib.

## Usage

```bash
# Basic usage report
python3 scripts/openrouter_usage.py

# JSON output (for scripts/piping)
python3 scripts/openrouter_usage.py --json

# Quiet mode - only output errors
python3 scripts/openrouter_usage.py --quiet
```

## Example Output

```
OpenRouter Usage Report
=======================
Key:           sk-or-v1-653...97e

Today:         $0.15
This Week:     $1.23
This Month:    $1.23

Credits:       $175.00 remaining
Total Used:    $150.76

Rate Limit:    Unlimited (10s interval)
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/auth/key` | Detailed usage breakdown (daily/weekly/monthly) |
| `GET /api/v1/credits` | Credit balance and total lifetime usage |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `OPENROUTER_API_KEY not found` | Key not in environment | Set `OPENROUTER_API_KEY` in `.env` |
| `401 Unauthorized` | Invalid key | Verify key at https://openrouter.ai/keys |
| `Connection timeout` | Network issue | Check connection, retry |

## Implementation Notes

**API Key Discovery:** Since the skill runs in subprocesses without inheriting the full agent environment, it scans `/proc/*/environ` from parent processes to find `OPENROUTER_API_KEY`. This mirrors the approach used by the `image-gen` skill.

**No External Dependencies:** Uses only Python stdlib (`urllib`, `json`, `os`) to avoid pip installation issues in constrained environments.
