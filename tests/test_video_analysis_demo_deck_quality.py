from __future__ import annotations

import unittest
import zipfile
from tempfile import NamedTemporaryFile
from unittest import mock

from tools.inline_editor_server import (
    assess_demo_deck_quality,
    build_video_demo_deck,
    build_video_deck_pptx,
    build_video_summary_card,
    build_opinion_argument_timeline,
    build_video_deck_markdown,
    classify_video_route_kind,
    demo_deck_has_frame_timing_issue,
    localize_video_copy_batch,
    normalize_demo_deck_slide_roles,
    video_deck_template_profile,
    video_slide_has_non_template_speaker_line,
    video_slide_has_raw_evidence,
)


def make_slide(index: int, *, frame: str = "", quote: str = "原字幕里能证明这一页发生了具体操作。") -> dict[str, str | int]:
    return {
        "index": index,
        "title": f"第 {index} 个操作节点",
        "role": f"节点{index}",
        "frameUrl": frame,
        "frameKind": "screenshot" if frame else "none",
        "action": "这里说明画面里实际发生的具体操作，不是泛泛总结。",
        "meaning": "这一页能解释观众为什么要继续看下去，也能支撑后面的选择判断。",
        "speakerNote": "讲的时候直接说这个操作解决了什么卡点。",
        "proof": "这页证明这个步骤不是装饰，而是影响后面结果验收的关键条件。",
        "audienceTakeaway": "观众需要带走一个判断：先确认这个条件，再继续下一步。",
        "productDimension": "核心流程",
        "productQuestion": "要跑通它，关键步骤是什么？",
        "productAnswer": "先确认这个条件，再继续下一步，后面的结果才有判断价值。",
        "sourceQuote": quote,
        "evidenceMode": "subtitle-led",
    }


class VideoAnalysisDemoDeckQualityTest(unittest.TestCase):
    def test_beginner_ai_video_guide_routes_as_tutorial(self) -> None:
        route = classify_video_route_kind("AI Video for Complete Beginners (2026 Starter Guide)", "")
        self.assertEqual(route, "tutorial")

    def test_ai_tools_list_routes_as_review(self) -> None:
        route = classify_video_route_kind("The Only AI Tools You Need in 2026 | Beginner Friendly Tutorial", "")
        self.assertEqual(route, "review")

    def test_ai_basics_misconception_routes_as_opinion(self) -> None:
        route = classify_video_route_kind("99% of Beginners Don't Know the Basics of AI", "")
        self.assertEqual(route, "opinion")

    def test_music_video_is_marked_unsuitable_instead_of_fake_demo_deck(self) -> None:
        timeline = [
            {
                "start": 18,
                "timeLabel": "00:18",
                "summary": "Never gonna give you up, never gonna let you down.",
                "transcriptExcerpt": "Never gonna give you up, never gonna let you down.",
                "frameUrl": "/api/video-analysis-file?path=/tmp/frame-001.jpg",
            },
            {
                "start": 141,
                "timeLabel": "02:21",
                "summary": "Never gonna run around and desert you.",
                "transcriptExcerpt": "Never gonna run around and desert you.",
                "frameUrl": "/api/video-analysis-file?path=/tmp/frame-002.jpg",
            },
        ]
        summary = build_video_summary_card(
            result={"title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)"},
            info_payload={"title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)"},
            analysis={"content_outline": ["歌词和画面为主。"]},
            timeline=timeline,
        )
        self.assertEqual(summary["contentSuitability"]["status"], "unsuitable")
        deck = build_video_demo_deck(
            title="Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/api/video-analysis-file?path=/tmp/source.mp4", "localPath": "/tmp/source.mp4"},
        )

        self.assertEqual(deck["slides"], [])
        self.assertEqual(deck["demoDeckQuality"]["status"], "blocked")
        self.assertIn("音乐", deck["demoDeckQuality"]["issues"][0])

    def test_too_short_low_material_video_is_marked_unsuitable(self) -> None:
        timeline = [
            {
                "start": 1,
                "timeLabel": "00:01",
                "summary": "好了，",
                "transcriptExcerpt": "好了，",
                "frameUrl": "/api/video-analysis-file?path=/tmp/zoo-001.jpg",
            }
        ]
        summary = build_video_summary_card(
            result={"title": "Me at the zoo"},
            info_payload={"title": "Me at the zoo"},
            analysis={},
            timeline=timeline,
        )
        self.assertEqual(summary["contentSuitability"]["status"], "unsuitable")
        self.assertIn("信息太少", summary["contentSuitability"]["reason"])

        deck = build_video_demo_deck(
            title="Me at the zoo",
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/api/video-analysis-file?path=/tmp/source.mp4", "localPath": "/tmp/source.mp4"},
            transcript_quality={"level": "strong", "label": "字幕", "usable": True},
        )
        self.assertEqual(deck["slides"], [])
        self.assertEqual(deck["demoDeckQuality"]["status"], "blocked")

    def test_no_transcript_video_does_not_generate_fake_demo_cards(self) -> None:
        timeline = [
            {
                "start": 0,
                "timeLabel": "00:00",
                "summary": "TED logo",
                "transcriptExcerpt": "未拿到字幕，只能先看标题和画面。",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-000.jpg",
            },
            {
                "start": 180,
                "timeLabel": "03:00",
                "summary": "speaker on stage",
                "transcriptExcerpt": "未拿到字幕，只能先看标题和画面。",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-180.jpg",
            },
            {
                "start": 360,
                "timeLabel": "06:00",
                "summary": "speaker continues",
                "transcriptExcerpt": "未拿到字幕，只能先看标题和画面。",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-360.jpg",
            },
        ]
        summary = build_video_summary_card(
            result={"title": "What Sitting All Day Does to Your Brain and Body | Keith Diaz | TED"},
            info_payload={"title": "What Sitting All Day Does to Your Brain and Body | Keith Diaz | TED"},
            analysis={},
            timeline=timeline,
        )
        deck = build_video_demo_deck(
            title="What Sitting All Day Does to Your Brain and Body | Keith Diaz | TED",
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/video.mp4", "watchUrl": "https://example.com"},
            transcript_quality={"level": "none", "label": "无字幕", "usable": False},
        )

        self.assertEqual(deck["slides"], [])
        self.assertEqual(deck["demoDeckQuality"]["status"], "blocked")
        self.assertIn("缺少可用字幕", deck["demoDeckQuality"]["issues"][0])
        self.assertNotIn("先抛出问题", deck["deckMarkdown"])
        self.assertNotIn("拿出证据", deck["deckMarkdown"])

    def test_ted_talk_with_subtitles_uses_talk_specific_deck_not_product_template(self) -> None:
        timeline = [
            {
                "start": 0,
                "timeLabel": "00:00",
                "summary": "演讲者从夏令营工作说起：身体很累，但精神不空。",
                "transcriptExcerpt": "My favorite job ever was as a summer-camp counselor. At the end of the day, I was physically tired but not mentally drained.",
                "writingValue": "用亲身经历把久坐带来的疲惫和真正运动后的疲惫区分开。",
                "quoteCandidate": "physically tired but not mentally drained",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-000.jpg",
            },
            {
                "start": 180,
                "timeLabel": "03:00",
                "summary": "他说现代工作把很多人固定在椅子上，身体不动但脑子反而更累。",
                "transcriptExcerpt": "Most of us spend much of our day sitting, and many people still feel tired at the end of it.",
                "writingValue": "把问题从个人感受推到现代工作方式。",
                "quoteCandidate": "spend much of our day sitting",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-180.jpg",
            },
            {
                "start": 360,
                "timeLabel": "06:00",
                "summary": "研究对比久坐和走动后的大脑与身体状态。",
                "transcriptExcerpt": "After 20 minutes of sitting and after 20 minutes of walking, the scans show different activity patterns.",
                "writingValue": "这里开始拿实验图像和对比证据支撑判断。",
                "quoteCandidate": "After 20 minutes of sitting and after 20 minutes of walking",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-360.jpg",
            },
            {
                "start": 540,
                "timeLabel": "09:00",
                "summary": "结尾把建议落到日常动作：别等运动时间，先减少连续久坐。",
                "transcriptExcerpt": "The point is not only exercise. Breaking up sitting time changes how your brain and body feel.",
                "writingValue": "最后的行动不是喊口号，而是把久坐切碎。",
                "quoteCandidate": "Breaking up sitting time changes how your brain and body feel",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-540.jpg",
            },
        ]
        title = "What Sitting All Day Does to Your Brain and Body | Keith Diaz | TED"
        summary = build_video_summary_card(
            result={"title": title},
            info_payload={"title": title},
            analysis={},
            timeline=timeline,
        )
        deck = build_video_demo_deck(
            title=title,
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/video.mp4", "watchUrl": "https://example.com"},
            transcript_quality={"level": "strong", "label": "字幕", "usable": True},
        )

        combined = " ".join(
            str(slide.get(key) or "")
            for slide in deck["slides"]
            for key in ("title", "role", "action", "meaning", "speakerNote", "productDimension", "productQuestion", "productAnswer")
        )
        self.assertEqual(deck["templateKey"], "opinion")
        self.assertGreaterEqual(len(deck["slides"]), 4)
        self.assertNotRegex(combined, r"模型进步|产品是什么|谁会用|跑通证据|工程入口|CLAUDE|终端")
        self.assertNotRegex(combined, r"这段有可回看的证据|先看证据|拿出证据|继续看证据|补充证据|补一条证据")
        self.assertNotRegex(
            combined,
            r"把支撑判断的例子|先把这条视频要反驳|最后把前面的材料|"
            r"观点视频不能先堆信息|判断要站住|真正的变化，往往藏在这个转折里|"
            r"读者能复述|判断不是泛泛总结",
        )
        self.assertRegex(combined, r"夏令营|久坐|走动|大脑|身体|研究|证据")
        self.assertTrue(all(slide.get("sourceQuote") for slide in deck["slides"]))
        self.assertEqual(deck["demoDeckQuality"]["status"], "ready")

    def test_demo_deck_prefers_unused_keyframes_when_nearest_frame_repeats(self) -> None:
        title = "What Sitting All Day Does to Your Brain and Body | Keith Diaz | TED"
        timeline = [
            {
                "start": 4.3,
                "timeLabel": "00:04",
                "summary": "开场先用夏令营经历区分身体累和脑子累。",
                "transcriptExcerpt": "My favorite job ever was as a summer-camp counselor. I was physically tired but not mentally drained.",
                "writingValue": "用个人经历打开久坐问题。",
                "quoteCandidate": "physically tired but not mentally drained",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-000.jpg",
            },
            {
                "start": 89.6,
                "timeLabel": "01:29",
                "summary": "演讲者转入现代人久坐的工作状态。",
                "transcriptExcerpt": "Most of us spend much of our day sitting, and still feel tired at the end of it.",
                "writingValue": "把个人感受推进到现代工作方式。",
                "quoteCandidate": "spend much of our day sitting",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-000.jpg",
            },
            {
                "start": 174.6,
                "timeLabel": "02:54",
                "summary": "进入实验和研究对比。",
                "transcriptExcerpt": "The scans show different activity patterns after sitting and after walking.",
                "writingValue": "拿实验图像支撑判断。",
                "quoteCandidate": "different activity patterns",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-180.jpg",
            },
            {
                "start": 349.2,
                "timeLabel": "05:49",
                "summary": "结尾落到打断连续久坐。",
                "transcriptExcerpt": "Breaking up sitting time changes how your brain and body feel.",
                "writingValue": "把建议落到可执行动作。",
                "quoteCandidate": "Breaking up sitting time",
                "frameUrl": "/api/video-analysis-file?path=/tmp/ted-360.jpg",
            },
        ]
        summary = build_video_summary_card(
            result={"title": title},
            info_payload={"title": title},
            analysis={},
            timeline=timeline,
        )
        summary["frames"] = [
            {"timestamp": 0.0, "label": "00:00 关键帧", "url": "/api/video-analysis-file?path=/tmp/ted-000.jpg"},
            {"timestamp": 180.0, "label": "03:00 关键帧", "url": "/api/video-analysis-file?path=/tmp/ted-180.jpg"},
            {"timestamp": 360.0, "label": "06:00 关键帧", "url": "/api/video-analysis-file?path=/tmp/ted-360.jpg"},
            {"timestamp": 540.0, "label": "09:00 关键帧", "url": "/api/video-analysis-file?path=/tmp/ted-540.jpg"},
        ]
        deck = build_video_demo_deck(
            title=title,
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/video.mp4", "watchUrl": "https://example.com"},
            transcript_quality={"level": "strong", "label": "字幕", "usable": True},
        )

        frame_urls = [slide.get("frameUrl") for slide in deck["slides"] if slide.get("frameKind") == "screenshot"]
        self.assertEqual(len(set(frame_urls)), len(frame_urls))
        self.assertEqual(deck["demoDeckQuality"]["status"], "needs_work")
        self.assertFalse(any("时间点偏离" in item for item in deck["demoDeckQuality"]["issues"]))
        self.assertTrue(any("缺画面" in item for item in deck["demoDeckQuality"]["issues"]))
        self.assertFalse(demo_deck_has_frame_timing_issue({"frames": summary["frames"], "demoDeck": deck}))

    def test_demo_deck_accepts_targeted_keyframes_near_slide_times(self) -> None:
        title = "What Sitting All Day Does to Your Brain and Body | Keith Diaz | TED"
        timeline = [
            {
                "start": 4.3,
                "timeLabel": "00:04",
                "summary": "开场先用夏令营经历区分身体累和脑子累。",
                "transcriptExcerpt": "My favorite job ever was as a summer-camp counselor. I was physically tired but not mentally drained.",
                "writingValue": "用个人经历打开久坐问题。",
                "quoteCandidate": "physically tired but not mentally drained",
                "frameUrl": "/api/video-analysis-file?path=/tmp/target-004.jpg",
            },
            {
                "start": 89.6,
                "timeLabel": "01:29",
                "summary": "演讲者转入现代人久坐的工作状态。",
                "transcriptExcerpt": "Most of us spend much of our day sitting, and still feel tired at the end of it.",
                "writingValue": "把个人感受推进到现代工作方式。",
                "quoteCandidate": "spend much of our day sitting",
                "frameUrl": "/api/video-analysis-file?path=/tmp/target-090.jpg",
            },
            {
                "start": 174.6,
                "timeLabel": "02:54",
                "summary": "进入实验和研究对比。",
                "transcriptExcerpt": "The scans show different activity patterns after sitting and after walking.",
                "writingValue": "拿实验图像支撑判断。",
                "quoteCandidate": "different activity patterns",
                "frameUrl": "/api/video-analysis-file?path=/tmp/target-175.jpg",
            },
            {
                "start": 349.2,
                "timeLabel": "05:49",
                "summary": "结尾落到打断连续久坐。",
                "transcriptExcerpt": "Breaking up sitting time changes how your brain and body feel.",
                "writingValue": "把建议落到可执行动作。",
                "quoteCandidate": "Breaking up sitting time",
                "frameUrl": "/api/video-analysis-file?path=/tmp/target-349.jpg",
            },
        ]
        summary = build_video_summary_card(
            result={"title": title},
            info_payload={"title": title},
            analysis={},
            timeline=timeline,
        )
        summary["frames"] = [
            {"timestamp": 4.0, "label": "00:04 关键帧", "url": "/api/video-analysis-file?path=/tmp/target-004.jpg"},
            {"timestamp": 90.0, "label": "01:30 关键帧", "url": "/api/video-analysis-file?path=/tmp/target-090.jpg"},
            {"timestamp": 175.0, "label": "02:55 关键帧", "url": "/api/video-analysis-file?path=/tmp/target-175.jpg"},
            {"timestamp": 349.0, "label": "05:49 关键帧", "url": "/api/video-analysis-file?path=/tmp/target-349.jpg"},
        ]
        deck = build_video_demo_deck(
            title=title,
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/video.mp4", "watchUrl": "https://example.com"},
            transcript_quality={"level": "strong", "label": "字幕", "usable": True},
        )

        deltas = [float(slide.get("frameDeltaSeconds") or 999) for slide in deck["slides"]]
        self.assertTrue(all(delta <= 2.0 for delta in deltas))
        self.assertFalse(any("时间点偏离" in item for item in deck["demoDeckQuality"]["issues"]))
        self.assertFalse(demo_deck_has_frame_timing_issue({"frames": summary["frames"], "demoDeck": deck}))

    def test_long_talk_with_enough_material_is_not_marked_ready_with_only_three_pages(self) -> None:
        slides = [
            {
                **make_slide(index, frame=f"frame-{index}.jpg"),
                "role": ["问题", "证据", "判断"][index - 1],
                "title": ["先抛出问题", "拿出证据", "收成判断"][index - 1],
                "productDimension": ["问题", "证据", "判断"][index - 1],
                "productQuestion": "这页回答观点视频里的哪个关键问题？",
                "productAnswer": "这页能支撑一个具体判断，不是泛泛总结。",
            }
            for index in range(1, 4)
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 3,
                "sourceItemCount": 6,
                "recommendedSlides": 4,
                "screenshotSlides": 3,
                "uniqueScreenshots": 3,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=False,
            route_kind="opinion",
        )

        self.assertEqual(quality["status"], "needs_work")
        self.assertTrue(any("页数偏少" in item for item in quality["issues"]))

    def test_claude_code_interview_does_not_fall_back_to_generic_opinion_cards(self) -> None:
        timeline = [
            {
                "start": 0,
                "timeLabel": "00:00",
                "summary": "Boris 说 Claude Code 不是为今天的模型设计，而是押注六个月后的模型能力。",
                "transcriptExcerpt": "You should not build for the model of today. Build for the model six months from now.",
                "writingValue": "产品判断是为未来几个月的模型能力预留空间。",
                "quoteCandidate": "Build for the model six months from now.",
                "frameUrl": "/api/video-analysis-file?path=/tmp/claude-000.jpg",
            },
            {
                "start": 420,
                "timeLabel": "07:00",
                "summary": "早期原型两天做完，内部工程师很快拿去处理真实代码任务。",
                "transcriptExcerpt": "The prototype took two days, and people internally started using it for real work.",
                "writingValue": "需求不是发布会想象，而是内部工程任务先跑通。",
                "quoteCandidate": "started using it for real work",
                "frameUrl": "/api/video-analysis-file?path=/tmp/claude-420.jpg",
            },
            {
                "start": 1500,
                "timeLabel": "25:00",
                "summary": "终端入口能直接碰到 git、bash 和测试，适合低风险工程动作。",
                "transcriptExcerpt": "The terminal gives you git, bash, tests, files, and a very direct interface.",
                "writingValue": "终端留下来，是因为它能直接进入工程环境。",
                "quoteCandidate": "git, bash, tests, files",
                "frameUrl": "/api/video-analysis-file?path=/tmp/claude-1500.jpg",
            },
        ]
        title = "Inside Claude Code With Its Creator Boris Cherny"
        summary = build_video_summary_card(
            result={"title": title},
            info_payload={"title": title},
            analysis={},
            timeline=timeline,
        )
        deck = build_video_demo_deck(
            title=title,
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/video.mp4", "watchUrl": "https://example.com"},
            transcript_quality={"level": "strong", "label": "字幕", "usable": True},
        )

        combined = " ".join(
            str(slide.get(key) or "")
            for slide in deck["slides"]
            for key in ("title", "action", "meaning", "speakerNote", "proof", "talkTrack")
        )
        self.assertNotRegex(combined, r"这段有可回看的证据|先看证据|拿出证据|继续看证据|补充证据|补一条证据")
        self.assertNotRegex(
            combined,
            r"把支撑判断的例子|先把这条视频要反驳|最后把前面的材料|"
            r"观点视频不能先堆信息|判断要站住|读者能复述|判断不是泛泛总结",
        )
        self.assertRegex(combined, r"六个月|模型|原型|真实|终端|git|bash|测试")

    def test_interview_argument_timeline_backfills_fourth_page_from_real_subtitle(self) -> None:
        windows = [
            [{"start": 0, "duration": 40, "text": "At Anthropic we do not build for the model of today. We build for the model six months from now."}],
            [{"start": 420, "duration": 40, "text": "The first prototype took two days, and people internally started using it for real work."}],
            [{"start": 900, "duration": 40, "text": "The terminal gives you git, bash, tests, files, and a very direct interface for engineering work."}],
            [{"start": 1500, "duration": 40, "text": "There is a trade-off in scaffolding: sometimes the model gets better and deletes the layer you built."}],
            [{"start": 2100, "duration": 40, "text": "The key is to keep the tool close to real workflows, not only to a chat interface."}],
        ]
        timeline = build_opinion_argument_timeline(
            title="Inside Claude Code With Its Creator Boris Cherny",
            windows=windows,
            frames=[],
            video_embed={"type": "local", "watchUrl": "https://example.com"},
            max_items=4,
        )

        self.assertGreaterEqual(len(timeline), 4)
        combined = " ".join(str(item.get(key) or "") for item in timeline for key in ("summary", "transcriptExcerpt", "writingValue", "quoteCandidate"))
        self.assertIn("scaffolding", combined)
        self.assertNotRegex(combined, r"补一条证据|继续看证据|拿出证据")

    def test_pptx_export_does_not_leak_internal_template_copy(self) -> None:
        slides = [
            make_slide(
                1,
                quote="Build for the model six months from now.",
            )
        ]
        payload = build_video_deck_pptx(
            title="Inside Claude Code With Its Creator Boris Cherny",
            source_status="已下载到本地 · 截图已保存",
            slides=slides,
        )
        self.assertTrue(payload.startswith(b"PK"))
        with NamedTemporaryFile(suffix=".pptx") as handle:
            handle.write(payload)
            handle.flush()
            with zipfile.ZipFile(handle.name) as package:
                names = package.namelist()
                slide_xml = "\n".join(
                    package.read(name).decode("utf-8", errors="ignore")
                    for name in names
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
        for required in ("视频讲稿", "判断", "画面", "讲这一页", "收束"):
            self.assertIn(required, slide_xml)
        for leaked in (
            "VIDEO MATERIAL DECK",
            "本地证据演示稿",
            "本地证据",
            "视频拆解稿",
            "先看画面，再讲判断",
            "发生了什么",
            "讲给观众听",
            "观众记住",
            "这一页回答什么",
            "Codex 视频材料",
        ):
            self.assertNotIn(leaked, slide_xml)

    def test_deck_template_profiles_are_route_specific(self) -> None:
        tutorial = video_deck_template_profile(route_kind="tutorial", is_tutorial=True)
        review = video_deck_template_profile(route_kind="review", is_tutorial=False)
        opinion = video_deck_template_profile(route_kind="opinion", is_tutorial=False)

        self.assertEqual(tutorial["label"], "教程拆解")
        self.assertEqual(review["label"], "工具评测")
        self.assertEqual(opinion["label"], "观点拆解")
        self.assertIn("操作步骤", tutorial["spine"])
        self.assertIn("选择标准", review["spine"])
        self.assertIn("转折", opinion["spine"])

    def test_deck_markdown_exposes_template_and_slide_roles(self) -> None:
        template = video_deck_template_profile(route_kind="review", is_tutorial=False)
        markdown = build_video_deck_markdown(
            headline="工具评测拆解",
            source_status="已下载到本地。",
            evidence_note="证据：字幕和截图一起用。",
            deck_template=template,
            slides=[
                {
                    "index": 1,
                    "title": "谁会用",
                    "timeLabel": "00:00",
                    "role": "场景",
                    "productQuestion": "谁真的需要它？",
                    "productAnswer": "需要在真实项目里让 AI 接手一部分开发的人。",
                    "action": "开场先说明目标用户。",
                    "evidence": "原字幕说明了目标用户。",
                    "proof": "先让观众判断自己是不是目标用户。",
                    "talkTrack": "先讲适用场景，再看功能。",
                }
            ],
        )

        self.assertIn("> 类型：工具评测", markdown)
        self.assertIn("> 主线：适用场景 -> 核心功能", markdown)
        self.assertIn("位置：场景", markdown)
        self.assertIn("- 画面：开场先说明目标用户。", markdown)
        self.assertIn("- 这页留下：先让观众判断自己是不是目标用户。", markdown)
        self.assertIn("- 讲法：先讲适用场景，再看功能。", markdown)

    def test_notes_over_reused_screenshots_without_blocking_tutorial_deck(self) -> None:
        slides = [
            make_slide(1, frame="frame-a.jpg"),
            make_slide(2, frame="frame-a.jpg"),
            make_slide(3, frame="frame-b.jpg"),
            make_slide(4, frame="frame-b.jpg"),
            make_slide(5, frame="frame-c.jpg"),
            make_slide(6, frame="frame-c.jpg"),
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 6,
                "screenshotSlides": 6,
                "uniqueScreenshots": 3,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=True,
            route_kind="tutorial",
        )

        self.assertNotIn("截图区分度不够", " ".join(quality["issues"]))
        self.assertTrue(any("截图区分度有限" in item for item in quality["strengths"]))

    def test_blocks_missing_source_quote_for_subtitle_led_deck(self) -> None:
        slides = [make_slide(index, frame=f"frame-{index}.jpg", quote="") for index in range(1, 5)]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 4,
                "screenshotSlides": 4,
                "uniqueScreenshots": 4,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=False,
            route_kind="review",
        )

        self.assertEqual(quality["status"], "needs_work")
        self.assertTrue(any("缺少原字幕" in item for item in quality["issues"]))

    def test_review_deck_rejects_tutorial_step_template(self) -> None:
        roles = ["入口", "准备", "操作", "连接", "验收"]
        dimensions = ["产品是什么", "谁会用", "核心能力", "真实结果", "选择门槛"]
        slides = []
        for index, role in enumerate(roles, start=1):
            slides.append(
                {
                    **make_slide(index, frame=f"frame-{index}.jpg"),
                    "role": role,
                    "title": f"第 {index} 个步骤",
                    "productDimension": dimensions[index - 1],
                    "productQuestion": "这页回答产品评测里的哪个问题？",
                    "productAnswer": "这页有产品判断，但页面角色仍然像教程步骤，不像评测结构。",
                }
            )
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 5,
                "screenshotSlides": 5,
                "uniqueScreenshots": 5,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=False,
            route_kind="review",
        )

        self.assertEqual(quality["status"], "needs_work")
        self.assertIn("评测视频被拆成教程步骤", " ".join(quality["issues"]))
        self.assertIn("按视频类型重拆", quality["nextBestUse"])
        self.assertTrue(quality["routeRoleIssue"])

    def test_opinion_deck_rejects_review_template(self) -> None:
        roles = ["场景", "功能", "结果", "门槛"]
        slides = [
            {
                **make_slide(index, frame=f"frame-{index}.jpg"),
                "role": role,
                "title": f"评测页 {index}",
                "productDimension": ["问题", "证据", "转折", "判断"][index - 1],
                "productQuestion": "这页回答观点稿里的哪个问题？",
                "productAnswer": "这页虽然有观点字段，但角色仍然在评测产品功能，不像论证结构。",
            }
            for index, role in enumerate(roles, start=1)
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 4,
                "screenshotSlides": 4,
                "uniqueScreenshots": 4,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=False,
            route_kind="opinion",
        )

        self.assertEqual(quality["status"], "needs_work")
        self.assertIn("观点视频被拆成工具评测", " ".join(quality["issues"]))

    def test_rejects_repeated_short_english_subtitle_fragments_as_evidence(self) -> None:
        self.assertFalse(
            video_slide_has_raw_evidence(
                "calls, transcription. calls, transcription. calls, transcription.",
                route_kind="review",
            )
        )
        self.assertTrue(
            video_slide_has_raw_evidence(
                "meeting summaries, content calendars, and brand guidelines can be generated from one prompt.",
                route_kind="review",
            )
        )

    def test_tutorial_speaker_line_can_reference_process_and_interface(self) -> None:
        self.assertTrue(
            video_slide_has_non_template_speaker_line(
                "先讲它替你处理哪一步，再进入界面。",
                route_kind="tutorial",
            )
        )

    def test_blocks_slides_without_viewer_or_writing_value(self) -> None:
        slides = [
            {
                **make_slide(index, frame=f"frame-{index}.jpg"),
                "meaning": "这一页展示了一个普通画面，内容本身比较完整。",
                "proof": "这一页展示了一个普通画面，内容本身比较完整。",
                "audienceTakeaway": "这一页展示了一个普通画面，内容本身比较完整。",
            }
            for index in range(1, 4)
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 3,
                "screenshotSlides": 3,
                "uniqueScreenshots": 3,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=False,
            route_kind="review",
        )

        self.assertEqual(quality["status"], "needs_work")
        self.assertTrue(any("写出什么判断" in item for item in quality["issues"]))

    def test_tutorial_summary_and_deck_expose_product_lens(self) -> None:
        timeline = [
            {
                "timeLabel": "00:00",
                "summary": "开场说明会演示双端互联，也会处理连不上。",
                "transcriptExcerpt": "这个视频给大家演示正常使用流程，以及大家反馈比较多的联系不上该怎么处理。",
                "writingValue": "教程价值在于覆盖正常流程和失败排查。",
                "frameUrl": "/frame-1.jpg",
            },
            {
                "timeLabel": "01:15",
                "summary": "进入面试前，先上传简历，再选择音频来源。",
                "transcriptExcerpt": "进入面试配置页以后需要上传简历，并选择输入输出设备。",
                "writingValue": "简历和音频源决定后面的回答有没有上下文。",
                "frameUrl": "/frame-2.jpg",
            },
            {
                "timeLabel": "03:47",
                "summary": "连接失败时，先打开连接地址，再按提示完成证书安装。",
                "transcriptExcerpt": "如果打不开，需要继续访问这个地址，然后完成证书安装。",
                "writingValue": "真实卡点在地址和证书，而不是功能按钮。",
                "frameUrl": "/frame-3.jpg",
            },
            {
                "timeLabel": "05:02",
                "summary": "开始语音识别，检查视频声音和自己的声音是否都进入消息列表。",
                "transcriptExcerpt": "看到视频声音和自己的话都进入消息列表，才算真的跑通。",
                "writingValue": "跑通要看真实结果，不是看页面状态。",
                "frameUrl": "/frame-4.jpg",
            },
        ]
        summary = build_video_summary_card(
            result={"title": "双端互联教程 - Offer IN AI 面试笔试助手"},
            info_payload={"title": "双端互联教程 - Offer IN AI 面试笔试助手"},
            analysis={},
            timeline=timeline,
        )
        deck = build_video_demo_deck(
            title="双端互联教程 - Offer IN AI 面试笔试助手",
            video_summary=summary,
            timeline=timeline,
            video_embed={"type": "local", "src": "/video.mp4", "watchUrl": "https://example.com"},
        )

        self.assertEqual(summary["productLens"]["productType"], "AI 面试/笔试辅助工具")
        self.assertIn("面试", summary["productLens"]["targetUser"])
        self.assertTrue(deck["productLens"]["mainFriction"])
        self.assertTrue(all(slide.get("productQuestion") for slide in deck["slides"]))
        self.assertTrue(all(slide.get("productAnswer") for slide in deck["slides"]))
        dimensions = {slide.get("productDimension") for slide in deck["slides"]}
        self.assertIn("失败门槛", dimensions)
        self.assertIn("跑通证据", dimensions)

    def test_tutorial_deck_quality_blocks_missing_product_lens(self) -> None:
        slides = [
            {
                **make_slide(index, frame=f"frame-{index}.jpg"),
                "productDimension": "",
                "productQuestion": "",
                "productAnswer": "",
            }
            for index in range(1, 4)
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 3,
                "screenshotSlides": 3,
                "uniqueScreenshots": 3,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=True,
            route_kind="tutorial",
        )

        self.assertEqual(quality["status"], "needs_work")

    def test_tutorial_deck_quality_blocks_one_note_product_dimensions(self) -> None:
        roles = ["入口", "准备", "操作", "验收"]
        slides = [
            {
                **make_slide(
                    index,
                    frame=f"frame-{index}.jpg",
                    quote="进入面试前，先上传简历，再选择音频来源，最后看消息列表里有没有真实转写结果。",
                ),
                "role": roles[index - 1],
                "productDimension": "核心流程",
                "productQuestion": "要跑通它，关键步骤是什么？",
                "productAnswer": "这一页只说明流程，但没有交代失败门槛、验收证据或适用边界。",
            }
            for index in range(1, 5)
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 4,
                "screenshotSlides": 4,
                "uniqueScreenshots": 4,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=True,
            route_kind="tutorial",
        )

        self.assertEqual(quality["status"], "needs_work")
        self.assertIn("产品拆解不完整", " ".join(quality["issues"]))
        self.assertIn("失败门槛", quality["missingProductDimensions"])
        self.assertIn("先补产品问题", quality["nextBestUse"])

    def test_role_normalization_does_not_overwrite_clear_tutorial_roles(self) -> None:
        slides = [
            {"role": "入口", "title": "这条视频排的是连接失败"},
            {"role": "准备", "title": "简历和声音源决定回答质量"},
            {"role": "设备", "title": "两台设备的分工要先讲清"},
        ]

        normalize_demo_deck_slide_roles(slides, is_tutorial=True, route_kind="tutorial")

        self.assertEqual([slide["role"] for slide in slides], ["入口", "准备", "设备"])

    def test_tutorial_deck_quality_blocks_step_summary_without_product_boundary(self) -> None:
        slides = [
            {
                **make_slide(1, frame="frame-1.jpg", quote="这次演示正常使用流程，也处理连不上。"),
                "role": "入口",
                "title": "这条视频排的是连接失败",
                "action": "开场先交代：这次不只是演示正常流程，也会处理连不上。",
                "meaning": "教程的价值不在功能列表，而在它有没有覆盖真实卡点。",
                "proof": "开场先讲这次要解决什么问题：怎么连上，连不上先查哪里。",
                "talkTrack": "别把这段当功能介绍看，它是在现场跑一次连接流程。",
                "audienceTakeaway": "先讲卡点，再讲功能。",
                "productDimension": "产品是什么",
                "productQuestion": "这到底是什么产品/方法？",
                "productAnswer": "这是 AI 面试辅助工具，重点是它在视频里完成的任务。",
            },
            {
                **make_slide(2, frame="frame-2.jpg", quote="进入面试前，先上传简历，再选择音频来源。"),
                "role": "准备",
                "title": "简历和声音源决定回答质量",
                "action": "进入面试前，先上传简历，再选清楚音频来源。",
                "meaning": "简历和声音源是后面回答的输入材料，给错了结果就没有上下文。",
                "proof": "进入配置页后，简历和音频源要先给对，后面的回答才有上下文。",
                "talkTrack": "简历和声音源给错，后面的回答就会飘。",
                "audienceTakeaway": "先把简历和音频源选好。",
                "productDimension": "核心流程",
                "productQuestion": "要跑通它，关键步骤是什么？",
                "productAnswer": "先接设备，再传简历和音频源，最后启动识别检查结果。",
            },
            {
                **make_slide(3, frame="frame-3.jpg", quote="连接失败时，先打开连接地址，再按提示完成证书安装。"),
                "role": "连接",
                "title": "地址和证书是第一关",
                "action": "连接失败时，先打开连接地址，再按提示把证书装完。",
                "meaning": "这一步把连不上拆成两个可执行检查：地址能不能打开，证书有没有走完。",
                "proof": "这里开始处理连接失败：打开地址，继续访问，把证书装完。",
                "talkTrack": "连不上先看地址和证书，再说别的。",
                "audienceTakeaway": "连不上先别重装。",
                "productDimension": "失败门槛",
                "productQuestion": "用户最可能卡在哪里？",
                "productAnswer": "最容易卡在地址、证书、防火墙和权限，不能只看按钮状态。",
            },
            {
                **make_slide(4, frame="frame-4.jpg", quote="看到视频声音和自己的话都进入消息列表，才算真的跑通。"),
                "role": "验收",
                "title": "跑通要看真实结果",
                "action": "开始识别以后，看视频声音和自己的话有没有进入消息列表。",
                "meaning": "跑通不是按钮亮了，而是结果真的进入工作流。",
                "proof": "真正的验收在消息列表：视频声音和你自己的话都要进去。",
                "talkTrack": "最后直接看结果有没有出来，不要只盯界面状态。",
                "audienceTakeaway": "真正跑通是视频声音和自己的声音都进入消息列表。",
                "productDimension": "跑通证据",
                "productQuestion": "怎样才算真的跑通？",
                "productAnswer": "真正跑通是视频声音和自己的声音都进入消息列表。",
            },
        ]
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 4,
                "screenshotSlides": 4,
                "uniqueScreenshots": 4,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=True,
            route_kind="tutorial",
        )

        self.assertIn("边界限制", quality["missingProductInsights"])
        self.assertFalse(any("边界限制" in item for item in quality["issues"]))
        self.assertTrue(any("边界限制" in item for item in quality["strengths"]))

    def test_tutorial_deck_quality_reports_demo_ready_next_use(self) -> None:
        dimensions = ["产品是什么", "谁会用", "核心流程", "失败门槛", "跑通证据", "限制"]
        roles = ["入口", "准备", "操作", "连接", "验收", "收束"]
        slides = []
        for index, dimension in enumerate(dimensions, start=1):
            slides.append(
                {
                    **make_slide(
                        index,
                        frame=f"frame-{index}.jpg",
                        quote="进入面试前，先上传简历，再选择音频来源，最后看消息列表里有没有真实转写结果。",
                    ),
                    "role": roles[index - 1],
                    "proof": "视频里能看到设备连接、简历上传和转写结果，这些画面能支撑这一页判断。",
                    "talkTrack": "讲的时候先说这一步解决什么卡点，再说观众应该怎么验收。",
                    "audienceTakeaway": "观众最后要带走一个动作：别只看连接成功，要看结果是否出现。",
                    "productDimension": dimension,
                    "productQuestion": {
                        "产品是什么": "这到底是什么产品/方法？",
                        "谁会用": "谁真的需要它？",
                        "核心流程": "要跑通它，关键步骤是什么？",
                        "失败门槛": "用户最可能卡在哪里？",
                        "跑通证据": "怎样才算真的跑通？",
                        "限制": "这条视频没有证明什么？",
                    }[dimension],
                    "productAnswer": {
                        "产品是什么": "这是一套双端互联流程，重点是把设备、简历和音频源接到同一条链路里。",
                        "谁会用": "需要一边面试一边接收辅助回答的人，尤其容易卡在 Windows 和 iPad 双端连接。",
                        "核心流程": "先接设备，再传简历和音频源，最后启动识别检查结果。",
                        "失败门槛": "最容易卡在地址、证书、防火墙和权限，不能只看按钮状态。",
                        "跑通证据": "真正跑通是视频声音和自己的声音都进入消息列表。",
                        "限制": "这条视频只证明这一套 Windows + iPad 场景，其他设备和网络环境仍要单独验证。",
                    }[dimension],
                }
            )
        quality = assess_demo_deck_quality(
            slides,
            {
                "slideCount": 4,
                "screenshotSlides": 4,
                "uniqueScreenshots": 4,
                "coverSlides": 0,
                "missingImages": 0,
            },
            is_tutorial=True,
            route_kind="tutorial",
        )

        self.assertEqual(quality["status"], "ready")
        self.assertIn("可直接做演示稿", quality["nextBestUse"])
        self.assertGreaterEqual(len(quality["coveredProductDimensions"]), 4)
        self.assertIn("边界限制", quality["coveredProductInsights"])

    def test_video_copy_localization_is_deterministic_by_default(self) -> None:
        items = {
            "0:summary": {"role": "summary", "text": "I use around 10 AI tools for 90% of my work."},
            "1:summary": {"role": "summary", "text": "Only Gemini can handle all four types of tasks."},
        }

        with mock.patch("tools.inline_editor_server.kimi_localize_video_copy_items") as remote:
            first = localize_video_copy_batch(title="AI tools", items=items)
            second = localize_video_copy_batch(title="AI tools", items=items)

        remote.assert_not_called()
        self.assertEqual(first, second)
        self.assertTrue(first["0:summary"])

if __name__ == "__main__":
    unittest.main()
