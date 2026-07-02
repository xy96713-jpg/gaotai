#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outDir = path.join(root, ".cache", "video-analysis-full-qa");
const reportPath = path.join(outDir, "latest.json");
const withSampleMatrix = process.argv.includes("--with-sample-matrix");

fs.mkdirSync(outDir, { recursive: true });

const steps = [
  ["js syntax", ["node", "--check", "video_analysis_v1/app.js"]],
  ["server syntax", ["python3", "-m", "py_compile", "tools/inline_editor_server.py"]],
  ["unit: video gates", ["python3", "-m", "unittest",
    "tests.test_video_analysis_demo_deck_quality",
    "tests.test_video_analysis_acceptance_matrix",
    "tests.test_video_analysis_readiness",
    "tests.test_video_analysis_release_gate",
  ]],
  ["browser: clean entry", ["node", "tools/video_analysis_clean_entry_smoke.mjs"]],
  ["browser: click lifecycle", ["node", "tools/video_analysis_click_lifecycle_smoke.mjs"]],
  ["browser: progress", ["node", "tools/video_analysis_progress_smoke.mjs"]],
  ["browser: auth failure", ["node", "tools/video_analysis_auth_failure_smoke.mjs"]],
  ["browser: local upload", ["node", "tools/video_analysis_local_upload_smoke.mjs"]],
  ["browser: drag drop", ["node", "tools/video_analysis_drag_drop_smoke.mjs"]],
  ["browser: matrix states", ["node", "tools/video_analysis_browser_matrix_smoke.mjs"]],
  ["browser: professional deck", ["node", "tools/video_analysis_professional_deck_smoke.mjs"]],
];

if (withSampleMatrix) {
  steps.push(["sample matrix", [
    "python3",
    "tools/video_analysis_sample_matrix.py",
    "--strict-commercial",
    "--output-dir",
    ".cache/video-analysis-sample-matrix",
  ]]);
}

const results = [];

for (const [name, command] of steps) {
  const started = Date.now();
  const result = spawnSync(command[0], command.slice(1), {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 20,
  });
  const entry = {
    name,
    ok: result.status === 0,
    ms: Date.now() - started,
    command: command.join(" "),
    stdout: (result.stdout || "").slice(-5000),
    stderr: (result.stderr || "").slice(-5000),
  };
  results.push(entry);
  process.stdout.write(`${entry.ok ? "PASS" : "FAIL"} ${name}\n`);
  if (!entry.ok) {
    process.stdout.write(entry.stderr || entry.stdout || "\n");
    break;
  }
}

const report = {
  ok: results.every((item) => item.ok) && results.length === steps.length,
  generatedAt: new Date().toISOString(),
  withSampleMatrix,
  stepCount: steps.length,
  passedCount: results.filter((item) => item.ok).length,
  results,
};

const sampleEntry = results.find((item) => item.name === "sample matrix");
if (sampleEntry?.stdout) {
  const jsonStart = sampleEntry.stdout.lastIndexOf("{");
  if (jsonStart >= 0) {
    try {
      report.sampleMatrix = JSON.parse(sampleEntry.stdout.slice(jsonStart));
    } catch {
      report.sampleMatrix = null;
    }
  }
}

fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
process.stdout.write(`report: ${reportPath}\n`);
process.exit(report.ok ? 0 : 1);
