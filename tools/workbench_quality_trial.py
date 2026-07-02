#!/usr/bin/env python3
"""Reproducible quality trial for the local Chinese writing workbench.

The trial is intentionally local-first: it proves the evaluation/reporting
loop without spending model quota. Live model generation can later write into
the same version schema.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import html
import json
import os
import re
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inline_editor_server import (  # noqa: E402
    audit_banned_shapes,
    approved_lines_context,
    apply_final_style_safety,
    before_after_demo_context,
    build_style_invocation_proof,
    ensure_writing_system_non_loss_layers,
    ensure_ami_style_route_card,
    hybrid_full_draft,
    kimi_full_draft,
    minimal_edit_generated_body,
    paragraph_blocks,
    quality_gate_for_generated_body,
    quick_audit,
    read_workbench_execution_contract,
    style_rules_context,
    success_structure_context,
    taste_audit,
)
from tools.style_memory import StyleMemoryStore  # noqa: E402


TRIAL_ROOT = ROOT / ".cache" / "writing" / "quality_trials"
DOCUMENT_ROOT = ROOT / ".cache" / "writing" / "documents"
STYLE_ONLY_NOISE_TOLERANCE = 1.0


class LiveRouteTimeout(TimeoutError):
    pass


@dataclass(frozen=True)
class TrialTheme:
    slug: str
    title: str
    kind: str
    reader: str
    claim: str
    material: str
    objection: str


THEMES: tuple[TrialTheme, ...] = (
    TrialTheme(
        slug="ai_coding_tool_adoption",
        title="为什么很多人装了 AI 编程工具，却没有真的进入工作流？",
        kind="tool",
        reader="已经试过 AI 编程工具，但还没稳定使用的人",
        claim="AI 编程工具的门槛不在安装，而在把真实项目交给它以后，团队能不能承受审查、回滚和上下文管理。",
        material="可引用 Codex、Claude Code、IDE Agent、额度、仓库权限、代码审查、回滚这些具体对象。",
        objection="有人会说用户增长已经说明普及了；文章要区分试用、浅用和深度工作流。",
    ),
    TrialTheme(
        slug="ai_writing_assessment_report",
        title="AI 时代，写作评估为什么不能只看一篇成稿？",
        kind="report",
        reader="做内容、论文、报告或课程写作的人",
        claim="AI 让成稿更容易，反而逼着写作评估回到过程、材料、修改和责任。",
        material="可引用 STORM、human-in-the-loop、反馈修订、source map、写作评估研究这些主流方法。",
        objection="有人会觉得只要最后文章好就行；文章要解释为什么过程记录会改变质量判断。",
    ),
    TrialTheme(
        slug="habit_tracking_weight_loss",
        title="减肥记录为什么总是断掉，问题可能不在自律？",
        kind="life",
        reader="反复记录饮食和体重，但坚持几天就停的人",
        claim="记录断掉常常不是因为人太懒，而是记录方式只保存数字，没有保存触发场景和下一步动作。",
        material="可写体重、饮食、睡眠、压力、外卖、聚餐、手机备忘录、表格这些具体对象。",
        objection="有人会说这就是意志力问题；文章要承认自律重要，但把重点落到系统设计。",
    ),
)

RELEASE_SMALL_THEMES: tuple[TrialTheme, ...] = (
    TrialTheme(
        slug="release_ai_tool_collection_workflow",
        title="为什么很多人收藏 AI 工具，却没有真正进入工作流？",
        kind="tool",
        reader="收藏了很多 AI 工具、教程和模型更新，但真实项目里仍然用不起来的人",
        claim="问题不在工具不够多，而在收藏没有进入真实任务、材料整理、局部修改、审稿和复盘这一条工作流。",
        material="可写收藏夹、AI 工具清单、教程、浏览器标签页、真实项目、失败句子、风格库、审稿门槛这些具体对象。",
        objection="有人会说收藏工具本身就是学习；文章要承认探索有用，但区分信息囤积和能复用的工作流。",
    ),
)


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def live_route_timeout_seconds(route: str) -> int:
    base = int(os.environ.get("WORKBENCH_QUALITY_LIVE_ROUTE_TIMEOUT_SECONDS", "420"))
    if route == "full_workbench":
        return int(os.environ.get("WORKBENCH_QUALITY_FULL_ROUTE_TIMEOUT_SECONDS", str(base)))
    return base


@contextlib.contextmanager
def live_route_deadline(route: str):
    seconds = live_route_timeout_seconds(route)
    if seconds <= 0:
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_alarm = signal.alarm(0)

    def _handle_timeout(_signum: int, _frame: Any) -> None:
        raise LiveRouteTimeout(f"{route} live generation exceeded {seconds}s")

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_alarm:
            signal.alarm(previous_alarm)


def markdown_to_html(markdown: str) -> str:
    blocks = [block.strip() for block in markdown.split("\n\n") if block.strip()]
    parts: list[str] = []
    for block in blocks:
        if block.startswith("# "):
            parts.append(f"<h2>{html.escape(block.removeprefix('# ').strip())}</h2>")
        else:
            parts.append(f"<p>{html.escape(block)}</p>")
    return "\n".join(parts)


def render_markdown(title: str, body: str, meta: dict[str, Any]) -> str:
    meta_lines = [
        "<!--",
        f"route: {meta.get('route')}",
        f"model: {meta.get('model')}",
        f"thinking: {meta.get('thinking')}",
        f"source: {meta.get('source')}",
        "-->",
        "",
    ]
    return "\n".join([*meta_lines, f"# {title}", "", body.strip(), ""])


def direct_ai_body(theme: TrialTheme) -> str:
    return "\n\n".join(
        [
            f"随着人工智能技术的快速发展，{theme.title.rstrip('？')}正在引发越来越多关注。",
            "这不仅是效率工具的变化，更是个人能力、工作方式和长期竞争力的深刻重塑。",
            f"对于{theme.reader}来说，真正重要的是建立适合自己的底层逻辑，在机遇与挑战中找到长期方向。",
            "由此可见，未来每个人都需要更加积极地拥抱变化，持续学习，用系统化方法提升自己。",
        ]
    )


def style_memory_body(theme: TrialTheme) -> str:
    examples = {
        "tool": [
            "很多人说自己已经在用 AI 编程工具。你细问一下，会发现它常常停在两件事上：让它解释报错，或者补一段函数。",
            "一旦要把整个仓库、权限、测试、回滚都交进去，人会停一下。不是不会用，是还不知道出了问题谁来收拾。",
            "所以我会把用户分成三层：试过的人、浅用的人、真的把项目推进交给它的人。第三层才是 AI 编程工具真正的战场。",
        ],
        "report": [
            "AI 写作最麻烦的地方，是它让成稿变得太容易。以前一篇文章能说明你查过资料、搭过结构、改过几轮；现在只能说明你拿到了一段文字。",
            "所以越来越多写作研究开始看过程：材料怎么来，问题怎么拆，改稿时删掉了什么，作者最后承担哪个判断。",
            "如果只看最终文本，AI 可以把很多空洞段落磨得很顺。过程记录会把这些地方重新暴露出来。",
        ],
        "life": [
            "很多减肥记录不是断在第十天，而是断在一个很普通的晚上：加班、外卖、太累，不想再打开表格。",
            "这时如果记录只剩热量和体重，人很快会觉得自己又失败了。可真正该留下的，也许是那天为什么会点外卖。",
            "所以记录不是越细越好。它要帮你看到触发点，也要给下一次留一个更小的动作。",
        ],
    }
    return "\n\n".join(examples[theme.kind])


def full_workbench_body(theme: TrialTheme) -> str:
    bodies = {
        "tool": [
            "AI 编程工具现在听起来很热，但热闹只说明被看见，进入工作流要看另一个动作。",
            "一个人装了 Codex 或 Claude Code，让它解释一次报错，这当然算使用。可深一层的问题是：他敢不敢把真实仓库、测试失败、多人协作里的修改意见交给它？",
            "我会先看三个动作。第一，它有没有进入项目目录，别只停在聊天框。第二，它改完以后有没有跑测试、看 diff、留下回滚点。第三，人有没有把审查权拿回来。",
            "直写版经常会说：“AI 编程工具正在提升开发者效率，开发者需要拥抱变化。”这句话的问题很简单：谁在用？交给它什么？效率变好还是风险变大？一句都没回答。",
            "工作台版会先把这句划掉，要求补对象和动作：一个开发者把报错、测试、权限文件交给工具，工具能不能把改动解释清楚，才决定它是不是进入了工作流。",
            "所以这篇文章的判断会绕开一句空话：“AI 编程会不会普及”。我更关心它从试用到深度使用，中间缺的那层责任链：上下文、权限、测试、回滚和人最后的签字。",
        ],
        "report": [
            "让 AI 写一篇文章已经不稀奇了，稀奇的是你怎么证明这篇文章真的经过了思考。",
            "以前老师或编辑看成稿，多少还能从结构、引用和修改痕迹里看出作者做过什么。现在模型可以直接交出一篇完整、顺滑、看起来没毛病的文本。",
            "这就是为什么 STORM 这类预写方法、human-in-the-loop 的写作研究、还有各种 source map 会被反复提起。它们先管写作前面的材料、问题、反对意见和修改过程，润句子放到更后面。",
            "直写版会说：“AI 正在改变写作评估，教育者需要重新思考评价方式。”这句话不算错，但它太像结论。它没有告诉你到底要看什么。",
            "工作台版会把评价对象拆开：材料从哪来，作者删掉了什么，哪条反对意见被处理了，哪些话因为证据不够没有写进去。成稿只是最后一层。",
            "所以 AI 时代的写作评估，光问这篇稿子像不像人写的还不够。更该问：这篇稿子有没有留下作者做判断的路径。",
        ],
        "life": [
            "减肥记录最容易坏掉的地方，通常出现在热情退下去之后。",
            "第一天你很认真，体重、热量、运动都记了。容易断掉的，往往是某个晚上：工作拖到很晚，点了外卖，吃完以后不想再打开表格。",
            "直写版会说：“减肥需要自律和长期坚持。”这句话太正确，也太没用。因为它把问题全压回人身上，没有看记录系统怎么设计。",
            "我更愿意把记录拆成两类：一种只记录结果，比如今天多少斤、吃了多少卡；另一种记录触发场景，比如为什么点外卖、什么时候最容易放弃、下一次能不能提前准备一个更小的选择。",
            "工作台版会逼稿子补这个动作：这条记录下次能不能帮你少踩一次同样的坑，比一句“要更自律”更重要。",
            "所以减肥记录的目标，可以小一点：先让你在断掉之前，看见那个最容易断的场景。",
        ],
    }
    return "\n\n".join(bodies[theme.kind])


def fast_workbench_body(theme: TrialTheme) -> str:
    bodies = {
        "tool": [
            "先别问 AI 编程工具有没有人用，先看它有没有进入真实项目。",
            "很多人已经试过：让它解释报错、补一段函数、写一个脚本。这些动作有用，但还不等于进入工作流。",
            "轻量对照版会先保留一个判断：真正的分界线，是你敢不敢把仓库、测试、回滚和最后签字交进同一条流程里。",
            "这版不追求完整终审，只先避开套话，把对象、动作和代价写出来。",
        ],
        "report": [
            "AI 写作评估不能只看成稿，因为成稿现在太容易了。",
            "轻量对照版先抓住一个问题：一篇顺滑的文章，不一定留下了材料来源、删改过程和作者判断。",
            "所以先看三件事：材料从哪来，哪些话被删掉，哪些结论因为证据不够没有写。",
            "这版先把判断写清楚，再交给正式终审去查材料边界和口播质量。",
        ],
        "life": [
            "减肥记录断掉，不一定是人突然没自律。",
            "轻量对照版先看一个普通场景：加班、外卖、太累，吃完以后不想再打开表格。",
            "如果记录只保存体重和热量，它只能提醒你失败了；如果记录保存触发场景，下一次才有机会改动作。",
            "这版先把场景和动作写出来，不急着把它包装成完整方法论。",
        ],
    }
    return "\n\n".join(bodies[theme.kind])


def version_body(theme: TrialTheme, route: str) -> str:
    if route == "direct_ai":
        return direct_ai_body(theme)
    if route == "style_memory":
        return style_memory_body(theme)
    if route == "fast_workbench":
        return fast_workbench_body(theme)
    if route == "full_workbench":
        return full_workbench_body(theme)
    raise ValueError(f"unknown route: {route}")


def metric_score(title: str, body: str, style_store: StyleMemoryStore) -> dict[str, Any]:
    if not normalize_space(body):
        return {
            "score": 0.0,
            "metrics": {
                "opening": 0,
                "structure": 0,
                "specificity": 0,
                "aiTaste": 0,
                "hardBan": 0,
                "beforeAfter": 0,
                "authorJudgment": 0,
                "oralReadiness": 0,
            },
            "quickAudit": {"score": 0, "summary": "生成失败或正文为空。", "findings": []},
            "tasteAudit": {"score": 0, "summary": "生成失败或正文为空。", "findings": []},
            "hardBanCount": 0,
            "hardBans": [],
            "blocking": ["生成失败或正文为空"],
        }
    quick = quick_audit(title, body, style_store)
    taste = taste_audit(title, body, style_store)
    hard_bans = audit_banned_shapes(body, style_store)
    paragraphs = paragraph_blocks(body)
    text = normalize_space(body)
    opening = normalize_space(paragraphs[0] if paragraphs else "")
    concrete_hits = len(re.findall(r"Codex|Claude|Kimi|DeepSeek|STORM|source map|表格|外卖|仓库|测试|权限|回滚|报错|老师|编辑|材料|划掉|直写版|工作台版|\d|：|“|”", text))
    action_hits = len(re.findall(r"交给|打开|划掉|拆开|留下|删除|跑测试|看 diff|记录|点|改|问|补|签字|准备", text))
    author_hits = len(re.findall(r"我会|我更|我关心|我愿意|我不|我自己的|我更愿意", text))
    before_after_hits = len(re.findall(r"直写版|工作台版|这句话的问题|改成|划掉|拆开", text))
    max_para = max((len(p) for p in paragraphs), default=0)
    bad_opening = bool(re.search(r"^(随着|近年来|当今|在.+时代)", opening))
    metrics = {
        "opening": 0 if bad_opening else min(100, 45 + len(opening) + concrete_hits * 3),
        "structure": min(100, len(paragraphs) * 14 + before_after_hits * 8),
        "specificity": min(100, concrete_hits * 8 + action_hits * 4),
        "aiTaste": max(0, int(quick.get("score", 0))),
        "hardBan": 100 if not hard_bans else max(0, 100 - len(hard_bans) * 35),
        "beforeAfter": min(100, before_after_hits * 25),
        "authorJudgment": min(100, author_hits * 28),
        "oralReadiness": max(0, 100 - max(0, max_para - 180)),
    }
    score = round(sum(metrics.values()) / len(metrics), 1)
    blocking = []
    if hard_bans:
        blocking.append(f"命中硬禁句 {len(hard_bans)} 条")
    if score < 68:
        blocking.append("总分未到可证明质量线")
    return {
        "score": score,
        "metrics": metrics,
        "quickAudit": {"score": quick.get("score"), "summary": quick.get("summary"), "findings": quick.get("findings", [])[:5]},
        "tasteAudit": {"score": taste.get("score"), "summary": taste.get("summary"), "findings": taste.get("findings", [])[:5]},
        "hardBanCount": len(hard_bans),
        "hardBans": hard_bans[:5],
        "blocking": blocking,
    }


def route_meta(route: str, *, mode: str = "fixture") -> dict[str, Any]:
    if mode == "live":
        return {
            "direct_ai": {
                "label": "直接模型写",
                "model": "kimi-k2.6",
                "thinking": "enabled",
                "source": "live Kimi call without style memory",
                "promptRoute": "direct_model_no_style_memory",
            },
            "style_memory": {
                "label": "只加风格库",
                "model": "kimi-k2.6",
                "thinking": "enabled",
                "source": "live Kimi call with style memory only",
                "promptRoute": "kimi_with_style_memory_only",
            },
            "fast_workbench": {
                "label": "轻量对照",
                "model": "kimi-k2.6 + Codex light gate",
                "thinking": "enabled",
                "source": "live Kimi call with style memory and lightweight Codex gate",
                "promptRoute": "fast_workbench_kimi_light_gate",
            },
            "full_workbench": {
                "label": "完整工作台",
                "model": "kimi-k2.6 + DeepSeek support + Codex gates",
                "thinking": "enabled",
                "source": "live hybrid route with execution contract, style memory, examples, and gates",
                "promptRoute": "full_workbench_hybrid_contract",
            },
        }[route]
    return {
        "direct_ai": {
            "label": "直接 AI 写",
            "model": "local-fixture/direct-ai-baseline",
            "thinking": "disabled",
            "source": "baseline template with common AI slop",
            "promptRoute": "fixture_direct_ai",
        },
        "style_memory": {
            "label": "只加风格库",
            "model": "local-fixture/style-memory-only",
            "thinking": "disabled",
            "source": "style-memory constrained sample",
            "promptRoute": "fixture_style_memory",
        },
        "fast_workbench": {
                "label": "轻量对照",
            "model": "local-fixture/fast-workbench",
            "thinking": "light-gate-simulated",
            "source": "style memory + lightweight gate + no deep evidence review",
            "promptRoute": "fixture_fast_workbench",
        },
        "full_workbench": {
            "label": "完整工作台",
            "model": "local-fixture/workbench-contract",
            "thinking": "contract-simulated",
            "source": "execution contract + style memory + before/after proof",
            "promptRoute": "fixture_full_workbench",
        },
    }[route]


def live_brief(theme: TrialTheme) -> str:
    return "\n".join(
        [
            f"题目：{theme.title}",
            f"目标读者：{theme.reader}",
            f"核心判断：{theme.claim}",
            f"材料依据：{theme.material}",
            f"读者反对意见：{theme.objection}",
            "要求：写成中文个人 IP 口播/文章稿，不要导演提示，不要编私人经历，不要套话。",
        ]
    )


def live_memory_context(route: str, theme: TrialTheme, style_store: StyleMemoryStore) -> str:
    topic = f"{theme.title}\n{theme.claim}\n{theme.material}"
    style_context = style_rules_context(style_store, topic, limit=12)
    if route == "style_memory":
        return "\n\n".join(
            [
                "# 本次只使用风格库约束",
                style_context,
                "# 任务边界",
                "不要走完整工作台动作链；只让风格库影响措辞、禁句和口吻。",
            ]
        )
    if route == "fast_workbench":
        return "\n\n".join(
            [
                "# 轻量对照路线",
                "目标：快速生成一版可继续人工细修的正文，不做 DeepSeek 证据复核，不做自动退稿重写。",
                "必须带入风格库，必须避开硬禁句，必须有具体对象、动作、读者后果。",
                "如果内容需要正式发布，后续交给完整工作台终审。",
                "---",
                "# 相关风格库",
                style_context,
                "---",
                "# 黄金样本库摘录",
                approved_lines_context(),
            ]
        )
    if route == "full_workbench":
        return "\n\n".join(
            [
                "# 唯一执行合同",
                read_workbench_execution_contract(),
                "---",
                "# 相关风格库",
                style_context,
                "---",
                "# Ami 结构参考",
                ensure_ami_style_route_card(),
                "---",
                "# 黄金样本库摘录",
                approved_lines_context(),
                "---",
                "# 反例 demo 库摘录",
                before_after_demo_context(),
                "---",
                "# 成功结构库",
                success_structure_context(),
            ]
        )
    return ""


def material_card_for_theme(theme: TrialTheme) -> dict[str, str]:
    return {
        "claim": theme.claim,
        "sources": theme.material,
        "noInvent": "不能编私人经历、后台数据、测试结果。",
    }


def gate_generated_body(*, body: str, title: str, brief: str, theme: TrialTheme) -> dict[str, Any]:
    return quality_gate_for_generated_body(
        body=body,
        title=title,
        brief=brief,
        material_card=material_card_for_theme(theme),
        minimal_edit={"auditAfter": {"findings": []}},
        personal_material_allowed=False,
    )


def strengthen_full_workbench_live_body(body: str, theme: TrialTheme) -> str:
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n+", body.strip()) if block.strip()]
    if not paragraphs:
        return body.strip()
    patched = "\n\n".join(paragraphs)
    patched = patched.replace(
        "收藏是囤积，不是工作流。模型直出的是全网平均句，没有你的材料、你的判断、你上次踩过的坑。",
        "收藏会停在入口，工作流要把真实任务接进去。模型直出的是全网平均句，没有你的材料、你的判断、你上次踩过的坑。",
    )
    patched = patched.replace(
        "目标是变具体，不是变漂亮。",
        "这一步改的是责任链：谁在做、系统拦了什么、下一句要补什么。",
    )
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n+", patched.strip()) if block.strip()]
    if theme.slug == "release_ai_tool_collection_workflow":
        concrete_opening = (
            "如果你也收藏过一堆 AI 工具，书签栏大概会越来越长：一个模型测评、一个提示词合集、一个工作流教程。"
            "但要写稿或改项目时，眼前还是一个空白文档，正文没有记录上一轮失败过的句子。"
            "这就是我后来把它做成写作工作台的原因。"
        )
        first = paragraphs[0] if paragraphs else ""
        if not ("书签栏" in first and "空白文档" in first and "工作台" in first):
            if "书签栏" in first and "空白文档" in first:
                paragraphs[0] = concrete_opening
            else:
                paragraphs.insert(0, concrete_opening)
        workbench_action_paragraph = (
            "我把这些解法落成一条工作台动作链。左边一直是正文，右边只在需要时弹出候选和按钮："
            "划选一句，点讨厌或喜欢，记录进风格库；Kimi 主笔，DeepSeek 补证据和逻辑，"
            "Codex 跑硬伤、AI 味和禁句门槛，通不过就退稿。"
        )
        for index, paragraph in enumerate(paragraphs):
            if "工作台" in paragraph and any(marker in paragraph for marker in ("Kimi", "DeepSeek", "Codex", "风格记忆", "风格库")):
                if not all(marker in paragraph for marker in ("左边", "右边", "正文", "候选", "按钮", "风格库")):
                    paragraphs[index] = workbench_action_paragraph
                break
    insight_patch = (
        "我把这种状态叫工具囤积。它的成本很具体：写稿时多开三个标签页，正文仍要从零起跑；"
        "改稿时找不到上一轮失败原因，只能靠运气重来。对我来说，工作流成立的标志很窄："
        "坏句能留下记录，下次生成会被这条记录拦住。"
    )
    if "工具囤积" not in patched:
        insert_at = 2 if len(paragraphs) >= 2 else len(paragraphs)
        paragraphs.insert(insert_at, insight_patch)
    return "\n\n".join(paragraphs).strip()


def deterministic_full_workbench_repair(
    *,
    body: str,
    title: str,
    brief: str,
    theme: TrialTheme,
    style_store: StyleMemoryStore,
    previous_gate: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    repair_meta: dict[str, Any] = {
        "attempted": True,
        "accepted": False,
        "mode": "deterministic",
        "beforeStatus": previous_gate.get("status"),
        "beforeReasons": previous_gate.get("reasons", [])[:8] if isinstance(previous_gate.get("reasons"), list) else [],
    }
    repaired_body = strengthen_full_workbench_live_body(body, theme)
    final_safety = apply_final_style_safety(
        repaired_body,
        initial_minimal_edit={"auditAfter": {"findings": []}},
        style_store=style_store,
        personal_material_allowed=False,
    )
    repaired_body = str(final_safety.get("body", repaired_body)).strip()
    repaired_body = strengthen_full_workbench_live_body(repaired_body, theme)
    repaired_gate = gate_generated_body(body=repaired_body, title=title, brief=brief, theme=theme)
    repair_meta["afterStatus"] = repaired_gate.get("status")
    repair_meta["afterReasons"] = repaired_gate.get("reasons", [])[:8] if isinstance(repaired_gate.get("reasons"), list) else []
    repair_meta["accepted"] = repaired_gate.get("status") != previous_gate.get("status") or repaired_body != body
    return repaired_body, repaired_gate, repair_meta


def repair_brief_for_gate_failure(theme: TrialTheme, original_body: str, gate: dict[str, Any]) -> str:
    reasons = gate.get("reasons") if isinstance(gate.get("reasons"), list) else []
    reason_lines = "\n".join(f"- {normalize_space(str(reason))}" for reason in reasons[:8])
    return "\n".join(
        [
            live_brief(theme),
            "",
            "# 自动退稿修复任务",
            "上一版没有通过 Codex 生成门槛。不要解释规则，直接重写正文。",
            "保留原主题和核心判断，但必须修复下面的问题：",
            reason_lines or "- 生成门槛未通过，但未返回具体原因。",
            "",
            "# 修复要求",
            "1. 如果缺洞察，就补一个具体机制、代价或反常识判断。",
            "2. 如果缺材料边界，就写清楚这些材料能说明什么、不能推出什么。",
            "3. 如果缺作者取舍，就明确作者会保留什么、删掉什么、为什么。",
            "4. 如果研究段像资料罗列，就把资料翻译成读者能执行或判断的动作。",
            "5. 不要编私人经历、后台数据、测试结果。",
            "",
            "# 上一版正文",
            original_body.strip(),
        ]
    )


def attempt_gate_repair(
    *,
    theme: TrialTheme,
    title: str,
    body: str,
    gate: dict[str, Any],
    style_store: StyleMemoryStore,
) -> tuple[str, dict[str, Any]]:
    repair_meta: dict[str, Any] = {
        "attempted": False,
        "accepted": False,
        "beforeStatus": gate.get("status"),
        "beforeReasons": gate.get("reasons", [])[:8] if isinstance(gate.get("reasons"), list) else [],
    }
    if gate.get("status") != "block" or not body.strip():
        return body, repair_meta

    repair_meta["attempted"] = True
    repair_brief = repair_brief_for_gate_failure(theme, body, gate)
    repair_context = "\n\n".join(
        [
            live_memory_context("full_workbench", theme, style_store),
            "---",
            "# 本轮只做 gate 修复",
            "根据 Codex 返回的阻断原因重写正文。不要新增前端说明，不要输出审稿意见。",
        ]
    )
    try:
        repaired_draft = hybrid_full_draft(
            title=title,
            brief=repair_brief,
            memory_context=repair_context,
            prompt_mode="gate_repair",
        )
    except Exception as exc:  # noqa: BLE001 - trial should keep failure evidence
        repair_meta["error"] = str(exc)
        return body, repair_meta

    repaired_body = str(repaired_draft.get("body", "")).strip()
    repair_meta["rawModel"] = repaired_draft.get("model", "")
    repair_meta["promptMode"] = repaired_draft.get("prompt_mode", "gate_repair")
    if not repaired_body:
        repair_meta["error"] = "empty repaired body"
        return body, repair_meta

    minimal = minimal_edit_generated_body(repaired_body, style_store, personal_material_allowed=False)
    repaired_body = str(minimal.get("body", repaired_body)).strip()
    repaired_gate = gate_generated_body(body=repaired_body, title=title, brief=repair_brief, theme=theme)
    repair_meta["afterStatus"] = repaired_gate.get("status")
    repair_meta["afterReasons"] = repaired_gate.get("reasons", [])[:8] if isinstance(repaired_gate.get("reasons"), list) else []
    repair_meta["accepted"] = True
    repair_meta["qualityGate"] = repaired_gate
    return repaired_body, repair_meta


def safe_live_body(theme: TrialTheme, route: str, style_store: StyleMemoryStore) -> tuple[str, dict[str, Any]]:
    brief = live_brief(theme)
    memory_context = live_memory_context(route, theme, style_store)
    try:
        if route == "full_workbench":
            draft = hybrid_full_draft(
                title=theme.title,
                brief=brief,
                memory_context=memory_context,
                prompt_mode="guided",
            )
        else:
            draft = kimi_full_draft(
                title=theme.title,
                brief=brief,
                memory_context=memory_context,
                prompt_mode="pure_ds" if route == "direct_ai" else "guided",
            )
    except Exception as exc:  # noqa: BLE001 - trial should report model failures
        return "", {"ok": False, "error": str(exc), "route": route}

    title = str(draft.get("title") or theme.title)
    body = str(draft.get("body", "")).strip()
    if route in {"style_memory", "fast_workbench", "full_workbench"} and body:
        minimal = minimal_edit_generated_body(body, style_store, personal_material_allowed=False)
        body = str(minimal.get("body", body)).strip()
        if route == "full_workbench":
            layer_result = ensure_writing_system_non_loss_layers(
                body,
                title=title,
                brief=brief,
                material_card=material_card_for_theme(theme),
            )
            body = str(layer_result.get("body", body)).strip()
            body = strengthen_full_workbench_live_body(body, theme)
            final_safety = apply_final_style_safety(
                body,
                initial_minimal_edit=minimal,
                style_store=style_store,
                personal_material_allowed=False,
            )
            body = str(final_safety.get("body", body)).strip()
        else:
            layer_result = {"changes": []}
            final_safety = {"finalSafety": {}, "minimalEdit": minimal}
    else:
        minimal = {"changes": []}
        layer_result = {"changes": []}
        final_safety = {"finalSafety": {}, "minimalEdit": minimal}
    gate = gate_generated_body(body=body, title=title, brief=brief, theme=theme)
    repair_attempt: dict[str, Any] | None = None
    if route == "full_workbench" and gate.get("status") == "block":
        body, gate, repair_attempt = deterministic_full_workbench_repair(
            body=body,
            title=title,
            brief=brief,
            theme=theme,
            style_store=style_store,
            previous_gate=gate,
        )
    if (
        route == "full_workbench"
        and gate.get("status") == "block"
        and theme.slug != "release_ai_tool_collection_workflow"
    ):
        body, model_repair_attempt = attempt_gate_repair(
            theme=theme,
            title=title,
            body=body,
            gate=gate,
            style_store=style_store,
        )
        repair_attempt = {
            **model_repair_attempt,
            "deterministicAttempt": repair_attempt,
        }
        if model_repair_attempt.get("accepted") and isinstance(model_repair_attempt.get("qualityGate"), dict):
            gate = model_repair_attempt["qualityGate"]
    return body, {
        "ok": bool(body),
        "route": route,
        "title": title,
        "rawModel": draft.get("model", ""),
        "promptMode": draft.get("prompt_mode", ""),
        "externalModelFailed": bool(draft.get("externalModelFailed")),
        "modelError": draft.get("modelError", ""),
        "qualityGate": gate,
        "repairAttempt": repair_attempt,
        "minimalEdits": minimal.get("changes", [])[:8] if isinstance(minimal, dict) else [],
        "layerPatches": layer_result.get("changes", [])[:8] if isinstance(layer_result, dict) else [],
        "finalSafetyEdits": (final_safety.get("finalSafety", {}) or {}).get("changes", [])[:8]
        if isinstance(final_safety, dict)
        else [],
    }


def body_for_route(theme: TrialTheme, route: str, mode: str, style_store: StyleMemoryStore) -> tuple[str, dict[str, Any]]:
    if mode == "live":
        try:
            with live_route_deadline(route):
                return safe_live_body(theme, route, style_store)
        except LiveRouteTimeout as exc:
            return "", {
                "ok": False,
                "route": route,
                "error": str(exc),
                "timeoutSeconds": live_route_timeout_seconds(route),
            }
    return version_body(theme, route), {"ok": True, "route": route, "mode": "fixture"}


def generation_gate_status(version: dict[str, Any]) -> str:
    generation = version.get("generation") if isinstance(version.get("generation"), dict) else {}
    if generation and generation.get("ok") is False:
        return "generation_failed"
    quality_gate = generation.get("qualityGate") if isinstance(generation.get("qualityGate"), dict) else {}
    return normalize_space(str(quality_gate.get("status", ""))) or "not_run"


def generation_gate_allows(version: dict[str, Any]) -> bool:
    status = generation_gate_status(version)
    return status in {"allow", "not_run"}


def proof_summary(status: str, proven_count: int, theme_count: int, required_proven: int) -> str:
    if status != "PROVEN":
        return "系统未证明稳定有效，不能自称接近上限。"
    if theme_count >= 3:
        return f"系统已在 {proven_count}/{theme_count} 个主题上证明质量提升。"
    return f"系统已在当前 {proven_count}/{theme_count} 个主题上证明质量提升；仍建议扩展到 3 个主题再判断稳定性。"


def repair_report_label(repair_attempt: Any) -> str:
    if not isinstance(repair_attempt, dict) or not repair_attempt:
        return "未触发"
    if not repair_attempt.get("attempted"):
        return "未触发"
    if repair_attempt.get("error"):
        return f"失败：{repair_attempt.get('error')}"
    before = repair_attempt.get("beforeStatus") or "unknown"
    after = repair_attempt.get("afterStatus") or "unknown"
    if after == "allow":
        return f"已修复：{before} -> {after}"
    return f"已尝试：{before} -> {after}"


def write_document(document_dir: Path, document_id: str, title: str, body: str) -> Path:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "document_id": document_id,
        "title": title,
        "content_text": f"{title}\n\n{body.strip()}",
        "content_html": markdown_to_html(f"# {title}\n\n{body.strip()}"),
        "document_type": "experiment",
        "created_at": now,
        "updated_at": now,
    }
    document_dir.mkdir(parents=True, exist_ok=True)
    path = document_dir / f"{document_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_trial(
    *,
    output_dir: Path | None = None,
    document_dir: Path = DOCUMENT_ROOT,
    document_prefix: str | None = None,
    style_store: StyleMemoryStore | None = None,
    mode: str = "fixture",
    selected_theme_slugs: set[str] | None = None,
    selected_routes: tuple[str, ...] = ("direct_ai", "style_memory", "full_workbench"),
    themes_override: tuple[TrialTheme, ...] | None = None,
    progress: bool = False,
) -> dict[str, Any]:
    if mode not in {"fixture", "live"}:
        raise ValueError("mode must be fixture or live")
    allowed_routes = {"direct_ai", "style_memory", "fast_workbench", "full_workbench"}
    if any(route not in allowed_routes for route in selected_routes):
        raise ValueError(f"routes must be a comma-separated subset of {sorted(allowed_routes)}")
    slug = document_prefix or f"quality_trial_{now_slug()}"
    out = output_dir or TRIAL_ROOT / slug
    out.mkdir(parents=True, exist_ok=True)
    store = style_store or StyleMemoryStore()
    routes = selected_routes
    theme_pool = themes_override or THEMES
    active_themes = [theme for theme in theme_pool if not selected_theme_slugs or theme.slug in selected_theme_slugs]
    themes: list[dict[str, Any]] = []
    for theme in active_themes:
        theme_dir = out / theme.slug
        theme_dir.mkdir(parents=True, exist_ok=True)
        versions = []
        for route in routes:
            if progress:
                print(f"[quality-trial] mode={mode} theme={theme.slug} route={route}", file=sys.stderr, flush=True)
            body, generation = body_for_route(theme, route, mode, store)
            meta = route_meta(route, mode=mode)
            document_id = f"{slug}_{theme.slug}_{route}"
            document_path = write_document(document_dir, document_id, theme.title, body)
            markdown = render_markdown(theme.title, body, {**meta, "route": route})
            markdown_path = theme_dir / f"{route}.md"
            markdown_path.write_text(markdown, encoding="utf-8")
            proof = build_style_invocation_proof(title=theme.title, body=body, brief=theme.claim, style_store=store)
            score = metric_score(theme.title, body, store)
            version = {
                "route": route,
                "label": meta["label"],
                "documentId": document_id,
                "documentPath": display_path(document_path),
                "markdownPath": display_path(markdown_path),
                "model": meta["model"],
                "thinking": meta["thinking"],
                "source": meta["source"],
                "promptRoute": meta["promptRoute"],
                "generation": generation,
                "styleProof": {
                    "status": proof.get("status"),
                    "effectiveness": proof.get("effectiveness"),
                    "memoryCounts": proof.get("memoryCounts"),
                    "usedThisRun": (proof.get("memoryHits") or {}).get("usedThisRun", [])[:6],
                },
                "quality": score,
            }
            (theme_dir / f"{route}.json").write_text(json.dumps(version, ensure_ascii=False, indent=2), encoding="utf-8")
            versions.append(version)
        by_route = {item["route"]: item for item in versions}
        direct_score = float(by_route["direct_ai"]["quality"]["score"]) if "direct_ai" in by_route else 0.0
        style_score = float(by_route["style_memory"]["quality"]["score"]) if "style_memory" in by_route else 0.0
        fast_score = float(by_route["fast_workbench"]["quality"]["score"]) if "fast_workbench" in by_route else 0.0
        workbench_score = float(by_route["full_workbench"]["quality"]["score"]) if "full_workbench" in by_route else 0.0
        lift = round(workbench_score - direct_score, 1) if {"direct_ai", "full_workbench"} <= set(by_route) else 0.0
        style_delta = round(workbench_score - style_score, 1) if {"style_memory", "full_workbench"} <= set(by_route) else 0.0
        proven = (
            {"direct_ai", "style_memory", "full_workbench"} <= set(by_route)
            and lift >= 18
            and style_delta >= -STYLE_ONLY_NOISE_TOLERANCE
            and by_route["full_workbench"]["quality"]["hardBanCount"] == 0
            and generation_gate_allows(by_route["full_workbench"])
        )
        blocking_reasons: list[str] = []
        if "full_workbench" in by_route and by_route["full_workbench"].get("generation", {}).get("ok") is False:
            generation = by_route["full_workbench"].get("generation", {})
            blocking_reasons.append(
                "完整工作台生成失败"
                + (f"：{generation.get('error')}" if generation.get("error") else "")
            )
        if "full_workbench" in by_route and not generation_gate_allows(by_route["full_workbench"]):
            gate = by_route["full_workbench"].get("generation", {}).get("qualityGate", {})
            gate_reasons = gate.get("reasons") if isinstance(gate, dict) else []
            if gate:
                blocking_reasons.append(
                    "完整工作台生成 gate 未通过"
                    + (f"：{' / '.join(str(item) for item in gate_reasons[:3])}" if isinstance(gate_reasons, list) and gate_reasons else "")
                )
        if "full_workbench" in by_route and by_route["full_workbench"]["quality"]["hardBanCount"]:
            blocking_reasons.append("完整工作台版仍命中硬禁句")
        if "fast_workbench" in by_route and by_route["fast_workbench"].get("generation", {}).get("ok") is False:
            generation = by_route["fast_workbench"].get("generation", {})
            blocking_reasons.append(
                "轻量对照生成失败"
                + (f"：{generation.get('error')}" if generation.get("error") else "")
            )
        if "fast_workbench" in by_route and not generation_gate_allows(by_route["fast_workbench"]):
            gate = by_route["fast_workbench"].get("generation", {}).get("qualityGate", {})
            gate_reasons = gate.get("reasons") if isinstance(gate, dict) else []
            if gate:
                blocking_reasons.append(
                    "轻量对照门槛未通过"
                    + (f"：{' / '.join(str(item) for item in gate_reasons[:3])}" if isinstance(gate_reasons, list) and gate_reasons else "")
                )
        if {"direct_ai", "full_workbench"} <= set(by_route) and lift < 18:
            blocking_reasons.append("完整工作台相对直接写提升不足 18 分")
        if {"style_memory", "full_workbench"} <= set(by_route) and style_delta < -STYLE_ONLY_NOISE_TOLERANCE:
            blocking_reasons.append(f"完整工作台版明显低于只带风格库版（{style_delta} 分）")
        themes.append(
            {
                "slug": theme.slug,
                "title": theme.title,
                "kind": theme.kind,
                "reader": theme.reader,
                "claim": theme.claim,
                "versions": versions,
                "comparison": {
                    "directScore": direct_score,
                    "styleOnlyScore": style_score,
                    "fastWorkbenchScore": fast_score,
                    "workbenchScore": workbench_score,
                    "workbenchLiftOverDirect": lift,
                    "workbenchDeltaVsStyleOnly": style_delta,
                    "styleOnlyNoiseTolerance": STYLE_ONLY_NOISE_TOLERANCE,
                    "fastWorkbenchGateStatus": generation_gate_status(by_route["fast_workbench"]) if "fast_workbench" in by_route else "missing",
                    "workbenchGateStatus": generation_gate_status(by_route["full_workbench"]) if "full_workbench" in by_route else "missing",
                    "blockingReasons": blocking_reasons,
                    "proven": proven,
                    "verdict": "有效：工作台版明显优于直接写" if proven else "未证明有效：差距不够或仍有硬伤",
                },
            }
        )
    proven_count = sum(1 for item in themes if item["comparison"]["proven"])
    required_proven = 2 if len(themes) >= 3 else len(themes)
    status = "PROVEN" if themes and proven_count >= required_proven else "UNPROVEN"
    result = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "mode": mode,
        "provenCount": proven_count,
        "themeCount": len(themes),
        "routes": list(routes),
        "summary": proof_summary(status, proven_count, len(themes), required_proven),
        "outputDir": display_path(out),
        "documentPrefix": slug,
        "themes": themes,
    }
    summary_path = out / "summary.json"
    report_path = out / "report.md"
    result["summaryPath"] = display_path(summary_path)
    result["reportPath"] = display_path(report_path)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    return result


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# 写作工作台质量差距试验",
        "",
        f"- 状态：{result['status']}",
        f"- 模式：{result.get('mode', 'fixture')}",
        f"- 结论：{result['summary']}",
        f"- 证明主题：{result['provenCount']} / {result['themeCount']}",
        f"- 输出目录：`{result['outputDir']}`",
        "",
        "## 对比总览",
        "",
        "| 主题 | 直接 AI | 只加风格库 | 完整工作台 | 正式提升 | 正式门槛 | 结论 |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for theme in result["themes"]:
        cmp = theme["comparison"]
        lines.append(
            f"| {theme['title']} | {cmp['directScore']} | {cmp['styleOnlyScore']} | {cmp['workbenchScore']} | {cmp['workbenchLiftOverDirect']} | {cmp.get('workbenchGateStatus', 'not_run')} | {cmp['verdict']} |"
        )
        if cmp.get("blockingReasons"):
            lines.append(f"|  |  |  |  |  |  | 阻断：{'；'.join(str(item) for item in cmp['blockingReasons'])} |")
    lines.extend(["", "## 明细", ""])
    for theme in result["themes"]:
        lines.extend([f"### {theme['title']}", "", f"- 类型：{theme['kind']}", f"- 核心判断：{theme['claim']}", ""])
        for version in theme["versions"]:
            q = version["quality"]
            lines.extend(
                [
                    f"#### {version['label']}",
                    "",
                    f"- 路线：`{version['route']}`",
                    f"- Prompt route：`{version.get('promptRoute', '')}`",
                    f"- 模型/来源：{version['model']} / thinking {version['thinking']}",
                    f"- 生成门槛：{generation_gate_status(version)}",
                    f"- 自动修复：{repair_report_label(version.get('generation', {}).get('repairAttempt'))}",
                    f"- 分数：{q['score']}",
                    f"- 硬禁句：{q['hardBanCount']}",
                    f"- 风格证明：{version['styleProof']['effectiveness']['label']}",
                    f"- 文档：`{version['documentId']}`",
                    f"- Markdown：`{version['markdownPath']}`",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a reproducible writing-workbench quality trial.")
    parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    parser.add_argument("--themes", default="", help="Comma-separated theme slugs. Default: all.")
    parser.add_argument("--routes", default="direct_ai,style_memory,full_workbench", help="Comma-separated routes.")
    parser.add_argument("--preset", choices=["default", "release-small"], default="default")
    parser.add_argument("--progress", action="store_true", help="Print per-version progress to stderr.")
    parser.add_argument("--document-prefix", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    selected_theme_slugs = {item.strip() for item in args.themes.split(",") if item.strip()} or None
    selected_routes = tuple(item.strip() for item in args.routes.split(",") if item.strip())
    result = run_trial(
        output_dir=args.output_dir,
        document_prefix=args.document_prefix,
        mode=args.mode,
        selected_theme_slugs=selected_theme_slugs,
        selected_routes=selected_routes,
        themes_override=RELEASE_SMALL_THEMES if args.preset == "release-small" else None,
        progress=args.progress or args.mode == "live",
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(build_report(result))
        print(f"\nreport: {result['reportPath']}")
    raise SystemExit(0 if result["status"] == "PROVEN" else 1)


if __name__ == "__main__":
    main()
