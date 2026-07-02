# Gaotai

English · [中文](README.md)

Move AI-assisted writing out of the chat box and into an editor.

Gaotai is a local writing workbench for Chinese long-form drafts. Hand this GitHub repo to Codex, Claude Code, Cursor Agent, or another coding agent, fill in your own model API settings, and run it on your machine.

Gaotai is not built around “generate a full article.” It is built around what happens after the first draft: rewrite one selected sentence, save lines you like, save lines you dislike, and reuse those preferences during later rewrites, paragraph fills, and final review.

Drafts, versions, and style memory stay local. For Chinese writing, you can plug in Chinese-strong domestic models first, or use any OpenAI-compatible `/chat/completions` API. Gaotai is not tied to one provider.

## Give This To Your Agent

```text
Clone https://github.com/xy96713-jpg/gaotai, copy .env.local.example to .env.local,
fill GAOTAI_API_KEY / GAOTAI_BASE_URL / GAOTAI_MODEL, run make workbench-start,
then open http://127.0.0.1:8766/v2/.
```

## Why Not Just Use Chat

Chat is good for asking questions. It is awkward for editing a long draft over time.

Gaotai gives you a writing surface with reusable actions:

| Action | What it does |
| --- | --- |
| Rewrite | Select one sentence and generate candidates for that sentence only. |
| Like | Save a line that fits your style so future edits can move closer to it. |
| Dislike | Save empty, generic, over-explained, or AI-sounding lines so future edits avoid them. |
| Fill | Write a short note in a blank paragraph and let the model fill it using nearby context. |
| Final review | Check wording, repetition, loose structure, filler, and speaking rhythm without auto-rewriting the draft. |

## Core Loop

```text
prepare material -> draft -> rewrite selected lines -> save preferences -> final review -> export
```

The style memory is the important part. It does not train a model. It keeps a reusable record of your editing decisions: which lines can stay, and which shapes should show up less often next time.

## Quick Start

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

Start the workbench:

```bash
make workbench-start
```

Open:

```text
http://127.0.0.1:8766/v2/
```

Run a local check:

```bash
make workbench-verify
```

## What It Includes

- Browser writing editor.
- Topic and version saving.
- Sentence-level rewrite candidates.
- Like/dislike memory for reusable style preferences.
- Paragraph assist from an in-draft note.
- Final review for wording, repetition, loose structure, and empty filler.
- Export and presentation mode.
- Video material intake and analysis helpers.

## Current Status

Gaotai is ready for local technical users and small private trials. It is not a hosted product yet.

The public repo is a clean export without private draft history, local cache, or API keys.
