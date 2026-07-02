#!/usr/bin/env python3
"""Local style-memory store for inline rewriting workflows.

The store is deliberately small and local-first. It persists user feedback such
as approved lines, banned lines, rewrite pairs, and style rules as JSONL records
that can be retrieved for prompt context or future UI work.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / ".cache" / "writing" / "style_memory.jsonl"
DEFAULT_DELETED_STORE = ROOT / ".cache" / "writing" / "style_memory_deleted.jsonl"

KINDS = {"approved_line", "banned_line", "rewrite_pair", "rule"}
STRENGTHS = {"hard", "soft", "example"}
STATUSES = {"active", "deleted"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def normalize_kind(kind: str) -> str:
    aliases = {
        "approved": "approved_line",
        "good": "approved_line",
        "like": "approved_line",
        "banned": "banned_line",
        "bad": "banned_line",
        "dislike": "banned_line",
        "pair": "rewrite_pair",
        "rewrite": "rewrite_pair",
    }
    normalized = aliases.get(kind.strip(), kind.strip())
    if normalized not in KINDS:
        raise ValueError(f"unsupported kind: {kind}; expected one of {sorted(KINDS)}")
    return normalized


def normalize_strength(strength: str) -> str:
    normalized = strength.strip() or "soft"
    if normalized not in STRENGTHS:
        raise ValueError(f"unsupported strength: {strength}; expected one of {sorted(STRENGTHS)}")
    return normalized


def parse_tags(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        parts = value
    else:
        parts = re.split(r"[,，]", value)
    result: list[str] = []
    seen: set[str] = set()
    for part in parts:
        tag = str(part).strip()
        if tag and tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def memory_tag_labels(tags: list[str]) -> list[str]:
    labels: list[str] = []
    for tag in tags:
        normalized = normalize_space_for_memory(str(tag))
        if not normalized:
            continue
        label = normalized.split(":", 1)[1] if ":" in normalized else normalized
        label = normalize_space_for_memory(label)
        if label and label not in labels:
            labels.append(label)
    return labels


def entry_id(*parts: str) -> str:
    digest = hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"mem_{digest}"


def normalize_space_for_memory(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def candidate_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_space_for_memory(left), normalize_space_for_memory(right)).ratio()


def text_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+-]{1,30}", text.lower()):
        terms.add(token)
    for block in re.findall(r"[\u4e00-\u9fff]{2,60}", text):
        if len(block) <= 8:
            terms.add(block)
        for size in (2, 3, 4):
            for index in range(0, max(len(block) - size + 1, 0)):
                terms.add(block[index : index + size])
    return terms


STRUCTURE_PATTERNS: list[tuple[str, str]] = [
    ("binary-reversal", r"不是|而是|而不是|不只是|更是"),
    ("two-step-verdict", r"前一句|后一句|第一句|第二句|真的|没有那么真"),
    ("cheap-opening", r"这个题目|第一眼|看上去|有点大|听起来"),
    ("director-note", r"画面|镜头|B-roll|字幕|视频开场"),
    ("report-slop", r"随着|当今|近年来|深刻|重塑|赋能|值得|底层逻辑|广泛关注"),
    ("ai-workflow", r"工作台|Kimi|DeepSeek|Codex|退稿|风格库|主笔|审计"),
    ("source-research", r"研究|资料|证据|source|STORM|报告|引用|检索"),
    ("opening", r"开头|标题|入口|第一段|第一句"),
    ("ending", r"结尾|收尾|最后|结束"),
]


def structure_signals(text: str) -> set[str]:
    return {label for label, pattern in STRUCTURE_PATTERNS if re.search(pattern, text, flags=re.I)}


PROBLEM_CUE_PATTERNS: list[tuple[str, str]] = [
    ("macro-subject-soft-verb", r"(当前|当下|今天|如今)?[^。！？!?；;\n]{0,16}(行业|时代|内容生产|AI|技术|创作者|用户|系统).{0,24}(快速发展|正在改变|进入新阶段|提升自身竞争力|拥抱变化|提效|赋能|降本增效)"),
    ("false-agency", r"(数据|市场|时代|系统|工具|模型|平台|行业|争议|讨论|风向|文本|句子)[^。！？!?；;\n]{0,12}(告诉|要求|决定|奖励|惩罚|理解|记住|接住|保护)"),
    ("pseudo-oral", r"(稳稳[地的]?接住|不绕弯|最直接|我懂你|懂你|接住你|给你答案|不废话)"),
    ("ai-english-lexicon", r"\b(delve|tapestry|landscape|pivotal|robust|comprehensive|cutting-edge|leverage|underscore|seamless|vibrant)\b"),
    ("generic-recommendation", r"(值得(?:关注|一看|一读|探索|思考|警惕|讨论)|worth (?:reading|exploring|watching|checking|paying attention))"),
    ("em-dash-punch", r"(—|--)"),
    ("source-pileup", r"(STORM|PaperDebugger|CoAuthor|LongWriter|Antislop|综述|论文|研究|工具)"),
    ("binary-reversal", r"(不是.+而是|真正.+不是|你要问的不是)"),
    ("blank-judgment", r"(这套东西|这个工作台|这个系统|这件事|这个问题|这种麻烦|后面这种|前面这种|发现问题|最好看一句话|值不值得|有没有用|更深)"),
    ("cheap-suspense-hook", r"(反直觉的事|反直觉的一点|一个反直觉的)"),
    ("half-sentence-note", r"(语气在这里变重|语气变重|声音变重|话说得很重|往往发生在第一屏)"),
]


def problem_cues(text: str) -> set[str]:
    return {label for label, pattern in PROBLEM_CUE_PATTERNS if re.search(pattern, text, flags=re.I)}


REASON_CLASS_LABELS: dict[str, str] = {
    "binary_reversal": "二段反转",
    "negative_runway": "先否后正",
    "light_heavy_contrast": "轻重对照",
    "meta_opening": "解释题目",
    "cheap_suspense_hook": "空悬念起手",
    "macro_subject_soft_verb": "大主语软动词",
    "false_agency": "假主语假动作",
    "pseudo_oral_comfort": "伪口语安慰句",
    "ai_english_lexicon": "AI英语词表",
    "generic_recommendation": "泛建议",
    "em_dash_template": "横杠模板腔",
    "source_pileup": "资料罗列",
    "report_tone": "报告腔",
    "too_abstract": "抽象词过多",
    "fake_depth": "假深刻",
    "engineering_briefing": "工程腔",
    "half_sentence_note": "半句批注",
    "blank_judgment": "空判断",
    "looks_complete_but_hollow": "看着完整但改不动",
    "essay_formula": "作文开头",
    "boundary_disclaimer": "免责声明",
    "model_role_comparison": "模型分工空话",
    "abstract_evaluation": "抽象评价",
    "empty_efficiency_claim": "效率空话",
    "actor_action_consequence": "对象动作后果完整",
    "actor_action_clear": "对象动作明确",
    "spoken_action_sentence": "口播短句有动作",
    "compact_judgment": "短句收紧",
    "plain_language": "说人话",
    "reframe": "换框架",
    "concretize": "补对象",
    "action": "补动作",
    "ground_context": "接前后文",
    "oralize": "更顺口",
    "compress": "压缩",
    "split": "拆短句",
}


def _has_labels(labels: set[str], *needles: str) -> bool:
    return set(needles) <= labels


def canonical_reason_classes(
    kind: str,
    tags: list[str],
    *,
    source_text: str = "",
    replacement_text: str = "",
    reason: str = "",
) -> list[str]:
    labels = set(memory_tag_labels(tags))
    classes: list[str] = []

    def add(key: str) -> None:
        if key in REASON_CLASS_LABELS and key not in classes:
            classes.append(key)

    if kind == "banned_line":
        if _has_labels(labels, "先否后正") or "连否两次" in labels:
            add("negative_runway")
        if _has_labels(labels, "二段反转") or "不是X而是Y" in labels:
            add("binary_reversal")
        if _has_labels(labels, "假深刻"):
            add("fake_depth")
        if _has_labels(labels, "大主语软动词", "缺对象动作") or "大主语软动词" in labels:
            add("macro_subject_soft_verb")
        if _has_labels(labels, "假主语假动作", "没写谁在做") or "假主语假动作" in labels:
            add("false_agency")
        if _has_labels(labels, "伪口语", "缺真实场景") or "伪口语" in labels:
            add("pseudo_oral_comfort")
        if _has_labels(labels, "AI英语词表") or "翻译腔" in labels:
            add("ai_english_lexicon")
        if _has_labels(labels, "泛建议") or _has_labels(labels, "没给理由"):
            add("generic_recommendation")
        if _has_labels(labels, "横杠转折") or _has_labels(labels, "语气太像模板"):
            add("em_dash_template")
        if _has_labels(labels, "资料罗列", "缺写作动作") or "资料罗列" in labels:
            add("source_pileup")
        if _has_labels(labels, "报告腔"):
            add("report_tone")
        if _has_labels(labels, "抽象词过多"):
            add("too_abstract")
        if _has_labels(labels, "工程腔", "不像正文") or "工程腔" in labels:
            add("engineering_briefing")
        if _has_labels(labels, "轻重对照") or _has_labels(labels, "分量对照"):
            add("light_heavy_contrast")
        if "解释题目" in labels or "元话语" in labels:
            add("meta_opening")
        if _has_labels(labels, "空悬念", "卖关子") or "空悬念" in labels:
            add("cheap_suspense_hook")
        if _has_labels(labels, "像半句") or _has_labels(labels, "没落正文"):
            add("half_sentence_note")
        if _has_labels(labels, "空泛判断", "没落地") or "空泛判断" in labels:
            add("blank_judgment")
        if _has_labels(labels, "外观看似完整", "改不动") or "改不动" in labels:
            add("looks_complete_but_hollow")
        if _has_labels(labels, "作文开头", "缺失败现场") or "作文开头" in labels:
            add("essay_formula")
        if _has_labels(labels, "免责声明", "缺具体边界") or "免责声明" in labels:
            add("boundary_disclaimer")
        if _has_labels(labels, "模型分工空话", "缺操作现场") or "模型分工空话" in labels:
            add("model_role_comparison")
        if _has_labels(labels, "抽象评价", "缺可观察标准") or "抽象评价" in labels:
            add("abstract_evaluation")
        if _has_labels(labels, "效率空话", "缺具体减少了什么") or "效率空话" in labels:
            add("empty_efficiency_claim")
    elif kind == "approved_line":
        if _has_labels(labels, "对象明确", "动作明确", "后果可感"):
            add("actor_action_consequence")
        elif _has_labels(labels, "对象明确", "动作明确"):
            add("actor_action_clear")
        if _has_labels(labels, "动作明确", "口播顺"):
            add("spoken_action_sentence")
        if _has_labels(labels, "句子收紧") or normalize_space_for_memory(reason).startswith("这句好用"):
            add("compact_judgment")
    elif kind == "rewrite_pair":
        if _has_labels(labels, "去术语") or re.search(r"\bworkflow|style memory|gate|prompt|context|brief\b", source_text, re.I):
            add("plain_language")
        if _has_labels(labels, "换框架"):
            add("reframe")
        if _has_labels(labels, "补对象"):
            add("concretize")
        if _has_labels(labels, "补动作"):
            add("action")
        if _has_labels(labels, "接前后文") or _has_labels(labels, "补材料"):
            add("ground_context")
        if _has_labels(labels, "口播顺") or _has_labels(labels, "更像口播"):
            add("oralize")
        if _has_labels(labels, "压缩") or _has_labels(labels, "句子收紧"):
            add("compress")
        if _has_labels(labels, "拆短句"):
            add("split")
        if not classes and candidate_similarity(source_text, replacement_text) < 0.72:
            add("reframe")
    return classes


def canonical_reason_labels(classes: list[str]) -> list[str]:
    labels: list[str] = []
    for key in classes:
        label = REASON_CLASS_LABELS.get(normalize_space_for_memory(str(key)), "")
        if label and label not in labels:
            labels.append(label)
    return labels


def query_reason_classes(query: str) -> set[str]:
    normalized = normalize_space_for_memory(query)
    classes: set[str] = set()
    cues = problem_cues(normalized)
    signals = structure_signals(normalized)

    if "macro-subject-soft-verb" in cues:
        classes.add("macro_subject_soft_verb")
    if "false-agency" in cues:
        classes.add("false_agency")
    if "pseudo-oral" in cues:
        classes.add("pseudo_oral_comfort")
    if "ai-english-lexicon" in cues:
        classes.add("ai_english_lexicon")
    if "generic-recommendation" in cues:
        classes.add("generic_recommendation")
    if "em-dash-punch" in cues:
        classes.add("em_dash_template")
    if "source-pileup" in cues:
        classes.add("source_pileup")
    if "binary-reversal" in cues or "binary-reversal" in signals:
        classes.add("binary_reversal")
    if "blank-judgment" in cues:
        classes.add("blank_judgment")
    if "cheap-suspense-hook" in cues:
        classes.add("cheap_suspense_hook")
    if "half-sentence-note" in cues:
        classes.add("half_sentence_note")
    if "cheap-opening" in cues:
        classes.add("meta_opening")
    if "report-slop" in signals:
        classes.add("report_tone")
    if re.search(r"(先否后正|连否两次|先否两次)", normalized):
        classes.add("negative_runway")
    if re.search(r"(很轻|不重).{0,24}(背后|其实).{0,24}(很重|更重|更复杂)", normalized):
        classes.add("light_heavy_contrast")
    if re.search(r"(先说结论|根因|闭环|对齐一下|坐实)", normalized):
        classes.add("engineering_briefing")
    if re.search(r"(workflow|style memory|gate|prompt|context|brief|术语|工作流)", normalized, re.I):
        classes.add("plain_language")
    if re.search(r"(本文将|展开分析|历史长河|文明发展|表达方式的变革|作文开头)", normalized):
        classes.add("essay_formula")
    if re.search(r"(不是万能|不能替你|仍然存在局限|局限性|免责声明)", normalized):
        classes.add("boundary_disclaimer")
    if re.search(r"(Kimi.{0,40}DeepSeek.{0,40}Codex|中文表达上更自然|逻辑推理上更强|工程编排上更稳定|模型分工空话)", normalized):
        classes.add("model_role_comparison")
    if re.search(r"(高质量输出|良好的用户体验|兼具|持续积累|个性化写作能力|抽象评价|可观察标准)", normalized):
        classes.add("abstract_evaluation")
    if re.search(r"(显著提升|提升.{0,8}效率|减少.{0,8}返工|降低.{0,8}成本|效率空话)", normalized):
        classes.add("empty_efficiency_claim")
    if re.search(r"(换框架|换说法|别沿用原句骨架)", normalized):
        classes.add("reframe")
    if re.search(r"(补对象|谁在做|对象)", normalized):
        classes.add("concretize")
    if re.search(r"(补动作|下一步|做了什么|动作)", normalized):
        classes.add("action")
    if re.search(r"(接前后文|接上下文|补材料|前后文|上下文)", normalized):
        classes.add("ground_context")
    if re.search(r"(更像口播|口语化|更顺口|念出来)", normalized):
        classes.add("oralize")
    if re.search(r"(压缩|更短|收紧)", normalized):
        classes.add("compress")
    if re.search(r"(拆短句|短句|拆成两句)", normalized):
        classes.add("split")
    return classes


def meta_search_blob(meta: dict[str, Any] | None) -> str:
    if not isinstance(meta, dict) or not meta:
        return ""
    parts: list[str] = []
    for key in ("variantMove", "variantLabel", "sourcePrompt", "derivedRule", "feedbackClass", "reasonSummary"):
        value = normalize_space_for_memory(str(meta.get(key, "")))
        if value:
            parts.append(value)
    for key in ("principles", "structureSignals", "reasonClasses", "reasonLabels"):
        value = meta.get(key)
        if isinstance(value, list):
            parts.extend(normalize_space_for_memory(str(item)) for item in value if normalize_space_for_memory(str(item)))
    problem_profile = meta.get("problemProfile")
    if isinstance(problem_profile, dict):
        for key in ("keys", "labels", "directives", "hints", "tags"):
            value = problem_profile.get(key)
            if isinstance(value, list):
                parts.extend(normalize_space_for_memory(str(item)) for item in value if normalize_space_for_memory(str(item)))
        reason = normalize_space_for_memory(str(problem_profile.get("reason", "")))
        if reason:
            parts.append(reason)
    audit_issue = meta.get("auditIssue")
    if isinstance(audit_issue, dict):
        for key in ("category", "kind", "reason"):
            value = normalize_space_for_memory(str(audit_issue.get(key, "")))
            if value:
                parts.append(value)
    return "\n".join(parts)


@dataclass
class StyleMemoryEntry:
    id: str
    kind: str
    source_text: str
    replacement_text: str = ""
    reason: str = ""
    tags: list[str] = field(default_factory=list)
    strength: str = "soft"
    scope: str = "personal-ip"
    origin: str = "manual"
    status: str = "active"
    usage_count: int = 0
    last_used_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    deleted_at: str = ""

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "StyleMemoryEntry":
        data = dict(record)
        data["kind"] = normalize_kind(str(data.get("kind", "")))
        data["strength"] = normalize_strength(str(data.get("strength", "soft")))
        data["tags"] = parse_tags(data.get("tags"))
        data.setdefault("replacement_text", "")
        data.setdefault("reason", "")
        data.setdefault("scope", "personal-ip")
        data.setdefault("origin", "manual")
        data.setdefault("status", "active")
        data.setdefault("usage_count", 0)
        data.setdefault("last_used_at", "")
        meta = data.get("meta")
        data["meta"] = dict(meta) if isinstance(meta, dict) else {}
        data.setdefault("created_at", now_iso())
        data.setdefault("updated_at", data["created_at"])
        data.setdefault("deleted_at", "")
        if data["status"] not in STATUSES:
            data["status"] = "active"
        return cls(**data)

    def to_record(self) -> dict[str, Any]:
        return asdict(self)

    def score(self, query: str) -> int:
        haystack = "\n".join([
            self.source_text,
            self.replacement_text,
            self.reason,
            " ".join(self.tags),
            meta_search_blob(self.meta),
        ])
        score = 0
        if query and query in haystack:
            score += 20
        query_terms = text_terms(query)
        if query_terms:
            score += len(query_terms & text_terms(haystack))
        shared_signals = structure_signals(query) & structure_signals(haystack)
        if shared_signals:
            score += 8 * len(shared_signals)
            if self.kind == "banned_line" and self.strength == "hard":
                score += 4
        shared_problem_cues = problem_cues(query) & problem_cues(haystack)
        if shared_problem_cues:
            score += 10 * len(shared_problem_cues)
            if self.kind == "banned_line":
                score += 3
            if self.kind == "rewrite_pair":
                score += 2
        meta = self.meta if isinstance(self.meta, dict) else {}
        stored_reason_classes = {
            normalize_space_for_memory(str(item))
            for item in meta.get("reasonClasses", [])
            if normalize_space_for_memory(str(item))
        } if isinstance(meta.get("reasonClasses"), list) else set()
        shared_reason_classes = query_reason_classes(query) & stored_reason_classes
        if shared_reason_classes:
            score += 12 * len(shared_reason_classes)
            if self.kind == "banned_line" and self.strength == "hard":
                score += 4
        if self.strength == "hard":
            score += 2
        return score


def merge_entry_meta(existing: dict[str, Any] | None, incoming: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(existing or {})
    for key, value in (incoming or {}).items():
        if value in ("", None, [], {}):
            continue
        if isinstance(value, dict):
            current = merged.get(key)
            if isinstance(current, dict):
                nested = dict(current)
                for nested_key, nested_value in value.items():
                    if nested_value in ("", None, [], {}):
                        continue
                    nested[nested_key] = nested_value
                merged[key] = nested
            else:
                merged[key] = dict(value)
            continue
        merged[key] = value
    return merged


def tag_short_label(tag: str) -> str:
    parts = str(tag or "").split(":", 1)
    return parts[1].strip() if len(parts) > 1 else str(tag or "").strip()


def preferred_tag_labels(entry: StyleMemoryEntry, *, limit: int = 3) -> list[str]:
    prefixes_by_kind = {
        "banned_line": ("问题", "结构", "姿态", "语域", "开头", "比喻", "节奏"),
        "approved_line": ("优点",),
        "rewrite_pair": ("改法", "修复"),
        "rule": ("规则",),
    }
    generic_tags = {"banned", "approved", "rewrite_pair", "v2", "hard", "soft", "example"}
    prefixes = prefixes_by_kind.get(entry.kind, ())
    labels: list[str] = []
    for tag in entry.tags:
        normalized = str(tag or "").strip()
        if not normalized:
            continue
        if normalized.lower() in generic_tags:
            continue
        if prefixes and ":" in normalized:
            prefix, _ = normalized.split(":", 1)
            if prefix not in prefixes:
                continue
        label = tag_short_label(normalized)
        if label and label not in labels:
            labels.append(label)
        if len(labels) >= limit:
            break
    return labels


def context_move_label(entry: StyleMemoryEntry) -> str:
    meta = entry.meta if isinstance(entry.meta, dict) else {}
    variant_label = normalize_space_for_memory(str(meta.get("variantLabel", "")))
    if variant_label:
        return variant_label
    variant_move = normalize_space_for_memory(str(meta.get("variantMove", "")))
    move_labels = {
        "plain-language": "说人话",
        "less-ai": "少 AI 味",
        "oralize": "更像口播",
        "concretize": "更具体",
        "compress": "压缩",
        "source-ground": "接前后文",
        "rhythm-shift": "换节奏",
        "remove-slop": "去套话",
        "insert-paragraph": "补这一段",
    }
    return move_labels.get(variant_move, variant_move)


def context_scene_bits(entry: StyleMemoryEntry) -> list[str]:
    meta = entry.meta if isinstance(entry.meta, dict) else {}
    bits: list[str] = []
    audit_issue = meta.get("auditIssue")
    if isinstance(audit_issue, dict):
        category = normalize_space_for_memory(str(audit_issue.get("category", "")))
        if category:
            bits.append(f"触发问题：{category}")
    if meta.get("paragraphAssist"):
        bits.append("来源：补段候选")
    return bits[:2]


def render_context_entry(entry: StyleMemoryEntry) -> list[str]:
    focus = preferred_tag_labels(entry)
    lines: list[str] = []
    meta = entry.meta if isinstance(entry.meta, dict) else {}
    reason_labels = [
        normalize_space_for_memory(str(item))
        for item in meta.get("reasonLabels", [])
        if normalize_space_for_memory(str(item))
    ] if isinstance(meta.get("reasonLabels"), list) else []
    derived_rule = normalize_space_for_memory(str(meta.get("derivedRule", "")))
    principles = [
        normalize_space_for_memory(str(item))
        for item in meta.get("principles", [])
        if normalize_space_for_memory(str(item))
    ] if isinstance(meta.get("principles"), list) else []
    if entry.kind == "banned_line":
        lines.append(f"- 讨厌句：{entry.source_text}")
        if reason_labels:
            lines.append(f"  归类：{' / '.join(reason_labels[:3])}")
        if focus:
            lines.append(f"  问题：{' / '.join(focus)}")
        if entry.reason:
            lines.append(f"  为什么不行：{entry.reason}")
        if derived_rule:
            lines.append(f"  下次怎么避开：{derived_rule}")
        elif principles:
            lines.append(f"  下次怎么避开：{'；'.join(principles[:2])}")
    elif entry.kind == "approved_line":
        lines.append(f"- 喜欢句：{entry.source_text}")
        if reason_labels:
            lines.append(f"  归类：{' / '.join(reason_labels[:3])}")
        if focus:
            lines.append(f"  成立点：{' / '.join(focus)}")
        if entry.reason:
            lines.append(f"  为什么能留：{entry.reason}")
        if derived_rule:
            lines.append(f"  下次怎么借：{derived_rule}")
        elif principles:
            lines.append(f"  下次怎么借：{'；'.join(principles[:2])}")
    elif entry.kind == "rewrite_pair":
        lines.append(f"- 原句：{entry.source_text}")
        if entry.replacement_text:
            lines.append(f"  改后：{entry.replacement_text}")
        move_label = context_move_label(entry)
        if move_label:
            lines.append(f"  改法路线：{move_label}")
        if reason_labels:
            lines.append(f"  归类：{' / '.join(reason_labels[:3])}")
        if focus:
            lines.append(f"  有效点：{' / '.join(focus)}")
        if entry.reason:
            lines.append(f"  为什么有效：{entry.reason}")
        if derived_rule:
            lines.append(f"  下次优先：{derived_rule}")
        elif principles:
            lines.append(f"  下次优先：{'；'.join(principles[:2])}")
    else:
        lines.append(f"- 规则：{entry.source_text}")
        if entry.reason:
            lines.append(f"  说明：{entry.reason}")
    for extra in context_scene_bits(entry):
        if extra not in lines:
            lines.append(f"  {extra}")
    return lines


class StyleMemoryStore:
    def __init__(self, path: Path = DEFAULT_STORE, deleted_path: Path = DEFAULT_DELETED_STORE):
        self.path = path
        self.deleted_path = deleted_path

    def load(self, include_deleted: bool = False) -> list[StyleMemoryEntry]:
        entries: list[StyleMemoryEntry] = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entries.append(StyleMemoryEntry.from_record(json.loads(line)))
        if include_deleted and self.deleted_path.exists():
            for line in self.deleted_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entries.append(StyleMemoryEntry.from_record(json.loads(line)))
        return entries

    def save_active(self, entries: list[StyleMemoryEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        active = [entry for entry in entries if entry.status == "active"]
        self.path.write_text(
            "".join(json.dumps(entry.to_record(), ensure_ascii=False, sort_keys=True) + "\n" for entry in active),
            encoding="utf-8",
        )

    def append_deleted(self, entry: StyleMemoryEntry) -> None:
        self.deleted_path.parent.mkdir(parents=True, exist_ok=True)
        with self.deleted_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_record(), ensure_ascii=False, sort_keys=True) + "\n")

    def delete_conflicting_line_feedback(
        self,
        entries: list[StyleMemoryEntry],
        *,
        kind: str,
        source_text: str,
        scope: str,
    ) -> None:
        if kind not in {"approved_line", "banned_line"}:
            return
        opposite_kind = "approved_line" if kind == "banned_line" else "banned_line"
        normalized_source = normalize_space_for_memory(source_text)
        normalized_scope = scope.strip() or "personal-ip"
        for entry in entries:
            if (
                entry.status == "active"
                and entry.kind == opposite_kind
                and normalize_space_for_memory(entry.source_text) == normalized_source
                and (entry.scope.strip() or "personal-ip") == normalized_scope
            ):
                entry.status = "deleted"
                entry.deleted_at = now_iso()
                entry.updated_at = entry.deleted_at
                entry.reason = entry.reason or f"Superseded by {kind}"
                self.append_deleted(entry)

    def add(
        self,
        *,
        kind: str,
        source_text: str,
        replacement_text: str = "",
        reason: str = "",
        tags: str | list[str] | None = None,
        strength: str = "soft",
        scope: str = "personal-ip",
        origin: str = "manual",
        meta: dict[str, Any] | None = None,
        touch_usage_on_duplicate: bool = True,
    ) -> StyleMemoryEntry:
        normalized_kind = normalize_kind(kind)
        normalized_strength = normalize_strength(strength)
        normalized_tags = parse_tags(tags)
        source_text = source_text.strip()
        replacement_text = replacement_text.strip()
        if not source_text:
            raise ValueError("source_text is required")

        entries = self.load()
        normalized_scope = scope.strip() or "personal-ip"
        self.delete_conflicting_line_feedback(entries, kind=normalized_kind, source_text=source_text, scope=normalized_scope)
        stable_id = entry_id(normalized_kind, source_text, replacement_text, normalized_scope)
        for entry in entries:
            if entry.id == stable_id:
                entry.reason = reason.strip() or entry.reason
                entry.tags = parse_tags([*entry.tags, *normalized_tags])
                entry.strength = normalized_strength
                entry.origin = origin
                if touch_usage_on_duplicate:
                    entry.usage_count += 1
                entry.meta = merge_entry_meta(entry.meta, meta)
                entry.updated_at = now_iso()
                self.save_active(entries)
                return entry

        entry = StyleMemoryEntry(
            id=stable_id,
            kind=normalized_kind,
            source_text=source_text,
            replacement_text=replacement_text,
            reason=reason.strip(),
            tags=normalized_tags,
            strength=normalized_strength,
            scope=normalized_scope,
            origin=origin.strip() or "manual",
            meta=merge_entry_meta({}, meta),
        )
        entries.append(entry)
        self.save_active(entries)
        return entry

    def mark_used(self, entry_ids: list[str]) -> None:
        normalized_ids = [str(item).strip() for item in entry_ids if str(item).strip()]
        if not normalized_ids:
            return
        target_ids = set(normalized_ids)
        entries = self.load()
        changed = False
        used_at = now_iso()
        for entry in entries:
            if entry.id not in target_ids:
                continue
            entry.usage_count += 1
            entry.last_used_at = used_at
            changed = True
        if changed:
            self.save_active(entries)

    def delete(self, memory_id: str) -> StyleMemoryEntry:
        entries = self.load()
        for entry in entries:
            if entry.id == memory_id:
                entry.status = "deleted"
                entry.deleted_at = now_iso()
                entry.updated_at = entry.deleted_at
                self.append_deleted(entry)
                self.save_active(entries)
                return entry
        raise KeyError(f"memory not found: {memory_id}")

    def list(self, *, kind: str | None = None, include_deleted: bool = False) -> list[StyleMemoryEntry]:
        entries = self.load(include_deleted=include_deleted)
        if kind:
            target = normalize_kind(kind)
            entries = [entry for entry in entries if entry.kind == target]
        return sorted(entries, key=lambda entry: (entry.kind, entry.created_at, entry.id))

    def search(self, query: str, *, limit: int = 8, kind: str | None = None) -> list[StyleMemoryEntry]:
        entries = self.list(kind=kind)
        scored = [(entry.score(query), entry) for entry in entries]
        scored = [(score, entry) for score, entry in scored if score > 0]
        scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
        return [entry for _, entry in scored[:limit]]

    def render_context(self, query: str, *, limit: int = 10) -> str:
        entries = self.search(query, limit=limit)
        if not entries:
            return "# 本次相关风格记忆\n\n- 暂无相关风格记忆。\n"
        hard_banned_sources = {
            normalize_space_for_memory(entry.source_text)
            for entry in entries
            if entry.kind == "banned_line" and entry.strength == "hard"
        }
        entries = [
            entry
            for entry in entries
            if not (
                entry.kind == "approved_line"
                and normalize_space_for_memory(entry.source_text) in hard_banned_sources
            )
        ]
        self.mark_used([entry.id for entry in entries])
        groups = [
            ("这次必须避开", [entry for entry in entries if entry.kind == "banned_line" or entry.strength == "hard"]),
            ("这次可以借用", [entry for entry in entries if entry.kind == "approved_line"]),
            ("之前有效的改法", [entry for entry in entries if entry.kind == "rewrite_pair"]),
            ("额外规则", [entry for entry in entries if entry.kind == "rule"]),
        ]
        lines = [
            "# 本次相关风格记忆",
            "",
            "用途：不要只换词；先避开硬禁结构，再借喜欢样本和有效改法。",
            "",
        ]
        seen: set[str] = set()
        for title, group in groups:
            filtered = [entry for entry in group if entry.id not in seen]
            if not filtered:
                continue
            lines.append(f"## {title}")
            for entry in filtered:
                seen.add(entry.id)
                lines.extend(render_context_entry(entry))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def entry_to_line(entry: StyleMemoryEntry) -> str:
    tags = f" tags={','.join(entry.tags)}" if entry.tags else ""
    replacement = f" -> {entry.replacement_text}" if entry.replacement_text else ""
    return f"{entry.id}\t{entry.kind}\t{entry.strength}{tags}\t{entry.source_text}{replacement}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_STORE, help="JSONL store path.")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add or update a style memory entry.")
    add.add_argument("--kind", required=True, help="approved_line, banned_line, rewrite_pair, or rule.")
    add.add_argument("--source", required=True, help="Original selected text or rule text.")
    add.add_argument("--replacement", default="", help="Preferred replacement text.")
    add.add_argument("--reason", default="", help="Why this is liked/disliked.")
    add.add_argument("--tags", default="", help="Comma-separated tags.")
    add.add_argument("--strength", default="soft", help="hard, soft, or example.")
    add.add_argument("--scope", default="personal-ip", help="Memory scope.")
    add.add_argument("--origin", default="manual", help="manual, selection, import, gate.")
    add.add_argument("--json", action="store_true", help="Print JSON record.")

    list_cmd = sub.add_parser("list", help="List active style memory.")
    list_cmd.add_argument("--kind", help="Filter by kind.")
    list_cmd.add_argument("--include-deleted", action="store_true")
    list_cmd.add_argument("--json", action="store_true")

    delete = sub.add_parser("delete", help="Delete a memory by id.")
    delete.add_argument("id")
    delete.add_argument("--json", action="store_true")

    search = sub.add_parser("search", help="Search relevant style memory.")
    search.add_argument("query")
    search.add_argument("--kind", help="Filter by kind.")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--json", action="store_true")

    render = sub.add_parser("render-context", help="Render prompt-ready relevant memory.")
    render.add_argument("query")
    render.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = StyleMemoryStore(args.path, args.path.with_name(args.path.stem + "_deleted" + args.path.suffix))

    try:
        if args.command == "add":
            entry = store.add(
                kind=args.kind,
                source_text=args.source,
                replacement_text=args.replacement,
                reason=args.reason,
                tags=args.tags,
                strength=args.strength,
                scope=args.scope,
                origin=args.origin,
            )
            print(json.dumps(entry.to_record(), ensure_ascii=False, sort_keys=True) if args.json else entry_to_line(entry))
            return 0
        if args.command == "list":
            entries = store.list(kind=args.kind, include_deleted=args.include_deleted)
            if args.json:
                print(json.dumps([entry.to_record() for entry in entries], ensure_ascii=False, indent=2, sort_keys=True))
            else:
                for entry in entries:
                    print(entry_to_line(entry))
            return 0
        if args.command == "delete":
            entry = store.delete(args.id)
            print(json.dumps(entry.to_record(), ensure_ascii=False, sort_keys=True) if args.json else f"deleted {entry.id}")
            return 0
        if args.command == "search":
            entries = store.search(args.query, limit=args.limit, kind=args.kind)
            if args.json:
                print(json.dumps([entry.to_record() for entry in entries], ensure_ascii=False, indent=2, sort_keys=True))
            else:
                for entry in entries:
                    print(entry_to_line(entry))
            return 0
        if args.command == "render-context":
            print(store.render_context(args.query, limit=args.limit), end="")
            return 0
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    parser.error("unreachable command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
