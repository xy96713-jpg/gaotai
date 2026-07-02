# Gaotai

English · [中文](README.md)

![License](https://img.shields.io/badge/license-MIT-black)
![Local First](https://img.shields.io/badge/local--first-yes-0f766e)
![API](https://img.shields.io/badge/API-OpenAI--compatible-2563eb)

Move AI-assisted writing out of the chat box and into an editor.

Gaotai is a local writing workbench for Chinese long-form drafts. Hand this repo to Codex, Claude Code, Cursor Agent, or another coding agent. It can clone the project, copy `.env.local.example`, fill in your model API settings, and start the local server. You open a browser and write there.

Gaotai is not another chat window. It turns revision into reusable actions: rewrite one selected sentence, save lines you like, save lines you dislike, and run a final review before export. Those choices go into style memory and come back during later rewrites, paragraph fills, and reviews.

Drafts, versions, and style memory stay local. For Chinese writing, you can start with Chinese-strong domestic models, or use any API compatible with OpenAI `/chat/completions`.

## Give This To Your Agent

```text
Clone https://github.com/xy96713-jpg/gaotai, copy .env.local.example to .env.local,
fill GAOTAI_API_KEY / GAOTAI_BASE_URL / GAOTAI_MODEL, run make workbench-start,
then open http://127.0.0.1:8766/v2/.
```

## Why It Exists

Chat is good for asking questions. It is clumsy for editing a long draft over time. A draft may look complete but still be hard to keep: sentences are smooth but vague, paragraphs exist but the point drifts, and the model forgets the style notes you gave it last time.

Gaotai puts the revision actions on one page.

| Action | What it does |
| --- | --- |
| Rewrite | Select one sentence and generate candidates for that sentence only. |
| Like | Save a line that fits your style so future edits can move closer to it. |
| Dislike | Save empty, generic, over-explained, or AI-sounding lines so future edits avoid them. |
| Fill | Write a short note in a blank paragraph and let the model fill it using nearby context. |
| Final review | Check wording, repetition, loose structure, filler, and speaking rhythm without auto-rewriting the draft. |

## Writing Loop

```text
prepare material -> draft -> rewrite selected lines -> save preferences -> final review -> export
```

Style memory is the center of the loop. It does not train a model. It keeps a reusable record of your editing decisions: which lines can stay, and which shapes should show up less often next time.

## Model API

Gaotai reads three values from `.env.local`:

```bash
GAOTAI_API_KEY=your_api_key
GAOTAI_BASE_URL=https://your-provider.example/v1
GAOTAI_MODEL=your-model-name
```

Any OpenAI-compatible `/chat/completions` service can be used. For Chinese writing, use a model that handles Chinese prose and long-form revision well. Existing gateways, aggregator APIs, and local model servers can also be used if they expose a compatible endpoint.

## Quick Start

```bash
git clone https://github.com/xy96713-jpg/gaotai.git
cd gaotai
cp .env.local.example .env.local
```

After editing `.env.local`, start the workbench:

```bash
make workbench-start
```

Open:

```text
http://127.0.0.1:8766/v2/
```

Check the local setup:

```bash
make workbench-verify
```

## Features

- Local browser writing editor
- Topic and version saving
- Sentence-level rewrite candidates
- Like and dislike memory
- Style memory
- Context-aware paragraph fill
- Final review
- Export and presentation mode
- Video material download and analysis helpers

## Status

Gaotai is ready for local personal use and small technical trials. It is not a hosted product. It does not include accounts, team collaboration, cloud sync, queues, or cost controls.

The public repo is a clean export without private draft history, local cache, or API keys.

## Project Layout

```text
inline_editor_v2/          # writing editor frontend
tools/inline_editor_server.py
video_analysis_v1/         # video material page
tools/                     # local server, writing tools, verification scripts
tests/                     # regression tests
.env.local.example         # API config template
```

## License

MIT
