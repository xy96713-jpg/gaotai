# Quick Start

This project is a local Chinese writing workbench. It is meant for people who can run a local Python server and provide their own model API keys. The default route uses an OpenAI-compatible chat completions API plus local/Codex workflow checks. Older provider-specific routes remain available for existing local installs.

It is not a public SaaS, not a one-click desktop app, and not a multi-user service.

## 1. Clone And Enter

```bash
git clone https://github.com/xy96713-jpg/gaotai.git
cd gaotai
```

## 2. Create Local Config

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and fill in:

```bash
GAOTAI_API_KEY=your_api_key
GAOTAI_BASE_URL=https://your-provider.example/v1
GAOTAI_MODEL=your-model-name
```

Keep `.env.local` private. It is ignored by Git.

Default model roles:

- The default OpenAI-compatible route writes formal drafts, rewrites selected lines, and helps with support review.
- Codex/local scripts route work, run checks, save documents, and enforce gates.
- Legacy provider-specific routes can be configured only if you are maintaining an older setup.

## 3. Start The Workbench

```bash
make workbench-start
```

Open:

```text
http://127.0.0.1:8766/v2/
```

Check service status:

```bash
make workbench-status
```

The health output should show:

- `screenRunning: true`
- `health.ok: true`
- `deepseek_configured: true`, or a `GAOTAI_*` setup mapped to the default route

## 4. First Test Run

1. Click `新主题`.
2. Write a title.
3. Click `保存`.
4. Type or paste a short draft.
5. Select one sentence in the body.
6. Use the floating rewrite action.
7. Accept or record a liked/disliked line.
8. Use paragraph assist only from a blank line inside the body.
9. Run `收稿` before export.

For a command-line smoke test:

```bash
make workbench-smoke
```

For a broader local check:

```bash
make workbench-verify
```

## 5. Topic And Archive Behavior

The workbench is the source of truth.

- Use `打开主题` to search and reopen old topics.
- Use `版本` inside the workbench for recent saved versions.
- Obsidian is optional and read-only.
- Obsidian only receives formal topic index pages.
- Individual style-memory records, test topics, and version nodes are not synced into Obsidian.

## 6. Common Problems

### The Default Model API Is Not Configured

Run:

```bash
make workbench-status
```

If `deepseek_configured` is false, check `.env.local`. The public template maps `GAOTAI_*` settings onto the internal default route.

### Port 8766 Is Busy

Restart the workbench:

```bash
make workbench-restart
```

### Model Calls Are Slow

This is expected for formal drafting. Selected-line rewrites and paragraph assist are lighter routes. Formal full drafting uses heavier model settings and should not be treated as instant UI work.

### I Do Not Want Obsidian

Do nothing. The workbench works without Obsidian. Obsidian sync is only an optional archive layer.

## 7. Before Sharing Your Fork

Run:

```bash
make workbench-external-readiness
make workbench-fresh-clone-smoke
make workbench-release-check
```

Then inspect:

```bash
git status --short
```

Do not commit:

- `.env.local`
- `.cache/writing/documents/`
- `.cache/writing/topic_archives/`
- model request/response files
- local Obsidian vault content
- screenshots or exported personal drafts
