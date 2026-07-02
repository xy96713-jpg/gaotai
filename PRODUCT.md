# Writing Workbench Product Handoff

This document fixes the product boundary for the local Chinese writing workbench.
Use it when deciding whether a change belongs in the workbench, how a new topic
should be written, and what must be verified before calling the product stable.

## Current Status

The workbench is ready for private local use and small technical beta sharing.

It is not a public SaaS, not a multi-user app, and not a one-click writing
machine. It is a local writing cockpit for one operator who can run a Python
service, configure model API keys, and judge final prose manually.

## Product Promise

The product should make Chinese long-form writing less fragile by preserving the
writer's decisions across drafts.

It should help with:

- starting each article as a separate topic;
- keeping the full draft visible while editing;
- rewriting one selected sentence without taking over the whole article;
- recording liked and disliked lines as reusable style memory;
- filling a missing paragraph from local context;
- checking a finished draft without auto-changing the body;
- exporting or presenting the current draft.

It should not promise:

- one-click publishable articles;
- automatic topic judgment;
- automatic fact research inside the frontend;
- public deployment;
- multi-user permissions;
- cloud sync;
- AI detector evasion.

## Daily User Flow

Use the workbench like this:

1. Open `http://127.0.0.1:8766/v2/`.
2. Click `新主题` for a new article, or `打开主题` for an old one.
3. Write the title and save once.
4. Let Codex prepare the serious writing brief outside the frontend when the
   topic needs research.
5. Put the controlled draft into the editor.
6. Read the draft in the editor, not in a chat window.
7. Select a weak sentence and use `改句`.
8. Mark useful sentences as `喜欢`.
9. Mark bad patterns as `讨厌`.
10. Add a blank paragraph and write a short demand when a section needs one more
    paragraph.
11. Run `收稿` near the end.
12. Export or enter presentation mode.

The frontend is the editing surface. Codex remains the operator for research,
briefs, source packs, and final judgment.

## Model Routing

Keep the routing narrow:

- **Codex**: research, source pack, article brief, style-memory recall,
  orchestration,收稿检查, rejection, final operator judgment.
- **DeepSeek**: default formal draft, selected-sentence rewrite, local support
  review, logic patching, and lightweight paragraph support.
- **Kimi**: optional legacy route only. Do not make it a required dependency for
  the public clone path.

Do not add more model choices to the default UI. New models can be tested in
scripts or backend routes first. The frontend should stay simple.

## Frontend Boundary

The default frontend should stay light.

Keep visible:

- title;
- `新主题`;
- `保存`;
- `导出`;
- `演示`;
- `打开主题`;
- `版本`;
- current word count / duration;
- contextual selected-line actions;
- candidate results when they exist.

Avoid adding permanent panels for:

- full drafting;
- deep audit internals;
- model debugging;
- Obsidian graph state;
- prompt engineering;
- API diagnostics.

Those can exist in scripts, logs, or backend reports. They should not become the
default writing surface.

## Style Memory Rule

Style memory is useful only when it stores a reason, not just a sentence.

Each durable preference should answer:

- What was the original line?
- Was it liked or disliked?
- Why?
- What class is it?
- What should happen next time?

Good reasons include:

- object is clear;
- action is clear;
- consequence is visible;
- sounds like a report;
- too abstract;
- fake oral tone;
- forbidden two-step contrast;
- hollow AI phrase.

If a style rule makes candidates worse, delete or weaken the rule. Do not keep
rules forever just because they were once recorded.

## Topic Management Rule

Every serious article should have one topic document.

Use `新主题` for a genuinely new article. Use `打开主题` for old work. Do not
create duplicate themes just to test UI behavior. Smoke tests must use temporary
document IDs and should not pollute the formal topic list.

Soft delete is preferred over permanent delete. Public or shared releases should
default to hiding test topics.

## What Counts As Done

A normal product change is done only when:

- the intended behavior works in the local app;
- `git status --short` is clean or only contains intentionally separated work;
- the smallest relevant test has passed;
- UI changes have at least one browser or product-audit check;
- user-facing docs are updated when the workflow changed.

For the writing workbench release gate, use:

```bash
make workbench-release-check
```

For lighter local confidence, use:

```bash
node --check inline_editor_v2/app.js
python3 tools/workbench_product_audit.py
python3 -m unittest tests.test_inline_editor_server
```

## Known Limits

- Final article taste still needs human judgment.
- Model latency is real; formal generation should not be treated as instant UI.
- Selected-sentence rewriting can still miss wider context.
- Style memory improves routing but cannot guarantee the user's voice.
- Obsidian is optional archive/mirror material, not the writing source of truth.
- External users must configure their own model keys.

## Do Not Mix Projects

This repository has accumulated adjacent experiments. For future work, keep
project scope strict:

- writing-workbench changes belong here;
- unrelated video, AR, map, audio, or motion work should live in separate
  project folders or separate PRs;
- do not clean unrelated dirty files by merging them into the writing workbench
  release line;
- if an unrelated diff appears, back it up or isolate it before continuing.

## Maintenance Checklist

Before calling the product stable for the day:

```bash
git status --short
node --check inline_editor_v2/app.js
python3 tools/workbench_product_audit.py
```

Before sharing the repository:

```bash
make workbench-external-readiness
make workbench-fresh-clone-smoke
make workbench-release-check
```

Before writing a serious new article:

1. Create or open the topic in the workbench.
2. Build source pack and brief in Codex.
3. Let DeepSeek write only after the brief is ready, or place an existing draft
   into the editor.
4. Use selected-line rewrite/support for local repair, not whole-draft churn.
5. Use `收稿` before export.
