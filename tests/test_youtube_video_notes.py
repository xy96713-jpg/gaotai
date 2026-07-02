import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace

from tools import youtube_video_notes as yvn


class YoutubeVideoNotesTests(unittest.TestCase):
    def test_detect_platform(self):
        self.assertEqual(yvn.detect_platform("https://www.youtube.com/watch?v=abc"), "youtube")
        self.assertEqual(yvn.detect_platform("https://youtu.be/abc"), "youtube")
        self.assertEqual(yvn.detect_platform("https://www.bilibili.com/video/BV1xx411c7mD"), "bilibili")
        self.assertEqual(yvn.detect_platform("https://www.douyin.com/video/7123456789012345678"), "douyin")
        self.assertEqual(yvn.detect_platform("https://v.douyin.com/abc123/"), "douyin")
        self.assertEqual(yvn.detect_platform("https://example.com/video"), "generic")

    def test_default_browser_cookie_source_uses_chrome_for_supported_social_video_sites(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(yvn.default_browser_cookie_source("youtube"), "chrome")
            self.assertEqual(yvn.default_browser_cookie_source("bilibili"), "chrome")
            self.assertEqual(yvn.default_browser_cookie_source("douyin"), "chrome")
            self.assertIsNone(yvn.default_browser_cookie_source("generic"))

    def test_apply_cookie_options_can_disable_browser_cookies(self):
        opts = {}
        auth = yvn.apply_cookie_options(opts, "youtube", None, "none")

        self.assertEqual(auth, "disabled")
        self.assertNotIn("cookiesfrombrowser", opts)

    def test_download_policy_records_auth_runtime_and_local_video(self):
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir, "source.mp4")
            source.write_bytes(b"video")

            policy = yvn.download_policy_from_notes(
                platform="youtube",
                auth_note="browser:chrome",
                notes=[
                    "yt-dlp-frame-range:0-60s",
                    "yt-dlp-video-option:full-compatible",
                    "yt-dlp-video-strategy:youtube-client:ios",
                ],
                local_video_path=str(source),
                require_local_video=True,
            )

        self.assertEqual(policy["status"], "saved")
        self.assertEqual(policy["browserCookies"], "chrome")
        self.assertTrue(policy["required"])
        self.assertEqual(policy["localVideoBytes"], 5)
        self.assertIn("full-compatible", policy["strategies"])
        self.assertIn("youtube-client:ios", policy["strategies"])

    def test_build_comment_preview_keeps_small_safe_sample(self):
        preview = yvn.build_comment_preview(
            {
                "comments": [
                    {"author": "a", "text": "这条评论有具体反应", "like_count": 3},
                    {"author": "b", "text": ""},
                    {"author": "c", "text": "第二条评论"},
                ]
            },
            limit=2,
        )

        self.assertEqual(len(preview), 2)
        self.assertEqual(preview[0]["author"], "a")
        self.assertEqual(preview[0]["like_count"], 3)
        self.assertEqual(preview[1]["text"], "第二条评论")

    def test_parse_description_chapters(self):
        description = """
        一些介绍
        00:00 技术条件
        05:14 资本条件
        11:43 心理条件
        """

        chapters = yvn.parse_description_chapters(description)

        self.assertEqual(
            chapters,
            [
                {"start": 0, "title": "技术条件"},
                {"start": 314, "title": "资本条件"},
                {"start": 703, "title": "心理条件"},
            ],
        )

    def test_build_outline_sections_from_transcript_and_chapters(self):
        transcript = [
            {"text": "投资是一门生意", "start": 10.0, "duration": 1.0},
            {"text": "需要完整的系统", "start": 20.0, "duration": 1.0},
            {"text": "至少要有三到五年生活费", "start": 320.0, "duration": 1.0},
            {"text": "最难的是自律和耐心", "start": 720.0, "duration": 1.0},
        ]
        chapters = [
            {"start": 0, "title": "技术条件"},
            {"start": 314, "title": "资本条件"},
            {"start": 703, "title": "心理条件"},
        ]

        outline = yvn.build_outline_sections(transcript, chapters)

        self.assertEqual(len(outline), 3)
        self.assertEqual(outline[0]["title"], "技术条件")
        self.assertIn("投资是一门生意", outline[0]["summary"])
        self.assertEqual(outline[1]["title"], "资本条件")
        self.assertIn("三到五年生活费", outline[1]["summary"])
        self.assertEqual(outline[2]["title"], "心理条件")
        self.assertIn("自律和耐心", outline[2]["summary"])

    def test_analyze_with_rules_returns_channel_friendly_structure(self):
        payload = {
            "platform": "youtube",
            "title": "全职投资人，需要具备哪些条件？",
            "channel": "LEI",
            "duration_human": "12:34",
            "outline": [
                {"title": "技术条件", "start": 0, "summary": "先讲系统和方法"},
                {"title": "资本条件", "start": 314, "summary": "再讲生活费和本金"},
            ],
            "key_points": [
                "00:00 技术条件：先讲系统和方法",
                "05:14 资本条件：再讲生活费和本金",
            ],
            "transcript_preview": "[00:00] 投资是一门生意",
        }

        result = yvn.analyze_with_rules(payload)

        self.assertEqual(result["backend"], "rules")
        self.assertTrue(result["summary"])
        self.assertTrue(result["core_claim"])
        self.assertTrue(result["recommended_hook"])
        self.assertGreaterEqual(len(result["content_outline"]), 3)
        self.assertGreaterEqual(len(result["talking_points"]), 1)
        self.assertGreaterEqual(len(result["repurpose_angles"]), 2)
        self.assertGreaterEqual(len(result["hidden_premises"]), 1)
        self.assertGreaterEqual(len(result["creator_tactics"]), 2)
        self.assertGreaterEqual(len(result["channel_adaptation"]), 2)
        self.assertEqual(result["visual_timeline"], [])
        self.assertGreaterEqual(len(result["anti_ai_notes"]), 3)

    def test_build_fallback_angles_filters_noisy_key_point(self):
        angles = yvn.build_fallback_angles(
            {
                "title": "测试标题",
                "key_points": [
                    "00:00 片段 1：真正值钱的是它能不能替你吞掉前置整理工作。 后面还有一长串无关转写噪音 ..."
                ],
            }
        )

        self.assertIn("真正值钱的是它能不能替你吞掉前置整理工作", angles[0])
        self.assertNotIn("00:00", angles[0])
        self.assertNotIn("...", angles[0])

    def test_rules_analysis_uses_specific_claude_code_signal(self):
        payload = {
            "platform": "youtube",
            "title": "Inside Claude Code With Its Creator Boris Cherny",
            "channel": "Y Combinator",
            "duration_human": "50:10",
            "outline": [
                {"title": "Intro", "start": 0, "summary": "future model"},
                {"title": "The terminal", "start": 300, "summary": "terminal product"},
            ],
            "key_points": ["00:00 build for the model six months from now"],
            "transcript_plain": (
                "We do not build for the model of today. We build for the model six months from now. "
                "Claude Code started in a terminal because it was the cheapest thing to build."
            ),
            "transcript_preview": "[00:00] build for the model six months from now",
            "transcript_source": "yt-dlp-captions",
            "transcript_source_count": 120,
            "visual_notes": [],
        }

        result = yvn.analyze_with_rules(payload)

        self.assertIn("六个月后的能力", result["core_claim"])
        self.assertIn("终端", result["repurpose_angles"][1])
        self.assertIn("六个月后", result["talking_points"][0])
        self.assertIn("项目上下文", result["content_outline"][-1])
        self.assertEqual(result["editorial_decision"]["level"], "值得写")
        self.assertIn("写作要求", result["editorial_decision"]["brief"])
        self.assertNotIn("核心命题落在", result["core_claim"])
        self.assertNotIn("很多人看", result["recommended_hook"])
        self.assertNotRegex("\n".join(result["channel_adaptation"]), r"不是.{0,40}而是")
        self.assertNotRegex("\n".join(result["content_outline"]), r"不是.{0,40}而是")
        self.assertNotRegex("\n".join(result["talking_points"]), r"不是.{0,40}而是")

    def test_analyze_with_rules_detects_ted_talk_report(self):
        payload = {
            "url": "https://www.ted.com/talks/yoshua_bengio_the_catastrophic_risks_of_ai_and_a_safer_path",
            "platform": "generic",
            "title": "The catastrophic risks of AI — and a safer path",
            "channel": "Yoshua Bengio",
            "duration_human": "14:52",
            "description_preview": "TED2025 talk about AI risk",
            "outline": [],
            "key_points": [],
            "transcript_preview": "",
            "transcript_plain": (
                "My name is Yoshua Bengio. I want to talk about the catastrophic risks of AI. "
                "What I'm most worried about today is increasing agency of AI. "
                "Recent studies show deception, cheating, and self-preservation behavior. "
                "We call it Scientist AI. You just need to make good, trustworthy predictions."
            ),
        }

        result = yvn.analyze_with_rules(payload)

        self.assertEqual(result["report_type"], "talk")
        self.assertIn("talk_report", result)
        self.assertIn("creator_draft_pack", result)
        self.assertGreaterEqual(len(result["talk_report"]["summary"]), 3)
        self.assertGreaterEqual(len(result["talk_report"]["argument_chain"]), 3)
        self.assertGreaterEqual(len(result["talk_report"]["channel_angles"]), 3)
        self.assertGreaterEqual(len(result["creator_draft_pack"]["candidate_titles"]), 3)
        self.assertGreaterEqual(len(result["creator_draft_pack"]["opening_options"]), 3)

    def test_short_product_tutorial_does_not_use_talk_template(self):
        payload = {
            "url": "https://www.youtube.com/watch?v=qzq_-plz0bQ",
            "platform": "youtube",
            "title": "AI Subtitle Generator – Add Captions in SECONDS | CapCut Alternative",
            "channel": "VEED STUDIO",
            "duration_human": "0:26",
            "outline": [],
            "key_points": [
                "00:00 Let me show you how you can easily create captions like this using AI.",
                "00:04 All you need to do is head over to VEED and upload your video.",
                "00:07 Head over to Subtitles to auto-caption your video.",
                "00:11 Choose an engaging subtitle style and customize your captions.",
                "00:19 Click on Done to export your video.",
            ],
            "transcript_source": "yt-dlp-captions",
            "transcript_source_count": 18,
            "transcript_preview": "[00:00] Let me show you how you can easily create captions like this using AI.",
            "transcript_plain": (
                "Hey everyone. Let me show you how you can easily create captions like this using AI. "
                "All you need to do is head over to VEED and upload your video. "
                "In the editor, head over to Subtitles to auto-caption your video. "
                "Then check your transcript and choose an engaging subtitle style. "
                "Click Edit next to the preset to further customize your captions. "
                "You can add effects, one-click animations, and make them on-brand. "
                "When you're happy, click Done to export your video. Thank you so much for watching."
            ),
        }

        result = yvn.analyze_with_rules(payload)
        combined = "\n".join(
            [
                result["report_type"],
                result["core_claim"],
                result["recommended_hook"],
                "\n".join(result["content_outline"]),
                "\n".join(result["talking_points"]),
                "\n".join(result["repurpose_angles"]),
            ]
        )

        self.assertEqual(result["report_type"], "tutorial")
        self.assertIn("VEED", combined)
        self.assertIn("上传", combined)
        self.assertIn("字幕", combined)
        self.assertIn("导出", combined)
        self.assertNotIn("Claude Code", combined)
        self.assertNotIn("TED", combined)
        self.assertNotIn("公共议题", combined)

    def test_analyze_with_rules_includes_existing_visual_assets(self):
        result = yvn.analyze_with_rules(
            {
                "url": "https://www.youtube.com/watch?v=abc",
                "platform": "youtube",
                "title": "测试视频",
                "channel": "测试频道",
                "duration_human": "10:00",
                "description_preview": "",
                "outline": [],
                "key_points": [],
                "transcript_preview": "",
                "transcript_plain": "",
                "visual_assets": [
                    {"type": "thumbnail", "url": "https://example.com/cover.jpg", "source": "metadata-thumbnail"},
                    {"type": "frame", "path": "/tmp/frame-001.jpg", "source": "ffmpeg", "timestamp": 600},
                ],
            }
        )

        self.assertIn("封面", result["visual_timeline"][0])
        self.assertIn("10:00 关键帧", result["visual_timeline"][1])

    def test_describe_visual_asset_formats_frame_timestamp(self):
        self.assertEqual(yvn.describe_visual_asset({"type": "thumbnail"}), "封面")
        self.assertEqual(yvn.describe_visual_asset({"type": "frame", "timestamp": 125}), "02:05 关键帧")

    def test_can_download_audio_is_true_with_bundled_ffmpeg(self):
        self.assertTrue(yvn.can_download_audio())

    def test_extract_audio_from_video_returns_none_for_missing_source(self):
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.mp4"
            output = Path(temp_dir) / "audio.mp3"
            self.assertIsNone(yvn.extract_audio_from_video(missing, output))

    def test_extract_keyframes_uses_target_seconds_when_provided(self):
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            source_video = out_dir / "source.mp4"
            source_video.write_bytes(b"video")
            commands = []

            def fake_run(command, capture_output=True, text=True):
                commands.append(command)
                Path(command[-1]).write_bytes(b"frame")

                class Result:
                    returncode = 0
                    stderr = ""

                return Result()

            with patch("tools.youtube_video_notes.resolve_binary", return_value="/usr/bin/ffmpeg"), patch(
                "tools.youtube_video_notes.download_video_for_frames_with_auth", return_value=source_video
            ), patch("tools.youtube_video_notes.subprocess.run", side_effect=fake_run):
                assets, notes = yvn.extract_keyframes(
                    "https://example.com/video",
                    out_dir,
                    interval_seconds=180,
                    max_frames=5,
                    target_seconds=[0, 120, "04:00", 120],
                )

            self.assertEqual([asset["timestamp"] for asset in assets], [0.0, 120.0, 240.0])
            self.assertIn("frame-extraction-targeted", notes)
            self.assertEqual([command[command.index("-ss") + 1] for command in commands], ["0.0", "120.0", "240.0"])

    def test_cached_caption_files_can_be_reused_after_online_failure(self):
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            caption = out_dir / "abc.zh-Hans.vtt"
            caption.write_text(
                "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n第一句字幕\n\n00:00:04.000 --> 00:00:06.000\n第二句字幕\n",
                encoding="utf-8",
            )

            files = yvn.find_cached_caption_files(out_dir, "abc")
            items = yvn.extract_caption_transcript(files)

        self.assertEqual([path.name for path in files], ["abc.zh-Hans.vtt"])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["text"], "第一句字幕")

    def test_caption_file_selection_prefers_simplified_chinese_over_english(self):
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            (out_dir / "abc.en.vtt").write_text(
                "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nEnglish caption\n",
                encoding="utf-8",
            )
            (out_dir / "abc.zh-Hans-en.vtt").write_text(
                "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n简中文字幕\n",
                encoding="utf-8",
            )

            files = yvn.find_cached_caption_files(out_dir, "abc")
            items = yvn.extract_caption_transcript(files)

        self.assertEqual([path.name for path in files], ["abc.zh-Hans-en.vtt", "abc.en.vtt"])
        self.assertEqual(items[0]["text"], "简中文字幕")

    def test_download_audio_falls_back_to_video_when_audio_download_fails(self):
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            fallback_video = out_dir / "fallback.mp4"
            fallback_video.write_bytes(b"video")
            fallback_audio = out_dir / "audio-from-video.mp3"

            class FakeYoutubeDL:
                def __init__(self, _opts):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def download(self, _urls):
                    raise RuntimeError("audio failed")

            with patch("tools.youtube_video_notes.get_youtube_dl", return_value=FakeYoutubeDL), patch(
                "tools.youtube_video_notes.download_video_for_frames_with_auth", return_value=fallback_video
            ), patch(
                "tools.youtube_video_notes.extract_audio_from_video", return_value=fallback_audio
            ):
                result = yvn.download_audio_for_transcription_with_auth("https://example.com/video", out_dir)

        self.assertEqual(result, fallback_audio)

    def test_parse_json_object_from_text_handles_wrapper_text(self):
        parsed = yvn.parse_json_object_from_text('before {"summary":"x","talking_points":[] } after')
        self.assertEqual(parsed["summary"], "x")

    def test_remove_user_banned_report_phrasing_blocks_binary_frame(self):
        cleaned = yvn.remove_user_banned_report_phrasing(
            "这个重点不是标题，而是执行权。真正的问题不是会不会用，而是谁来负责。"
        )

        self.assertNotRegex(cleaned, r"不是.{0,40}而是")
        self.assertNotRegex(cleaned, r"不是.{0,40}，而是")

    def test_extract_transcript_from_rosetta_html(self):
        html = """
        <section id="transcript">
        <h2>Full transcript</h2>
        <details open>
        <div class="prose"><p>At Anthropic we build for the model six months from now.
        This is a long enough transcript paragraph with many words that should be accepted.
        Users wrote markdown files and Claude Code turned that into CLAUDE.md.
        The terminal started as a prototype and stayed because it was thin.
        Productivity was discussed with rough pull request metrics.</p></div>
        </details>
        </section>
        """

        transcript = yvn.extract_transcript_from_html(html)

        self.assertIn("six months from now", transcript)
        self.assertIn("CLAUDE.md", transcript)

    def test_transcript_text_to_items_segments_plain_text(self):
        text = " ".join(f"word{i}" for i in range(100))

        items = yvn.transcript_text_to_items(text, segment_words=25)

        self.assertGreaterEqual(len(items), 4)
        self.assertEqual(items[0]["start"], 0.0)
        self.assertEqual(items[1]["start"], 12.0)

    def test_rosetta_slug_matches_archive_shape(self):
        self.assertEqual(yvn.rosetta_slug("Y Combinator", compact=True), "ycombinator")
        self.assertEqual(
            yvn.rosetta_slug("Inside Claude Code With Its Creator Boris Cherny"),
            "inside-claude-code-with-its-creator-boris-cherny",
        )

    def test_build_ytdlp_attempts_adds_youtube_client_fallbacks(self):
        with patch.dict("os.environ", {}, clear=True):
            attempts = yvn.build_ytdlp_attempts("https://www.youtube.com/watch?v=abc", {"quiet": True})

        self.assertEqual(attempts[0][0], "default")
        strategy_names = [name for name, _opts in attempts]
        self.assertIn("youtube-client:web_safari,mweb,web", strategy_names)
        self.assertIn("youtube-client:ios", strategy_names)
        self.assertIn("youtube-client:android", strategy_names)
        fallback_opts = dict(attempts)["youtube-client:ios"]
        self.assertEqual(fallback_opts["extractor_args"]["youtube"]["player_client"], ["ios"])

    def test_ytdlp_resilience_opts_adds_youtube_network_defaults(self):
        opts = yvn.build_ytdlp_resilience_opts("youtube")

        self.assertEqual(opts["retries"], 4)
        self.assertTrue(opts["force_ipv4"])
        self.assertEqual(opts["concurrent_fragment_downloads"], 1)
        self.assertIn("User-Agent", opts["http_headers"])

    def test_ytdlp_resilience_opts_keeps_metadata_attempts_shorter(self):
        opts = yvn.build_ytdlp_resilience_opts("youtube", phase="metadata")

        self.assertEqual(opts["retries"], 2)
        self.assertEqual(opts["socket_timeout"], 18)
        self.assertEqual(opts["concurrent_fragment_downloads"], 2)

    def test_ytdlp_pot_logger_compat_accepts_once_argument(self):
        yvn.ensure_ytdlp_pot_logger_compat()
        from yt_dlp.extractor.youtube.pot._director import YoutubeIEContentProviderLogger

        class FakeIE:
            def __init__(self):
                self.messages = []

            def write_debug(self, message, only_once=False):
                self.messages.append((message, only_once))

            def to_screen(self, message):
                self.messages.append((message, False))

            def report_warning(self, message, only_once=False):
                self.messages.append((message, only_once))

        fake_ie = FakeIE()
        logger = YoutubeIEContentProviderLogger(
            fake_ie,
            "pot",
            log_level=YoutubeIEContentProviderLogger.LogLevel.DEBUG,
        )
        logger.debug("provider check", once=True)

        self.assertTrue(fake_ie.messages)
        self.assertIn("provider check", fake_ie.messages[-1][0])

    def test_video_download_variants_retry_without_range_and_compatible_format(self):
        base = {
            "format": yvn.default_frame_download_format(),
            "download_ranges": object(),
            "force_keyframes_at_cuts": False,
        }

        variants = yvn.build_video_download_option_variants(base)
        labels = [label for label, _opts in variants]

        self.assertEqual(labels[:3], ["ranged-low", "full-low", "full-compatible"])
        self.assertIn("download_ranges", variants[0][1])
        self.assertNotIn("download_ranges", variants[1][1])
        self.assertNotIn("download_ranges", variants[2][1])
        self.assertEqual(variants[2][1]["format"], yvn.compatible_local_video_format())

    def test_download_video_tries_youtube_client_fallback_after_default_failure(self):
        recorded_opts = []

        class FakeYoutubeDL:
            def __init__(self, opts):
                self.opts = opts
                recorded_opts.append(opts)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, _urls):
                extractor_args = self.opts.get("extractor_args") or {}
                clients = extractor_args.get("youtube", {}).get("player_client") or []
                if "ios" not in clients:
                    raise RuntimeError("403")
                Path(self.opts["outtmpl"].replace("%(ext)s", "mp4")).write_bytes(b"video")

        notes = []
        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.get_youtube_dl", return_value=FakeYoutubeDL):
            result = yvn.download_video_for_frames_with_auth(
                "https://www.youtube.com/watch?v=abc",
                Path(temp_dir),
                notes=notes,
            )

        self.assertIsNotNone(result)
        self.assertIn("yt-dlp-video-strategy:youtube-client:ios", notes)
        self.assertGreaterEqual(len(recorded_opts), 3)

    def test_download_video_for_frames_uses_range_and_low_video_format(self):
        recorded_opts = []

        class FakeYoutubeDL:
            def __init__(self, opts):
                self.opts = opts
                recorded_opts.append(opts)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, _urls):
                Path(self.opts["outtmpl"].replace("%(ext)s", "webm")).write_bytes(b"video")

        notes = []
        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.get_youtube_dl", return_value=FakeYoutubeDL):
            result = yvn.download_video_for_frames_with_auth(
                "https://www.youtube.com/watch?v=abc",
                Path(temp_dir),
                notes=notes,
                section_end_seconds=620,
            )

        self.assertIsNotNone(result)
        self.assertIn("download_ranges", recorded_opts[0])
        self.assertIn("height<=360", recorded_opts[0]["format"])
        self.assertIn("protocol=https", recorded_opts[0]["format"])
        self.assertIn("yt-dlp-frame-range:0-620s", notes)
        self.assertTrue(any(note.startswith("yt-dlp-frame-format:") for note in notes))

    def test_download_video_retries_full_download_when_range_strategy_fails(self):
        recorded_opts = []

        class FakeYoutubeDL:
            def __init__(self, opts):
                self.opts = opts
                recorded_opts.append(opts)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, _urls):
                if "download_ranges" in self.opts:
                    raise RuntimeError("ffmpeg exited with code 8")
                Path(self.opts["outtmpl"].replace("%(ext)s", "mp4")).write_bytes(b"video")

        notes = []
        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.get_youtube_dl", return_value=FakeYoutubeDL):
            result = yvn.download_video_for_frames_with_auth(
                "https://www.youtube.com/watch?v=abc",
                Path(temp_dir),
                notes=notes,
                section_end_seconds=210,
            )

        self.assertIsNotNone(result)
        self.assertIn("yt-dlp-video-option:full-low", notes)
        self.assertTrue(any("download_ranges" in opts for opts in recorded_opts))
        self.assertTrue(any("download_ranges" not in opts for opts in recorded_opts))

    def test_persist_source_video_prefers_mp4_remux(self):
        class FakeCompleted:
            returncode = 0
            stderr = ""

        def fake_run(command, capture_output=True, text=True):
            Path(command[-1]).write_bytes(b"mp4")
            return FakeCompleted()

        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.resolve_binary", return_value="/usr/bin/ffmpeg"), patch(
            "tools.youtube_video_notes.subprocess.run", side_effect=fake_run
        ):
            temp_path = Path(temp_dir)
            source = temp_path / "source.webm"
            source.write_bytes(b"webm")
            notes = []

            result = yvn.persist_source_video_for_material(source, temp_path / "asset", notes=notes)

            self.assertEqual(result.name, "source-video.mp4")
            self.assertEqual(result.read_bytes(), b"mp4")
            self.assertIn("local-video-remuxed:mp4", notes)

    def test_persist_source_video_falls_back_to_original_extension_when_remux_fails(self):
        class FakeCompleted:
            returncode = 1
            stderr = "invalid data"

        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.resolve_binary", return_value="/usr/bin/ffmpeg"), patch(
            "tools.youtube_video_notes.subprocess.run", return_value=FakeCompleted()
        ):
            temp_path = Path(temp_dir)
            source = temp_path / "source.webm"
            source.write_bytes(b"webm")
            notes = []

            result = yvn.persist_source_video_for_material(source, temp_path / "asset", notes=notes)

            self.assertEqual(result.name, "source-video.webm")
            self.assertEqual(result.read_bytes(), b"webm")
            self.assertTrue(any(note.startswith("local-video-remux-failed:") for note in notes))

    def test_extract_keyframes_reuses_preloaded_local_video(self):
        class FakeCompleted:
            returncode = 0
            stderr = ""

        def fake_run(command, capture_output=True, text=True):
            Path(command[-1]).write_bytes(b"jpg")
            return FakeCompleted()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_video = temp_path / "source.mp4"
            source_video.write_bytes(b"video")
            with patch("tools.youtube_video_notes.resolve_binary", return_value="/usr/bin/ffmpeg"), patch(
                "tools.youtube_video_notes.subprocess.run", side_effect=fake_run
            ), patch(
                "tools.youtube_video_notes.download_video_for_frames_with_auth",
                side_effect=AssertionError("should reuse local video"),
            ):
                assets, notes = yvn.extract_keyframes(
                    "https://www.youtube.com/watch?v=abc",
                    temp_path / "assets",
                    60,
                    2,
                    source_video_path=source_video,
                )

        self.assertEqual(len(assets), 2)
        self.assertIn("frame-source:preloaded-local-video", notes)
        self.assertTrue(any(note.startswith("local-video-") for note in notes))

    def test_download_video_ignores_partial_or_empty_source_files(self):
        class FakeYoutubeDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, _urls):
                template = self.opts["outtmpl"]
                Path(template.replace("%(ext)s", "mp4.part")).write_bytes(b"partial")
                Path(template.replace("%(ext)s", "webm")).write_bytes(b"")

        notes = []
        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.get_youtube_dl", return_value=FakeYoutubeDL):
            result = yvn.download_video_for_frames_with_auth(
                "https://www.youtube.com/watch?v=abc",
                Path(temp_dir),
                notes=notes,
            )

        self.assertIsNone(result)
        self.assertTrue(any(note.startswith("yt-dlp-video-download-failed:") for note in notes))

    def test_process_url_requires_local_video_persists_source_without_frame_extraction(self):
        fake_info = {
            "id": "abc123",
            "title": "Test Video",
            "channel": "Test",
            "duration": 120,
            "upload_date": "20260630",
            "description": "00:00 Intro",
            "subtitles": {},
            "automatic_captions": {},
            "webpage_url": "https://www.youtube.com/watch?v=abc123",
        }
        transcript = [{"text": "This is a usable transcript.", "start": 0.0, "duration": 4.0}]

        def fake_download(_url, out_dir, **_kwargs):
            out_dir.mkdir(parents=True, exist_ok=True)
            source = out_dir / "source.webm"
            source.write_bytes(b"webm")
            return source

        class FakeCompleted:
            returncode = 0
            stderr = ""

        def fake_run(command, capture_output=True, text=True):
            Path(command[-1]).write_bytes(b"mp4")
            return FakeCompleted()

        with TemporaryDirectory() as temp_dir, patch(
            "tools.youtube_video_notes.extract_video", return_value=(fake_info, [])
        ), patch(
            "tools.youtube_video_notes.download_video_for_frames_with_auth", side_effect=fake_download
        ), patch(
            "tools.youtube_video_notes.try_video_parser_transcript", return_value=(transcript, "video-parser")
        ), patch(
            "tools.youtube_video_notes.resolve_binary", return_value="/usr/bin/ffmpeg"
        ), patch(
            "tools.youtube_video_notes.subprocess.run", side_effect=fake_run
        ):
            args = SimpleNamespace(
                output_dir=temp_dir,
                langs="zh,en",
                cookies_file=None,
                cookies_from_browser=None,
                disable_video_parser=False,
                disable_whisper_fallback=True,
                disable_transcript_fallbacks=True,
                extract_frames=False,
                frame_interval_seconds=45,
                max_frames=6,
                target_frame_seconds=[],
                analysis_backend="rules",
                skip_rewrites=True,
                require_local_video=True,
                include_comments=False,
                asr_backend="auto",
            )

            result = yvn.process_url(args, "https://www.youtube.com/watch?v=abc123")

            self.assertTrue(result["source_video_path"].endswith("source-video.mp4"))
            self.assertTrue(Path(result["source_video_path"]).exists())
            self.assertEqual(result["download_policy"]["status"], "saved")
            self.assertIn("local-video-remuxed:mp4", result["transcript_notes"])

    def test_process_url_uses_web_transcript_fallback_after_local_failures(self):
        fake_info = {
            "id": "PQU9o_5rHC4",
            "title": "Inside Claude Code With Its Creator Boris Cherny",
            "channel": "Y Combinator",
            "duration": 3010,
            "upload_date": "20260217",
            "description": "00:00 Intro",
            "subtitles": {},
            "automatic_captions": {},
            "webpage_url": "https://www.youtube.com/watch?v=PQU9o_5rHC4",
        }
        transcript = [
            {"text": "Boris says build for future models.", "start": 0.0, "duration": 12.0},
            {"text": "Claude Code kept the terminal surface.", "start": 12.0, "duration": 12.0},
        ]
        with TemporaryDirectory() as temp_dir, patch(
            "tools.youtube_video_notes.extract_video", return_value=(fake_info, [])
        ), patch(
            "tools.youtube_video_notes.try_video_parser_transcript", return_value=([], "parser-failed")
        ), patch(
            "tools.youtube_video_notes.download_audio_for_transcription_with_auth", return_value=None
        ), patch(
            "tools.youtube_video_notes.fetch_rosetta_transcript",
            return_value=(transcript, "rosetta-transcript:https://rosetta.to/u/test"),
        ):
            args = SimpleNamespace(
                output_dir=temp_dir,
                langs="zh,en",
                cookies_file=None,
                cookies_from_browser=None,
                disable_video_parser=False,
                disable_whisper_fallback=False,
                disable_transcript_fallbacks=False,
                extract_frames=False,
                frame_interval_seconds=45,
                max_frames=6,
                analysis_backend="rules",
                skip_rewrites=True,
            )

            result = yvn.process_url(args, "https://www.youtube.com/watch?v=PQU9o_5rHC4")
            transcript_path_exists = Path(result["transcript_md_path"]).exists()

        self.assertEqual(result["transcript_source"], "rosetta-transcript:https://rosetta.to/u/test")
        self.assertTrue(transcript_path_exists)

    def test_load_urls_combines_cli_and_file_and_dedupes(self):
        with TemporaryDirectory() as temp_dir:
            url_file = Path(temp_dir) / "urls.txt"
            url_file.write_text(
                "# comment\nhttps://example.com/a\n\nhttps://example.com/b\nhttps://example.com/a\n",
                encoding="utf-8",
            )
            urls = yvn.load_urls(["https://example.com/c", "https://example.com/a"], str(url_file))

        self.assertEqual(
            urls,
            ["https://example.com/c", "https://example.com/a", "https://example.com/b"],
        )

    def test_build_openai_compatible_user_content_includes_remote_and_local_images(self):
        png_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO"
            "mD2mQAAAAASUVORK5CYII="
        )
        with TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "frame.png"
            image_path.write_bytes(__import__("base64").b64decode(png_base64))

            class FakeHeaders:
                def get_content_type(self):
                    return "image/jpeg"

            class FakeResponse:
                headers = FakeHeaders()

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def read(self):
                    return b"fake-jpeg"

            with patch("tools.youtube_video_notes.urlopen", return_value=FakeResponse()):
                content = yvn.build_openai_compatible_user_content(
                    {
                        "title": "test",
                        "transcript_preview": "hello",
                        "visual_assets": [
                            {"type": "thumbnail", "url": "https://example.com/cover.jpg", "source": "remote"},
                            {"type": "frame", "path": str(image_path), "source": "ffmpeg"},
                        ],
                    }
                )

        image_items = [item for item in content if item["type"] == "image_url"]
        self.assertEqual(len(image_items), 2)
        self.assertTrue(image_items[0]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertTrue(image_items[1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_render_markdown_report_prioritizes_editorial_sections(self):
        report = yvn.render_markdown_report(
            url="https://example.com/video",
            platform="youtube",
            info={"title": "test", "id": "abc", "duration": 60, "description": "", "subtitles": {}, "automatic_captions": {}},
            auth_note="browser:chrome",
            transcript_source="video-parser",
            transcript_notes=[],
            caption_files=[],
            outline=[],
            key_points=[],
            visual_assets=[],
            visual_notes=[],
            analysis={
                "backend": "mlx-vlm-local",
                "report_type": "talk",
                "summary": "summary",
                "core_claim": "claim",
                "recommended_hook": "hook",
                "content_outline": [],
                "talking_points": [],
                "repurpose_angles": [],
                "hidden_premises": ["premise"],
                "creator_tactics": ["tactic"],
                "channel_adaptation": ["adapt"],
                "visual_timeline": ["封面：黑底头像", "01:00 关键帧：屏幕录制界面"],
                "anti_ai_notes": [],
                "editorial_decision": {
                    "level": "值得写",
                    "reason": "材料够。",
                    "candidates": ["选题一"],
                    "gaps": ["缺评论区"],
                    "brief": "写稿 Brief",
                },
                "talk_report": {
                    "summary": ["s1", "s2", "s3"],
                    "speaker_context": "speaker",
                    "argument_chain": ["a1"],
                    "evidence_examples": ["e1"],
                    "key_excerpts": ["q1"],
                    "tensions": ["t1"],
                    "channel_angles": ["c1"],
                    "plain_chinese_summary": "plain",
                },
                "creator_draft_pack": {
                    "candidate_titles": ["t1", "t2"],
                    "opening_options": [{"route": "r1", "text": "o1"}],
                    "oral_script_beats": ["b1", "b2"],
                    "personal_judgment_entries": ["j1"],
                    "sample_opening": "sample",
                    "guardrails": ["g1"],
                    "source_anchor": ["q1"],
                },
            },
            backend_notes=[],
            transcript_preview="preview",
        )
        self.assertIn("## 核心判断", report)
        self.assertIn("## 可写评分", report)
        self.assertIn("## 选题候选", report)
        self.assertIn("## 写稿 Brief", report)
        self.assertIn("## 适合怎么写", report)
        self.assertIn("## 可写选题", report)
        self.assertIn("## 最值得抓的点", report)
        self.assertIn("## 先别急着相信的地方", report)
        self.assertIn("## 人物 / 动机 / 论证链", report)
        self.assertIn("## 可直接进入写稿的材料", report)
        self.assertIn("## 技术信息", report)
        self.assertLess(report.index("## 核心判断"), report.index("## 技术信息"))
        self.assertNotRegex(report, r"不是.{0,40}而是")
        self.assertNotRegex(report, r"不是.{0,40}，而是")

    def test_subtitle_text_to_items_parses_srt_timing(self):
        items = yvn.subtitle_text_to_items(
            "1\n00:00:01,000 --> 00:00:03,500\n第一句字幕\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\n第二句字幕\n"
        )

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["text"], "第一句字幕")
        self.assertAlmostEqual(items[0]["start"], 1.0)
        self.assertAlmostEqual(items[0]["duration"], 2.5)

    def test_extract_embedded_subtitle_transcript_prefers_bilibili_ai_zh(self):
        info = {
            "subtitles": {
                "danmaku": [{"ext": "xml", "url": "https://comment.bilibili.com/1.xml"}],
                "ai-zh": [
                    {
                        "ext": "srt",
                        "data": "1\n00:00:01,000 --> 00:00:03,000\n自动字幕内容\n",
                    }
                ],
            }
        }
        notes: list[str] = []

        items, source = yvn.extract_embedded_subtitle_transcript(info, notes)

        self.assertEqual(source, "yt-dlp-embedded-subtitle:ai-zh")
        self.assertEqual(items[0]["text"], "自动字幕内容")
        self.assertIn("yt-dlp-embedded-subtitle:ai-zh", notes)

    def test_ass_subtitle_to_items_parses_dialogue(self):
        items = yvn.ass_subtitle_to_items(
            "[Events]\n"
            "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\\\pos(0,0)}第一句\\\\N字幕\n"
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["text"], "第一句 字幕")
        self.assertAlmostEqual(items[0]["start"], 1.0)
        self.assertAlmostEqual(items[0]["duration"], 2.0)

    def test_try_bbdown_bilibili_transcript_skips_when_missing(self):
        notes: list[str] = []

        with patch("tools.youtube_video_notes.find_bbdown_binary", return_value=None):
            items, source = yvn.try_bbdown_bilibili_transcript(
                "https://www.bilibili.com/video/BV1xx411c7mD/",
                Path(self.id()),
                notes,
            )

        self.assertEqual(items, [])
        self.assertIsNone(source)
        self.assertIn("bbdown-skipped:not-installed", notes)

    def test_try_bbdown_bilibili_transcript_reads_srt_output(self):
        notes: list[str] = []

        def fake_run(command, cwd, capture_output, text, timeout):
            Path(cwd, "demo.srt").write_text(
                "1\n00:00:01,000 --> 00:00:03,000\nBBDown 字幕\n",
                encoding="utf-8",
            )

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            return Result()

        with TemporaryDirectory() as temp_dir, patch("tools.youtube_video_notes.find_bbdown_binary", return_value="/usr/local/bin/BBDown"), patch(
            "tools.youtube_video_notes.subprocess.run", side_effect=fake_run
        ):
            items, source = yvn.try_bbdown_bilibili_transcript(
                "https://www.bilibili.com/video/BV1xx411c7mD/",
                Path(temp_dir),
                notes,
            )

        self.assertEqual(source, "bbdown-subtitle")
        self.assertEqual(items[0]["text"], "BBDown 字幕")
        self.assertTrue(any(note.startswith("bbdown-subtitle:") for note in notes))

    def test_build_rewrite_pack_returns_publishable_sections(self):
        pack = yvn.build_rewrite_pack(
            info={"title": "自媒体神器：Codex", "channel": "黄益贺", "duration": 402},
            transcript_source="faster-whisper:tiny",
            analysis={
                "summary": "这条视频在讲 Codex 怎么进入内容工作流。",
                "core_claim": "它真正的价值不是会不会聊天，而是能不能替你推进任务。",
                "recommended_hook": "很多人把它理解窄了。",
            },
            payload={
                "outline": [{"title": "片段 1", "summary": "先讲它为什么不只是代码工具"}],
                "key_points": ["00:00 片段 1：先讲它为什么不只是代码工具"],
                "transcript_preview": "[00:00] 先讲它为什么不只是代码工具",
            },
        )

        self.assertEqual(pack["meta"]["title"], "自媒体神器：Codex")
        self.assertGreaterEqual(len(pack["core_takeaway"]), 3)
        self.assertGreaterEqual(len(pack["short_video_script"]), 5)
        self.assertGreaterEqual(len(pack["personal_judgment_script"]), 5)
        self.assertGreaterEqual(len(pack["angles"]), 3)
        self.assertTrue(pack["final_take"])

    def test_build_rewrite_pack_does_not_leak_english_transcript_signal(self):
        pack = yvn.build_rewrite_pack(
            info={"title": "AI Agents Need Computers", "channel": "Latent Space", "duration": 4000},
            transcript_source="video-parser",
            analysis={
                "summary": "summary",
                "core_claim": "",
                "recommended_hook": "",
            },
            payload={
                "outline": [{"title": "Hook", "summary": "I've never experienced this that people call you for access."}],
                "key_points": ["00:00 Hook: I've never experienced this that people call you for access."],
                "transcript_preview": "[00:00] I've never experienced this that people call you for access.",
            },
        )

        rendered = yvn.render_rewrite_pack(pack)
        self.assertNotIn("I've never experienced", rendered)

    def test_build_rewrite_pack_uses_specific_background_agent_angle(self):
        pack = yvn.build_rewrite_pack(
            info={"title": "Devin's 80% Moment", "channel": "Latent Space", "duration": 4172},
            transcript_source="video-parser",
            analysis={"summary": "", "core_claim": "", "recommended_hook": ""},
            payload={
                "description_preview": "background agents, spec to pull request, repo setup, testing harder than computer use",
                "outline": [
                    {"title": "Why Everyone Is Building Their Own Devin", "summary": "english transcript"},
                    {"title": "Repo Setup, Secrets, Docker, and Full VMs", "summary": "english transcript"},
                ],
                "key_points": [],
                "transcript_preview": "",
            },
        )

        rendered = yvn.render_rewrite_pack(pack)
        self.assertIn("spec 稳定推进到 PR", rendered)
        self.assertIn("repo setup、权限、测试和验证", rendered)

    def test_render_rewrite_pack_includes_versions(self):
        markdown = yvn.render_rewrite_pack(
            {
                "meta": {
                    "title": "自媒体神器：Codex",
                    "channel": "黄益贺",
                    "duration": "6:42",
                    "transcript_source": "faster-whisper:tiny",
                },
                "source_note": "测试说明",
                "core_takeaway": ["a", "b", "c"],
                "short_video_script": ["s1", "s2"],
                "personal_judgment_script": ["p1", "p2"],
                "social_post": ["x1", "x2"],
                "cold_open": ["c1", "c2"],
                "angles": ["angle1", "angle2"],
                "avoid_lines": ["avoid1"],
                "safer_lines": ["safe1"],
                "final_take": "final",
            }
        )

        self.assertIn("## 版本 1：短视频口播版", markdown)
        self.assertIn("## 版本 2：更像你频道的个人判断版", markdown)
        self.assertIn("## 版本 3：适合发小红书 / B站动态的短文案", markdown)
        self.assertIn("## 版本 4：更冷一点的 TheMarketMemo 式开头", markdown)
        self.assertIn("## 我给你的最终建议", markdown)

    def test_render_batch_summary_markdown_includes_core_fields(self):
        markdown = yvn.render_batch_summary_markdown(
            requested=2,
            results=[
                {
                    "url": "https://example.com/a",
                    "video_id": "aaa",
                    "title": "测试视频 A",
                    "channel": "频道 A",
                    "duration_human": "6:42",
                    "transcript_source": "faster-whisper:tiny",
                    "note_path": "/tmp/a_notes.md",
                    "json_path": "/tmp/a_info.json",
                    "rewrites_path": "/tmp/a_rewrites.md",
                    "core_claim": "A 的核心落在工作流。",
                    "repurpose_angles": ["角度 1", "角度 2"],
                    "final_take": "最终落点 A",
                }
            ],
            failures=[{"url": "https://example.com/b", "error": "502"}],
        )

        self.assertIn("# 批量视频分析汇总", markdown)
        self.assertIn("### 1. 测试视频 A", markdown)
        self.assertIn("核心判断", markdown)
        self.assertIn("可用角度", markdown)
        self.assertIn("推荐落点", markdown)
        self.assertIn("失败条目", markdown)
        self.assertIn("502", markdown)

    def test_render_topic_pool_markdown_includes_titles_and_angles(self):
        markdown = yvn.render_topic_pool_markdown(
            [
                {
                    "title": "测试视频 A",
                    "channel": "频道 A",
                    "url": "https://example.com/a",
                    "rewrites_path": "/tmp/a_rewrites.md",
                    "core_claim": "A 的核心落在工作流。",
                    "repurpose_angles": ["角度 1", "角度 2"],
                    "final_take": "建议落点 A",
                }
            ]
        )

        self.assertIn("# 批量选题池", markdown)
        self.assertIn("## 1. 测试视频 A", markdown)
        self.assertIn("可直接拿来发的题目", markdown)
        self.assertIn("角度 1", markdown)
        self.assertIn("建议落点 A", markdown)

    def test_batch_summary_written_for_multiple_urls(self):
        with TemporaryDirectory() as temp_dir:
            args = SimpleNamespace(
                output_dir=temp_dir,
                url=[],
                url_file=None,
                langs="zh,en",
                cookies_file=None,
                cookies_from_browser=None,
                disable_video_parser=True,
                disable_whisper_fallback=True,
                analysis_backend="rules",
                extract_frames=False,
                frame_interval_seconds=45,
                max_frames=6,
                skip_rewrites=False,
            )
            urls = ["https://example.com/a", "https://example.com/b"]

            def fake_process_url(_args, url):
                slug = "a" if url.endswith("/a") else "b"
                return {
                    "url": url,
                    "video_id": slug,
                    "note_path": str(Path(temp_dir) / f"{slug}_notes.md"),
                    "json_path": str(Path(temp_dir) / f"{slug}_info.json"),
                    "rewrites_path": str(Path(temp_dir) / f"{slug}_rewrites.md"),
                }

            with patch("tools.youtube_video_notes.build_arg_parser") as build_parser:
                fake_parser = build_parser.return_value
                fake_parser.parse_args.return_value = args
                with patch("tools.youtube_video_notes.load_urls", return_value=urls), patch(
                    "tools.youtube_video_notes.process_url", side_effect=fake_process_url
                ):
                    exit_code = yvn.main()

            summary_path = Path(temp_dir) / "batch_run_summary.json"
            summary_md_path = Path(temp_dir) / "batch_run_summary.md"
            topic_pool_path = Path(temp_dir) / "topic_pool.md"
            self.assertEqual(exit_code, 0)
            self.assertTrue(summary_path.exists())
            self.assertTrue(summary_md_path.exists())
            self.assertTrue(topic_pool_path.exists())
            summary = __import__("json").loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["requested"], 2)
            self.assertEqual(summary["succeeded"], 2)
            self.assertEqual(summary["failed"], 0)

    def test_resolve_binary_falls_back_to_imageio_ffmpeg(self):
        with patch("tools.youtube_video_notes.shutil.which", return_value=None):
            ffmpeg_path = yvn.resolve_binary("ffmpeg")

        self.assertTrue(ffmpeg_path)
        self.assertIn("ffmpeg", Path(ffmpeg_path).name.lower())

    def test_runtime_diagnostics_reports_po_provider_and_ffmpeg(self):
        diagnostics = yvn.ytdlp_runtime_diagnostics()

        self.assertTrue(diagnostics["ytDlp"])
        self.assertTrue(diagnostics["ffmpeg"])
        self.assertIn("poTokenProvider", diagnostics)


if __name__ == "__main__":
    unittest.main()
