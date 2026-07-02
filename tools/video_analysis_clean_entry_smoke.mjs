#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const server = (process.env.VIDEO_ANALYSIS_SERVER || "http://127.0.0.1:8766").replace(/\/$/, "");
const outDir = path.join(root, ".cache", "video-analysis-clean-entry");
const reportPath = path.join(outDir, "latest.json");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
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

try {
  await step("open clean entry", async () => {
    await page.goto(`${server}/video-analysis`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#urlInput");
    await page.waitForTimeout(500);
    const state = await page.evaluate(() => ({
      href: location.href,
      title: document.querySelector("#resultTitle")?.textContent?.trim() || "",
      status: document.querySelector("#jobStatus")?.textContent?.trim() || "",
      videoHidden: document.querySelector("#videoStage")?.classList.contains("hidden"),
      summaryHidden: document.querySelector(".video-summary")?.classList.contains("hidden"),
      deckHidden: document.querySelector("#demoDeckSection")?.classList.contains("hidden"),
      timelineHidden: document.querySelector(".timeline-section")?.classList.contains("hidden"),
      playback: document.querySelector("#playbackSource")?.textContent?.trim() || "",
      jobId: new URL(location.href).searchParams.get("jobId") || "",
      body: document.body.innerText,
    }));
    if (state.jobId) throw new Error(`clean entry should not inject jobId, got ${state.jobId}`);
    if (state.title !== "贴一个视频链接") throw new Error(`clean entry should keep empty title, got ${state.title}`);
    if (!state.videoHidden) throw new Error("clean entry should hide video stage");
    if (!state.summaryHidden) throw new Error("clean entry should hide summary");
    if (!state.deckHidden) throw new Error("clean entry should hide demo deck");
    if (!state.timelineHidden) throw new Error("clean entry should hide timeline");
    if (state.playback) throw new Error(`clean entry should not show playback source: ${state.playback}`);
    if (/已保存本地|已下载到本地|结论|拆解卡|拆解页/.test(state.body)) {
      throw new Error("clean entry leaked previous job content");
    }
    return {
      href: state.href,
      title: state.title,
      status: state.status,
      screenshot: path.join(outDir, "clean.png"),
    };
  });

  await page.screenshot({ path: path.join(outDir, "clean.png"), fullPage: true });

  await step("history can load previous job", async () => {
    await page.locator("#openHistory").click();
    await page.waitForSelector("#historyDrawer:not(.hidden)");
    await page.waitForSelector("#jobList .job.local-ready");
    await page.locator("#jobList .job.local-ready").first().click();
    await page.waitForFunction(() => new URL(location.href).searchParams.get("jobId"));
    await page.waitForFunction(() => {
      const title = document.querySelector("#resultTitle")?.textContent?.trim() || "";
      const videoHidden = document.querySelector("#videoStage")?.classList.contains("hidden");
      return title && title !== "贴一个视频链接" && !videoHidden;
    });
    const loaded = await page.evaluate(() => ({
      href: location.href,
      title: document.querySelector("#resultTitle")?.textContent?.trim() || "",
      playback: document.querySelector("#playbackSource")?.textContent?.trim() || "",
    }));
    if (!loaded.playback.includes("已保存本地")) {
      throw new Error(`history loaded job should show local video state, got ${loaded.playback}`);
    }
    return {
      href: loaded.href,
      title: loaded.title,
      playback: loaded.playback,
      screenshot: path.join(outDir, "history-loaded.png"),
    };
  });

  await page.screenshot({ path: path.join(outDir, "history-loaded.png"), fullPage: true });
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
