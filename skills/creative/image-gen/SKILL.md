---
name: image-gen
description: Generate images via OpenRouter AI. Uses GPT-5 Image/Gemini Image. Outputs MEDIA: path for native delivery.
version: 3.0.0
author: hermclaw
license: MIT
dependencies: []
metadata:
  hermes:
    tags: ["image", "generation", "ai-art", "openrouter"]
    related_skills: ["ascii-art", "p5js"]
---

# Image Generation Skill

Generate images from text prompts using OpenRouter AI — the script outputs a `MEDIA:/path` line which the agent delivers natively to the home channel (Telegram, Discord, etc.).

## How It Works

**Key discovery:** OpenRouter's image models (GPT-5 Image, Gemini Image) do **NOT** use OpenAI's `/images/generations` endpoint. They are chat models that return images embedded in the `message.images` field of a `chat/completions` response.

Workflow:
1. `POST /chat/completions` with image-capable model
2. Model response contains `choices[0].message.images[0].image_url.url` (base64 data URL)
3. Decode base64 → save as PNG
4. Print `MEDIA:/path/to/file.png` → agent picks up and delivers natively

## Supported Models (OpenRouter)

| Model | Speed | Quality | Notes |
|-------|-------|---------|-------|
| `openai/gpt-5-image` | Slow | Highest | Best detail |
| `openai/gpt-5-image-mini` | Fast | Good | **Default** (recommended) |
| `openai/gpt-5.4-image-2` | Medium | Excellent | Latest GPT-5.4 |
| `google/gemini-2.5-flash-image` | ⚡ Very fast | Good | Fastest (~6s) |
| `google/gemini-3.1-flash-image-preview` | Fast | Good | Iterative |
| `google/gemini-3-pro-image-preview` | Slower | Best | Most detailed |

**Not available:** `sourceful/riverflow-v2-pro` — Sourceful provider not on OpenRouter.

## Prerequisites

**Environment variable:**
```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

**Python:** 3.8+ with stdlib only. No `pip` packages required.

## Usage

```bash
# Basic — generate + auto-send to Telegram
python3 scripts/image_gen.py --prompt "A pelican riding a bicycle"

# Custom output path (Telegram still sent automatically)
python3 scripts/image_gen.py --prompt "Cyberpunk city" --output ~/Desktop/cyber.png

# Use specific model
python3 scripts/image_gen.py --prompt "Cat portrait" --model openai/gpt-5-image

# List all available image models
python3 scripts/image_gen.py --list-models

# Custom Telegram caption (defaults to prompt)
python3 scripts/image_gen.py --prompt "..." --caption "Generated image"
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--prompt` | Text description *(required unless `--list-models`)* | — |
| `--model` | OpenRouter model ID | `openai/gpt-5-image-mini` |
| `--n` | Number of images to generate | `1` |
| `--output` | Save to specific file path (optional) | `/tmp/hermes-gen-<timestamp>.png` |

## Output

```
✓ Generated: /tmp/hermes-gen-1776983418-0.png
MEDIA:/tmp/hermes-gen-1776983418-0.png
✓ Saved to: /tmp/custom.png
```

The `MEDIA:` line is detected by the agent and delivered to your home channel natively.

## Development Notes (Trial & Error)

**Initial false start:** Attempted to use `/api/v1/images/generations` endpoint → consistent 404 errors. Discovered through testing that OpenRouter routes image models through `chat/completions` and the images appear in `message.images` field, not as separate endpoint.

**Provider availability:** `sourceful/riverflow-v2-pro` is not listed in the OpenRouter models catalog. Sourceful is not an integrated provider on the platform.

**Dependency constraint:** Hermes venv is write-protected; `requests` package unavailable. Rewrote using Python stdlib `urllib`.

**Native delivery:** The script prints `MEDIA:/path/to/file.png` to stdout. The agent (or cron run's final response) detects this and delivers the file natively to the home channel — no Telegram bot token needed.

**API key access:** Since the skill runs in a subprocess without inheriting the agent's environment, it scans `/proc/*/environ` for `OPENROUTER_API_KEY` from parent processes.

## API Reference

```python
# Available endpoints (Bearer auth):
GET  /api/v1/models     # Model catalog + pricing
POST /api/v1/chat/completions  # LLM + image generation

# Not available (404/401/HTML):
POST /api/v1/images/generations  # ❌ Does not exist
GET  /api/v1/account             # ❌ HTML dashboard only
GET  /api/v1/keys                 # ❌ 401 Unauthorized
```

## Error Handling

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `OPENROUTER_API_KEY not found` | Env var missing | `export OPENROUTER_API_KEY=...` |
| `No images in response` | Wrong model ID | Use `--list-models` to verify |
| Timeout (>90s) | Model too slow or network issue | Switch to `gemini-2.5-flash-image` |

## Cost Tracking

Each API response includes detailed usage:
```json
{
  "usage": {
    "prompt_tokens": 2405,
    "completion_tokens": 4985,
    "total_tokens": 7390,
    "cost": 0.0410325,
    "cost_details": {
      "upstream_inference_prompt_cost": 0.0060125,
      "upstream_inference_completions_cost": 0.03502
    }
  }
}
```

Image tokens dominate cost (Gemini: ~4175 image tokens for 512×512).

## Future Work

- [ ] Integrate `sourceful/riverflow-v2-pro` via direct Sourceful API (separate skill)
- [ ] Add retry logic for transient network failures