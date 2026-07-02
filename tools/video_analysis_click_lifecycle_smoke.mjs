#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const server = (process.env.VIDEO_ANALYSIS_SERVER || "http://127.0.0.1:8766").replace(/\/$/, "");
const outDir = path.join(root, ".cache", "video-analysis-click-lifecycle");
const reportPath = path.join(outDir, "latest.json");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
page.setDefaultTimeout(30000);

const results = [];

async function step(name, fn) {
  const started = Date.now();
  try {
    const value = await fn();
    results.push({ name, ok: true, ms: Date.now() - started, value });
    return value;
  } catch (error) {
    results.push({ name, ok: false, ms: Date.now() - started, error: String(error?.message || error) });
    throw error;
  }
}

async function visibleState() {
  return page.evaluate(() => {
    const visible = (selector) => {
      const node = document.querySelector(selector);
      if (!node) return false;
      if (node.classList.contains("hidden")) return false;
      const style = window.getComputedStyle(node);
      return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
    };
    const text = (selector) => document.querySelector(selector)?.textContent?.replace(/\s+/g, " ").trim() || "";
    return {
      href: location.href,
      body: document.body.innerText.replace(/\s+/g, " ").trim(),
      jobSummaryVisible: visible("#jobSummary"),
      jobSummaryText: text("#jobSummary"),
      progressVisible: visible("#downloadProgress"),
      progressText: text("#downloadProgress"),
      progressCardCount: document.querySelectorAll("#downloadProgress:not(.hidden)").length,
      statusCardCount: document.querySelectorAll("#jobSummary.status-log:not(.hidden)").length,
      progressBarWidth: document.querySelector("#downloadProgressBar")?.style.width || "",
    };
  });
}

function assertNoDuplicateRunning(state, label) {
  if (state.progressCardCount !== 1) {
    throw new Error(`${label}: expected one progress card, got ${state.progressCardCount}: ${JSON.stringify(state)}`);
  }
  if (state.statusCardCount !== 0 || state.jobSummaryVisible) {
    throw new Error(`${label}: job summary should not be visible while progress is active: ${JSON.stringify(state)}`);
  }
  const runningCopies = (state.body.match(/保存视频|正在下载/g) || []).length;
  if (runningCopies > 2) {
    throw new Error(`${label}: duplicated running copy in visible UI: ${JSON.stringify(state)}`);
  }
}

try {
  await step("click download renders one real progress card", async () => {
    const jobId = "video_click_lifecycle_running";
    const runningJob = {
      id: jobId,
      url: "https://www.youtube.com/watch?v=click-lifecycle",
      title: "Click Lifecycle Video",
      status: "running",
      stage: "download",
      message: "下载中",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      cookiesFromBrowser: "chrome",
      requireLocalVideo: true,
      events: [{
        at: new Date().toISOString(),
        stage: "download",
        message: "下载中",
        extra: {
          progressKind: "download",
          downloadStatus: "downloading",
          downloadedBytes: 3 * 1024 * 1024,
          totalBytes: 12 * 1024 * 1024,
          speedBytesPerSecond: 1024 * 1024,
          etaSeconds: 9,
          percent: 25,
        },
      }],
    };
    await page.route("**/api/video-analysis-request", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(runningJob) });
    });
    await page.route(`**/api/video-analysis-job/${jobId}`, async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(runningJob) });
    });
    await page.goto(`${server}/video-analysis`, { waitUntil: "domcontentloaded" });
    await page.locator("#urlInput").fill(runningJob.url);
    await page.locator("#startAnalysis").click();
    await page.waitForFunction(() => {
      const text = document.querySelector("#downloadProgress")?.textContent || "";
      return text.includes("25%") && text.includes("12MB");
    });
    const state = await visibleState();
    assertNoDuplicateRunning(state, "click running");
    await page.screenshot({ path: path.join(outDir, "click-running.png"), fullPage: true });
    await page.unroute("**/api/video-analysis-request");
    await page.unroute(`**/api/video-analysis-job/${jobId}`);
    return state;
  });

  await step("click failure clears temporary progress", async () => {
    await page.route("**/api/video-analysis-request", async (route) => {
      await route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({ error: "当前已有 1 个视频任务在处理，最多同时 1 个。" }),
      });
    });
    await page.goto(`${server}/video-analysis`, { waitUntil: "domcontentloaded" });
    await page.locator("#urlInput").fill("https://www.youtube.com/watch?v=click-failure");
    await page.locator("#startAnalysis").click();
    await page.waitForFunction(() => {
      const summary = document.querySelector("#jobSummary")?.textContent || "";
      return summary.includes("失败");
    });
    const state = await visibleState();
    if (state.progressVisible || state.progressCardCount !== 0) {
      throw new Error(`temporary progress should be hidden after submit failure: ${JSON.stringify(state)}`);
    }
    if (!state.jobSummaryVisible || !state.jobSummaryText.includes("失败")) {
      throw new Error(`failure summary should be visible: ${JSON.stringify(state)}`);
    }
    if (/保存视频.*失败|正在下载.*失败/.test(state.body)) {
      throw new Error(`failure UI should not mix active download copy: ${JSON.stringify(state)}`);
    }
    await page.screenshot({ path: path.join(outDir, "click-failure.png"), fullPage: true });
    await page.unroute("**/api/video-analysis-request");
    return state;
  });
} catch (error) {
  results.push({ name: "uncaught", ok: false, error: String(error?.message || error) });
  try {
    await page.screenshot({ path: path.join(outDir, "failure.png"), fullPage: true });
  } catch {}
} finally {
  await browser.close();
}

const report = {
  ok: results.every((item) => item.ok),
  generatedAt: new Date().toISOString(),
  results,
};

fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
process.exit(report.ok ? 0 : 1);
