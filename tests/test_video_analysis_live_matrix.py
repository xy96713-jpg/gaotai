import tempfile
import unittest
from pathlib import Path

from tools.video_analysis_live_matrix import Sample, evaluate_job


class VideoAnalysisLiveMatrixTests(unittest.TestCase):
    def test_unsuitable_downloaded_video_counts_as_correctly_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_video = Path(tmp) / "source.mp4"
            local_video.write_bytes(b"video")

            job = {
                "status": "done",
                "summary": {
                    "videoEmbed": {"type": "local", "localPath": str(local_video)},
                    "sourceStatus": "已下载到本地 · 1.0 MB；截图 2 张已保存。",
                    "downloadPolicy": {
                        "required": True,
                        "status": "saved",
                        "auth": "browser:chrome",
                        "browserCookies": "chrome",
                        "localVideoPath": str(local_video),
                        "localVideoBytes": len(b"video"),
                    },
                    "transcriptQuality": {"usable": True, "label": "字幕可靠"},
                    "videoSummary": {
                        "headline": "这更像音乐或纯娱乐视频，不适合生成教程拆解或写稿材料。",
                        "bullets": [],
                        "contentSuitability": {
                            "status": "unsuitable",
                            "reason": "这更像音乐或纯娱乐视频，不适合生成教程拆解或写稿材料。",
                        },
                    },
                    "demoDeck": {
                        "sourceStatus": "已下载到本地 · 1.0 MB；截图 2 张已保存。",
                        "slides": [],
                        "demoDeckQuality": {
                            "status": "blocked",
                            "issues": ["这更像音乐或纯娱乐视频，不适合生成教程拆解或写稿材料。"],
                        },
                    },
                },
            }

            result = evaluate_job(
                Sample("music", "https://example.com/music", "weak-transcript", "youtube"),
                "job_music",
                job,
            )

            self.assertTrue(result["ok"], result["failures"])
            self.assertTrue(result["correctlyBlocked"])
            self.assertEqual(result["slides"], 0)

    def test_missing_download_policy_blocks_even_when_local_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_video = Path(tmp) / "source.mp4"
            local_video.write_bytes(b"video")

            result = evaluate_job(
                Sample("tutorial", "https://example.com/video", "tutorial", "youtube"),
                "job_missing_policy",
                {
                    "status": "done",
                    "summary": {
                        "videoEmbed": {"type": "local", "localPath": str(local_video)},
                        "sourceStatus": "已下载到本地 · 1.0 MB；截图 2 张已保存。",
                        "transcriptQuality": {"usable": True, "label": "字幕可靠"},
                        "videoSummary": {"headline": "这是一个可以写成教程的视频", "bullets": ["第一点", "第二点"]},
                        "demoDeck": {"slides": [{"title": "第一步"}, {"title": "第二步"}, {"title": "第三步"}]},
                    },
                },
            )

            self.assertFalse(result["ok"])
            self.assertIn("download policy does not prove saved/cached video: empty", result["failures"])


if __name__ == "__main__":
    unittest.main()
