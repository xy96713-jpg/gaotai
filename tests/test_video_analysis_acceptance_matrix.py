import json
import tempfile
import unittest
from pathlib import Path

from tools import workbench_video_acceptance_matrix as matrix


class VideoAnalysisAcceptanceMatrixTest(unittest.TestCase):
    def write_report(self, root: Path, name: str, payload: dict) -> Path:
        path = root / f"{name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_matrix_passes_when_core_contract_is_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            job_dir = base / "jobs"
            job_dir.mkdir()
            video = base / "source.mp4"
            video.write_bytes(b"video")
            reports = {
                "clean_entry": self.write_report(base, "clean", {"ok": True, "results": [{"value": {"title": "贴一个视频链接"}}]}),
                "progress": self.write_report(
                    base,
                    "progress",
                    {
                        "ok": True,
                        "progressText": "正在下载 50% · 5.0MB / 10MB",
                        "unknownTotalProgressText": "正在下载 已下载 5.0MB · 分片 2/8",
                        "unknownTotalTrackHidden": True,
                        "width": "50%",
                    },
                ),
                "auth_failure": self.write_report(base, "auth", {"ok": True, "failureText": "平台要求登录验证 打开 YouTube 登录"}),
                "local_upload": self.write_report(base, "local", {"ok": True, "finalState": {"playback": "已保存本地 · 64KB", "href": "/video-analysis?jobId=local"}}),
                "browser_matrix": self.write_report(
                    base,
                    "browser",
                    {
                        "ok": True,
                        "scenarios": [
                            {"name": "stale_caption_cache_recovers", "ok": True, "url": "/video-analysis?jobId=stale"},
                            {"name": "required_local_remote_cache_fails", "ok": True, "url": "/video-analysis?jobId=remote"},
                        ],
                    },
                ),
                "professional_matrix": self.write_report(
                    base,
                    "professional",
                    {
                        "ok": True,
                        "platforms": [
                            {
                                "platform": "youtube",
                                "ok": True,
                                "candidate": {"id": "youtube", "uniqueScreenshots": 4},
                                "smoke": {
                                    "parsed": {
                                        "steps": [
                                            {
                                                "name": "download PPTX and inspect content",
                                                "value": {"slides": 5, "media": 5},
                                            }
                                        ]
                                    }
                                },
                            },
                            {
                                "platform": "bilibili",
                                "ok": True,
                                "candidate": {"id": "bilibili", "uniqueScreenshots": 5},
                                "smoke": {
                                    "parsed": {
                                        "steps": [
                                            {
                                                "name": "download PPTX and inspect content",
                                                "value": {"slides": 6, "media": 6},
                                            }
                                        ]
                                    }
                                },
                            },
                        ],
                    },
                ),
            }
            for platform in ("youtube", "bilibili"):
                (job_dir / f"{platform}.json").write_text(
                    json.dumps(
                        {
                            "id": platform,
                            "status": "done",
                            "summary": {
                                "platform": platform,
                                "videoEmbed": {"type": "local", "localPath": str(video)},
                            },
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            result = matrix.build_matrix(reports=reports, job_dir=job_dir, out_dir=base / "out")

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "SELF_USE_READY")
        self.assertFalse(result["blockers"])

    def test_matrix_blocks_fake_stage_progress_and_missing_bilibili_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            job_dir = base / "jobs"
            job_dir.mkdir()
            video = base / "source.mp4"
            video.write_bytes(b"video")
            reports = {
                "clean_entry": self.write_report(base, "clean", {"ok": True}),
                "progress": self.write_report(
                    base,
                    "progress",
                    {
                        "ok": True,
                        "progressText": "正在下载 50% 保存 取图 字幕 整理",
                        "unknownTotalProgressText": "正在下载 已下载 5.0MB",
                        "unknownTotalTrackHidden": True,
                    },
                ),
                "auth_failure": self.write_report(base, "auth", {"ok": True, "failureText": "打开 YouTube 登录"}),
                "local_upload": self.write_report(base, "local", {"ok": True, "finalState": {"playback": "已保存本地"}}),
                "browser_matrix": self.write_report(
                    base,
                    "browser",
                    {
                        "ok": True,
                        "scenarios": [
                            {"name": "stale_caption_cache_recovers", "ok": True},
                            {"name": "required_local_remote_cache_fails", "ok": True},
                        ],
                    },
                ),
            }
            (job_dir / "youtube.json").write_text(
                json.dumps(
                    {
                        "id": "youtube",
                        "status": "done",
                        "summary": {
                            "platform": "youtube",
                            "videoEmbed": {"type": "local", "localPath": str(video)},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = matrix.build_matrix(reports=reports, job_dir=job_dir, out_dir=base / "out")

        self.assertFalse(result["ok"])
        blocker_names = {row["name"] for row in result["blockers"]}
        self.assertIn("real_progress", blocker_names)
        self.assertIn("bilibili_local", blocker_names)
        self.assertIn("youtube_professional_ppt", blocker_names)
        self.assertIn("bilibili_professional_ppt", blocker_names)


if __name__ == "__main__":
    unittest.main()
