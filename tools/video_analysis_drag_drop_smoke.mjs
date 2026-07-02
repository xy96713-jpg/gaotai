#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const server = (process.env.VIDEO_ANALYSIS_SERVER || "http://127.0.0.1:8766").replace(/\/$/, "");
const outDir = path.join(root, ".cache", "video-analysis-drag-drop-smoke");
const videoPath = path.join(root, ".cache", "video-analysis", "test-local-drag-drop.mp4");
const reportPath = path.join(outDir, "latest.json");
fs.mkdirSync(outDir, { recursive: true });

if (!fs.existsSync(videoPath)) {
  execFileSync("python3", ["-"], {
    cwd: root,
    stdio: ["pipe", "inherit", "inherit"],
    input: `
from pathlib import Path
import subprocess
from tools import youtube_video_notes as video_notes
ffmpeg = video_notes.resolve_binary("ffmpeg")
out = Path(".cache/video-analysis/test-local-drag-drop.mp4")
out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([
    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
    "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24",
    "-f", "lavfi", "-i", "sine=frequency=660:sample_rate=44100",
    "-t", "4", "-shortest", "-pix_fmt", "yuv420p",
    str(out),
], check=True)
`,
  });
}

const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
page.setDefaultTimeout(45000);

const result = { ok: false };

async function createDataTransfer(filePath) {
  const buffer = fs.readFileSync(filePath).toString("base64");
  const name = path.basename(filePath);
  return page.evaluateHandle(({ buffer, name }) => {
    const data = Uint8Array.from(atob(buffer), (char) => char.charCodeAt(0));
    const file = new File([data], name, { type: "video/mp4" });
    const transfer = new DataTransfer();
    transfer.items.add(file);
    return transfer;
  }, { buffer, name });
}

try {
  await page.goto(`${server}/video-analysis`, { waitUntil: "domcontentloaded" });
  await page.locator("#localMode").click();
  await page.waitForFunction(() => !document.querySelector("#localInputWrap")?.classList.contains("hidden"));

  const dataTransfer = await createDataTransfer(videoPath);
  await page.dispatchEvent("#localInputWrap", "dragenter", { dataTransfer });
  await page.dispatchEvent("#localInputWrap", "dragover", { dataTransfer });
  const dragState = await page.evaluate(() => ({
    highlighted: document.querySelector("#localInputWrap")?.classList.contains("is-drag-over"),
  }));
  if (!dragState.highlighted) throw new Error("dragover should highlight local drop zone");
  await page.dispatchEvent("#localInputWrap", "drop", { dataTransfer });
  await page.waitForFunction(() => {
    const fileName = document.querySelector("#localFileName")?.textContent || "";
    return fileName.includes("test-local-drag-drop.mp4");
  });
  const selectedState = await page.evaluate(() => ({
    fileName: document.querySelector("#localFileName")?.textContent?.trim() || "",
    highlighted: document.querySelector("#localInputWrap")?.classList.contains("is-drag-over"),
  }));
  if (selectedState.highlighted) throw new Error("drop should clear drag highlight");

  await page.locator("#startAnalysis").click();
  await page.waitForFunction(() => new URL(location.href).searchParams.get("jobId"), null, { timeout: 15000 });
  await page.waitForFunction(() => {
    const status = document.querySelector("#jobStatus")?.textContent?.trim() || "";
    return status === "完成" || status === "失败";
  }, null, { timeout: 45000 });

  const finalState = await page.evaluate(() => ({
    href: location.href,
    status: document.querySelector("#jobStatus")?.textContent?.trim() || "",
    title: document.querySelector("#resultTitle")?.textContent?.trim() || "",
    playback: document.querySelector("#playbackSource")?.textContent?.trim() || "",
    videoSrc: document.querySelector("#videoPlayer video")?.getAttribute("src") || "",
    progressCards: document.querySelectorAll("#downloadProgress:not(.hidden)").length,
  }));
  if (finalState.status !== "完成") throw new Error(`drag upload did not finish: ${finalState.status}`);
  if (!finalState.videoSrc.includes("/api/video-analysis-file")) {
    throw new Error(`drag upload should render local video src, got ${finalState.videoSrc}`);
  }
  if (!finalState.playback.includes("已保存本地")) {
    throw new Error(`drag upload should show saved-local state, got ${finalState.playback}`);
  }
  if (finalState.progressCards !== 0) {
    throw new Error(`completed job should hide progress card, visible=${finalState.progressCards}`);
  }

  const screenshot = path.join(outDir, "drag-drop-upload.png");
  await page.screenshot({ path: screenshot, fullPage: true });
  Object.assign(result, {
    ok: true,
    generatedAt: new Date().toISOString(),
    dragState,
    selectedState,
    finalState,
    screenshot,
  });
} catch (error) {
  result.error = String(error?.message || error);
  result.generatedAt = new Date().toISOString();
  try {
    result.screenshot = path.join(outDir, "failure.png");
    await page.screenshot({ path: result.screenshot, fullPage: true });
  } catch {}
} finally {
  await browser.close();
}

fs.writeFileSync(reportPath, JSON.stringify(result, null, 2), "utf8");
console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
