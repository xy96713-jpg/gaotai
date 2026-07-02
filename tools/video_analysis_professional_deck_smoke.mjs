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
const requestedJobId = (process.env.VIDEO_ANALYSIS_JOB_ID || "").trim();
const outDir = path.join(root, ".cache", "video-analysis-professional-deck-smoke");
const reportPath = path.join(outDir, "latest.json");

fs.mkdirSync(outDir, { recursive: true });

async function fetchJson(endpoint) {
  const response = await fetch(`${server}${endpoint}`);
  if (!response.ok) throw new Error(`${endpoint} returned ${response.status}`);
  return response.json();
}

function parseTimeSeconds(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const text = String(value || "").trim();
  if (!text) return null;
  if (!text.includes(":")) {
    const numeric = Number(text);
    return Number.isFinite(numeric) && numeric >= 0 ? numeric : null;
  }
  const parts = text.split(":").map((part) => Number(part));
  if (parts.some((part) => !Number.isFinite(part))) return null;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return null;
}

function normalizeAssetUrl(value) {
  return String(value || "").trim();
}

function slideFrameTiming(detail) {
  const frames = Array.isArray(detail.frames)
    ? detail.frames
    : Array.isArray(detail.summary?.frames)
      ? detail.summary.frames
      : [];
  const frameTimestamps = new Map();
  for (const frame of frames) {
    const url = normalizeAssetUrl(frame?.url || frame?.frameUrl || "");
    const timestamp = parseTimeSeconds(frame?.timestamp);
    if (url && timestamp !== null) frameTimestamps.set(url, timestamp);
  }
  const slides = detail.demoDeck?.slides || [];
  const deltas = [];
  for (const slide of slides) {
    if (String(slide?.frameKind || "") !== "screenshot") continue;
    const start = parseTimeSeconds(slide?.startSeconds ?? slide?.start ?? slide?.timeLabel);
    const frameUrl = normalizeAssetUrl(slide?.frameUrl || "");
    let frameTime = parseTimeSeconds(slide?.frameTimestamp);
    if (frameTime === null && frameUrl) frameTime = frameTimestamps.get(frameUrl) ?? null;
    if (start === null || frameTime === null) continue;
    deltas.push({
      index: slide?.index || deltas.length + 1,
      title: normalizeText(slide?.title || ""),
      start,
      frameTime,
      delta: Math.abs(frameTime - start),
    });
  }
  const maxDelta = deltas.reduce((max, item) => Math.max(max, item.delta), 0);
  const bad = deltas.filter((item) => item.delta > 75);
  return { deltas, maxDelta, bad };
}

async function goodJob(id) {
  const detail = await fetchJson(`/api/video-analysis-job/${encodeURIComponent(id)}`);
  const source = `${detail.playbackSource || detail.sourceStatus || ""}`;
  const slides = detail.demoDeck?.slides || [];
  const quality = detail.transcriptQuality || detail.summary?.transcriptQuality || {};
  const deckQuality = detail.demoDeck?.demoDeckQuality || {};
  const screenshotUrls = slides
    .filter((slide) => slide?.frameUrl && !/cover/i.test(String(slide.frameKind || "")))
    .map((slide) => String(slide.frameUrl || ""));
  const screenshots = screenshotUrls.length;
  const uniqueScreenshots = new Set(screenshotUrls).size;
  const timing = slideFrameTiming(detail);
  return {
    id,
    detail,
    ok:
      /已保存本地|已下载到本地/.test(source)
      && quality.usable !== false
      && slides.length >= 4
      && screenshots >= 3
      && uniqueScreenshots >= Math.min(4, slides.length)
      && deckQuality.status !== "blocked"
      && deckQuality.status !== "needs_work"
      && timing.bad.length === 0,
    source,
    slides: slides.length,
    screenshots,
    uniqueScreenshots,
    maxFrameDelta: Math.round(timing.maxDelta),
    badFrameDeltas: timing.bad,
    deckStatus: deckQuality.status || "",
  };
}

async function resolveJobId() {
  if (requestedJobId) {
    const candidate = await goodJob(requestedJobId);
    if (!candidate.ok) {
      throw new Error(`requested job is not professional-ready: ${JSON.stringify({
        id: candidate.id,
        source: candidate.source,
        slides: candidate.slides,
        screenshots: candidate.screenshots,
        uniqueScreenshots: candidate.uniqueScreenshots,
        maxFrameDelta: candidate.maxFrameDelta,
        badFrameDeltas: candidate.badFrameDeltas,
        deckStatus: candidate.deckStatus,
      })}`);
    }
    return requestedJobId;
  }
  for (const id of [
    "video_20260702_041238_b2c055ca",
    "video_20260701_233659_b6f487ba",
    "video_20260702_004605_670c7f05",
  ]) {
    try {
      const candidate = await goodJob(id);
      if (candidate.ok) return id;
    } catch {
      // Try the next stable job.
    }
  }
  const jobsPayload = await fetchJson("/api/video-analysis-jobs");
  const items = Array.isArray(jobsPayload) ? jobsPayload : jobsPayload?.jobs || [];
  for (const item of items) {
    const id = item.jobId || item.id;
    if (!id || item.status !== "done") continue;
    try {
      const candidate = await goodJob(id);
      if (candidate.ok) return id;
    } catch {
      // Try the next job.
    }
  }
  throw new Error("missing local downloaded video job with >=4 slides and >=3 screenshots");
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function assertNoForbiddenText(label, text, forbidden) {
  const hits = forbidden.filter((pattern) => pattern.test(text));
  if (hits.length) {
    throw new Error(`${label} contains forbidden template/system copy: ${hits.map((item) => item.source).join(", ")}`);
  }
}

const visibleForbidden = [
  /依据：/,
  /材料不足/,
  /材料状态/,
  /先补材料/,
  /补充/,
  /等视频/,
  /原视频/,
  /内嵌播放，未下载/,
  /登录态/,
  /本地缓存/,
  /保存副本/,
  /可写成/,
  /AI字幕/,
  /这段有可回看的证据/,
  /先抛出问题/,
  /拿出证据/,
  /别和模型进步硬拼/,
  /观众记住/,
  /这一页回答/,
  /后台规则/,
  /假进度/,
  /模板味/,
  /系统话/,
];

const pptxForbidden = [
  /VIDEO MATERIAL DECK/,
  /本地证据/,
  /视频拆解稿/,
  /先看画面，再讲判断/,
  /发生了什么/,
  /讲给观众听/,
  /观众记住/,
  /这一页回答什么/,
  /Codex 视频材料/,
  /无截图/,
];

const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-gpu"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 2200 },
  acceptDownloads: true,
});
const page = await context.newPage();
page.setDefaultTimeout(30000);

const report = {
  ok: false,
  generatedAt: new Date().toISOString(),
  steps: [],
};

async function step(name, fn) {
  const started = Date.now();
  try {
    const value = await fn();
    report.steps.push({ name, ok: true, ms: Date.now() - started, value });
    return value;
  } catch (error) {
    report.steps.push({ name, ok: false, ms: Date.now() - started, error: String(error?.message || error) });
    throw error;
  }
}

try {
  const jobId = await resolveJobId();
  report.jobId = jobId;
  const url = `${server}/video-analysis?jobId=${encodeURIComponent(jobId)}`;
  report.url = url;

  await step("open downloaded video job", async () => {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#urlInput");
    await page.waitForFunction(() => {
      const title = document.querySelector("#resultTitle")?.textContent || "";
      const source = document.querySelector("#playbackSource")?.textContent || "";
      const cards = document.querySelectorAll("#demoDeckList .demo-card").length;
      return title.trim() && /已保存本地|已下载到本地/.test(source) && cards >= 4;
    });
    return {
      title: normalizeText(await page.locator("#resultTitle").textContent()),
      source: normalizeText(await page.locator("#playbackSource").textContent()),
    };
  });

  await step("visible material is clean and concrete", async () => {
    const bodyText = normalizeText(await page.locator("body").evaluate((node) => node.innerText));
    assertNoForbiddenText("visible page", bodyText, visibleForbidden);
    const cards = await page.locator("#demoDeckList .demo-card").count();
    if (cards < 4) throw new Error(`expected >=4 demo cards, got ${cards}`);
    const imageCount = await page.locator("#demoDeckList .demo-card img").count();
    if (imageCount < 3) throw new Error(`expected >=3 screenshot images, got ${imageCount}`);
    const imageSources = await page.locator("#demoDeckList .demo-card img").evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute("src") || "").filter(Boolean)
    );
    const uniqueImageSources = new Set(imageSources);
    if (uniqueImageSources.size < Math.min(4, cards)) {
      throw new Error(`expected varied screenshots, got ${uniqueImageSources.size}/${imageSources.length} unique images`);
    }
    for (let index = 1; index < imageSources.length; index += 1) {
      if (imageSources[index] === imageSources[index - 1]) {
        throw new Error(`adjacent demo cards reuse the same screenshot at ${index} and ${index + 1}`);
      }
    }
    const emptyCards = await page.locator("#demoDeckList .demo-card-empty").count();
    if (emptyCards > 1) throw new Error(`too many empty media slots: ${emptyCards}`);
    const timeLabels = await page.locator("#demoDeckList .demo-card-time").evaluateAll((nodes) => nodes.map((node) => node.textContent?.trim()).filter(Boolean));
    const uniqueTimes = new Set(timeLabels);
    if (uniqueTimes.size < Math.min(4, timeLabels.length)) {
      throw new Error(`timestamps are not varied enough: ${timeLabels.join(", ")}`);
    }
    const cardTexts = await page.locator("#demoDeckList .demo-card").evaluateAll((nodes) => nodes.map((node) => node.innerText.replace(/\s+/g, " ").trim()));
    cardTexts.forEach((text, index) => {
      if (text.length < 38) throw new Error(`card ${index + 1} is too thin: ${text}`);
      if (!/第\s*\d+\s*页/.test(text)) throw new Error(`card ${index + 1} missing page index: ${text}`);
      assertNoForbiddenText(`card ${index + 1}`, text, visibleForbidden);
    });
    await page.screenshot({ path: path.join(outDir, "material.png"), fullPage: true });
    const detail = await fetchJson(`/api/video-analysis-job/${encodeURIComponent(jobId)}`);
    const timing = slideFrameTiming(detail);
    if (timing.bad.length) {
      throw new Error(`screenshot timestamps drift from slide times: ${JSON.stringify(timing.bad)}`);
    }
    return { cards, imageCount, uniqueImageCount: uniqueImageSources.size, emptyCards, timeLabels, maxFrameDelta: Math.round(timing.maxDelta) };
  });

  await step("generate deck workspace", async () => {
    await page.locator("#generateDeck").click();
    await page.waitForSelector("#deckWorkspace:not(.hidden)");
    await page.waitForSelector("#draftActions:not(.hidden)");
    const workspaceText = normalizeText(await page.locator("#draftPanel").evaluate((node) => node.innerText));
    assertNoForbiddenText("deck workspace", workspaceText, visibleForbidden);
    const focusTitle = normalizeText(await page.locator("#deckFocus .deck-focus-title").textContent());
    if (!focusTitle) throw new Error("missing focused slide title");
    await page.screenshot({ path: path.join(outDir, "deck-workspace.png"), fullPage: true });
    return {
      focusTitle,
      previewSlides: await page.locator("#deckPreview .deck-slide-preview").count(),
    };
  });

  await step("download PPTX and inspect content", async () => {
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.locator("#saveDeckPptx").click(),
    ]);
    const suggested = download.suggestedFilename() || "video-deck.pptx";
    const pptxPath = path.join(outDir, suggested.endsWith(".pptx") ? suggested : `${suggested}.pptx`);
    await download.saveAs(pptxPath);
    const stat = fs.statSync(pptxPath);
    if (stat.size < 15_000) throw new Error(`PPTX too small: ${stat.size} bytes`);
    const header = fs.readFileSync(pptxPath).subarray(0, 2).toString("utf8");
    if (header !== "PK") throw new Error("downloaded file is not a PPTX zip");
    const slideXml = execFileSync("unzip", ["-p", pptxPath, "ppt/slides/slide*.xml"], { encoding: "utf8" });
    assertNoForbiddenText("PPTX", slideXml, pptxForbidden);
    for (const required of ["视频讲稿", "判断", "画面", "讲这一页", "收束", "视频截图"]) {
      if (!slideXml.includes(required)) throw new Error(`PPTX missing required public label: ${required}`);
    }
    const entries = execFileSync("unzip", ["-Z1", pptxPath], { encoding: "utf8" })
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);
    const slideEntries = entries
      .filter((item) => /^ppt\/slides\/slide\d+\.xml$/.test(item))
      .sort((a, b) => Number(a.match(/slide(\d+)\.xml/)?.[1] || 0) - Number(b.match(/slide(\d+)\.xml/)?.[1] || 0));
    const mediaEntries = entries.filter((item) => /^ppt\/media\/.+\.(jpe?g|png)$/i.test(item));
    if (slideEntries.length < 5) throw new Error(`PPTX should include cover plus >=4 content slides, got ${slideEntries.length}`);
    if (mediaEntries.length < 4) throw new Error(`PPTX should embed >=4 media images, got ${mediaEntries.length}`);
    const contentSlideEntries = slideEntries.slice(1);
    for (const slideEntry of contentSlideEntries) {
      const relEntry = slideEntry.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels";
      const relXml = execFileSync("unzip", ["-p", pptxPath, relEntry], { encoding: "utf8" });
      if (!/relationships\/image/.test(relXml)) {
        throw new Error(`${slideEntry} has no embedded image relationship`);
      }
    }
    return {
      file: pptxPath,
      bytes: stat.size,
      suggested,
      slides: slideEntries.length,
      media: mediaEntries.length,
    };
  });

  report.ok = true;
} catch (error) {
  report.ok = false;
  report.error = String(error?.message || error);
} finally {
  await browser.close();
}

fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
process.exit(report.ok ? 0 : 1);
