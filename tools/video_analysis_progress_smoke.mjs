#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const server = (process.env.VIDEO_ANALYSIS_SERVER || "http://127.0.0.1:8766").replace(/\/$/, "");
const outDir = path.join(root, ".cache", "video-analysis-progress-smoke");
const jobDir = path.join(root, ".cache", "video-analysis", "jobs");
const jobId = "video_progress_smoke_running";
const unknownTotalJobId = "video_progress_smoke_unknown_total";
const stalledNoBytesJobId = "video_progress_smoke_no_bytes_yet";
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(jobDir, { recursive: true });

const fixture = {
  id: jobId,
  url: "https://www.youtube.com/watch?v=progress-smoke",
  title: "Progress Smoke Video",
  status: "running",
  stage: "download",
  message: "下载中",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  cookiesFromBrowser: "chrome",
  requireLocalVideo: true,
  events: [
    {
      at: new Date().toISOString(),
      stage: "download",
      message: "下载中",
      extra: {
        progressKind: "download",
        downloadStatus: "downloading",
        downloadedBytes: 5242880,
        totalBytes: 10485760,
        percent: 50,
        speedBytesPerSecond: 1048576,
        etaSeconds: 5,
      },
    },
  ],
};

fs.writeFileSync(path.join(jobDir, `${jobId}.json`), JSON.stringify(fixture, null, 2), "utf8");
fs.writeFileSync(path.join(jobDir, `${unknownTotalJobId}.json`), JSON.stringify({
  ...fixture,
  id: unknownTotalJobId,
  events: [
    {
      at: new Date().toISOString(),
      stage: "download",
      message: "下载中",
      extra: {
        progressKind: "download",
        downloadStatus: "downloading",
        downloadedBytes: 5242880,
        totalBytes: 0,
        speedBytesPerSecond: 1048576,
        etaSeconds: 0,
        fragmentIndex: 2,
        fragmentCount: 8,
      },
    },
  ],
}, null, 2), "utf8");
fs.writeFileSync(path.join(jobDir, `${stalledNoBytesJobId}.json`), JSON.stringify({
  ...fixture,
  id: stalledNoBytesJobId,
  updatedAt: new Date(Date.now() - 90_000).toISOString(),
  events: [
    {
      at: new Date(Date.now() - 90_000).toISOString(),
      stage: "download",
      message: "正在保存本地视频",
      extra: {},
    },
  ],
}, null, 2), "utf8");

const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-gpu"],
});

const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
page.setDefaultTimeout(30000);
const result = { ok: false };

async function readRunningChromeState() {
  return page.evaluate(() => {
    const visible = (selector) => {
      const node = document.querySelector(selector);
      if (!node) return false;
      if (node.classList.contains("hidden")) return false;
      const style = window.getComputedStyle(node);
      return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
    };
    const text = (selector) => document.querySelector(selector)?.textContent?.replace(/\s+/g, " ").trim() || "";
    const widgets = [
      ["jobSummary", "#jobSummary"],
      ["quickMeta", "#quickMeta"],
      ["pipelineStatus", "#pipelineStatus"],
      ["downloadProgress", "#downloadProgress"],
    ].map(([name, selector]) => ({ name, selector, visible: visible(selector), text: text(selector) }));
    const visibleText = document.body?.innerText?.replace(/\s+/g, " ").trim() || "";
    return {
      visibleProgressCards: document.querySelectorAll("#downloadProgress:not(.hidden)").length,
      visibleStatusCards: document.querySelectorAll("#jobSummary.status-log:not(.hidden)").length,
      visibleText,
      statusText: text("#jobStatus"),
      progressLabel: text("#downloadProgressLabel"),
      progressText: text("#downloadProgress"),
      quickMetaVisible: visible("#quickMeta"),
      quickMetaText: text("#quickMeta"),
      pipelineVisible: visible("#pipelineStatus"),
      pipelineText: text("#pipelineStatus"),
      widgets,
    };
  });
}

function assertSingleRunningProgress(state, label) {
  if (state.visibleProgressCards !== 1) {
    throw new Error(`${label}: running page should show one progress card, got ${state.visibleProgressCards}: ${JSON.stringify(state)}`);
  }
  if (state.visibleStatusCards !== 0) {
    throw new Error(`${label}: running page should not show a second status card: ${JSON.stringify(state)}`);
  }
  if (state.quickMetaVisible) {
    throw new Error(`${label}: running page should not show quick meta chips: ${JSON.stringify(state)}`);
  }
  if (state.pipelineVisible) {
    throw new Error(`${label}: running page should not show pipeline chips: ${JSON.stringify(state)}`);
  }
  if (state.statusText === state.progressLabel || state.statusText === "下载中") {
    throw new Error(`${label}: top status should not duplicate progress wording: ${JSON.stringify(state)}`);
  }
  const repeatedRunning = (state.visibleText.match(/正在下载/g) || []).length;
  if (repeatedRunning > 1) {
    throw new Error(`${label}: visible page repeats running download copy ${repeatedRunning} times: ${JSON.stringify(state)}`);
  }
  const forbiddenVisible = /(后台规则|材料不足|先补材料|补充|假进度|保存\s+取图\s+字幕\s+整理)/.exec(state.visibleText);
  if (forbiddenVisible) {
    throw new Error(`${label}: visible page leaks internal or fake progress copy: ${forbiddenVisible[0]}`);
  }
}

try {
  await page.goto(`${server}/video-analysis?jobId=${jobId}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#downloadProgress:not(.hidden)");
  await page.waitForFunction(() => {
    const text = document.querySelector("#downloadProgress")?.textContent || "";
    return text.includes("50%") && /5(?:\.0)?\s*MB/.test(text) && /10(?:\.0)?\s*MB/.test(text);
  });
  const progressText = (await page.locator("#downloadProgress").evaluate((node) => node.innerText)).replace(/\s+/g, " ").trim();
  if (/保存\s+取图\s+字幕\s+整理/.test(progressText)) {
    throw new Error(`progress should not expose staged pseudo-steps: ${progressText}`);
  }
  const normalProgressState = await readRunningChromeState();
  assertSingleRunningProgress(normalProgressState, "normal download");
  const width = await page.locator("#downloadProgressBar").evaluate((node) => node.style.width);
  const screenshot = path.join(outDir, "progress.png");
  await page.screenshot({ path: screenshot, fullPage: true });
  result.progressText = progressText;
  result.width = width;
  result.normalProgressState = normalProgressState;
  result.screenshot = screenshot;

  await page.goto(`${server}/video-analysis?jobId=${unknownTotalJobId}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#downloadProgress:not(.hidden)");
  await page.waitForFunction(() => {
    const text = document.querySelector("#downloadProgress")?.textContent || "";
    return text.includes("已下载") && text.includes("分片 2/8") && !text.includes("剩 0");
  });
  const unknownText = (await page.locator("#downloadProgress").evaluate((node) => node.innerText)).replace(/\s+/g, " ").trim();
  if (/保存\s+取图\s+字幕\s+整理/.test(unknownText)) {
    throw new Error(`unknown-total progress should not expose staged pseudo-steps: ${unknownText}`);
  }
  const trackHidden = await page.locator(".download-progress__track").evaluate((node) => node.classList.contains("hidden"));
  const indeterminate = await page.locator("#downloadProgressBar").evaluate((node) => node.hasAttribute("data-indeterminate"));
  if (!trackHidden || indeterminate) {
    throw new Error(`unknown total progress should not show fake bar: hidden=${trackHidden} indeterminate=${indeterminate}`);
  }
  result.unknownTotalProgressText = unknownText;
  result.unknownTotalTrackHidden = trackHidden;

  await page.goto(`${server}/video-analysis?jobId=${stalledNoBytesJobId}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#downloadProgress:not(.hidden)");
  await page.waitForFunction(() => {
    const text = document.querySelector("#downloadProgress")?.textContent || "";
    return text.includes("已等待");
  });
  const stalledText = (await page.locator("#downloadProgress").evaluate((node) => node.innerText)).replace(/\s+/g, " ").trim();
  const progressState = await readRunningChromeState();
  assertSingleRunningProgress(progressState, "stalled download");
  const stalledTrackHidden = await page.locator(".download-progress__track").evaluate((node) => node.classList.contains("hidden"));
  if (!stalledTrackHidden) {
    throw new Error("no-byte download should not show a fake progress bar");
  }
  result.stalledNoBytesText = stalledText;
  result.stalledNoBytesTrackHidden = stalledTrackHidden;
  result.stalledProgressState = progressState;
  result.ok = true;
} catch (error) {
  result.ok = false;
  result.error = String(error?.message || error);
} finally {
  await browser.close();
  try {
    fs.rmSync(path.join(jobDir, `${jobId}.json`), { force: true });
    fs.rmSync(path.join(jobDir, `${unknownTotalJobId}.json`), { force: true });
    fs.rmSync(path.join(jobDir, `${stalledNoBytesJobId}.json`), { force: true });
  } catch {
    // Best-effort cleanup; this fixture should not pollute the user's history.
  }
}

const report = {
  ...result,
  generatedAt: new Date().toISOString(),
  url: `${server}/video-analysis?jobId=${jobId}`,
};
fs.writeFileSync(path.join(outDir, "latest.json"), JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
process.exit(report.ok ? 0 : 1);
