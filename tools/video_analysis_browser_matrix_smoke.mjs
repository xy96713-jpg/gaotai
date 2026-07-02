#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const server = (process.env.VIDEO_ANALYSIS_SERVER || "http://127.0.0.1:8766").replace(/\/$/, "");
const outDir = path.join(root, ".cache", "video-analysis-browser-matrix");
const reportPath = path.join(outDir, "latest.json");
const jobDir = path.join(root, ".cache", "video-analysis", "jobs");

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function latestLocalJob(platform, options = {}) {
  const minSlides = Number(options.minSlides || 0);
  const requireTranscript = options.requireTranscript !== false;
  const entries = fs
    .readdirSync(jobDir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => {
      const filePath = path.join(jobDir, name);
      try {
        return { filePath, mtime: fs.statSync(filePath).mtimeMs, data: readJson(filePath) };
      } catch (error) {
        if (error?.code === "ENOENT") return null;
        throw error;
      }
    })
    .filter(Boolean)
    .filter(({ data }) => {
      const summary = data?.summary || {};
      const embed = summary.videoEmbed || data?.videoEmbed || {};
      const actualPlatform = summary.platform || data?.platform || "";
      const slides = summary.demoDeck?.slides || data?.demoDeck?.slides || [];
      const transcriptQuality = summary.transcriptQuality || data?.transcriptQuality || {};
      return (
        data?.status === "done"
        && actualPlatform === platform
        && embed.type === "local"
        && embed.src
        && (!requireTranscript || transcriptQuality.usable !== false)
        && (!minSlides || slides.length >= minSlides)
      );
    })
    .sort((a, b) => b.mtime - a.mtime);
  if (!entries.length) throw new Error(`missing local downloaded ${platform} job`);
  return entries[0].data.id;
}

function writeRemoteCacheFailureFixture() {
  fs.mkdirSync(jobDir, { recursive: true });
  const jobId = "video_browser_matrix_required_local_remote_embed";
  const filePath = path.join(jobDir, `${jobId}.json`);
  const payload = {
    id: jobId,
    status: "done",
    stage: "done",
    message: "分析完成",
    requireLocalVideo: true,
    url: "https://www.bilibili.com/video/BV1ZB4zeeEEb/",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    summary: {
      platform: "bilibili",
      videoEmbed: {
        type: "bilibili",
        watchUrl: "https://www.bilibili.com/video/BV1ZB4zeeEEb/",
      },
      transcriptSource: "yt-dlp-embedded-subtitle:ai-zh",
      videoSummary: {
        headline: "旧缓存只有内嵌播放，不能算下载成功。",
        bullets: ["这个夹具用于确认严格下载门槛不会被旧缓存绕过。"],
        takeaway: "必须失败，而不是显示成完成。",
      },
      timeline: [{ timeLabel: "00:00", transcriptExcerpt: "旧缓存字幕" }],
      demoDeck: {
        slides: [{ title: "旧缓存页", frameKind: "screenshot" }],
        evidenceStatus: { label: "截图 1 张", ready: true },
      },
      demoDeckVersion: 54,
      videoTimelineVersion: 14,
      videoSummaryVersion: 25,
      writingCardsVersion: 3,
      writingPackVersion: 4,
    },
    events: [],
  };
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
  return jobId;
}

function writeStaleCaptionRecoveryFixture() {
  fs.mkdirSync(jobDir, { recursive: true });
  const url = "https://www.youtube.com/watch?v=matrixCaptionRecovery001";
  const localVideoPath = path.join(root, ".cache", "video-analysis", "test-local-upload.mp4");
  const localSrc = `/api/video-analysis-file?path=${encodeURIComponent(localVideoPath)}`;
  const cachedId = "video_browser_matrix_cached_caption_source";
  const staleId = "video_browser_matrix_stale_caption_recovery";
  const now = new Date().toISOString();
  const commonSummary = {
    platform: "youtube",
    auth: "chrome",
    downloadPolicy: {
      status: "ready",
      label: "已保存本地",
      localVideoBytes: 65536,
      sizeLabel: "64KB",
    },
    videoEmbed: {
      type: "local",
      src: localSrc,
      watchUrl: url,
      localPath: localVideoPath,
      localVideoPath,
    },
    transcriptSource: "local-cached-caption:matrixCaptionRecovery001.zh-Hans.vtt",
    transcriptQuality: {
      level: "strong",
      label: "字幕可靠",
      usable: true,
      fallback: "可以作为主要拆解依据。",
      segmentCount: 6,
      source: "local-cached-caption:matrixCaptionRecovery001.zh-Hans.vtt",
    },
    videoSummary: {
      headline: "这条视频用一个短演示说明坐太久为什么会影响状态。",
      bullets: ["开头先交代问题。", "中段拿出身体反应。", "结尾给出走动对比。"],
      takeaway: "先看证据，再写判断。",
    },
    timeline: [
      { timeLabel: "00:00", start: 0, frameUrl: "", summary: "先交代问题", writingValue: "开头先说明为什么要看。", writingAngle: "入口", transcriptExcerpt: "这不是精神不想动，而是身体先被坐住了。" },
      { timeLabel: "01:00", start: 60, frameUrl: "", summary: "说明常见感受", writingValue: "把问题落到人能感到的状态。", writingAngle: "感受", transcriptExcerpt: "很多人以为自己只是没精神，其实身体也在发出信号。" },
      { timeLabel: "02:00", start: 120, frameUrl: "", summary: "拿出身体反应", writingValue: "用身体状态解释问题。", writingAngle: "证据", transcriptExcerpt: "坐久以后，人会觉得身体累，注意力也跟着变差。" },
      { timeLabel: "03:00", start: 180, frameUrl: "", summary: "解释为什么会累", writingValue: "补上中间机制。", writingAngle: "机制", transcriptExcerpt: "身体长时间不动，血液循环和肌肉状态都会受影响。" },
      { timeLabel: "04:00", start: 240, frameUrl: "", summary: "给出走动对比", writingValue: "用对比收束结论。", writingAngle: "转折", transcriptExcerpt: "短时间走动以后，身体负担会明显不同。" },
      { timeLabel: "05:00", start: 300, frameUrl: "", summary: "落到可执行动作", writingValue: "给观众一个能做的动作。", writingAngle: "动作", transcriptExcerpt: "关键不是一次运动多久，而是不要让身体连续坐太久。" },
    ],
    demoDeck: {
      templateKey: "evidence",
      templateLabel: "拆解",
      slides: [
        { title: "先交代问题", frameKind: "screenshot", frameUrl: "", timeLabel: "00:00", action: "开场先讲为什么要看。", meaning: "让观众知道这不是泛泛谈健康。", speakerNote: "先说问题，再进入证据。", sourceQuote: "这不是精神不想动，而是身体先被坐住了。" },
        { title: "拿出身体反应", frameKind: "screenshot", frameUrl: "", timeLabel: "02:00", action: "中段讲身体反应。", meaning: "让判断落到人能感到的变化。", speakerNote: "把抽象健康风险讲成身体感受。", sourceQuote: "坐久以后，人会觉得身体累，注意力也跟着变差。" },
        { title: "给出走动对比", frameKind: "screenshot", frameUrl: "", timeLabel: "04:00", action: "结尾用走动做对比。", meaning: "给出观众能记住的动作。", speakerNote: "用一个动作收束。", sourceQuote: "短时间走动以后，身体负担会明显不同。" },
      ],
      evidenceStatus: { label: "字幕可靠", ready: true, slideCount: 3, screenshotSlides: 0, uniqueScreenshots: 0 },
      demoDeckQuality: { status: "ready", label: "可用", issues: [], strongSlideCount: 3, score: 80 },
    },
    demoDeckVersion: 999,
    videoTimelineVersion: 999,
    videoSummaryVersion: 999,
    writingCardsVersion: 3,
    writingPackVersion: 4,
  };
  commonSummary.transcriptSegments = commonSummary.timeline.map((item) => ({ start: item.start, duration: 6, text: item.transcriptExcerpt }));
  const cached = {
    id: cachedId,
    status: "done",
    stage: "done",
    message: "分析完成",
    url,
    requireLocalVideo: true,
    result: {
      url,
      title: "字幕缓存恢复夹具",
      source_video_path: localVideoPath,
      transcript_source: commonSummary.transcriptSource,
      transcript_segments: commonSummary.timeline.map((item) => ({ start: item.start, duration: 6, text: item.transcriptExcerpt })),
    },
    summary: commonSummary,
    transcriptMarkdown: "# Transcript\n\n- Source: local-cached-caption:matrixCaptionRecovery001.zh-Hans.vtt\n- Segment count: 6\n\n[00:00] 这不是精神不想动，而是身体先被坐住了。",
    createdAt: now,
    updatedAt: now,
    events: [],
  };
  const stale = {
    id: staleId,
    status: "done",
    stage: "done",
    message: "旧缓存",
    url,
    requireLocalVideo: true,
    result: {
      url,
      title: "字幕缓存恢复夹具",
      source_video_path: localVideoPath,
      transcript_source: "none",
      transcript_segments: [],
    },
    summary: {
      platform: "youtube",
      downloadPolicy: commonSummary.downloadPolicy,
      videoEmbed: commonSummary.videoEmbed,
      transcriptSource: "none",
      transcriptQuality: { level: "none", label: "无字幕", usable: false, segmentCount: 0 },
      timeline: [],
      demoDeck: {},
      demoDeckVersion: 0,
      videoTimelineVersion: 0,
      videoSummaryVersion: 0,
      writingCardsVersion: 0,
      writingPackVersion: 0,
    },
    createdAt: now,
    updatedAt: now,
    events: [],
  };
  fs.writeFileSync(path.join(jobDir, `${staleId}.json`), JSON.stringify(stale, null, 2), "utf8");
  fs.writeFileSync(path.join(jobDir, `${cachedId}.json`), JSON.stringify(cached, null, 2), "utf8");
  return staleId;
}

function writeLocalMissingTranscriptFixture() {
  fs.mkdirSync(jobDir, { recursive: true });
  const jobId = "video_browser_matrix_local_missing_transcript";
  const filePath = path.join(jobDir, `${jobId}.json`);
  const videoPath = path.join(root, ".cache", "video-analysis", "test-local-upload.mp4");
  const src = `/api/video-analysis-file?path=${encodeURIComponent(videoPath)}`;
  const payload = {
    id: jobId,
    status: "done",
    stage: "done",
    message: "分析完成",
    requireLocalVideo: true,
    url: `file://${videoPath}`,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    result: {
      title: "本地视频测试",
      source_video_path: videoPath,
      transcript_source: "none",
      transcript_segments: [],
    },
    summary: {
      platform: "local",
      transcriptSource: "none",
      transcriptQuality: {
        usable: false,
        label: "没拿到字幕",
        level: "missing",
        fallback: "暂不生成稿。",
        segmentCount: 0,
      },
      downloadPolicy: {
        status: "local",
        label: "本地视频",
        sizeLabel: "64KB",
      },
      videoEmbed: {
        type: "local",
        src,
        watchUrl: src,
        localVideoPath: videoPath,
      },
      videoSummary: {
        headline: "本地视频测试",
        bullets: ["本地视频已保存，但没有字幕。"],
        takeaway: "可以先看视频，暂不生成稿。",
      },
      timeline: [],
      demoDeck: {
        templateKey: "blocked",
        templateLabel: "字幕未取到",
        slides: [],
        evidenceStatus: {
          slideCount: 0,
          screenshotSlides: 0,
          uniqueScreenshots: 0,
          coverSlides: 0,
          missingImages: 0,
          ready: false,
          label: "字幕未取到",
        },
        demoDeckQuality: {
          status: "blocked",
          label: "字幕未取到",
          issues: ["没拿到字幕，暂不生成稿。"],
          strengths: [],
          coveredProductDimensions: [],
          missingProductDimensions: [],
          coveredProductInsights: [],
          missingProductInsights: [],
          requiredProductDimensions: [],
          routeRoleIssue: "没拿到字幕，暂不生成稿。",
          nextBestUse: "可以先看视频，暂不生成稿。",
          slideChecks: [],
          strongSlideCount: 0,
          score: 0,
        },
      },
      demoDeckVersion: 82,
      videoTimelineVersion: 15,
      videoSummaryVersion: 29,
      writingCardsVersion: 3,
      writingPackVersion: 4,
    },
    events: [],
  };
  payload.videoEmbed = payload.summary.videoEmbed;
  payload.demoDeck = payload.summary.demoDeck;
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
  return jobId;
}

const scenarios = [
  {
    name: "youtube_local_download",
    jobId: latestLocalJob("youtube", { minSlides: 3, requireTranscript: true }),
    expect: "ready",
    mustContain: ["已保存本地", "先看懂", "拆解"],
    mustNotContain: ["等视频", "原视频", "内嵌播放，未下载", "登录态", "本地缓存", "保存副本"],
  },
  {
    name: "bilibili_local_download",
    jobId: latestLocalJob("bilibili", { minSlides: 3, requireTranscript: true }),
    expect: "ready",
    mustContain: ["已保存本地", "先看懂", "拆解"],
    mustNotContain: ["等视频", "原视频", "内嵌播放，未下载", "登录态", "本地缓存", "保存副本"],
  },
  {
    name: "stale_caption_cache_recovers",
    jobId: writeStaleCaptionRecoveryFixture(),
    expect: "ready",
    mustContain: ["已保存本地", "先看懂", "拆解"],
    mustNotContain: ["无字幕", "缺字幕", "材料不足", "等视频", "原视频", "内嵌播放，未下载", "登录态", "本地缓存", "保存副本"],
  },
  {
    name: "local_video_missing_transcript_blocks_deck",
    jobId: writeLocalMissingTranscriptFixture(),
    expect: "blockedDeck",
    mustContain: ["已保存本地", "先看视频", "没拿到字幕"],
    mustNotContain: ["拆解", "生成讲稿", "材料状态", "材料不足", "无字幕", "缺字幕", "先抛出问题", "拿出证据", "讲清转折"],
  },
  {
    name: "required_local_remote_cache_fails",
    jobId: writeRemoteCacheFailureFixture(),
    expect: "error",
    mustContain: ["失败", "没有下载到本地视频", "本次没有继续分析"],
    mustNotContain: ["先看懂", "拆解", "登录态", "本地缓存"],
  },
];

const internalCopyMustNotAppear = [
  "先记对象",
  "画面判断",
  "原话转述",
  "再分清哪一段",
  "像证据",
  "像转折",
  "关键词和原话",
  "先做证据卡",
  "关键缺口",
  "可写成",
  "观点稿",
  "判断稿",
  "产品问题",
  "产品判断",
  "这一页值在哪",
  "原始证据",
  "现实门槛",
  "重点不是",
  "而是",
  "功能名",
  "需补材料",
  "这页可以作为文章主判断",
  "可作为文章主判断",
  "后台规则",
  "AI字幕",
  "AI 字幕",
  "转写工具",
  "依据：",
  "发生：",
  "可讲：",
  "用途：",
  "覆盖：",
  "还缺：",
  "注意：",
  "成语转换",
];

for (const scenario of scenarios) {
  scenario.mustNotContain = [...(scenario.mustNotContain || []), ...internalCopyMustNotAppear];
}

fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-gpu"],
});

const page = await browser.newPage({ viewport: { width: 1440, height: 1800 } });
page.setDefaultTimeout(30000);

const results = [];

async function runScenario(scenario) {
  const started = Date.now();
  const url = `${server}/video-analysis?jobId=${encodeURIComponent(scenario.jobId)}`;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#urlInput");
    if (scenario.expect === "ready") {
      await page.waitForFunction(() => {
        const playback = document.querySelector("#playbackSource")?.textContent || "";
        return playback.includes("已保存本地");
      });
    } else if (scenario.expect === "blockedDeck") {
      await page.waitForFunction(() => {
        const playback = document.querySelector("#playbackSource")?.textContent || "";
        const text = document.body.innerText || "";
        return playback.includes("已保存本地") && text.includes("没拿到字幕");
      });
    } else if (scenario.expect === "error") {
      await page.waitForFunction(() => /失败/.test(document.body.innerText) && document.body.innerText.includes("没有下载到本地视频"));
    } else {
      await page.waitForTimeout(900);
    }
    const bodyText = await page.evaluate(() => document.body.innerText.replace(/\s+/g, " "));
    const playback = ((await page.locator("#playbackSource").textContent().catch(() => "")) || "").trim();
    const cardCount = await page.locator("#demoDeckList .demo-card").count().catch(() => 0);
    for (const needle of scenario.mustContain || []) {
      if (!bodyText.includes(needle) && !playback.includes(needle)) {
        throw new Error(`missing expected copy: ${needle}`);
      }
    }
    for (const needle of scenario.mustNotContain || []) {
      if (bodyText.includes(needle) || playback.includes(needle)) {
        throw new Error(`unexpected stale copy: ${needle}`);
      }
    }
    if (scenario.expect === "ready") {
      if (!/已保存本地/.test(playback)) throw new Error(`expected local playback, got: ${playback}`);
      if (cardCount < 3) throw new Error(`expected at least 3 demo cards, got ${cardCount}`);
    }
    if (scenario.expect === "blockedDeck" && cardCount !== 0) {
      throw new Error(`missing-transcript scenario should hide demo cards, got ${cardCount}`);
    }
    if (scenario.expect === "error" && /已保存本地|已下载到本地/.test(playback)) {
      throw new Error(`error scenario should not show local playback: ${playback}`);
    }
    const screenshot = path.join(outDir, `${scenario.name}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    results.push({
      name: scenario.name,
      ok: true,
      ms: Date.now() - started,
      url: page.url(),
      playback,
      cards: cardCount,
      screenshot,
    });
  } catch (error) {
    results.push({
      name: scenario.name,
      ok: false,
      ms: Date.now() - started,
      url,
      error: String(error?.message || error),
    });
  }
}

try {
  for (const scenario of scenarios) {
    await runScenario(scenario);
  }
} finally {
  await browser.close();
}

const report = {
  ok: results.every((item) => item.ok),
  generatedAt: new Date().toISOString(),
  scenarios: results,
  note: "Browser matrix covers current product contract: successful jobs must show local video; strict remote-cache jobs must fail.",
};

fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
process.exit(report.ok ? 0 : 1);
