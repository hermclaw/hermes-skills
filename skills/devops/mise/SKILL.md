---
name: mise
description: Manage tool versions with mise. Use when a repository has a .mise.toml or mise.toml file — activate mise to get the correct toolchain versions without system-wide installs.
author: hermclaw
---

## Overview

mise (https://mise.jdx.dev/) is a polyglot version manager that manages tool versions per-project via `.mise.toml` or `mise.toml` files. It replaces asdf/rbenv/nvm/etc.

## When to Use

- A repository contains a `mise.toml` or `.mise.toml` file
- Need to use a specific version of Ruby, Node.js, Python, Bun, Go, or any supported tool
- Want to avoid system-wide tool version conflicts

## Setup

### Installation

Installed via `curl https://mise.run | sh` at `~/.local/bin/mise`.
Precompiled binaries enabled via `mise settings ruby.compile=false` to avoid slow source compilation.

### Activation (eval pattern)

Before running commands that need mise-managed tools, activate in your shell:

```bash
eval "$($HOME/.local/bin/mise activate bash)"
```

Activation must be included in every `terminal()` call chain, or run once at the start of a background session.

### Running Commands via `mise exec` (preferred for single commands)

For one-off commands, `mise exec` avoids the need for `eval activate`:

```bash
cd /path/to/repo && $HOME/.local/bin/mise exec -- bundle install
cd /path/to/repo && $HOME/.local/bin/mise exec -- rails test
$HOME/.local/bin/mise exec --node@20 -- which node
```

### Running Tasks

If `mise.toml` defines `[tasks]`, run them with:

```bash
cd /path/to/repo && $HOME/.local/bin/mise run <task_name>
```

### Installing Tools

```bash
cd /path/to/repo && eval "$($HOME/.local/bin/mise activate bash)" && mise install
```

### Trust

Untrusted `.mise.toml` files (fresh clones, new additions) must be trusted:

```bash
cd /path/to/repo && $HOME/.local/bin/mise trust
```

Trust persists until the file changes — if `.mise.toml` or `mise.toml` is modified, re-trust is required.

## Standard Pattern

```bash
cd ~/.hermes-openrouter/github-repos/REPO_NAME \
  && eval "$($HOME/.local/bin/mise activate bash)" \
  && your_command_here
```

Or for single commands with `mise exec`:
```bash
$HOME/.local/bin/mise exec -C ~/.hermes-openrouter/github-repos/REPO_NAME -- your_command_here
```

## Pitfalls

- **Activation is per-session**: `mise activate` modifies PATH and env vars for the current shell only. It does NOT persist across separate `terminal()` calls unless chained into each command.
- **Trust is per-file**: `mise trust` trusts a specific config file. If the file is modified or replaced, trust is revoked and must be re-applied.
- **Compiling from source is slow**: Ruby compilation takes 5+ minutes and can hit timeouts. Precompiled binaries are configured via `ruby.compile=false` — if this setting is missing on a fresh install, set it before `mise install`.
- **Never install globally**: Don't `apt install ruby` or `gem install` globally in mise-managed projects. Always use mise tool versions.
- **Working directory matters**: mise resolves tool versions from the current working directory upward through parent directories looking for config files. Always `cd` into the repo first, or use `mise exec -C <dir>` to specify explicitly.
- **Config file naming**: mise accepts both `mise.toml` and `.mise.toml` (hidden). Some projects use `.tool-versions` (asdf-compatible). All three are recognized.
