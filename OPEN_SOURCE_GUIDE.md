# Open Source Guide

This repository can be shared as a local, self-hosted writing workbench. It is
not packaged as a public SaaS.

## What Others Get

- A local Python web service on port `8766`.
- A browser writing workbench at `/v2/`.
- Local document saving under `.cache/writing/`.
- OpenAI-compatible drafting/rewrite routes when the user provides their own key.
- Codex-backed review routes when Codex Desktop/CLI is available on the machine.
- Optional legacy routes if the user already has an older provider-specific setup.

## External User Setup

```bash
git clone https://github.com/xy96713-jpg/gaotai.git
cd gaotai
cp .env.local.example .env.local
```

Edit `.env.local`:

```bash
GAOTAI_API_KEY=your_api_key
GAOTAI_BASE_URL=https://your-provider.example/v1
GAOTAI_MODEL=your-model-name
```

Start:

```bash
make workbench-start
```

Open:

```text
http://127.0.0.1:8766/v2/
```

Check:

```bash
make workbench-status
```

Minimum expected state:

- service is listening on `127.0.0.1:8766`;
- `health.ok` is true;
- `deepseek_configured` is true after `GAOTAI_*` has been mapped to the default route;
- legacy provider flags may be false on the default public setup.

## What To Tell Another Agent

If someone gives this repo to their own agent, the instruction should be:

```text
Clone the repo, copy .env.local.example to .env.local, fill GAOTAI_API_KEY,
GAOTAI_BASE_URL, and GAOTAI_MODEL for an OpenAI-compatible chat completions API,
install Python dependencies from requirements files if missing, run
make workbench-start, then open http://127.0.0.1:8766/v2/. Treat old
provider-specific routes as optional legacy support. Do not commit .env.local
or .cache runtime output.
```

## Maintainer Release Checklist

Before pushing a release branch:

```bash
git status --short
make workbench-external-readiness
make workbench-fresh-clone-smoke
make workbench-release-check
node --check inline_editor_v2/app.js
python3 -m py_compile tools/inline_editor_server.py
```

Sensitive-file scan:

```bash
rg -n "api[_-]?key|secret|token|Bearer|sk-|cookie|authorization" \
  --glob '!.cache/**' --glob '!*.bak*' --glob '!*.backup*' .
```

Review every hit manually. Documentation examples are allowed; real keys are
not.

## Do Not Publish

- `.env.local`
- `.env.*` backups
- `.cache/writing/documents/`
- `.cache/writing/topic_archives/`
- model request/response caches
- local screenshots and exported personal drafts
- Obsidian vault content
- browser cookies or platform login state

## Current Boundary

This is suitable for technical users who can configure local keys and run a
local service. It is not suitable for ordinary public users until it has:

- account isolation;
- hosted storage;
- queue and cost control;
- monitoring;
- data cleanup policy;
- deployment docs for a real server environment.
