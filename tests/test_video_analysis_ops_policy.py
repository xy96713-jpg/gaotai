from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.video_analysis_ops_policy import build_report


class VideoAnalysisOpsPolicyTest(unittest.TestCase):
    def test_budget_report_blocks_done_job_without_local_video(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "video-analysis"
            jobs_dir = cache_dir / "jobs"
            jobs_dir.mkdir(parents=True)
            (jobs_dir / "remote.json").write_text(
                json.dumps(
                    {
                        "id": "remote",
                        "url": "https://www.youtube.com/watch?v=PQU9o_5rHC4",
                        "status": "done",
                        "requireLocalVideo": True,
                        "maxFrames": 2,
                        "targetFrameSeconds": [0, 120],
                        "summary": {"videoEmbed": {"type": "youtube", "watchUrl": "https://youtube.com/watch?v=PQU9o_5rHC4"}},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            import tools.video_analysis_ops_policy as ops

            with mock.patch.object(ops, "VIDEO_CACHE", cache_dir), mock.patch.object(ops, "VIDEO_JOB_DIR", jobs_dir):
                report = build_report(
                    max_cache_mb=1500,
                    max_job_files=300,
                    retention_days=14,
                    error_retention_days=7,
                    apply=False,
                )

        self.assertFalse(report["ok"])
        self.assertEqual(report["budget"]["doneJobs"], 1)
        self.assertEqual(report["budget"]["localDoneJobs"], 0)
        self.assertIn("remote", report["budget"]["doneWithoutLocalVideo"])
        self.assertTrue(any("done jobs without local video" in item for item in report["blockers"]))

    def test_budget_report_accepts_local_youtube_and_bilibili_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "video-analysis"
            jobs_dir = cache_dir / "jobs"
            jobs_dir.mkdir(parents=True)
            local_youtube = cache_dir / "yt" / "source-video.mp4"
            local_bilibili = cache_dir / "bv" / "source-video.mp4"
            local_youtube.parent.mkdir(parents=True)
            local_bilibili.parent.mkdir(parents=True)
            local_youtube.write_bytes(b"yt")
            local_bilibili.write_bytes(b"bv")
            jobs = [
                ("yt", "https://www.youtube.com/watch?v=PQU9o_5rHC4", local_youtube),
                ("bv", "https://www.bilibili.com/video/BV1ZB4zeeEEb/", local_bilibili),
            ]
            for job_id, url, local_path in jobs:
                (jobs_dir / f"{job_id}.json").write_text(
                    json.dumps(
                        {
                            "id": job_id,
                            "url": url,
                            "tenantId": "local",
                            "ownerScope": "single-user-local",
                            "status": "done",
                            "requireLocalVideo": True,
                            "maxFrames": 2,
                            "targetFrameSeconds": [0, 120],
                            "summary": {
                                "videoEmbed": {
                                    "type": "local",
                                    "localPath": str(local_path),
                                }
                            },
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            import tools.video_analysis_ops_policy as ops

            with mock.patch.object(ops, "VIDEO_CACHE", cache_dir), mock.patch.object(ops, "VIDEO_JOB_DIR", jobs_dir):
                report = build_report(
                    max_cache_mb=1500,
                    max_job_files=300,
                    retention_days=14,
                    error_retention_days=7,
                    apply=False,
                )

        self.assertTrue(report["ok"])
        self.assertEqual(report["budget"]["doneJobs"], 2)
        self.assertEqual(report["budget"]["localDoneJobs"], 2)
        self.assertEqual(report["budget"]["supportedPlatforms"], ["bilibili", "youtube"])
        self.assertEqual(report["budget"]["maxFramesLimit"], 6)
        self.assertEqual(report["budget"]["maxActiveJobs"], 2)
        self.assertEqual(report["reliability"]["localSuccessRate"], 1.0)
        self.assertEqual(report["reliability"]["retryableFailureCount"], 0)
        self.assertEqual(report["serviceContract"]["monitoringPolicy"]["localSuccessRate"], 1.0)
        self.assertEqual(report["serviceContract"]["scope"], "single-user-local-preview")
        self.assertEqual(report["serviceContract"]["tenantPolicy"]["tenantCount"], 1)
        self.assertEqual(report["serviceContract"]["tenantPolicy"]["tenantIds"], ["local"])
        self.assertTrue(report["serviceContract"]["commercialPreviewReady"])
        self.assertFalse(report["serviceContract"]["publicLaunchReady"])
        self.assertIn("per_user_cost_quota", report["serviceContract"]["publicLaunchMissing"])

    def test_budget_report_blocks_multiple_local_tenants_without_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "video-analysis"
            jobs_dir = cache_dir / "jobs"
            jobs_dir.mkdir(parents=True)
            for tenant_id in ("local", "client-a"):
                local_video = cache_dir / tenant_id / "source-video.mp4"
                local_video.parent.mkdir(parents=True)
                local_video.write_bytes(tenant_id.encode("utf-8"))
                (jobs_dir / f"{tenant_id}.json").write_text(
                    json.dumps(
                        {
                            "id": tenant_id,
                            "url": "https://www.youtube.com/watch?v=PQU9o_5rHC4",
                            "tenantId": tenant_id,
                            "ownerScope": "single-user-local" if tenant_id == "local" else "named-local-tenant",
                            "status": "done",
                            "requireLocalVideo": True,
                            "maxFrames": 2,
                            "targetFrameSeconds": [0, 120],
                            "summary": {
                                "videoEmbed": {
                                    "type": "local",
                                    "localPath": str(local_video),
                                }
                            },
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            import tools.video_analysis_ops_policy as ops

            with mock.patch.object(ops, "VIDEO_CACHE", cache_dir), mock.patch.object(ops, "VIDEO_JOB_DIR", jobs_dir):
                report = build_report(
                    max_cache_mb=1500,
                    max_job_files=300,
                    retention_days=14,
                    error_retention_days=7,
                    apply=False,
                )

        self.assertFalse(report["ok"])
        self.assertEqual(report["serviceContract"]["tenantPolicy"]["tenantCount"], 2)
        self.assertFalse(report["serviceContract"]["commercialPreviewReady"])
        self.assertTrue(any("multiple local tenants" in item for item in report["blockers"]))

    def test_reliability_report_summarizes_retryable_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "video-analysis"
            jobs_dir = cache_dir / "jobs"
            jobs_dir.mkdir(parents=True)
            (jobs_dir / "fail.json").write_text(
                json.dumps(
                    {
                        "id": "fail",
                        "url": "https://www.bilibili.com/video/BV1ZB4zeeEEb/",
                        "tenantId": "local",
                        "ownerScope": "single-user-local",
                        "status": "error",
                        "requireLocalVideo": True,
                        "failure": {
                            "kind": "download_required",
                            "platform": "bilibili",
                            "title": "没有下载到本地视频",
                            "canRetry": True,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            import tools.video_analysis_ops_policy as ops

            with mock.patch.object(ops, "VIDEO_CACHE", cache_dir), mock.patch.object(ops, "VIDEO_JOB_DIR", jobs_dir):
                report = build_report(
                    max_cache_mb=1500,
                    max_job_files=300,
                    retention_days=14,
                    error_retention_days=7,
                    apply=False,
                )

        self.assertTrue(report["ok"])
        self.assertEqual(report["reliability"]["failedJobs"], 1)
        self.assertEqual(report["reliability"]["requireLocalFailedJobs"], 1)
        self.assertEqual(report["reliability"]["failureKinds"], {"download_required": 1})
        self.assertEqual(report["reliability"]["retryableFailures"][0]["id"], "fail")
        self.assertEqual(report["serviceContract"]["monitoringPolicy"]["retryableFailureCount"], 1)
        self.assertTrue(any("retryable video failures" in item for item in report["warnings"]))

    def test_budget_report_blocks_when_active_jobs_exceed_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "video-analysis"
            jobs_dir = cache_dir / "jobs"
            jobs_dir.mkdir(parents=True)
            for index, status in enumerate(("queued", "running", "queued"), start=1):
                (jobs_dir / f"active-{index}.json").write_text(
                    json.dumps(
                        {
                            "id": f"active-{index}",
                            "url": "https://www.youtube.com/watch?v=PQU9o_5rHC4",
                            "status": status,
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            import tools.video_analysis_ops_policy as ops

            with mock.patch.object(ops, "VIDEO_CACHE", cache_dir), mock.patch.object(ops, "VIDEO_JOB_DIR", jobs_dir):
                report = build_report(
                    max_cache_mb=1500,
                    max_job_files=300,
                    retention_days=14,
                    error_retention_days=7,
                    apply=False,
                )

        self.assertFalse(report["ok"])
        self.assertEqual(report["budget"]["activeJobCount"], 3)
        self.assertTrue(any("too many active video jobs" in item for item in report["blockers"]))


if __name__ == "__main__":
    unittest.main()
