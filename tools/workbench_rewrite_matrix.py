#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / ".cache" / "writing" / "workbench_rewrite_matrix_latest.json"
DEFAULT_LIVE_SMALL_REPORT = ROOT / ".cache" / "writing" / "workbench_rewrite_live_small_latest.json"


EDITOR_INSTRUCTION_RE = re.compile(
    r"这句还缺|把抽象判断|避免像孤立金句|先回答一个具体问题|先移除提示语|先把人、动作和后果|"
    r"先让这句话接住|接回上下文|给口播|(?:^|\s)候选\s*\d*[:：]?|\bvariant(?:s)?\b|"
    r"\brewrite\b|concretize|oralize|source-ground|接受|记住改法",
    re.I,
)


def request_json(base: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None
    method = "GET"
    headers = {"content-type": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body[:800]}") from exc


def variant_texts(response: dict[str, Any]) -> list[str]:
    return [str(item.get("text", "")).strip() for item in response.get("variants", []) if str(item.get("text", "")).strip()]


def candidate_similarity(left: str, right: str) -> float:
    def compact(value: str) -> str:
        return re.sub(r"[^\w\u4e00-\u9fff]+", "", value)

    a = compact(left)
    b = compact(right)
    if not a or not b:
        return 0.0
    counts: dict[str, int] = {}
    for char in a:
        counts[char] = counts.get(char, 0) + 1
    overlap = 0
    for char in b:
        count = counts.get(char, 0)
        if count > 0:
            overlap += 1
            counts[char] = count - 1
    return overlap / max(len(a), len(b))


def assert_candidate_quality(
    *,
    case_name: str,
    selected: str,
    texts: list[str],
    min_count: int = 3,
    banned: tuple[str, ...] = (),
    required_any: tuple[str, ...] = (),
) -> None:
    if len(texts) < min_count:
        raise AssertionError(f"{case_name}: expected >= {min_count} candidates, got {len(texts)}: {texts}")
    if len(set(texts)) != len(texts):
        raise AssertionError(f"{case_name}: duplicate candidates: {texts}")
    selected_compact = re.sub(r"[^\w\u4e00-\u9fff]+", "", selected)
    for index, text in enumerate(texts):
        if text == selected:
            raise AssertionError(f"{case_name}: unchanged candidate: {text}")
        if selected and selected in text and len(text) <= len(selected) + 18:
            raise AssertionError(f"{case_name}: candidate wraps original without real rewrite: {text}")
        text_compact = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
        if selected_compact and text_compact and text_compact in selected_compact and len(text_compact) < max(24, len(selected_compact) * 0.72):
            raise AssertionError(f"{case_name}: candidate is just a selected-text fragment: {text}")
        if selected_compact and text_compact:
            closeness = candidate_similarity(text, selected)
            if (len(selected_compact) >= 80 and closeness >= 0.86) or (len(selected_compact) >= 35 and closeness >= 0.92) or (
                len(selected_compact) < 35 and closeness >= 0.96
            ):
                raise AssertionError(f"{case_name}: candidate is too close to original selection: {text}")
        for other in texts[:index]:
            if candidate_similarity(text, other) >= 0.82:
                raise AssertionError(f"{case_name}: candidates are too similar: {[other, text]}")
        if EDITOR_INSTRUCTION_RE.search(text):
            raise AssertionError(f"{case_name}: editor instruction leaked as candidate: {text}")
        hits = [phrase for phrase in banned if phrase and phrase in text]
        if hits:
            raise AssertionError(f"{case_name}: banned phrase {hits} in candidate: {text}")
    if required_any and not any(any(marker in text for marker in required_any) for text in texts):
        raise AssertionError(f"{case_name}: none of candidates contains any of {required_any}: {texts}")


def default_cases() -> list[dict[str, Any]]:
    return [
        {
            "name": "research paragraph gets three useful routes",
            "selected": (
                "到今天，比较成熟的解法已经很清楚。Stanford STORM 先检索材料、多视角提问、生成大纲，再进入正文。"
                "PaperDebugger 走的是研究、批判、修订的编辑器内流程。CoAuthor 这类研究把人和模型的写作互动拆开看。"
                "2025 年关于学术写作的综述也反复强调，AI 可以辅助，但责任和解释权还在人这里。"
            ),
            "banned": ("生大纲", "这句还缺", "把抽象判断", "接回上下文"),
            "requiredAny": ("解决同一件事", "日常写稿", "一次生成"),
        },
        {
            "name": "first screen hard-ban frame is replaced",
            "selected": "往往发生在第一屏",
            "contextBefore": "AI 写稿最麻烦的地方，",
            "contextAfter": "。它三十秒交出一篇完整稿。",
            "banned": ("往往", "第一屏", "这句还缺", "放在这里"),
            "requiredAny": ("题目交给模型", "看似完整", "铺好了"),
        },
        {
            "name": "short workbench self-intro becomes polished transition",
            "selected": "我做了个 ai辅助 写作工作台",
            "contextBefore": "Hi，",
            "contextAfter": "虽然说在今天，让 AI 撰写文章、论文或者报告，已经是 AI 应用场景里再基础不过的事情。",
            "banned": ("我做了个 ai辅助 写作工作台", "不是", "而是", "打开它", "标题、段落、总结", "补出读者能看到的对象"),
            "requiredAny": ("后来", "所以", "干脆", "写作工作台", "反复改稿", "顺但空", "全文一直在眼前"),
        },
        {
            "name": "macro AI trend sentence is not synonym-polished",
            "selected": "随着人工智能技术飞速发展，内容创作迎来前所未有的变革。",
            "banned": ("随着", "飞速发展", "前所未有", "重塑", "深刻变化", "机遇与挑战"),
            "requiredAny": ("写 AI 时代来了", "开写前", "文章要往哪走"),
        },
        {
            "name": "jargon sentence becomes plain Chinese",
            "selected": "AI writing workflow 需要通过 style memory 和审稿 gate 才能稳定降低 AI 味。",
            "action": "plain-language",
            "banned": ("workflow", "style memory", "gate", "concretize", "oralize", "source-ground"),
            "requiredAny": ("记住你的喜好", "先定好怎么写", "记不住你到底在说哪件事"),
        },
        {
            "name": "abstract usefulness sentence becomes demoable",
            "selected": "这套东西有没有用，最好看一句话。",
            "contextBefore": "手动改稿的时候，就用检查硬伤。",
            "contextAfter": "直接让模型写，原句很可能长这样。",
            "banned": ("这套东西有没有用", "最好看一句话", "管不管用，一句", "行不行"),
            "requiredAny": ("试一次改句", "拿一句空话", "拦下来"),
        },
        {
            "name": "workbench memory explanation becomes frontend action",
            "selected": "这套工作台改变的是坏句的去向。以前坏句混在全文里，最后靠人硬洗；现在坏句会被划出来、记录下来，变成下一次生成前的门槛。",
            "contextBefore": "这条记录还会影响下一次生成。",
            "contextAfter": "这个差别会慢慢累积。",
            "banned": ("坏句的去向", "硬洗", "门槛", "不合格就别放", "系统价值"),
            "requiredAny": ("选中", "讨厌", "为什么删", "删除理由", "原因", "下次", "下一次"),
        },
        {
            "name": "workbench abstract transition becomes operational",
            "selected": "这个差别会慢慢累积。没用的时候，你每次都在救一篇完整废稿；用了以后，系统先帮你挡掉一批低级问题。",
            "contextBefore": "在工作台里，我不会先整篇重写。我会在正文左侧划选这句，右侧点“记为讨厌”。",
            "contextAfter": "你要做的事情从整篇重写，变成判断这篇稿子还有没有继续改的价值。",
            "banned": ("系统价值", "流程本身", "门槛", "去向", "机制"),
            "requiredAny": ("选中", "改句", "讨厌", "记录", "下次", "下一篇", "正文"),
        },
        {
            "name": "fake reversal frame is replaced with direct claim",
            "selected": "不是模型不够聪明，而是你还没有真正理解写作的本质。",
            "banned": ("不是", "而是", "本质", "不够聪明"),
            "requiredAny": ("先", "判断", "材料", "读者", "写清"),
        },
        {
            "name": "enterprise jargon cluster becomes concrete",
            "selected": "这套系统通过多模型协同，构建内容生产闭环，持续赋能创作者提效。",
            "banned": ("赋能", "闭环", "协同", "提效", "内容生产"),
            "requiredAny": ("Codex", "Kimi", "DeepSeek", "改", "写", "拦", "记"),
        },
        {
            "name": "pseudo intimate slogan becomes specific action",
            "selected": "这个工具会稳稳地接住你的需求，不绕弯，给你最直接的答案。",
            "banned": ("稳稳", "接住", "不绕弯", "最直接", "答案"),
            "requiredAny": ("输入", "选中", "候选", "写", "改", "需求"),
        },
        {
            "name": "report transition becomes spoken bridge",
            "selected": "值得注意的是，AI 写作工具的快速发展正在带来新的机会和挑战。",
            "banned": ("值得注意", "快速发展", "机会和挑战", "带来"),
            "requiredAny": ("问题", "写", "读者", "稿子", "具体"),
        },
        {
            "name": "summary ending avoids generic conclusion",
            "selected": "总而言之，AI 写作已经成为不可忽视的重要趋势。",
            "banned": ("总而言之", "不可忽视", "重要趋势", "已经成为"),
            "requiredAny": ("下次", "写", "判断", "留下", "删"),
        },
        {
            "name": "empty efficiency claim becomes measurable",
            "selected": "这套流程可以显著提升写作效率，减少返工成本。",
            "banned": ("显著提升", "效率", "返工成本"),
            "requiredAny": ("少", "重写", "删", "改", "候选", "记录"),
        },
        {
            "name": "product pain-point language becomes real user moment",
            "selected": "它精准解决了创作者在内容生产过程中的核心痛点。",
            "banned": ("精准", "核心痛点", "内容生产", "创作者"),
            "requiredAny": ("打开", "选中", "一句", "改", "删", "写"),
        },
        {
            "name": "paper-name pileup becomes human explanation",
            "selected": "STORM、PaperDebugger 和 CoAuthor 分别代表了检索增强、批判修订和人机协作三个方向。",
            "banned": ("分别代表", "检索增强", "人机协作", "三个方向"),
            "requiredAny": ("先找材料", "退回去", "接力", "写稿"),
        },
        {
            "name": "model comparison becomes operational split",
            "selected": "Kimi 在中文表达上更自然，DeepSeek 在逻辑推理上更强，Codex 在工程编排上更稳定。",
            "banned": ("更自然", "更强", "更稳定", "表达上", "逻辑推理"),
            "requiredAny": ("Kimi", "DeepSeek", "Codex", "主笔", "改句", "拦稿"),
        },
        {
            "name": "boundary sentence avoids disclaimer tone",
            "selected": "当然，这套系统也不是万能的，它仍然存在一定局限性。",
            "banned": ("当然", "不是万能", "一定局限性", "仍然存在"),
            "requiredAny": ("不能替你", "选题", "材料", "判断", "最后"),
        },
        {
            "name": "essay intro formula becomes direct entry",
            "selected": "本文将从 AI 写作的现状、问题和解决方案三个方面展开分析。",
            "banned": ("本文将", "现状", "问题", "解决方案", "展开分析"),
            "requiredAny": ("先看", "一句", "稿子", "AI", "写"),
        },
        {
            "name": "grand history opening is grounded",
            "selected": "在人类文明发展的历史长河中，技术始终推动着表达方式的变革。",
            "banned": ("历史长河", "文明", "推动", "变革"),
            "requiredAny": ("今天", "写稿", "AI", "一句", "打开"),
        },
        {
            "name": "abstract evaluation sentence becomes concrete criterion",
            "selected": "好的 AI 写作系统应该兼具高质量输出和良好的用户体验。",
            "banned": ("高质量输出", "良好的用户体验", "兼具"),
            "requiredAny": ("能不能", "改", "记住", "候选", "正文"),
        },
        {
            "name": "workflow explanation becomes one visible loop",
            "selected": "通过持续积累风格数据，系统能够逐步形成个性化写作能力。",
            "banned": ("持续积累", "风格数据", "逐步形成", "个性化写作能力"),
            "requiredAny": ("喜欢", "讨厌", "下次", "记", "写"),
        },
    ]


def live_small_cases() -> list[dict[str, Any]]:
    return [
        {
            "name": "live protected reflective closing stays reflective",
            "selected": "写作工具该留下的，可能就是这点稳定感。",
            "expectedEngine": "local-fast",
            "banned": ("流程", "前端", "按钮", "候选", "正文", "系统价值"),
            "requiredAny": ("判断", "写下去", "往下改", "从头推翻", "继续"),
        },
        {
            "name": "live protected self intro stays first person",
            "selected": "我做了个 ai辅助写作工作台",
            "contextBefore": "Hi，",
            "contextAfter": "虽然说在今天，让 AI 撰写文章、论文或者报告，已经是 AI 应用场景里再基础不过的事情。",
            "expectedEngine": "local-fast",
            "banned": ("标题、段落、总结", "补出读者", "系统价值", "打开它"),
            "requiredAny": ("后来", "所以", "干脆", "写作工作台", "反复改稿", "顺但空"),
        },
        {
            "name": "live deepseek usefulness line becomes demo action",
            "selected": "这套东西有没有用，最好看一句话。",
            "contextBefore": "手动改稿的时候，就用检查硬伤。",
            "contextAfter": "直接让模型写，原句很可能长这样。",
            "expectedEngine": "deepseek",
            "banned": ("这套东西有没有用", "最好看一句话", "管不管用", "行不行"),
            "requiredAny": ("试一次改句", "拿一句空话", "拦下来"),
        },
        {
            "name": "live deepseek slogan becomes visible operator action",
            "selected": "这个工具会稳稳地接住你的需求，不绕弯，给你最直接的答案。",
            "expectedEngine": "deepseek",
            "banned": ("稳稳", "接住", "不绕弯", "最直接", "答案"),
            "requiredAny": ("输入", "选中", "候选", "改", "写", "需求"),
        },
        {
            "name": "live deepseek jargon cluster becomes concrete split",
            "selected": "这套系统通过多模型协同，构建内容生产闭环，持续赋能创作者提效。",
            "expectedEngine": "deepseek",
            "banned": ("赋能", "闭环", "协同", "提效", "内容生产"),
            "requiredAny": ("Codex", "Kimi", "DeepSeek", "改", "写", "拦", "记"),
        },
    ]


def cases_for_pack(case_pack: str) -> list[dict[str, Any]]:
    if case_pack == "live-small":
        return live_small_cases()
    return default_cases()


def resolve_report_path(report: Path | None, case_pack: str) -> Path:
    if report is not None:
        return report
    if case_pack == "live-small":
        return DEFAULT_LIVE_SMALL_REPORT
    return DEFAULT_REPORT


def run_case(base: str, case: dict[str, Any], *, requested_engine: str) -> dict[str, Any]:
    timeout_seconds = int(case.get("timeout", 90 if requested_engine == "deepseek" else 20))
    payload = {
        "documentId": "rewrite_matrix_temp",
        "engine": requested_engine,
        "action": case.get("action", "rewrite"),
        "selectedText": case["selected"],
        "contextBefore": case.get("contextBefore", ""),
        "contextAfter": case.get("contextAfter", ""),
        "documentText": " ".join([case.get("contextBefore", ""), case["selected"], case.get("contextAfter", "")]),
    }
    response = request_json(base, "/api/rewrite-selection", payload, timeout=timeout_seconds)
    route = response.get("route") or {}
    if route.get("lane") != "selected-rewrite" or route.get("weight") != "light":
        raise AssertionError(f"{case['name']}: rewrite route must stay light selected-rewrite, got {route}")
    if route.get("usesWeb") or route.get("usesFullSop"):
        raise AssertionError(f"{case['name']}: selected rewrite must not use web/full SOP, got {route}")
    expected_engine = case.get("expectedEngine")
    if expected_engine and response.get("engine") != expected_engine:
        raise AssertionError(
            f"{case['name']}: expected engine {expected_engine}, got {response.get('engine')}"
        )
    texts = variant_texts(response)
    assert_candidate_quality(
        case_name=case["name"],
        selected=case["selected"],
        texts=texts,
        min_count=case.get("minCount", 3),
        banned=tuple(case.get("banned", ())),
        required_any=tuple(case.get("requiredAny", ())),
    )
    return {
        "engine": response.get("engine"),
        "requestedEngine": requested_engine,
        "route": route,
        "candidateCount": len(texts),
        "texts": texts,
    }


def run(base: str, report_path: Path, *, requested_engine: str, case_pack: str) -> dict[str, Any]:
    cases = cases_for_pack(case_pack)
    steps: list[dict[str, Any]] = []

    def step(name: str, fn):
        started = time.time()
        try:
            value = fn()
            item = {"name": name, "ok": True, "ms": round((time.time() - started) * 1000), "value": value}
        except Exception as exc:  # noqa: BLE001
            item = {"name": name, "ok": False, "ms": round((time.time() - started) * 1000), "error": str(exc)}
        steps.append(item)
        print(json.dumps(item, ensure_ascii=False))
        return item

    step("health", lambda: request_json(base, "/api/health", timeout=10))
    for case in cases:
        step(case["name"], lambda current=case: run_case(base, current, requested_engine=requested_engine))

    failed = [item for item in steps if not item["ok"]]
    summary = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": not failed,
        "base": base,
        "requestedEngine": requested_engine,
        "casePack": case_pack,
        "total": len(steps),
        "failed": len(failed),
        "steps": steps,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast rewrite-candidate quality matrix for the writing workbench.")
    parser.add_argument("--base", default="http://127.0.0.1:8766")
    parser.add_argument("--engine", choices=("heuristic", "deepseek", "codex"), default="heuristic")
    parser.add_argument("--case-pack", choices=("default", "live-small"), default="default")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    report_path = resolve_report_path(args.report, args.case_pack)
    summary = run(
        args.base.rstrip("/"),
        report_path,
        requested_engine=args.engine,
        case_pack=args.case_pack,
    )
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
