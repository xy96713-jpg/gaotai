#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const base = "http://127.0.0.1:8766";
const reportPath = path.join(root, ".cache", "writing", "workbench_live_generation_latest.json");
const artifactDir = path.join(root, ".cache", "writing", "live_generation_smoke");
const screenshotDir = path.join(root, ".cache", "e2e-screenshots");
fs.mkdirSync(artifactDir, { recursive: true });
fs.mkdirSync(screenshotDir, { recursive: true });
fs.mkdirSync(path.dirname(reportPath), { recursive: true });

const title = "为什么会用 AI 的人，反而更需要自己的判断库？";
const documentId = `live_ai_judgment_library_${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`;
const materialCard = {
  brief:
    "写一篇 900-1200 字中文完整口播稿。主题是：AI 工具越来越强，但能持续用好的人，通常会维护自己的判断库、反例库和修改习惯。开头优先从一条 AI 直写坏句、一个删不掉的开头，或一次划选改句进入。先讲 AI 写作为什么经常不好用，再讲主流解法，紧接着接到我的写作工作台。",
  claim:
    "会用 AI 的关键在于把自己的判断、偏好、反例和工作流沉淀下来，让模型每次都被同一套标准约束；多试几个模型只能解决一小部分问题。",
  sources:
    "失败样本：AI 直写常见套话，比如“当前行业正在快速发展，创作者需要积极拥抱变化，提升自身竞争力”；研究锚点：79 篇实证研究、96 项自动写作评估、Axios 2026、STORM、PaperDebugger、CoAuthor；前后对比样本：直出版坏句 -> 被拦原因 -> 修后版本；读者代价：不用这套系统，最常见的是整篇返工、找不到该删哪一句、最后只能整段重写；工作台动作：主笔接口写稿、改句接口局部改句、收稿检查、前端划选、喜欢/讨厌、导出。",
  readerObjection:
    "读者会怀疑：写文章为什么要这么麻烦，换一个更强模型不就行了？",
  avoidShape:
    "不能写成 AI 写作技巧合集、产品说明书、模型排行，也不能只讲按钮功能。",
  authorTake:
    "我的态度是少相信一键生成，把判断、退稿和风格记忆固定到流程里。",
  noInvent:
    "不要编造具体后台数据、读者私信、采访对象、真实研究数字、平台增长数据、个人收入变化。",
};

const promptBody = [
  `主题：${materialCard.brief}`,
  `核心判断：${materialCard.claim}`,
  `材料事实：${materialCard.sources}`,
  `不能编：${materialCard.noInvent}`,
].join("\n");

const results = [];

function nowIso() {
  return new Date().toISOString();
}

function writeReport(summary) {
  fs.writeFileSync(reportPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
}

async function step(name, fn) {
  const started = Date.now();
  try {
    const value = await fn();
    const item = { name, ok: true, ms: Date.now() - started, value };
    results.push(item);
    console.log(JSON.stringify(item));
    return value;
  } catch (error) {
    const item = { name, ok: false, ms: Date.now() - started, error: String(error?.message || error) };
    results.push(item);
    console.log(JSON.stringify(item));
    return null;
  }
}

async function api(pathname, options = {}, timeoutMs = 360000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(base + pathname, {
      ...options,
      signal: controller.signal,
      headers: {
        "content-type": "application/json",
        ...(options.headers || {}),
      },
    });
    const text = await response.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw: text };
    }
    if (!response.ok) throw new Error(`${response.status} ${JSON.stringify(data).slice(0, 500)}`);
    return data;
  } finally {
    clearTimeout(timer);
  }
}

async function waitForFullDraftJob(jobId, timeoutMs = 600000) {
  if (!jobId) throw new Error("missing full draft job id");
  const started = Date.now();
  let last = null;
  while (Date.now() - started < timeoutMs) {
    last = await api(`/api/full-draft-job/${encodeURIComponent(jobId)}`, {}, 30000);
    if (last.status === "done") {
      return last.result || {};
    }
    if (last.status === "error") {
      throw new Error(last.error || `job ${jobId} failed`);
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error(`job ${jobId} timed out`);
}

function bodyTextFromDraft(draft) {
  return String(draft.minimalBody || draft.body || draft.rawBody || "").trim();
}

function bodyHasHardBan(text) {
  return /不是.{0,40}而是|而不是|不只是.{0,40}更是|真正的问题|真正的关键|随着|重塑|底层逻辑|机遇与挑战|由此可见|这意味着|这说明|B-roll|视频开场/.test(text);
}

async function reveal(page, selector) {
  await page.evaluate(() => {
    document.querySelectorAll("details").forEach((node) => {
      node.open = true;
    });
  });
  const locator = page.locator(selector);
  await locator.scrollIntoViewIfNeeded();
  return locator;
}

async function clickRevealed(page, selector) {
  const locator = await reveal(page, selector);
  await locator.click();
}

async function clickFirstVisible(page, selectors) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if ((await locator.count()) === 0) continue;
    const visible = await locator.isVisible().catch(() => false);
    if (!visible) continue;
    await locator.scrollIntoViewIfNeeded();
    await locator.click();
    return selector;
  }
  throw new Error(`no visible selector found: ${selectors.join(", ")}`);
}

async function selectFirstBodyParagraph(page) {
  await page.evaluate(() => {
    const paragraph = Array.from(document.querySelectorAll("#editor p")).find((node) => (node.textContent || "").trim().length > 20);
    if (!paragraph) throw new Error("no editable paragraph found");
    const range = document.createRange();
    range.selectNodeContents(paragraph);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    document.dispatchEvent(new Event("selectionchange"));
  });
  await page.waitForFunction(() => (document.querySelector("#selectionState")?.textContent || "").includes("已选"));
}

let generatedDraft = null;
let generatedDraftSummary = null;
let savedDocument = null;
let browserScreenshot = "";
let generationBlocked = null;

await step("health has live model config", async () => {
  const health = await api("/api/health", {}, 10000);
  const picked = {
    kimi_configured: health.kimi_configured,
    kimi_model: health.kimi_model,
    kimi_full_thinking: health.kimi_full_thinking,
    deepseek_configured: health.deepseek_configured,
    deepseek_model: health.deepseek_model,
    hybrid_configured: health.hybrid_configured,
  };
  if (!picked.kimi_configured || !picked.hybrid_configured) throw new Error(JSON.stringify(picked));
  return picked;
});

generatedDraftSummary = await step("generate new controlled draft via default writer", async () => {
  const payload = {
    title,
    brief: promptBody,
    materialCard,
    promptMode: "guided",
    provider: "hybrid",
    cleanAiTaste: true,
  };
  const job = await api(
    "/api/full-draft-job",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    30000
  );
  const draft = await waitForFullDraftJob(job.jobId, 600000);
  const body = bodyTextFromDraft(draft);
  const outPath = path.join(artifactDir, `${documentId}_draft.json`);
  fs.writeFileSync(outPath, `${JSON.stringify(draft, null, 2)}\n`, "utf8");
  if (draft.qualityGate?.status !== "allow") {
    generationBlocked = {
      status: draft.qualityGate?.status || "block",
      reasons: draft.qualityGate?.reasons || [],
      artifact: outPath,
      model: draft.model,
      thinking: draft.thinking,
      jobId: job.jobId,
    };
    throw new Error(`qualityGate=${draft.qualityGate?.status}: ${(draft.qualityGate?.reasons || []).join(" / ")}`);
  }
  if (body.length < 850) throw new Error(`draft too short: ${body.length}`);
  if (bodyHasHardBan(body)) throw new Error("draft contains hard-ban surface phrase");
  generatedDraft = draft;
  return {
    jobId: job.jobId,
    title: draft.title,
    model: draft.model,
    thinking: draft.thinking,
    qualityGate: draft.qualityGate,
    bodyLength: body.length,
    artifact: outPath,
  };
});

if (generationBlocked) {
  const failed = results.filter((item) => !item.ok);
  const summary = {
    generatedAt: nowIso(),
    ok: false,
    total: results.length,
    failed: failed.length,
    title,
    documentId,
    documentPath: "",
    screenshot: "",
    blockedByQualityGate: true,
    qualityGate: generationBlocked,
    abortedBeforeBrowser: true,
    results,
  };
  writeReport(summary);
  console.log(JSON.stringify({ summary }, null, 2));
  process.exit(1);
}

savedDocument = await step("save generated draft as workbench document", async () => {
  if (!generatedDraft) throw new Error("missing generated draft");
  const body = bodyTextFromDraft(generatedDraft);
  const contentHtml =
    generatedDraft.minimalContentHtml ||
    generatedDraft.contentHtml ||
    `<h2>${title}</h2>\n${body
      .split(/\n\s*\n+/)
      .map((part) => `<p>${part.replace(/[&<>]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[char]))}</p>`)
      .join("\n")}`;
  const doc = await api(
    "/api/document",
    {
      method: "POST",
      body: JSON.stringify({
        documentId,
        title: generatedDraft.title || title,
        contentHtml,
        contentText: body,
      }),
    },
    30000
  );
  return doc;
});

if (!generatedDraft || !generatedDraftSummary || !savedDocument) {
  const failed = results.filter((item) => !item.ok);
  const summary = {
    generatedAt: nowIso(),
    ok: false,
    total: results.length,
    failed: failed.length,
    title,
    documentId,
    documentPath: savedDocument?.path || "",
    screenshot: "",
    abortedBeforeBrowser: true,
    results,
  };
  writeReport(summary);
  console.log(JSON.stringify({ summary }, null, 2));
  process.exit(1);
}

await step("audit generated document via API", async () => {
  const doc = await api(`/api/document?documentId=${encodeURIComponent(documentId)}`, {}, 15000);
  const audit = await api(
    "/api/quick-audit",
    {
      method: "POST",
      body: JSON.stringify({ title: doc.title, body: doc.contentText }),
    },
    30000
  );
  if (Number(audit.score) < 80) throw new Error(`audit score too low: ${audit.score}`);
  return { score: audit.score, summary: audit.summary, findingCount: audit.findings?.length || 0 };
});

const browser = await chromium.launch({
  headless: true,
  executablePath: chromePath,
  args: ["--no-sandbox", "--disable-gpu"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
page.setDefaultTimeout(15000);

await step("open generated document in browser", async () => {
  await page.goto(`${base}/v2/?documentId=${encodeURIComponent(documentId)}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction((expected) => (document.querySelector("#documentTitle")?.value || "").includes(expected), title.slice(0, 12));
  return {
    title: await page.locator("#documentTitle").inputValue(),
    bodyStart: (await page.locator("#editor").innerText()).slice(0, 120),
  };
});

await step("browser hides manual audit controls", async () => {
  const state = await page.evaluate(() => ({
    topAuditVisible: Boolean(document.querySelector("#quickAuditButton")?.offsetParent),
    sideAuditVisible: Boolean(document.querySelector("#quickAuditAction")?.offsetParent),
    deliveryBlockHidden: Boolean(document.querySelector(".delivery-block")?.hidden),
  }));
  if (state.topAuditVisible || state.sideAuditVisible || !state.deliveryBlockHidden) {
    throw new Error(JSON.stringify(state));
  }
  return state;
});

await step("browser rewrite generated paragraph and accept", async () => {
  await selectFirstBodyParagraph(page);
  let candidateCount = await page.locator("#candidateList .candidate-text").count();
  if (candidateCount === 0) {
    await clickFirstVisible(page, ["#quickRewriteAction", "#runRewrite"]);
    await page.waitForFunction(
      () => Array.from(document.querySelectorAll("#candidateList .candidate-text")).some((node) => node.textContent.trim().length > 0),
      null,
      { timeout: 45000 }
    );
    candidateCount = await page.locator("#candidateList .candidate-text").count();
  }
  const before = await page.locator("#editor").innerText();
  await page.locator("#candidateList [data-accept]").first().click();
  await page.waitForTimeout(400);
  const after = await page.locator("#editor").innerText();
  if (before === after) throw new Error("rewrite accept did not change generated article");
  return {
    selected: (await page.locator("#selectedText").textContent()).slice(0, 120),
    candidateCount,
  };
});

await step("background audit remains available after accepted rewrite", async () => {
  const result = await page.evaluate(async () => {
    const response = await fetch("/api/quick-audit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        title: document.querySelector("#documentTitle")?.value || "",
        body: document.querySelector("#editor")?.innerText || "",
      }),
    });
    if (!response.ok) throw new Error(`audit failed: ${response.status}`);
    return response.json();
  });
  if (Number(result.score || 0) < 70) throw new Error(`audit score too low: ${result.score}`);
  return {
    score: result.score,
    summary: result.summaryLine || result.summary || "",
    findingCount: result.findings?.length || 0,
  };
});

await step("browser export generated article", async () => {
  const selector = await clickFirstVisible(page, ["#exportMd"]);
  await page.waitForTimeout(1500);
  const state = await page.locator("#saveState").textContent();
  const jobState = await page.locator("#jobState").textContent();
  const pathText = await page.locator("#documentPath").textContent();
  const exported = /已导出\s*MD/i.test(String(state || ""));
  const blocked = /硬伤未过|还没检查/.test(String(jobState || ""));
  if (!exported && !blocked) {
    throw new Error(`unexpected export state: saveState=${state || ""} / jobState=${jobState || ""}`);
  }
  return {
    selector,
    state,
    path: pathText,
    jobState,
    exported,
    blocked,
  };
});

await step("browser screenshot generated article", async () => {
  browserScreenshot = path.join(screenshotDir, `workbench-live-generation-${Date.now()}.png`);
  await page.screenshot({ path: browserScreenshot, fullPage: true });
  return browserScreenshot;
});

await browser.close();

const failed = results.filter((item) => !item.ok);
const summary = {
  generatedAt: nowIso(),
  ok: failed.length === 0,
  total: results.length,
  failed: failed.length,
  title,
  documentId,
  documentPath: savedDocument?.path || "",
  screenshot: browserScreenshot,
  results,
};
writeReport(summary);
console.log(JSON.stringify({ summary }, null, 2));
process.exit(failed.length ? 1 : 0);
