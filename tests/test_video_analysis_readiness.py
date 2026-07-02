from __future__ import annotations

import unittest

from tools.video_analysis_readiness import build_launch_tiers, build_verdict


class VideoAnalysisReadinessTest(unittest.TestCase):
    def test_launch_tiers_separate_preview_from_public_launch(self) -> None:
        result = build_launch_tiers(
            ready_for_real_use=True,
            commercial_mature=True,
            sample_summary={
                "locallyDownloaded": 8,
                "usableTranscript": 8,
                "deckQuality": {"ready": 8},
                "downloadedNonTutorialCount": 4,
            },
            release_gate={
                "commercialPreviewReady": True,
                "publicLaunchReady": False,
                "publicLaunchBlockers": ["missing auth and billing"],
            },
            ops_policy={"ok": True},
            hard_failures=[],
            risks=[],
        )

        self.assertEqual(result["stage"], "COMMERCIAL_PREVIEW_READY")
        self.assertTrue(result["internalReady"])
        self.assertTrue(result["commercialPreviewReady"])
        self.assertFalse(result["publicLaunchReady"])
        self.assertIn("missing auth and billing", result["publicLaunchBlockers"])
        self.assertIn("8 个有效样本已本地下载", result["proof"])

    def test_launch_tiers_blocks_when_core_chain_fails(self) -> None:
        result = build_launch_tiers(
            ready_for_real_use=False,
            commercial_mature=False,
            sample_summary={},
            release_gate={"commercialPreviewReady": False, "publicLaunchReady": False},
            ops_policy={"ok": False},
            hard_failures=["browser smoke did not prove local playback"],
            risks=["sample matrix stale"],
        )

        self.assertEqual(result["stage"], "BLOCKED")
        self.assertFalse(result["internalReady"])
        self.assertFalse(result["commercialPreviewReady"])
        self.assertFalse(result["publicLaunchReady"])
        self.assertTrue(any("browser smoke" in item for item in result["publicLaunchBlockers"]))
        self.assertTrue(any("sample matrix stale" in item for item in result["publicLaunchBlockers"]))

    def test_build_verdict_separates_core_ready_from_commercial_deck_quality(self) -> None:
        verdict = build_verdict(
            {
                "sample_matrix": {
                    "ok": False,
                    "coreReady": True,
                    "maturity": {
                        "coreReady": True,
                        "evaluatedCount": 8,
                        "locallyDownloadedCount": 8,
                        "downloadedPlatforms": ["bilibili", "youtube"],
                        "usableTranscriptCount": 6,
                        "weakTranscriptCount": 2,
                        "downloadedNonTutorialCount": 4,
                        "productRouteDepth": 1,
                        "thinkingRouteCount": 2,
                        "commercialReady": False,
                        "commercialFailures": ["6 samples have weak deck quality"],
                        "deckQualityCounts": {"ready": 2, "needs_work": 6},
                        "acceptanceCounts": {"ready": 2, "needs_work": 6},
                        "routeCoverage": {"tutorial": 2, "review": 2, "opinion": 3, "interview": 1},
                    },
                    "results": [
                        {"downloadedLocal": True, "transcriptUsable": True, "platform": "youtube"}
                        for _ in range(8)
                    ],
                },
                "browser_smoke": {
                    "ok": True,
                    "results": [
                        {"value": {"playback": "已保存本地 · 20MB", "cards": 4}},
                        {"value": {"chars": 800}},
                    ],
                },
                "export_smoke": {
                    "ok": True,
                    "slideCount": 5,
                    "mediaCount": 2,
                    "sizeBytes": 30000,
                },
                "release_gate": {"ok": False, "verdict": "BLOCKED", "blockers": ["commercial deck quality unproven"]},
                "ops_policy": {"ok": True, "reliability": {"localSuccessRate": 1.0}},
            }
        )

        self.assertTrue(verdict["ok"], verdict["hardFailures"])
        self.assertEqual(verdict["verdict"], "READY_FOR_REAL_USE")
        self.assertFalse(verdict["commercialMature"])
        self.assertEqual(verdict["launchTiers"]["stage"], "INTERNAL_READY")
        self.assertTrue(any("weak deck quality" in item for item in verdict["risks"]))

    def test_build_verdict_marks_commercial_preview_when_release_gate_and_clear_rejections_pass(self) -> None:
        verdict = build_verdict(
            {
                "sample_matrix": {
                    "ok": True,
                    "coreReady": True,
                    "maturity": {
                        "coreReady": True,
                        "evaluatedCount": 11,
                        "locallyDownloadedCount": 11,
                        "downloadedPlatforms": ["bilibili", "youtube"],
                        "usableTranscriptCount": 9,
                        "weakTranscriptCount": 2,
                        "clearRejectedCount": 2,
                        "downloadedNonTutorialCount": 6,
                        "productRouteDepth": 1,
                        "thinkingRouteCount": 4,
                        "commercialReady": True,
                        "commercialFailures": [],
                        "deckQualityCounts": {"ready": 9, "needs_work": 2},
                        "acceptanceCounts": {"ready": 8, "needs_work": 1, "blocked": 2},
                        "routeCoverage": {"tutorial": 4, "review": 2, "opinion": 3, "interview": 1, "demo": 1},
                    },
                    "results": [
                        {"downloadedLocal": True, "transcriptUsable": True, "platform": "youtube", "screenshots": 2}
                        for _ in range(9)
                    ]
                    + [
                        {"downloadedLocal": True, "transcriptUsable": False, "platform": "bilibili", "screenshots": 0}
                        for _ in range(2)
                    ],
                },
                "browser_smoke": {
                    "ok": True,
                    "results": [
                        {"value": {"playback": "已保存本地 · 20MB", "cards": 4}},
                        {"value": {"chars": 800}},
                    ],
                },
                "export_smoke": {
                    "ok": True,
                    "slideCount": 5,
                    "mediaCount": 2,
                    "sizeBytes": 30000,
                },
                "release_gate": {
                    "ok": True,
                    "verdict": "COMMERCIAL_PREVIEW_READY",
                    "commercialPreviewReady": True,
                    "publicLaunchReady": False,
                    "publicLaunchBlockers": ["缺少账号/租户隔离"],
                },
                "ops_policy": {
                    "ok": True,
                    "reliability": {"localSuccessRate": 1.0},
                    "serviceContract": {"publicLaunchMissing": ["account_or_tenant_isolation"]},
                },
            }
        )

        self.assertTrue(verdict["ok"], verdict["hardFailures"])
        self.assertTrue(verdict["commercialMature"])
        self.assertEqual(verdict["verdict"], "COMMERCIAL_PROOFED")
        self.assertEqual(verdict["launchTiers"]["stage"], "COMMERCIAL_PREVIEW_READY")


if __name__ == "__main__":
    unittest.main()
