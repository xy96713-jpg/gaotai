.PHONY: workbench-start workbench-stop workbench-restart workbench-status workbench-smoke workbench-verify video-analysis-verify

workbench-start:
	python3 tools/workbench_ops.py start

workbench-stop:
	python3 tools/workbench_ops.py stop

workbench-restart:
	python3 tools/workbench_ops.py restart

workbench-status:
	python3 tools/workbench_ops.py status

workbench-smoke:
	python3 tools/workbench_ops.py smoke

workbench-verify:
	python3 -m py_compile tools/inline_editor_server.py tools/workbench_ops.py tools/youtube_video_notes.py
	node --check inline_editor_v2/app.js
	node --check video_analysis_v1/app.js
	python3 -m unittest tests.test_youtube_video_notes tests.test_video_analysis_acceptance_matrix tests.test_video_analysis_demo_deck_quality -q

video-analysis-verify:
	python3 -m py_compile tools/inline_editor_server.py tools/youtube_video_notes.py
	node --check video_analysis_v1/app.js
	python3 -m unittest tests.test_youtube_video_notes tests.test_video_analysis_acceptance_matrix tests.test_video_analysis_demo_deck_quality -q
