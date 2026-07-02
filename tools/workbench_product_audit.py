#!/usr/bin/env python3
"""Product audit for the local Chinese writing workbench.

The goal is to keep the workbench honest: compact UI, usable writing loop,
style-memory wiring, and a visible lift over a direct AI-ish baseline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import (  # noqa: E402
    audit_banned_shapes,
    quick_audit,
    quality_gate_for_generated_body,
)
from tools.style_memory import StyleMemoryStore  # noqa: E402
from tools.style_memory import DEFAULT_DELETED_STORE, DEFAULT_STORE  # noqa: E402


DEFAULT_DRAFT = ROOT / ".cache" / "writing" / "ai_writing_best_way_fullrun_20260615" / "codex_minimal_repaired_body.md"
DEFAULT_DOCUMENT = ROOT / ".cache" / "writing" / "documents" / "real_loop_ai_writing_workbench_kimi.json"
FIXTURE_DRAFT = ROOT / "tests" / "fixtures" / "workbench_product_audit" / "codex_minimal_repaired_body.md"
FIXTURE_DOCUMENT = ROOT / "tests" / "fixtures" / "workbench_product_audit" / "real_loop_ai_writing_workbench_kimi.json"
FIXTURE_STYLE_MEMORY = ROOT / "tests" / "fixtures" / "workbench_product_audit" / "style_memory.jsonl"
FIXTURE_BROWSER_SMOKE = ROOT / "tests" / "fixtures" / "workbench_product_audit" / "workbench_browser_smoke_latest.json"
FIXTURE_LIVE_GENERATION = ROOT / "tests" / "fixtures" / "workbench_product_audit" / "workbench_live_generation_latest.json"
FORMAL_READONLY_SMOKE_LATEST = ROOT / ".cache" / "writing" / "workbench_formal_readonly_smoke_latest.json"
BROWSER_SMOKE_LATEST = ROOT / ".cache" / "writing" / "workbench_browser_smoke_latest.json"
LIVE_GENERATION_LATEST = ROOT / ".cache" / "writing" / "workbench_live_generation_latest.json"
REPORT_DIR = ROOT / ".cache" / "writing"
TITLE = "这可能是目前 AI 写作最好的方式"
BRIEF = (
    "做一期视频介绍我的写作工作台。主线：发现 AI 写作不好用 -> 查原因和主流解法 -> "
    "解释我的工作流和前端 -> 展示划选改句、喜欢/讨厌、审稿、导出 -> 给出用和不用的差距。"
    "本稿保留用户锁定开头，不能为了门槛替换入口。"
)
MATERIAL_CARD = {
    "claim": "写作工作台的价值要通过退稿、风格库、划选改句、审稿和前后对比证明。",
    "sources": "79 篇研究；96 项研究；Axios；STORM；PaperDebugger；本地工作台",
    "noInvent": "后台数据,取关曲线,私信,采访对象",
}

BASELINE_BODY = "\n\n".join(
    [
        "随着人工智能技术的快速发展，AI 写作正在深刻改变内容生产。",
        "它不仅能够提升写作效率，更能帮助创作者重塑表达方式，带来前所未有的机遇与挑战。",
        "真正值得关注的是，创作者如何在这个时代建立自己的底层逻辑，让工具释放更大的价值。",
        "由此可见，未来的写作会更加依赖人机协同，这也是每个内容创作者都需要面对的重要趋势。",
    ]
)


class PlainTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"p", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        value = "".join(self.parts)
        lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
        blocks = [line for line in lines if line]
        return "\n\n".join(blocks)


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def html_to_text(value: str) -> str:
    parser = PlainTextHTMLParser()
    parser.feed(value or "")
    return parser.text()


def split_markdown(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    title = TITLE
    if lines and lines[0].startswith("# "):
        title = lines[0].removeprefix("# ").strip() or title
        body = "\n".join(lines[1:]).strip()
    elif lines and lines[0].strip() and len(lines[0].strip()) <= 80:
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
    else:
        body = raw.strip()
    return title, body


def resolve_default_artifact(path: Path, fallback: Path) -> Path:
    if path.exists():
        return path
    if fallback.exists():
        return fallback
    return path


def product_audit_style_store() -> StyleMemoryStore:
    if DEFAULT_STORE.exists():
        return StyleMemoryStore(DEFAULT_STORE, DEFAULT_DELETED_STORE)
    return StyleMemoryStore(FIXTURE_STYLE_MEMORY, FIXTURE_STYLE_MEMORY.with_name("style_memory_deleted.jsonl"))


def document_text(path: Path) -> tuple[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    title = normalize_space(payload.get("title")) or TITLE
    text = str(payload.get("content_text") or "").strip()
    if not text:
        text = html_to_text(str(payload.get("content_html") or ""))
    return title, text


def run_gate(script: str, draft_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script), str(draft_path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=20,
        check=False,
    )
    output = result.stdout.strip()
    return {
        "script": script,
        "status": "pass" if result.returncode == 0 else "fail",
        "returncode": result.returncode,
        "summary": output.splitlines()[0] if output else "",
    }


def evaluate_text(
    title: str,
    body: str,
    store: StyleMemoryStore,
    *,
    brief: str = BRIEF,
    material_card: dict[str, str] = MATERIAL_CARD,
) -> dict[str, Any]:
    audit = quick_audit(title, body, store)
    gate = quality_gate_for_generated_body(
        body=body,
        title=title,
        brief=brief,
        material_card=material_card,
        minimal_edit={"auditAfter": {"findings": audit_banned_shapes(body, store)}},
        personal_material_allowed=False,
    )
    return {
        "score": audit.get("score", 0),
        "quickFindingCount": len([item for item in audit.get("findings", []) if item.get("kind") != "pass"]),
        "hardBanCount": len(audit_banned_shapes(body, store)),
        "qualityGate": gate.get("status"),
        "qualityReasons": gate.get("reasons", []),
        "paragraphCount": gate.get("paragraphCount", 0),
        "maxParagraphLength": gate.get("maxParagraphLength", 0),
    }


def ui_checks(index: str, app: str) -> list[dict[str, Any]]:
    styles = (ROOT / "inline_editor_v2/styles.css").read_text(encoding="utf-8")
    checks: list[tuple[str, bool, str]] = [
        ("正文浮层动作：改句", 'id="selectionMenu"' in index and "data-run" in index and "selectionMenu.hidden = false" in app, "改句应贴着正文选区出现，不应常驻右栏。"),
        ("正文浮层动作：记录", 'data-ban' in index and 'data-like' in index and "saveMemory" in app, "喜欢/讨厌应是正文上下文动作，记录到风格库。"),
        ("后台审计保留", "/api/ai-flavor-audit" in app and "renderAiFlavorAudit" in app and "runHardCheckWithProof" in app, "文本痕迹和硬伤审计保留给生成后自动终审，不放进默认按钮。"),
        ("默认不显示扫硬伤", 'class="action-block delivery-block" hidden aria-hidden="true"' in index and 'id="quickAuditButton" hidden aria-hidden="true"' in index, "硬伤快检不再占据用户主流程。"),
        ("导出入口保留", 'id="exportMd"' in index and 'exportDraft("md")' in app, "导出入口至少要保留在顶部。"),
        ("风格调用证明可用", "/api/style-proof" in app and "renderStyleProof" in app and "runStyleProof" in app, "系统必须能证明风格库被调用，而不是只说用了。"),
        ("风格证明默认折叠", 'id="proofFold"' in index and 'id="proofSummary"' in index, "证明报告不能默认铺满右侧，只显示一句摘要。"),
        ("Lite 隐藏顶部 tab", ".lite-mode .panel-tabs" in styles and "display: none" in styles, "默认入口应是少数高频动作，不再显示一个无信息量的改句 tab。"),
        ("右栏不显示选句工具", "selectionBlockNode.hidden = true" in app and ".selection-block[hidden]" in styles, "右侧只显示候选，不显示改句/讨厌/喜欢按钮堆。"),
        ("右栏只在有候选时出现", 'class="side" hidden' in index and 'body[data-result-panel="visible"] .workspace' in styles and "sideNode.hidden = !hasCandidateSurface" in app, "默认是一栏正文；改句/补段有候选时才打开右侧结果栏。"),
        ("默认可记录讨厌句", 'data-ban' in index, "用户讨厌句要能一键进风格库。"),
        ("默认可记录喜欢句", 'data-like' in index, "用户认可句要能一键进风格库。"),
        ("默认不要求手动检查", 'id="quickAuditAction" class="quick-action primary-action">扫硬伤</button>' in index and "deliveryState !== \"review\"" not in app, "默认导出不再被手动检查按钮阻断。"),
        ("默认不显示高级区", 'class="fold-card advanced-writing-tools"' not in index and "高级生成" not in index and 'id="deepReviewAction"' not in index, "高级能力不再作为用户默认工作流展示。"),
        ("深度终审保留后台能力", "runTasteAuditWithProof" in app and "/api/taste-audit" in app, "深度终审仍可由 Codex/脚本触发，但不放进默认界面。"),
        ("全文生成保留后台能力", 'data-panel="draft"' in index and "api(\"/api/full-draft-job\"" in app, "完整生成仍可作为后台工作流，不抢默认界面。"),
        ("结构拆段保留后台能力", 'data-panel="cowrite"' in index and "buildCowritePlan" in app, "结构拆段作为内部修复路径保留。"),
        ("Codex 交接单可见", 'id="editorialHandoffPreview"' in index and "renderEditorialHandoff" in app, "生成前必须看见 Codex 给 DeepSeek 的选题、材料和结构任务书。"),
        ("生成有等待状态", 'id="generateProgress"' in index and "startGenerateTimer" in app, "长生成必须给进度反馈。"),
        ("生成可取消等待", 'id="cancelGenerate"' in index and "activeGenerateController.abort" in app, "卡住时必须能退出等待。"),
        ("全文生成走后台任务", "/api/full-draft-job" in app and "waitForFullDraftJob" in app, "完整生成太慢，前端必须提交后台任务并轮询。"),
        ("生成后自动终审", 'title: "正在自动终审"' in app and 'label: "生成后自动终审中。"' in app and 'passPrefix: "自动终审通过"' in app, "DeepSeek 生成后应自动进入 Codex 终审，不再要求用户手动找按钮。"),
        ("生成稿来源可见", 'id="generatedProvenance"' in index and "formatGeneratedProvenance" in app, "必须看得出 DeepSeek/Codex 谁参与了。"),
        ("删除旧快改命名", "DS 快改" not in index, "避免让用户以为是固定模板快改。"),
    ]
    return [
        {"name": name, "status": "pass" if ok else "fail", "reason": reason}
        for name, ok, reason in checks
    ]


def product_loop_checks(body: str, document_body: str, style_store: StyleMemoryStore) -> list[dict[str, Any]]:
    text = normalize_space(body)
    doc_text = normalize_space(document_body)
    memory_count = len(style_store.load())
    checks: list[tuple[str, bool, str]] = [
        ("开头先讲失败体验", bool(re.search(r"AI 味|怪|卡住|抓不住重点|不像我会说", text)), "先让观众知道为什么要做工作台。"),
        ("第二步解释原因和主流解法", bool(re.search(r"研究|STORM|PaperDebugger|反馈|改稿|查漏|来源|大纲", text)), "不能直接跳到介绍系统。"),
        ("工作台操作说清楚", bool(re.search(r"划选|改句|讨厌|喜欢|风格库|审稿|导出", text)), "观众要知道前端能做什么。"),
        ("模型分工存在", all(token in text for token in ("DeepSeek", "Codex")), "必须说清主笔、局部改句、审稿编排。"),
        (
            "前后对比存在",
            bool(re.search(r"原句|改后|对照|不用这个流程|用了以后|工作台怎么处理", text)),
            "要证明不用和用了有什么差。",
        ),
        ("当前文档已同步", doc_text[:120] in text or text[:120] in doc_text, "前端文档要显示当前稿。"),
        ("风格库有记录", memory_count > 0, "偏好必须可持久化。"),
    ]
    return [
        {"name": name, "status": "pass" if ok else "fail", "reason": reason}
        for name, ok, reason in checks
    ]


def generic_document_checks(body: str, document_body: str, style_store: StyleMemoryStore) -> list[dict[str, Any]]:
    text = normalize_space(body)
    doc_text = normalize_space(document_body)
    memory_count = len(style_store.load())
    checks: list[tuple[str, bool, str]] = [
        ("当前文档已同步", doc_text[:120] in text or text[:120] in doc_text, "前端文档要显示当前稿。"),
        ("风格库有记录", memory_count > 0, "偏好必须可持久化。"),
        ("正文足够成稿", len(text) > 800 and text.count("。") >= 10, "普通文章至少要有完整展开，不应只是片段。"),
    ]
    return [
        {"name": name, "status": "pass" if ok else "fail", "reason": reason}
        for name, ok, reason in checks
    ]


def dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        text = normalize_space(value)
        if not text or text in seen:
            continue
        seen.add(text)
        items.append(text)
    return items


def latest_existing_artifact(*paths: Path) -> Path | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def summarize_live_generation(live_generation: dict[str, Any]) -> dict[str, Any]:
    if not live_generation:
        return {
            "status": "MISSING",
            "label": "MISSING",
            "ok": False,
            "qualityBlocked": False,
            "reasons": ["还没有最新的新主题真实生成记录。"],
            "generatedAt": "unknown",
            "documentId": "",
            "total": 0,
            "failed": 0,
        }

    summary = {
        "generatedAt": live_generation.get("generatedAt", "unknown"),
        "documentId": live_generation.get("documentId", ""),
        "total": int(live_generation.get("total", 0) or 0),
        "failed": int(live_generation.get("failed", 0) or 0),
    }
    if live_generation.get("ok"):
        return {
            **summary,
            "status": "PASS",
            "label": "PASS",
            "ok": True,
            "qualityBlocked": False,
            "reasons": [],
        }

    raw_errors: list[str] = []
    quality_reasons: list[str] = []
    direct_quality_gate = live_generation.get("qualityGate") or {}
    if direct_quality_gate and str(direct_quality_gate.get("status")) != "allow":
        quality_reasons.extend([str(item) for item in direct_quality_gate.get("reasons") or []])

    for item in live_generation.get("results") or []:
        error = normalize_space(item.get("error"))
        if not error:
            continue
        raw_errors.append(error)
        if error.startswith("qualityGate=block:"):
            tail = error.split(":", 1)[1].strip()
            quality_reasons.extend(part.strip() for part in tail.split(" / ") if part.strip())

    quality_reasons = dedupe_keep_order(quality_reasons)
    raw_errors = dedupe_keep_order(raw_errors)
    if quality_reasons:
        return {
            **summary,
            "status": "QUALITY_BLOCK",
            "label": "QUALITY BLOCK",
            "ok": False,
            "qualityBlocked": True,
            "reasons": quality_reasons,
            "errors": raw_errors[:3],
        }
    return {
        **summary,
        "status": "BLOCK",
        "label": "BLOCK",
        "ok": False,
        "qualityBlocked": False,
        "reasons": raw_errors[:3] or ["新主题真实生成链路未通过。"],
    }


def is_workbench_intro(title: str, body: str) -> bool:
    text = f"{title}\n{body}"
    return bool(re.search(r"写作工作台|AI 写作最好的方式|DeepSeek.*Codex|划选改句|风格库", text, re.S))


def build_report(result: dict[str, Any]) -> str:
    advanced = result.get("advancedGeneration") or {}
    lines = [
        "# 写作工作台产品验收报告",
        "",
        f"- 时间：{result['generatedAt']}",
        f"- 结论：{result['statusLabel']}",
        f"- 核心工作台：{result['coreStatus']}",
        f"- 新主题真实生成：{advanced.get('label', 'MISSING')}",
        f"- 覆盖度：{result['coverageStatus']}",
        f"- 当前稿得分：{result['current']['score']}",
        f"- 裸写基线得分：{result['baseline']['score']}",
        f"- 当前稿硬禁句：{result['current']['hardBanCount']}",
        f"- 裸写基线硬禁句：{result['baseline']['hardBanCount']}",
        "",
        "## UI 简洁性",
    ]
    for item in result["uiChecks"]:
        lines.append(f"- {item['status'].upper()} {item['name']}：{item['reason']}")
    lines.extend(["", "## 写作闭环"])
    for item in result["loopChecks"]:
        lines.append(f"- {item['status'].upper()} {item['name']}：{item['reason']}")
    lines.extend(["", "## 质量门槛"])
    for gate in result["gates"]:
        lines.append(f"- {gate['status'].upper()} {gate['script']}：{gate['summary']}")
    if result["current"]["qualityReasons"]:
        lines.extend(["", "## 当前稿阻塞原因"])
        lines.extend(f"- {reason}" for reason in result["current"]["qualityReasons"])
    browser_smoke = result.get("browserSmoke") or {}
    if browser_smoke:
        lines.extend(["", "## 浏览器点击验收"])
        lines.append(f"- 状态：{'PASS' if browser_smoke.get('ok') else 'BLOCK'}")
        lines.append(f"- 时间：{browser_smoke.get('generatedAt', 'unknown')}")
        lines.append(f"- 步骤：{browser_smoke.get('total', 0)}，失败：{browser_smoke.get('failed', 0)}")
    live_generation = advanced
    if live_generation:
        lines.extend(["", "## 新主题真实生成验收"])
        lines.append(f"- 状态：{live_generation.get('label', 'MISSING')}")
        lines.append(f"- 时间：{live_generation.get('generatedAt', 'unknown')}")
        lines.append(f"- 文档：{live_generation.get('documentId', '')}")
        lines.append(f"- 步骤：{live_generation.get('total', 0)}，失败：{live_generation.get('failed', 0)}")
        if live_generation.get("reasons"):
            lines.append("- 原因：")
            lines.extend(f"  - {reason}" for reason in live_generation.get("reasons", []))
    if result["residualRisks"]:
        lines.extend(["", "## 剩余风险"])
        lines.extend(f"- {risk}" for risk in result["residualRisks"])
    lines.append("")
    return "\n".join(lines)


def audit_workbench(draft_path: Path = DEFAULT_DRAFT, document_path: Path = DEFAULT_DOCUMENT) -> dict[str, Any]:
    store = product_audit_style_store()
    draft_path = resolve_default_artifact(draft_path, FIXTURE_DRAFT)
    document_path = resolve_default_artifact(document_path, FIXTURE_DOCUMENT)
    title, body = split_markdown(draft_path)
    document_title, document_body = document_text(document_path)
    index = (ROOT / "inline_editor_v2" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "inline_editor_v2" / "app.js").read_text(encoding="utf-8")
    workbench_intro = is_workbench_intro(title, body)
    current = evaluate_text(
        title,
        body,
        store,
        brief=BRIEF
        if workbench_intro
        else f"写一篇中文个人 IP 口播/文章稿，题目是：{title}。要求事实清楚、判断具体、避免硬禁句和空泛 AI 味。",
        material_card=MATERIAL_CARD
        if workbench_intro
        else {
            "claim": title,
            "sources": "当前稿件自带来源；以 source_pack 和正文事实为准。",
            "noInvent": "用户量,收入,个人经历,未给出的官方表述",
        },
    )
    baseline = evaluate_text(TITLE, BASELINE_BODY, store)
    gates = [
        run_gate("opening_line_taste_gate.py", draft_path),
        run_gate("oral_script_gate.py", draft_path),
        run_gate("insight_gate.py", draft_path),
    ]
    if workbench_intro:
        gates.append(run_gate("writing_lift_gate.py", draft_path))
    else:
        gates.append(run_gate("topic_viability_gate.py", draft_path))
    ui = ui_checks(index, app)
    loop = product_loop_checks(body, document_body, store) if workbench_intro else generic_document_checks(body, document_body, store)
    browser_smoke: dict[str, Any] = {}
    browser_smoke_path = latest_existing_artifact(FORMAL_READONLY_SMOKE_LATEST, BROWSER_SMOKE_LATEST) or (
        FIXTURE_BROWSER_SMOKE if FIXTURE_BROWSER_SMOKE.exists() else None
    )
    if browser_smoke_path:
        try:
            browser_smoke = json.loads(browser_smoke_path.read_text(encoding="utf-8"))
        except Exception:
            browser_smoke = {"ok": False, "failed": 1, "total": 0, "generatedAt": "unreadable"}
    live_generation: dict[str, Any] = {}
    live_generation_path = LIVE_GENERATION_LATEST if LIVE_GENERATION_LATEST.exists() else FIXTURE_LIVE_GENERATION
    if live_generation_path.exists():
        try:
            live_generation = json.loads(live_generation_path.read_text(encoding="utf-8"))
        except Exception:
            live_generation = {"ok": False, "failed": 1, "total": 0, "generatedAt": "unreadable"}
    advanced_generation = summarize_live_generation(live_generation)
    residual_risks = ["自动门槛只能证明功能闭环和明显 AI 味拦截，最终文章品味仍需要人工主观复核。"]
    if advanced_generation["status"] == "MISSING":
        residual_risks.insert(0, "还没有最新的新主题真实生成验收记录，所以高级生成链路尚未重新证明。")
    elif advanced_generation["status"] == "QUALITY_BLOCK":
        residual_risks.insert(0, "高级生成链路已经能真实跑通，但新主题仍会被质量门槛拦下，说明一键成稿还不稳定。")
    elif advanced_generation["status"] == "BLOCK":
        residual_risks.insert(0, "高级生成链路最近一次 smoke 仍未通过，当前只能证明核心编辑工作台稳定可用。")

    core_ok = (
        all(item["status"] == "pass" for item in ui)
        and all(item["status"] == "pass" for item in loop)
        and all(item["status"] == "pass" for item in gates)
        and current["hardBanCount"] == 0
        and current["qualityGate"] == "allow"
        and baseline["score"] < current["score"]
        and baseline["hardBanCount"] > current["hardBanCount"]
        and (not browser_smoke or bool(browser_smoke.get("ok")))
    )
    status = "PASS" if core_ok else "BLOCK"
    coverage_status = "FULL" if advanced_generation["status"] == "PASS" else "PARTIAL"
    if core_ok and advanced_generation["status"] == "PASS":
        status_label = "PASS"
    elif core_ok:
        status_label = f"PASS（核心可用，{advanced_generation['label']}）"
    else:
        status_label = "BLOCK"
    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "statusLabel": status_label,
        "coreStatus": "PASS" if core_ok else "BLOCK",
        "coverageStatus": coverage_status,
        "draftPath": str(draft_path.relative_to(ROOT)),
        "documentPath": str(document_path.relative_to(ROOT)),
        "documentTitle": document_title,
        "articleKind": "workbench_intro" if workbench_intro else "generic_article",
        "current": current,
        "baseline": baseline,
        "uiChecks": ui,
        "loopChecks": loop,
        "gates": gates,
        "browserSmoke": browser_smoke,
        "liveGeneration": live_generation,
        "advancedGeneration": advanced_generation,
        "residualRisks": residual_risks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the local writing workbench product loop.")
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--document", type=Path, default=DEFAULT_DOCUMENT)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--write-report", action="store_true", help="Write a Markdown report into .cache/writing.")
    args = parser.parse_args()

    result = audit_workbench(args.draft, args.document)
    if args.write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / f"workbench_product_audit_{now_slug()}.md"
        report_path.write_text(build_report(result), encoding="utf-8")
        result["reportPath"] = str(report_path.relative_to(ROOT))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(build_report(result))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
