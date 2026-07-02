# Release Manifest

Use this manifest before pushing the writing workbench to GitHub.

## Release Scope

Include:

- `README.md`
- `QUICKSTART.md`
- `PRODUCT.md`
- `PROJECT_BOUNDARIES.md`
- `OPEN_SOURCE_GUIDE.md`
- `RELEASE_MANIFEST.md`
- `AGENTS.md`
- `WRITING_ROOT_SOP.md`
- `WRITING_STAGE_GATES.md`
- `WRITING_SOP.md`
- `WORKBENCH_*.md`
- `Makefile`
- `inline_editor_v2/`
- `tools/inline_editor_server.py`
- `tools/workbench_*.py`
- `tools/workbench_*.mjs`
- `tools/style_memory.py`
- `tools/style_memory_hygiene.py`
- `tools/workbench_final_review.py`
- `tools/workbench_external_readiness.py`
- `tests/test_inline_editor_server.py`
- `tests/test_workbench_*.py`

Exclude:

- `.cache/` runtime output except intentionally tracked workflow config/templates
- `obsidian_vault/`
- `mlx_models/`
- `video_analysis_v1/`
- `inline_editor/` legacy prototype
- screenshots, logs, local exported drafts, and model request/response files
- API keys, tokens, cookies, local environment files

## Staging Command

Prefer explicit staging over `git add .`:

```bash
git add .gitignore README.md QUICKSTART.md PRODUCT.md PROJECT_BOUNDARIES.md OPEN_SOURCE_GUIDE.md RELEASE_MANIFEST.md AGENTS.md \
  WRITING_ROOT_SOP.md WRITING_STAGE_GATES.md WRITING_SOP.md WORKBENCH_*.md Makefile \
  inline_editor_v2 \
  tools/inline_editor_server.py tools/workbench_*.py tools/workbench_*.mjs \
  tools/style_memory.py tools/style_memory_hygiene.py tools/workbench_final_review.py \
  tests/test_inline_editor_server.py tests/test_workbench_*.py
```

Then inspect:

```bash
git diff --cached --name-only
git diff --cached --stat
```

## Verification

Run before commit:

```bash
python3 -m unittest tests.test_inline_editor_server tests.test_workbench_formal_artifacts
python3 -m unittest tests.test_run_article_sop tests.test_section_beat_check tests.test_article_delivery_contract tests.test_article_engine_audit tests.test_editorial_desk_preflight tests.test_opening_ending_taste_audit tests.test_project_story_pack tests.test_source_coverage_gate tests.test_style_memory tests.test_writing_sop_preflight
node --check inline_editor_v2/app.js
python3 -m py_compile tools/workbench_product_audit.py tools/inline_editor_server.py tools/run_article_sop.py tools/writing_sop_preflight.py
python3 tools/workbench_product_audit.py
WORKBENCH_DOCUMENT_ID=first_video_concise_strengthened_20260617 node tools/workbench_browser_smoke.mjs
```

For the small private beta release gate:

```bash
make workbench-external-readiness
make workbench-fresh-clone-smoke
make workbench-release-check
```

For provenance metadata:

```bash
WORKBENCH_DOCUMENT_ID=sop_drill_ai_boom_reality_check_20260627_kimi_draft_v2 node tools/workbench_provenance_smoke.mjs
```

## Local State Policy

Before opening a PR, `git status --short` should show only deliberate product changes. Local personal style-memory edits such as `.cache/writing/bad_lines_corpus.md` or `.cache/writing/config/personal_ip_tone_profile.md` should normally stay uncommitted unless the change is an intentional reusable rule for this repository.

## Sensitive File Scan

Run before pushing:

```bash
rg -n "api[_-]?key|secret|token|Bearer|sk-|KIMI|DEEPSEEK|OPENAI|MOONSHOT|cookie|authorization" \
  --glob '!.cache/**' --glob '!*.backup*' .
```

Review every hit manually. Some hits may be documentation examples, but none should contain real credentials.
