# Gaotai

English · [中文](README.md)

Gaotai is a local writing desk for people who already write long-form drafts with AI.

It does not try to turn one prompt into a finished article. You write in a browser editor, rewrite one sentence at a time, save the lines you like or dislike, and run a final pass before export. The model gives you candidates and fills gaps. You keep control of the draft.

Gaotai runs on your own machine. Bring any OpenAI-compatible `/chat/completions` API key, start the local server, and open the editor in your browser.

Good fit for:

- Writers who use AI for articles, scripts, demos, or project notes but do not want to work inside a chat box.
- People who want sentence-level rewrite, preference memory, topic/version saving, and a lightweight final review.
- Technical users comfortable with a local Python service, API keys, and local file storage.

Not a good fit for:

- Public SaaS, team accounts, cloud sync, or multi-user collaboration.
- Users who want a no-config desktop app.

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
