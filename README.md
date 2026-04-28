# Hermes Skills

A curated collection of skills for [Hermes Agent](https://github.com/NousResearch/hermes) — created and maintained by [hermclaw](https://github.com/hermclaw).

## Philosophy

This repository follows a **curation over collection** approach:
- Skills are self-contained with all scripts inside
- No standalone `scripts/` directory — everything lives within skills
- Published via whitelist (`public-skills.txt`) with security scanning
- Everything attributed to hermclaw

## Skills

### Core Infrastructure

| Skill | Path | Description |
|-------|------|-------------|
| **sync-public-skills** | `devops/sync-public-skills/` | Meta-skill that publishes selected skills to this repo. Scans for secrets before syncing. |
| **mise** | `devops/mise/` | Per-project toolchain version management. Replace asdf/rbenv/nvm — supports Ruby, Node.js, Python, Bun, Go, and more. |

### Utilities

| Skill | Path | Description |
|-------|------|-------------|
| **weather** | `productivity/weather/` | Daily weather reports using Open-Meteo. Auto-detects zipcode from context or prompts. |

### NYC Transit

| Skill | Path | Description |
|-------|------|-------------|
| **train-report** | `productivity/train-report/` | NYC Subway real-time ETA for any station. Enter a station name and get arrivals for all lines in both directions. Covers all 379 subway stations via MTA GTFS data. |

## Installing Skills

Clone this repo into your Hermes skills directory:

```bash
git clone https://github.com/hermclaw/hermes-skills.git \
  ~/.hermes-openrouter/skills
```

Or copy individual skills:

```bash
cp -r hermes-skills/productivity/weather \
  ~/.hermes-openrouter/skills/productivity/
```

## Using Skills

Each skill contains a `SKILL.md` with usage instructions. Run scripts directly:

```bash
# Example: weather skill
~/.hermes-openrouter/skills/productivity/weather/scripts/weather
~/.hermes-openrouter/skills/productivity/weather/scripts/weather 90210
~/.hermes-openrouter/skills/productivity/weather/scripts/weather 90210 tomorrow

# Example: train-report skill
~/.hermes-openrouter/skills/productivity/train-report/scripts/train-report "penn station"
~/.hermes-openrouter/skills/productivity/train-report/scripts/train-report "times square"
~/.hermes-openrouter/skills/productivity/train-report/scripts/train-report --list
```

## Publishing Your Own

This repo is managed by the `sync-public-skills` skill. To sync:

1. Add your skill to `~/.hermes-openrouter/public-skills.txt`
2. Run the sync script (scans for secrets automatically):
   ```bash
   ~/.hermes-openrouter/skills/devops/sync-public-skills/scripts/sync-public-skills
   ```
3. Commit and push from `~/.hermes-openrouter/github-repos/skills/`

## Security

All skills are scanned before publishing:
- API keys, tokens, secrets (regex patterns)
- AWS keys, GitHub tokens, OpenAI keys
- Private keys, bearer tokens
- High-entropy base64 blobs

Skills with detected secrets are blocked from syncing.

## License

MIT — See individual skills for details.

## Author

Created by [hermclaw](https://github.com/hermclaw) / [capotej](https://github.com/capotej)
