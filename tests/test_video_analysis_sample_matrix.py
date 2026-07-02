from __future__ import annotations

import json
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import video_analysis_sample_matrix as matrix
from tools.video_analysis_sample_matrix import summarize_matrix_maturity


class VideoAnalysisSampleMatrixTest(unittest.TestCase):
    def test_strict_commercial_passes_with_downloaded_route_coverage(self) -> None:
        results = [
            {
                "id": "yt_tutorial",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "tutorial",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "bi_demo",
                "platform": "bilibili",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "demo",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "review",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "review",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "opinion",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "opinion",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "interview",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "interview",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "weak",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": False,
                "routeKind": "demo",
                "materialAcceptanceStatus": "needs_work",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 3,
            },
            {
                "id": "extra1",
                "platform": "bilibili",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "tutorial",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "extra2",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "review",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
        ]

        maturity = summarize_matrix_maturity(results, strict_commercial=True)

        self.assertTrue(maturity["commercialReady"])
        self.assertEqual(maturity["commercialFailures"], [])
        self.assertEqual(maturity["downloadedWeakTranscriptCount"], 1)
        self.assertEqual(maturity["routeCoverage"]["review"], 2)
        self.assertEqual(maturity["downloadedNonTutorialCount"], 4)
        self.assertEqual(maturity["productRouteDepth"], 2)
        self.assertEqual(maturity["thinkingRouteCount"], 2)

    def test_strict_commercial_blocks_missing_route_and_weak_deck(self) -> None:
        results = [
            {
                "id": "tutorial",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "tutorial",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
            },
            {
                "id": "bili",
                "platform": "bilibili",
                "downloadedLocal": True,
                "transcriptUsable": False,
                "routeKind": "tutorial",
                "materialAcceptanceStatus": "blocked",
                "deckQualityStatus": "needs_work",
            },
            {
                "id": "weak_deck",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "review",
                "materialAcceptanceStatus": "needs_work",
                "deckQualityStatus": "needs_work",
            },
        ]

        maturity = summarize_matrix_maturity(results, strict_commercial=True)

        self.assertFalse(maturity["commercialReady"])
        self.assertTrue(any("at least 8 downloaded" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("missing opinion" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("missing interview" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("non-tutorial" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("product/demo routes" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("opinion/interview routes" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("blocked by material acceptance" in item for item in maturity["commercialFailures"]))
        self.assertTrue(any("weak deck quality" in item for item in maturity["commercialFailures"]))

    def test_strict_commercial_accepts_clear_material_rejection_as_product_decision(self) -> None:
        results = [
            {
                "id": "yt_tutorial",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "tutorial",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "bi_demo",
                "platform": "bilibili",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "demo",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "review_a",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "review",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "review_b",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "review",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "opinion_a",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "opinion",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "opinion_b",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "opinion",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "interview",
                "platform": "youtube",
                "downloadedLocal": True,
                "transcriptUsable": True,
                "routeKind": "interview",
                "materialAcceptanceStatus": "ready",
                "deckQualityStatus": "ready",
                "strongSlideCount": 3,
                "slides": 4,
            },
            {
                "id": "music",
                "platform": "bilibili",
                "downloadedLocal": True,
                "transcriptUsable": False,
                "routeKind": "demo",
                "materialAcceptanceStatus": "blocked",
                "materialAcceptanceSummary": "这更像音乐或纯娱乐视频，不适合生成教程拆解。",
                "deckQualityStatus": "needs_work",
                "deckQualityIssues": ["这更像音乐或纯娱乐视频，不适合生成教程拆解或写稿材料。"],
                "strongSlideCount": 0,
                "slides": 0,
            },
        ]

        maturity = summarize_matrix_maturity(results, strict_commercial=True)

        self.assertTrue(maturity["commercialReady"], maturity["commercialFailures"])
        self.assertEqual(maturity["clearRejectedCount"], 1)
        self.assertEqual(maturity["unexpectedBlockedAcceptanceCount"], 0)

    def test_deck_quality_status_prefers_recomputed_issues_over_stale_ready(self) -> None:
        deck = {
            "slides": [{}, {}, {}, {}],
            "demoDeckQuality": {"status": "ready", "strongSlideCount": 4, "issues": []},
        }
        recomputed = {
            "status": "needs_work",
            "strongSlideCount": 4,
            "issues": ["讲法有模板味，需要改成现场口播"],
        }

        self.assertEqual(matrix.demo_deck_quality_status(deck, recomputed), "needs_work")

    def test_read_refreshed_job_prefers_newest_matching_video_job(self) -> None:
        with TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            info_path = job_dir / "PQU9o_5rHC4_info.json"
            info_path.write_text("{}", encoding="utf-8")
            old_job = job_dir / "video_old.json"
            new_job = job_dir / "video_new.json"
            old_job.write_text(
                json.dumps(
                    {
                        "id": "video_old",
                        "result": {"id": "PQU9o_5rHC4", "json_path": str(info_path)},
                        "summary": {"title": "old summary"},
                    }
                ),
                encoding="utf-8",
            )
            new_job.write_text(
                json.dumps(
                    {
                        "id": "video_new",
                        "result": {"id": "PQU9o_5rHC4", "json_path": str(info_path)},
                        "summary": {"title": "new summary"},
                    }
                ),
                encoding="utf-8",
            )
            old_mtime = old_job.stat().st_mtime
            new_mtime = old_mtime + 10
            old_job.touch()
            new_job.touch()
            import os

            os.utime(old_job, (old_mtime, old_mtime))
            os.utime(new_job, (new_mtime, new_mtime))

            def fake_read_video_job(job_id: str) -> dict:
                if job_id == "video_new":
                    return {"id": job_id, "summary": {"title": "new summary"}}
                return {"id": job_id, "summary": {"title": "old summary"}}

            with patch.object(matrix, "VIDEO_JOB_DIR", job_dir), patch.object(
                matrix, "read_video_job", fake_read_video_job
            ):
                record = matrix.read_refreshed_job_for_info(info_path, "PQU9o_5rHC4")

        self.assertEqual(record["id"], "video_new")
        self.assertEqual(record["summary"]["title"], "new summary")


if __name__ == "__main__":
    unittest.main()
