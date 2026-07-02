# Gaotai

English · [中文](README.md)

Gaotai is a local writing desk you can hand to Codex or another coding agent to deploy.

Send your agent this repo, let it clone the project, copy `.env.local.example`, fill in your model API settings, and start the local server. You then open a browser editor instead of writing inside a chat box.

Gaotai is less about “generate an article” and more about what happens after the first draft. Select one sentence and ask for rewrites. Mark a line as liked when it sounds right. Mark a line as disliked when it feels empty, generic, or too AI-written. Those choices go into a style memory and come back during later rewrites, paragraph fills, and final review.

It runs on your own machine. Drafts, versions, and style memory stay local. The default model route uses any OpenAI-compatible `/chat/completions` API, so the project is not tied to one provider.

## Agent Setup Prompt

```text
Clone https://github.com/xy96713-jpg/gaotai, copy .env.local.example to .env.local,
fill GAOTAI_API_KEY / GAOTAI_BASE_URL / GAOTAI_MODEL, run make workbench-start,
then open http://127.0.0.1:8766/v2/.
```

## Good Fit

- You already use AI for articles, scripts, demos, or project notes.
- You care more about editing a draft than getting a single full response from chat.
- You want the system to remember which lines fit your style and which ones should be avoided.
- You are comfortable with a local Python service, API keys, and local file storage.

## Core Loop

```text
prepare material -> draft -> rewrite one sentence -> save preferences -> final review -> export
```

The middle matters most:

- **Rewrite**: select one sentence and rewrite only that sentence.
- **Like / dislike**: save what should be repeated or avoided next time.
- **Style memory**: carry those choices into later rewrites, paragraph fills, and final review.

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
