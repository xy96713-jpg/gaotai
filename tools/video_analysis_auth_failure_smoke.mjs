#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const server = (process.env.VIDEO_ANALYSIS_SERVER || "http://127.0.0.1:8766").replace(/\/$/, "");
const outDir = path.join(root, ".cache", "video-analysis-auth-failure-smoke");
const jobDir = path.join(root, ".cache", "video-analysis", "jobs");
const jobId = "video_auth_failure_smoke";
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(jobDir, { recursive: true });

const fixture = {
  id: jobId,
  url: "https://www.youtube.com/watch?v=auth-smoke",
  title: "Auth Smoke Video",
  status: "error",
  stage: "error",
  message: "视频资料抓取失败。这个链接暂时不可用、需要登录，或平台没有返回可下载视频。",
  error: "ERROR: [youtube] auth-smoke: Sign in to confirm you’re not a bot. Use --cookies-from-browser or --cookies for the authentication.",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  cookiesFromBrowser: "none",
  requireLocalVideo: true,
  events: [],
};

fs.writeFileSync(path.join(jobDir, `${jobId}.json`), JSON.stringify(fixture, null, 2), "utf8");

const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-gpu"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(30000);
const result = { ok: false };

try {
  let rerunPayload = null;
  await page.route(`${server}/api/video-analysis-request`, async (route) => {
    rerunPayload = JSON.parse(route.request().postData() || "{}");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "video_auth_failure_smoke_rerun",
        url: rerunPayload.url,
        title: "Auth Smoke Video",
        status: "queued",
        stage: "queued",
        cookiesFromBrowser: rerunPayload.cookiesFromBrowser,
        requireLocalVideo: true,
        events: [],
      }),
    });
  });

  await page.goto(`${server}/video-analysis?jobId=${jobId}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector('[data-video-action="open-platform-login"]');
  await page.waitForSelector('[data-video-action="rerun-with-chrome"]');
  const failureText = (await page.locator("#jobSummary").textContent()).replace(/\s+/g, " ").trim();
  const loginLabel = await page.locator('[data-video-action="open-platform-login"]').textContent();
  const rerunLabel = await page.locator('[data-video-action="rerun-with-chrome"]').textContent();
  const failureScreenshot = path.join(outDir, "auth-failure-before-rerun.png");
  await page.screenshot({ path: failureScreenshot, fullPage: true });
  await page.locator('[data-video-action="rerun-with-chrome"]').click();
  await page.waitForFunction(() => {
    const summary = document.querySelector("#jobSummary")?.textContent || "";
    const status = document.querySelector("#jobStatus")?.textContent || "";
    return summary.includes("准备下载") || summary.includes("等待中") || status.includes("待下载");
  });
  if (!rerunPayload || rerunPayload.cookiesFromBrowser !== "chrome") {
    throw new Error(`rerun did not use Chrome cookies: ${JSON.stringify(rerunPayload)}`);
  }
  const screenshot = path.join(outDir, "auth-failure-after-rerun.png");
  await page.screenshot({ path: screenshot, fullPage: true });
  result.ok = true;
  result.failureText = failureText;
  result.loginLabel = loginLabel;
  result.rerunLabel = rerunLabel;
  result.rerunPayload = rerunPayload;
  result.failureScreenshot = failureScreenshot;
  result.screenshot = screenshot;
} catch (error) {
  result.error = String(error?.message || error);
} finally {
  await browser.close();
  try {
    fs.rmSync(path.join(jobDir, `${jobId}.json`), { force: true });
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
