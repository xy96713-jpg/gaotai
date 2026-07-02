from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.video_analysis_release_gate import (
    browser_matrix_status,
    build_gate,
    required_routes,
    status_input,
    summarize_jobs,
)


class VideoAnalysisReleaseGateTest(unittest.TestCase):
    def test_required_routes_requires_interview_separately(self) -> None:
        matrix = {
            "maturity": {
                "routeCoverage": {
                    "tutorial": 2,
                    "review": 2,
                    "opinion": 3,
                }
            }
        }
        result = required_routes(matrix)
        self.assertEqual(result["missing"], ["interview"])

    def test_browser_matrix_requires_local_playback_copy(self) -> None:
        payload = {
            "scenarios": [
                {"name": "youtube_local_download", "ok": True, "playback": "YouTube 内嵌播放"},
                {"name": "bilibili_local_download", "ok": True, "playback": "已下载到本地 · 2MB"},
                {"name": "required_local_remote_cache_fails", "ok": True},
            ]
        }
        result = browser_matrix_status(payload)
        self.assertFalse(result["youtubeLocal"])
        self.assertTrue(result["bilibiliLocal"])
        self.assertTrue(result["strictRemoteFails"])

    def test_status_input_blocks_missing_report(self) -> None:
        self.assertFalse(status_input("readiness", None)["ok"])

    def test_build_gate_requires_ops_policy(self) -> None:
        gate = build_gate(
            {
                "readiness": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00", "verdict": "COMMERCIAL_PROOFED"},
                "sample_matrix": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "maturity": {
                        "evaluatedCount": 8,
                        "locallyDownloadedCount": 8,
                        "usableTranscriptCount": 8,
                        "routeCoverage": {"tutorial": 2, "review": 2, "opinion": 3, "interview": 1},
                    },
                },
                "browser_smoke": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
                "browser_matrix": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "scenarios": [
                        {"name": "youtube_local_download", "ok": True, "playback": "已下载到本地"},
                        {"name": "bilibili_local_download", "ok": True, "playback": "已下载到本地"},
                        {"name": "required_local_remote_cache_fails", "ok": True},
                    ],
                },
                "export_smoke": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "slideCount": 4,
                    "mediaCount": 4,
                    "sourceStatus": "已下载到本地",
                },
                "core_acceptance": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
                "ops_policy": None,
            }
        )
        self.assertFalse(gate["ok"])
        self.assertIn("ops policy report missing", gate["blockers"])

    def test_build_gate_accepts_ready_for_real_use_with_clear_rejections(self) -> None:
        gate = build_gate(
            {
                "readiness": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00", "verdict": "READY_FOR_REAL_USE"},
                "sample_matrix": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "maturity": {
                        "commercialReady": True,
                        "evaluatedCount": 11,
                        "locallyDownloadedCount": 11,
                        "usableTranscriptCount": 9,
                        "clearRejectedCount": 2,
                        "routeCoverage": {"tutorial": 4, "review": 2, "opinion": 3, "interview": 1, "demo": 1},
                    },
                },
                "browser_smoke": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
                "browser_matrix": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "scenarios": [
                        {"name": "youtube_local_download", "ok": True, "playback": "已保存本地"},
                        {"name": "bilibili_local_download", "ok": True, "playback": "已下载到本地"},
                        {"name": "required_local_remote_cache_fails", "ok": True},
                    ],
                },
                "export_smoke": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "slideCount": 5,
                    "mediaCount": 4,
                    "sourceStatus": "已下载到本地",
                },
                "core_acceptance": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
                "ops_policy": {
                    "ok": True,
                    "generatedAt": "2999-01-01T00:00:00+00:00",
                    "cache": {},
                    "policy": {},
                    "budget": {},
                    "reliability": {},
                    "serviceContract": {
                        "commercialPreviewReady": True,
                        "scope": "single-user-local-preview",
                        "monitoringPolicy": {"localSuccessRate": 1.0, "failureKinds": {}},
                    },
                },
            }
        )

        self.assertTrue(gate["ok"], gate["blockers"])

    def test_build_gate_requires_ops_budget_report(self) -> None:
        base_inputs = {
            "readiness": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00", "verdict": "COMMERCIAL_PROOFED"},
            "sample_matrix": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "maturity": {
                    "evaluatedCount": 8,
                    "locallyDownloadedCount": 8,
                    "usableTranscriptCount": 8,
                    "routeCoverage": {"tutorial": 2, "review": 2, "opinion": 3, "interview": 1},
                },
            },
            "browser_smoke": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
            "browser_matrix": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "scenarios": [
                    {"name": "youtube_local_download", "ok": True, "playback": "已下载到本地"},
                    {"name": "bilibili_local_download", "ok": True, "playback": "已下载到本地"},
                    {"name": "required_local_remote_cache_fails", "ok": True},
                ],
            },
            "export_smoke": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "slideCount": 4,
                "mediaCount": 4,
                "sourceStatus": "已下载到本地",
            },
            "core_acceptance": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
            "ops_policy": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00", "cache": {}, "policy": {}},
        }
        gate = build_gate(base_inputs)
        self.assertFalse(gate["ok"])
        self.assertIn("ops policy budget report missing", gate["blockers"])

    def test_build_gate_requires_ops_service_contract(self) -> None:
        base_inputs = {
            "readiness": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00", "verdict": "COMMERCIAL_PROOFED"},
            "sample_matrix": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "maturity": {
                    "evaluatedCount": 8,
                    "locallyDownloadedCount": 8,
                    "usableTranscriptCount": 8,
                    "routeCoverage": {"tutorial": 2, "review": 2, "opinion": 3, "interview": 1},
                },
            },
            "browser_smoke": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
            "browser_matrix": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "scenarios": [
                    {"name": "youtube_local_download", "ok": True, "playback": "已下载到本地"},
                    {"name": "bilibili_local_download", "ok": True, "playback": "已下载到本地"},
                    {"name": "required_local_remote_cache_fails", "ok": True},
                ],
            },
            "export_smoke": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "slideCount": 4,
                "mediaCount": 4,
                "sourceStatus": "已下载到本地",
            },
            "core_acceptance": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
            "ops_policy": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "cache": {},
                "policy": {},
                "budget": {},
            },
        }

        gate = build_gate(base_inputs)

        self.assertFalse(gate["ok"])
        self.assertIn("ops policy service contract missing", gate["blockers"])

    def test_build_gate_requires_ops_reliability_report(self) -> None:
        base_inputs = {
            "readiness": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00", "verdict": "COMMERCIAL_PROOFED"},
            "sample_matrix": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "maturity": {
                    "evaluatedCount": 8,
                    "locallyDownloadedCount": 8,
                    "usableTranscriptCount": 8,
                    "routeCoverage": {"tutorial": 2, "review": 2, "opinion": 3, "interview": 1},
                },
            },
            "browser_smoke": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
            "browser_matrix": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "scenarios": [
                    {"name": "youtube_local_download", "ok": True, "playback": "已下载到本地"},
                    {"name": "bilibili_local_download", "ok": True, "playback": "已下载到本地"},
                    {"name": "required_local_remote_cache_fails", "ok": True},
                ],
            },
            "export_smoke": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "slideCount": 4,
                "mediaCount": 4,
                "sourceStatus": "已下载到本地",
            },
            "core_acceptance": {"ok": True, "generatedAt": "2999-01-01T00:00:00+00:00"},
            "ops_policy": {
                "ok": True,
                "generatedAt": "2999-01-01T00:00:00+00:00",
                "cache": {},
                "policy": {},
                "budget": {},
                "serviceContract": {
                    "commercialPreviewReady": True,
                    "scope": "single-user-local-preview",
                    "monitoringPolicy": {"localSuccessRate": 1.0, "failureKinds": {}},
                },
            },
        }

        gate = build_gate(base_inputs)

        self.assertFalse(gate["ok"])
        self.assertIn("ops policy reliability report missing", gate["blockers"])

    def test_summarize_jobs_detects_required_local_without_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            (job_dir / "bad.json").write_text(
                json.dumps(
                    {
                        "id": "bad",
                        "status": "done",
                        "requireLocalVideo": True,
                        "summary": {"videoEmbed": {"type": "youtube", "localPath": ""}},
                    }
                ),
                encoding="utf-8",
            )
            import tools.video_analysis_release_gate as gate

            old_dir = gate.VIDEO_JOB_DIR
            gate.VIDEO_JOB_DIR = job_dir
            try:
                result = summarize_jobs()
            finally:
                gate.VIDEO_JOB_DIR = old_dir
        self.assertEqual(result["brokenRequiredLocal"], ["bad"])


if __name__ == "__main__":
    unittest.main()
