#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromE2e = createRequire(path.join(root, ".cache/e2e-node/package.json"));
const { chromium } = requireFromE2e("playwright-core");

const chromePath = process.env.WORKBENCH_CHROME_PATH || "";
const server = process.env.WORKBENCH_SERVER || "http://127.0.0.1:8766";
const documentId = process.env.WORKBENCH_DOCUMENT_ID || "real_loop_ai_writing_workbench_kimi";
const expectedTitle = process.env.WORKBENCH_EXPECTED_TITLE || "";
const url = `${server.replace(/\/$/, "")}/v2/?documentId=${encodeURIComponent(documentId)}`;
const tempDocumentId = `browser_smoke_temp_${Date.now()}`;
const tempUrl = `${server.replace(/\/$/, "")}/v2/?documentId=${encodeURIComponent(tempDocumentId)}`;
const paragraphTempDocumentId = `${tempDocumentId}_paragraph`;
const paragraphTempUrl = `${server.replace(/\/$/, "")}/v2/?documentId=${encodeURIComponent(paragraphTempDocumentId)}`;
const screenshotDir = path.join(root, ".cache", "e2e-screenshots");
const reportPath = path.join(root, ".cache", "writing", "workbench_browser_smoke_latest.json");
fs.mkdirSync(screenshotDir, { recursive: true });
fs.mkdirSync(path.dirname(reportPath), { recursive: true });

function registeredObsidianMirrorRoot() {
  try {
    const configPath = path.join(process.env.HOME || "", "Library", "Application Support", "obsidian", "obsidian.json");
    const payload = JSON.parse(fs.readFileSync(configPath, "utf8"));
    const vaults = payload?.vaults || {};
    const first = Object.values(vaults).find((item) => item && typeof item.path === "string" && item.path.trim());
    if (first?.path) return path.join(first.path, "Codex写作工作台");
  } catch {}
  return path.join(root, "obsidian_vault");
}

const obsidianMirrorRoot = registeredObsidianMirrorRoot();

const results = [];
const viewportWidth = Number(process.env.WORKBENCH_VIEWPORT_WIDTH || "1440");
const viewportHeight = Number(process.env.WORKBENCH_VIEWPORT_HEIGHT || "1100");

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

async function reveal(page, selector) {
  await page.evaluate((targetSelector) => {
    const node = document.querySelector(targetSelector);
    let current = node?.parentElement || null;
    while (current) {
      if (current.tagName === "DETAILS") current.open = true;
      current = current.parentElement;
    }
  }, selector);
  const locator = page.locator(selector);
  await locator.scrollIntoViewIfNeeded();
  return locator;
}

async function clickRevealed(page, selector) {
  const locator = await reveal(page, selector);
  await locator.click();
}

async function selectTextById(page, id) {
  const expectedText = await page.evaluate((targetId) => {
    const node = document.getElementById(targetId);
    if (!node) throw new Error(`missing ${targetId}`);
    const range = document.createRange();
    range.selectNodeContents(node);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    document.dispatchEvent(new Event("selectionchange"));
    return (node.textContent || "").trim();
  }, id);
  await page.waitForFunction((needle) => {
    const state = document.querySelector("#selectionState")?.textContent || "";
    const selectedText = document.querySelector("#selectedText")?.textContent || "";
    return state.includes("已选") && selectedText.includes(String(needle || "").slice(0, 24));
  }, expectedText);
}

function assertUsefulCandidates({ selectedText, candidateTexts, minCount = 3 }) {
  if (candidateTexts.length < minCount) {
    throw new Error(`expected at least ${minCount} candidates, got ${candidateTexts.length}: ${JSON.stringify(candidateTexts)}`);
  }
  const unique = new Set(candidateTexts);
  if (unique.size !== candidateTexts.length) throw new Error(`duplicate candidates: ${JSON.stringify(candidateTexts)}`);
  const compact = (value) => String(value || "").replace(/[^\w\u4e00-\u9fff]+/g, "");
  const similarity = (left, right) => {
    const a = compact(left);
    const b = compact(right);
    if (!a || !b) return 0;
    const counts = new Map();
    for (const char of a) counts.set(char, (counts.get(char) || 0) + 1);
    let overlap = 0;
    for (const char of b) {
      const count = counts.get(char) || 0;
      if (count > 0) {
        overlap += 1;
        counts.set(char, count - 1);
      }
    }
    return overlap / Math.max(a.length, b.length);
  };
  const selectedCompact = compact(selectedText);
  const blocked = /这句还缺|把抽象判断|避免像孤立金句|先回答一个具体问题|先移除提示语|先把人、动作和后果|先让这句话接住|接回上下文|\b(concretize|oralize|source-ground|workflow|style memory|gate)\b|生大纲/i;
  for (const [index, text] of candidateTexts.entries()) {
    if (!text.trim()) throw new Error("empty candidate");
    if (text.trim() === selectedText.trim()) throw new Error(`unchanged candidate: ${text}`);
    if (selectedText && text.includes(selectedText) && text.length <= selectedText.length + 18) {
      throw new Error(`candidate wraps original without real rewrite: ${text}`);
    }
    const textCompact = compact(text);
    if (selectedCompact.includes(textCompact) && textCompact.length < Math.max(24, selectedCompact.length * 0.72)) {
      throw new Error(`candidate is just a selected-text fragment: ${text}`);
    }
    if (
      selectedCompact &&
      textCompact &&
      ((selectedCompact.length >= 80 && similarity(text, selectedText) >= 0.86) ||
        (selectedCompact.length >= 35 && similarity(text, selectedText) >= 0.92) ||
        (selectedCompact.length < 35 && similarity(text, selectedText) >= 0.96))
    ) {
      throw new Error(`candidate is too close to original selection: ${text}`);
    }
    if (blocked.test(text)) throw new Error(`bad candidate leaked: ${text}`);
    if (/\\["']|["']\s*[,}\]]|["']$|\b(variants|move|label|text|reason)\s*[:：]/i.test(text)) {
      throw new Error(`json fragment leaked as candidate: ${text}`);
    }
    for (const other of candidateTexts.slice(0, index)) {
      if (similarity(text, other) >= 0.82) {
        throw new Error(`candidates are too similar: ${JSON.stringify([other, text])}`);
      }
    }
  }
}

async function cleanupTempMemories(page, sourceText) {
  await page.evaluate(async (text) => {
    const entries = await fetch("/api/memory").then((res) => res.json());
    const matches = entries.filter((entry) => entry.source_text === text);
    await Promise.all(matches.map((entry) => fetch(`/api/memory/${entry.id}`, { method: "DELETE" })));
  }, sourceText);
}

async function saveTempInteractionDocument(targetDocumentId = tempDocumentId) {
  const contentHtml = [
    `<h2>浏览器交互临时稿</h2>`,
    `<p id="browser-smoke-temp-line">${tempBadLine}</p>`,
    `<p id="browser-smoke-good-line">${tempGoodLine}</p>`,
    `<p id="browser-smoke-research-line">${tempResearchLine}</p>`,
    `<p id="browser-smoke-audit-line">${tempAuditLine}</p>`,
    `<p>这是一份临时交互测试稿，用来验证划选、改句、记录和检查硬伤，不写回正式文档。</p>`,
  ].join("\n");
  const response = await fetch(`${server.replace(/\/$/, "")}/api/document`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      documentId: targetDocumentId,
      title: "浏览器交互临时稿",
      contentHtml,
      contentText: `浏览器交互临时稿\n\n${tempBadLine}\n\n${tempResearchLine}\n\n${tempAuditLine}\n\n这是一份临时交互测试稿，用来验证划选、改句、记录和检查硬伤，不写回正式文档。`,
    }),
  });
  if (!response.ok) throw new Error(`failed to save temp document: ${response.status}`);
  return response.json();
}

const launchOptions = {
  headless: true,
  args: ["--no-sandbox", "--disable-gpu"],
};
if (chromePath) launchOptions.executablePath = chromePath;
const browser = await chromium.launch(launchOptions);

const context = await browser.newContext({
  viewport: { width: viewportWidth, height: viewportHeight },
  permissions: ["clipboard-read", "clipboard-write"],
});
let page = await context.newPage();
page.setDefaultTimeout(12000);

async function freshPage() {
  if (!page.isClosed()) await page.close();
  page = await context.newPage();
  page.setDefaultTimeout(12000);
  return page;
}

const tempBadLine = "随着人工智能技术飞速发展，内容创作迎来前所未有的变革。";
const tempGoodLine = "我把 AI 直出的开头放进审稿，系统先标出套话，再要求补上对象和动作。";
const tempResearchLine =
  "到今天，比较成熟的解法已经很清楚。Stanford STORM 先检索材料、多视角提问、生成大纲，再进入正文。PaperDebugger 走的是研究、批判、修订的编辑器内流程。CoAuthor 这类研究把人和模型的写作互动拆开看。2025 年关于学术写作的综述也反复强调，AI 可以辅助，但责任和解释权还在人这里。";
const tempAuditLine = "创作者需要在这个时代重新理解写作的价值、系统影响和长期意义。";
let acceptedResearchText = "";

await step("open current workbench document", async () => {
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction((titleNeedle) => {
    const title = document.querySelector("#documentTitle")?.value || "";
    const editor = document.querySelector("#editor")?.innerText || "";
    const titleOk = titleNeedle ? title.includes(titleNeedle) : title.trim().length > 0;
    return titleOk && editor.length > 1000;
  }, expectedTitle);
  return {
    title: await page.locator("#documentTitle").inputValue(),
    bodyStart: (await page.locator("#editor").innerText()).slice(0, 80),
  };
});

await step("obsidian bridge stays optional in lite UI", async () => {
  const state = await page.evaluate(() => {
    const fold = document.querySelector(".latest-fold");
    if (fold instanceof HTMLDetailsElement) fold.open = true;
    const button = document.querySelector("#openInObsidian");
    const rect = button?.getBoundingClientRect();
    return {
      exists: Boolean(button),
      visible: Boolean(rect && rect.width > 0 && rect.height > 0),
      disabled: Boolean(button?.disabled),
      text: button?.textContent || "",
      foldHidden: Boolean(fold?.hidden),
    };
  });
  if (!state.exists || state.text.trim() !== "打开笔记" || state.foldHidden) {
    throw new Error(JSON.stringify(state));
  }
  if (!state.visible) {
    return { ...state, optional: true, reason: "obsidian bridge hidden in lite UI" };
  }
  if (state.disabled) {
    throw new Error(JSON.stringify(state));
  }
  return state;
});

await step("default lite controls are contextual", async () => {
  const controls = await page.evaluate(() => ({
    quickRewrite: Boolean(document.querySelector("#quickRewriteAction")),
    quickRewriteVisible: Boolean(document.querySelector("#quickRewriteAction")?.offsetParent),
    quickAuditExists: Boolean(document.querySelector("#quickAuditAction")),
    quickAuditVisible: Boolean(document.querySelector("#quickAuditAction")?.offsetParent),
    toolbarExport: Boolean(document.querySelector("#exportMd")),
    rewrite: Boolean(document.querySelector("#runRewrite")),
    dislike: Boolean(document.querySelector("#saveBad")),
    dislikeVisible: Boolean(document.querySelector("#saveBad")?.offsetParent),
    like: Boolean(document.querySelector("#saveGood")),
    likeVisible: Boolean(document.querySelector("#saveGood")?.offsetParent),
    selectionBlockHidden: Boolean(document.querySelector(".selection-block")?.hidden),
    deliveryBlockHidden: Boolean(document.querySelector(".delivery-block")?.hidden),
    sideHidden: Boolean(document.querySelector(".side")?.hidden),
    resultPanelState: document.body.dataset.resultPanel || "",
    advancedPanel: Boolean(document.querySelector(".advanced-writing-tools")),
    deepReviewAction: Boolean(document.querySelector("#deepReviewAction")),
    openGeneratePanel: Boolean(document.querySelector("#openGeneratePanel")),
    panelTabsHidden: window.getComputedStyle(document.querySelector(".panel-tabs")).display === "none",
    activePanel: document.querySelector(".panel-view.active")?.dataset.view,
  }));
  if (
    !controls.quickRewrite ||
    controls.quickRewriteVisible ||
    !controls.quickAuditExists ||
    controls.quickAuditVisible ||
    !controls.toolbarExport ||
    !controls.rewrite ||
    !controls.dislike ||
    controls.dislikeVisible ||
    !controls.like ||
    controls.likeVisible ||
    !controls.selectionBlockHidden ||
    !controls.deliveryBlockHidden ||
    !controls.sideHidden ||
    controls.advancedPanel ||
    controls.deepReviewAction ||
    controls.openGeneratePanel ||
    !controls.panelTabsHidden ||
    controls.activePanel !== "rewrite"
  ) {
    throw new Error(JSON.stringify(controls));
  }
  return controls;
});

await step("background audit api catches obvious bad copy", async () => {
  const result = await page.evaluate(async () => {
    const response = await fetch("/api/quick-audit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        title: "坏稿测试",
        body: "随着 AI 时代的到来，当前行业正在快速发展。创作者需要积极拥抱变化，提升自身竞争力，形成闭环，实现降本增效。",
      }),
    });
    if (!response.ok) throw new Error(`audit failed: ${response.status}`);
    return response.json();
  });
  const findings = (result.findings || []).filter((item) => item.kind !== "pass");
  if (!findings.length) throw new Error("background audit missed obvious bad copy");
  return {
    score: result.score,
    summary: result.summaryLine || result.summary,
    first: findings[0]?.reason || "",
  };
});

await step("export current article as markdown", async () => {
  await clickRevealed(page, "#exportMd");
  await page.waitForFunction(() => (document.querySelector("#saveState")?.textContent || "").includes("已导出 MD"));
  return {
    state: await page.locator("#saveState").textContent(),
    path: await page.locator("#documentPath").textContent(),
  };
});

await step("screenshot current article without interaction pollution", async () => {
  const screenshotPath = path.join(screenshotDir, `workbench-current-readonly-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: false });
  return screenshotPath;
});

await step("final review waits for loaded body and stays editorial", async () => {
  await freshPage();
  const routePattern = `**/api/document?documentId=${encodeURIComponent(documentId)}*`;
  await page.route(routePattern, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 450));
    const response = await route.fetch();
    await route.fulfill({ response });
  });
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#finalReviewButton");
  await page.waitForTimeout(120);
  const duringHydration = await page.evaluate(() => ({
    disabled: Boolean(document.querySelector("#finalReviewButton")?.disabled),
    editorLength: (document.querySelector("#editor")?.innerText || "").length,
  }));
  if (!duringHydration.disabled) {
    throw new Error(`final review button should stay disabled during hydration: ${JSON.stringify(duringHydration)}`);
  }
  await page.waitForFunction(() => {
    const editorText = document.querySelector("#editor")?.innerText || "";
    const button = document.querySelector("#finalReviewButton");
    return editorText.length > 1500 && !button?.disabled;
  });
  await page.unroute(routePattern);
  await page.locator("#finalReviewButton").click();
  await page.waitForFunction(() => document.querySelectorAll(".final-review-item").length >= 1 || !!document.querySelector(".final-review-empty"), null, { timeout: 12000 });
  const panelState = await page.evaluate(() => ({
    job: document.querySelector("#jobState")?.textContent?.trim() || "",
    labels: Array.from(document.querySelector(".final-review-item")?.querySelectorAll(".final-review-label") || [])
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean),
    itemCount: document.querySelectorAll(".final-review-item").length,
    reasons: Array.from(document.querySelectorAll(".final-review-reason"))
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean),
    suggestions: Array.from(document.querySelectorAll(".final-review-suggestion"))
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean),
  }));
  const apiState = await page.evaluate(async () => {
    const response = await fetch("/api/final-review", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        title: "收稿检查时序临时稿",
        body: [
          "为了方便写作解决这个问题，我做了这个智能写作工作台。我利用三款模型来辅助我写作，分别是 Codex、Kimi 和 DeepSeek。",
          "可以看到整个前端比较简洁。最上方是标题，在下面就是正文内容，按 command + s 也是可以直接保存。下次再打开显示的就是最新保存的内容。可以在历史主题这里找到每次存档的版本，最多能查看最近五次，不会相互影响。",
          "如果觉得在正文里需要在段落之间补充什么，可以按回车新开一行按双击，这里输入你的需求，AI 会在后台根据上下段落来补充一段。",
        ].join("\n\n"),
      }),
    });
    if (!response.ok) throw new Error(`final review api failed: ${response.status}`);
    return response.json();
  });
  if (!panelState.job.includes("收稿发现") && !panelState.job.includes("没有扫到明显交稿问题")) {
    throw new Error(`final review summary did not appear: ${JSON.stringify(panelState)}`);
  }
  const isIssuePath = panelState.job.includes("收稿发现");
  const isCleanPath = panelState.job.includes("没有扫到明显交稿问题");
  if (isIssuePath && (!panelState.itemCount || !panelState.reasons.length || !panelState.suggestions.length)) {
    throw new Error(`final review issue cards missing reason or suggestion: ${JSON.stringify(panelState)}`);
  }
  if (isCleanPath && panelState.labels.length !== 0) {
    throw new Error(`clean final review should not show issue labels: ${JSON.stringify(panelState)}`);
  }
  const apiSuggestions = Array.isArray(apiState.items)
    ? apiState.items.map((item) => item?.suggestion || "").filter(Boolean)
    : [];
  const frontendOverviewSuggestion = apiSuggestions.find((line) => line.includes("打开页面第一眼会做什么")) || "";
  if (!frontendOverviewSuggestion) {
    throw new Error(`frontend-overview suggestion did not stay contextual: ${JSON.stringify({ apiSuggestions, apiState })}`);
  }
  const paragraphAssistSuggestion = apiSuggestions.find((line) => line.includes("空一行、写需求、右侧挑一个候选")) || "";
  if (!paragraphAssistSuggestion) {
    throw new Error(`paragraph-assist suggestion did not stay contextual: ${JSON.stringify({ apiSuggestions, apiState })}`);
  }
  return {
    duringHydration,
    panelState,
    matchedSuggestions: {
      frontendOverviewSuggestion,
      paragraphAssistSuggestion,
    },
  };
});

await step("open temporary interaction document", async () => {
  const saved = await saveTempInteractionDocument();
  await freshPage();
  await page.goto(tempUrl, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction(() => {
    const title = document.querySelector("#documentTitle")?.value || "";
    const editor = document.querySelector("#editor")?.innerText || "";
    return title.includes("浏览器交互临时稿") && editor.includes("前所未有的变革") && editor.includes("Stanford STORM");
  });
  return { documentId: saved.documentId, title: await page.locator("#documentTitle").inputValue() };
});

await step("final review fix button triggers rewrite on temporary issue doc", async () => {
  await page.locator("#finalReviewButton").click();
  await page.waitForFunction(() => document.querySelectorAll(".final-review-item").length >= 1, null, { timeout: 15000 });
  await page.locator(".final-review-item [data-fix]").first().click();
  await page.waitForFunction(() => {
    const text = document.querySelector("#candidateList")?.innerText || "";
    return (
      document.querySelectorAll("#candidateList .candidate .candidate-text").length >= 1 ||
      text.includes("改句中") ||
      text.includes("这组候选像原句换皮") ||
      text.includes("没有返回候选")
    );
  }, null, { timeout: 60000 });
  const rewriteFromAudit = await page.evaluate(() => ({
    issue: document.querySelector("#rewriteIssue")?.textContent?.trim() || "",
    progress: document.querySelector("#rewriteProgress")?.textContent?.trim() || "",
    selectionState: document.querySelector("#selectionState")?.textContent?.trim() || "",
    candidateCount: document.querySelectorAll("#candidateList .candidate .candidate-text").length,
    candidateTexts: Array.from(document.querySelectorAll("#candidateList .candidate .candidate-text")).map((node) => (node.textContent || "").trim()).filter(Boolean),
    surfaceText: document.querySelector("#candidateList")?.innerText?.trim() || "",
  }));
  const triggered =
    rewriteFromAudit.candidateCount > 0 ||
    rewriteFromAudit.surfaceText.includes("这组候选像原句换皮") ||
    rewriteFromAudit.surfaceText.includes("没有返回候选") ||
    rewriteFromAudit.surfaceText.includes("改句中");
  if (!triggered || rewriteFromAudit.selectionState === "未选") {
    throw new Error(`final review fix button did not produce rewrite candidates: ${JSON.stringify(rewriteFromAudit)}`);
  }
  return rewriteFromAudit;
});

await step("manual selection clears stale final-review context after switching paragraph", async () => {
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction(() => Boolean(document.querySelector("#browser-smoke-temp-line")));
  await page.evaluate(() => {
    if (typeof jumpToParagraph !== "function") throw new Error("jumpToParagraph unavailable");
    jumpToParagraph(
      4,
      {
        category: "硬禁句",
        reason: "假深刻提示词会替代具体判断。",
        paragraphIndex: 4,
        previewText: "以前碰到这种空话，我只能对着整篇反复洗；现在我会先把那一句挑出来，点“改句”，看它能不能直接回到正文里。",
        previewReason: "先落到真实改稿动作。",
      },
      0
    );
  });
  await page.waitForFunction(() => {
    const issue = document.querySelector("#rewriteIssue")?.textContent || "";
    const auditIssue = typeof selectedPayload === "function" ? selectedPayload().auditIssue : null;
    return issue.includes("硬禁句") && auditIssue?.category === "硬禁句" && Boolean(auditIssue?.previewText);
  });
  const before = await page.evaluate(() => ({
    issue: document.querySelector("#rewriteIssue")?.textContent || "",
    auditIssue: typeof selectedPayload === "function" ? selectedPayload().auditIssue : null,
  }));
  await selectTextById(page, "browser-smoke-good-line");
  await page.waitForFunction(() => {
    const auditIssue = typeof selectedPayload === "function" ? selectedPayload().auditIssue : null;
    const issue = document.querySelector("#rewriteIssue")?.textContent || "";
    return !auditIssue && !issue.includes("硬禁句");
  });
  const after = await page.evaluate(() => ({
    issue: document.querySelector("#rewriteIssue")?.textContent || "",
    auditIssue: typeof selectedPayload === "function" ? selectedPayload().auditIssue : null,
  }));
  await page.evaluate(() => {
    const selection = window.getSelection();
    selection?.removeAllRanges();
    if (typeof captureCaret === "function") captureCaret();
    const menu = document.querySelector("#selectionMenu");
    if (menu) menu.hidden = true;
  });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction(() => Boolean(document.querySelector("#browser-smoke-temp-line")));
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    document.querySelector("#browser-smoke-temp-line")?.scrollIntoView({ block: "center" });
  });
  return { before, after };
});

await step("pending paragraph assist prompt is transient across reload", async () => {
  const marker = `未接受写作需求 ${Date.now()}`;
  const gapPoint = await page.evaluate(() => {
    const node = document.querySelector("#browser-smoke-temp-line");
    if (!node) throw new Error("missing browser-smoke-temp-line");
    const next = node.nextElementSibling;
    if (!(next instanceof HTMLElement)) throw new Error("missing next paragraph for gap transient test");
    const currentRect = node.getBoundingClientRect();
    const nextRect = next.getBoundingClientRect();
    const gapHeight = nextRect.top - currentRect.bottom;
    const y = currentRect.bottom + Math.max(6, Math.min(18, gapHeight > 0 ? gapHeight / 2 : 10));
    const x = currentRect.left + Math.min(120, Math.max(40, currentRect.width * 0.28));
    return { x: x + window.scrollX, y: y + window.scrollY };
  });
  await page.mouse.dblclick(gapPoint.x, gapPoint.y);
  await page.waitForSelector('p[data-paragraph-assist-slot="1"]');
  await page.locator('p[data-paragraph-assist-slot="1"]').click();
  await page.keyboard.type(marker);
  await page.waitForFunction(
    (expected) => (document.querySelector('p[data-paragraph-assist-slot="1"]')?.innerText || "").includes(expected),
    marker
  );
  await page.waitForTimeout(900);
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector("#browser-smoke-temp-line");
  const after = await page.evaluate((expected) => ({
    slotCount: document.querySelectorAll('p[data-paragraph-assist-slot="1"]').length,
    editorHasMarker: (document.querySelector("#editor")?.innerText || "").includes(expected),
    saveState: document.querySelector("#saveState")?.textContent || "",
  }), marker);
  if (after.slotCount !== 0 || after.editorHasMarker) {
    throw new Error(`pending paragraph assist prompt survived reload: ${JSON.stringify(after)}`);
  }
  return after;
});

await step("double click creates paragraph assist slot and accepts typed prompt", async () => {
  const beforeCount = await page.locator("#editor p").count();
  const gapPoint = await page.evaluate(() => {
    const node = document.querySelector("#browser-smoke-temp-line");
    if (!node) throw new Error("missing browser-smoke-temp-line");
    const next = node.nextElementSibling;
    if (!(next instanceof HTMLElement)) throw new Error("missing next paragraph for gap dblclick");
    const currentRect = node.getBoundingClientRect();
    const nextRect = next.getBoundingClientRect();
    const gapHeight = nextRect.top - currentRect.bottom;
    const y = currentRect.bottom + Math.max(6, Math.min(18, gapHeight > 0 ? gapHeight / 2 : 10));
    const x = currentRect.left + Math.min(120, Math.max(40, currentRect.width * 0.28));
    return { x: x + window.scrollX, y: y + window.scrollY };
  });
  await page.mouse.dblclick(gapPoint.x, gapPoint.y);
  await page.waitForFunction(() => {
    const slot = document.querySelector('p[data-paragraph-assist-slot="1"]');
    return Boolean(slot && slot.classList.contains("paragraph-assist-slot"));
  });
  const before = await page.evaluate(() => ({
    state: document.querySelector("#paragraphAssistState")?.textContent || "",
    hint: document.querySelector("#paragraphAssistHint")?.textContent || "",
    disabled: Boolean(document.querySelector("#paragraphAssistAction")?.disabled),
    slotPlaceholder: document.querySelector('p[data-paragraph-assist-slot="1"]')?.dataset.placeholder || "",
    slotLabel: document.querySelector('p[data-paragraph-assist-slot="1"]')?.dataset.label || "",
    inlineBarExists: Boolean(document.querySelector("#paragraphAssistInlineBar")),
  }));
  const afterCreateCount = await page.locator("#editor p").count();
  if (afterCreateCount <= beforeCount) throw new Error(`dblclick did not create a slot: ${beforeCount} -> ${afterCreateCount}`);
  if (!before.slotLabel.includes("待写段")) throw new Error(`unexpected slot label: ${before.slotLabel}`);
  if (before.inlineBarExists) throw new Error("paragraph assist inline bar should not exist");
  if (!before.slotPlaceholder.includes("回车生成")) throw new Error(`slot prompt missing keyboard action: ${before.slotPlaceholder}`);
  const secondGapPoint = await page.evaluate(() => {
    const blocks = Array.from(document.querySelectorAll("#editor p")).filter(
      (node) => node.dataset.paragraphAssistSlot !== "1"
    );
    if (blocks.length < 2) throw new Error("not enough text paragraphs for second gap test");
    const currentRect = blocks[0].getBoundingClientRect();
    const nextRect = blocks[1].getBoundingClientRect();
    const gapHeight = nextRect.top - currentRect.bottom;
    const y = currentRect.bottom + Math.max(6, Math.min(18, gapHeight > 0 ? gapHeight / 2 : 10));
    const x = currentRect.left + Math.min(120, Math.max(40, currentRect.width * 0.28));
    return { x: x + window.scrollX, y: y + window.scrollY };
  });
  await page.mouse.dblclick(secondGapPoint.x, secondGapPoint.y);
  const afterSecondDblclick = await page.evaluate(() => ({
    slotCount: document.querySelectorAll('p[data-paragraph-assist-slot="1"]').length,
  }));
  if (afterSecondDblclick.slotCount !== 1) {
    throw new Error(`expected one active assist slot, got ${afterSecondDblclick.slotCount}`);
  }
  await page.locator('p[data-paragraph-assist-slot="1"]').click();
  await page.keyboard.type("写一些 AI 味最常见的句子例子，并解释为什么这些句子看着稳却很空。");
  await page.waitForFunction(() => {
    const text = document.querySelector('p[data-paragraph-assist-slot="1"]')?.innerText || "";
    return text.includes("AI 味最常见的句子例子");
  });
  await page.waitForFunction(
    () => (document.querySelector("#paragraphAssistState")?.textContent || "").includes("可补写"),
    null,
    { timeout: 3000 }
  );
  const afterPrompt = await page.evaluate(() => ({
    inlineBarExists: Boolean(document.querySelector("#paragraphAssistInlineBar")),
    state: document.querySelector("#paragraphAssistState")?.textContent || "",
    hint: document.querySelector("#paragraphAssistHint")?.textContent || "",
    slotText: document.querySelector('p[data-paragraph-assist-slot="1"]')?.innerText || "",
  }));
  if (afterPrompt.inlineBarExists) throw new Error("paragraph assist inline bar appeared after typing");
  if (!afterPrompt.state.includes("可补写")) throw new Error(`paragraph prompt did not become writable: ${JSON.stringify(afterPrompt)}`);
  await page.evaluate(() => {
    document.querySelectorAll('p[data-paragraph-assist-slot="1"]').forEach((node) => node.remove());
    document.querySelector("#editor")?.dispatchEvent(new Event("input", { bubbles: true }));
  });
  return {
    beforeCount,
    afterCreateCount,
    before,
    afterSecondDblclick,
    afterPrompt,
  };
});

await step("paragraph assist supports paste, shows inline progress after Enter and returns candidates", async () => {
  await saveTempInteractionDocument(paragraphTempDocumentId);
  await freshPage();
  await page.goto(paragraphTempUrl, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction(() => Boolean(document.querySelector("#browser-smoke-temp-line")));
  await page.evaluate(() => {
    document.querySelectorAll('p[data-paragraph-assist-slot="1"]').forEach((node) => node.remove());
    document.querySelector("#candidateList")?.replaceChildren();
    document.querySelector("#editor")?.dispatchEvent(new Event("input", { bubbles: true }));
  });
  const gapPoint = await page.evaluate(() => {
    const node = document.querySelector("#browser-smoke-temp-line");
    if (!node) throw new Error("missing browser-smoke-temp-line");
    const next = node.nextElementSibling;
    if (!(next instanceof HTMLElement)) throw new Error("missing next paragraph for paragraph assist run");
    const currentRect = node.getBoundingClientRect();
    const nextRect = next.getBoundingClientRect();
    const gapHeight = nextRect.top - currentRect.bottom;
    const y = currentRect.bottom + Math.max(6, Math.min(18, gapHeight > 0 ? gapHeight / 2 : 10));
    const x = currentRect.left + Math.min(120, Math.max(40, currentRect.width * 0.28));
    return { x: x + window.scrollX, y: y + window.scrollY };
  });
  await page.mouse.dblclick(gapPoint.x, gapPoint.y);
  await page.waitForSelector('p[data-paragraph-assist-slot="1"]');
  await page.locator('p[data-paragraph-assist-slot="1"]').click();
  const promptText = "写一些 AI 味最常见的句子例子，并解释为什么这些句子看着稳却很空。";
  await page.evaluate(async (text) => {
    await navigator.clipboard.writeText(text);
  }, promptText);
  await page.keyboard.press("Meta+V");
  await page.waitForFunction((text) => {
    const slot = document.querySelector('p[data-paragraph-assist-slot="1"]');
    return (slot?.innerText || "").includes(text);
  }, promptText);
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => {
    const slot = document.querySelector('p[data-paragraph-assist-slot="1"]');
    return (slot?.dataset.runState || "") === "running" && (slot?.dataset.label || "").includes("补写中");
  });
  const pending = await page.evaluate(() => {
    const slot = document.querySelector('p[data-paragraph-assist-slot="1"]');
    return {
      runState: slot?.dataset.runState || "",
      label: slot?.dataset.label || "",
      progress: slot?.dataset.progress || "",
      sideVisible: !document.querySelector(".side")?.hidden,
      loadingVisible: Boolean(document.querySelector("#candidateList .rewrite-loading-card")),
    };
  });
  const hasRunningProgress =
    pending.progress.includes("已发送给写作助手") ||
    pending.progress.includes("正在") ||
    /·\s*\d+s/.test(pending.progress);
  if (!hasRunningProgress) throw new Error(`inline progress missing after Enter: ${JSON.stringify(pending)}`);
  if (!pending.sideVisible || !pending.loadingVisible) {
    throw new Error(`result surface did not open while paragraph assist runs: ${JSON.stringify(pending)}`);
  }
  await page.waitForFunction(() => {
    const slot = document.querySelector('p[data-paragraph-assist-slot="1"]');
    const texts = Array.from(document.querySelectorAll("#candidateList .candidate-text"))
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean);
    return texts.length >= 1 || ["ready", "failed"].includes(slot?.dataset.runState || "");
  }, null, { timeout: 90000 });
  const resolved = await page.evaluate(() => {
    const slot = document.querySelector('p[data-paragraph-assist-slot="1"]');
    const candidateTexts = Array.from(document.querySelectorAll("#candidateList .candidate-text"))
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean);
    const candidateHeads = Array.from(document.querySelectorAll("#candidateList .candidate-head span:first-child"))
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean);
    const proofLines = Array.from(document.querySelectorAll("#candidateList .paragraph-assist-proof-line"))
      .map((node) => (node.textContent || "").trim())
      .filter(Boolean);
    return {
      runState: slot?.dataset.runState || "",
      label: slot?.dataset.label || "",
      progress: slot?.dataset.progress || "",
      candidateCount: candidateTexts.length,
      candidateTexts,
      candidateHeads,
      proofLines,
      surface: document.querySelector("#candidateList")?.textContent || "",
    };
  });
  if (resolved.candidateCount < 1) {
    throw new Error(`paragraph assist did not return candidates: ${JSON.stringify(resolved)}`);
  }
  if (!resolved.label.includes("有候选") || !resolved.progress.includes("已生成")) {
    throw new Error(`slot did not expose ready state after paragraph assist: ${JSON.stringify(resolved)}`);
  }
  if (!resolved.proofLines.some((line) => line.includes("补段证明："))) {
    throw new Error(`paragraph assist proof line missing: ${JSON.stringify(resolved)}`);
  }
  if (resolved.proofLines.some((line) => line.includes("候选：") || line.includes("检索：") || line.includes("带入 "))) {
    throw new Error(`paragraph assist proof line still too verbose: ${JSON.stringify(resolved)}`);
  }
  if (!resolved.candidateHeads.some((line) => line && !/^候选\\s+\\d+$/.test(line))) {
    throw new Error(`paragraph assist labels still generic: ${JSON.stringify(resolved)}`);
  }
  return { pending, resolved };
});

await step("temporary selection taste memory", async () => {
  await freshPage();
  await page.goto(tempUrl, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction(() => Boolean(document.querySelector("#browser-smoke-temp-line")));
  let memoryCount = "";
  let menuStatus = "";
  let contextualControls = {};
  try {
    await page.waitForTimeout(750);
    await selectTextById(page, "browser-smoke-temp-line");
    contextualControls = await page.evaluate(() => {
      const ids = ["quickRewriteAction", "saveBad", "saveGood"];
      const controls = Object.fromEntries(
        ids.map((id) => {
          const node = document.getElementById(id);
          const rect = node?.getBoundingClientRect();
          return [
            id,
            {
              exists: Boolean(node),
              visible: Boolean(rect && rect.width > 0 && rect.height > 0),
              disabled: Boolean(node?.disabled),
            },
          ];
        })
      );
      return {
        ...controls,
        selectionMenu: {
          exists: Boolean(document.querySelector("#selectionMenu")),
          visible: (() => {
            const node = document.querySelector("#selectionMenu");
            if (!node || node.hidden) return false;
            const rect = node.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          })(),
        },
      };
    });
    if (!contextualControls.selectionMenu.visible) throw new Error(`inline selection menu did not appear: ${JSON.stringify(contextualControls)}`);
    const badControls = Object.entries(contextualControls)
      .filter(([id]) => id !== "selectionMenu")
      .filter(([, value]) => !value.exists || value.visible);
    if (badControls.length) throw new Error(`right rail selection tools should stay hidden: ${JSON.stringify(contextualControls)}`);
    await page.waitForSelector("#selectionMenu [data-ban]", { state: "visible" });
    await page.locator("#selectionMenu [data-ban]").click();
    await page.waitForFunction(() => {
      const menu = document.querySelector("#selectionMenuStatus")?.textContent || "";
      const rule = document.querySelector("#memoryList .memory-entry.banned_line .memory-rule")?.textContent || "";
      return menu.includes("已记：") && rule.includes("下次怎么避开");
    });
    await selectTextById(page, "browser-smoke-good-line");
    await page.waitForSelector("#selectionMenu [data-like]", { state: "visible" });
    await page.locator("#selectionMenu [data-like]").click();
    await page.waitForFunction(() => {
      const menu = document.querySelector("#selectionMenuStatus")?.textContent || "";
      const rules = Array.from(document.querySelectorAll("#memoryList .memory-entry .memory-rule"))
        .map((node) => node.textContent || "")
        .filter(Boolean);
      return menu.includes("已记：") && rules.some((line) => line.includes("下次怎么借"));
    });
    memoryCount = await page.locator("#memoryCount").textContent();
    menuStatus = await page.locator("#selectionMenuStatus").textContent();
    const memoryRules = await page.evaluate(() =>
      Array.from(document.querySelectorAll("#memoryList .memory-entry .memory-rule"))
        .map((node) => (node.textContent || "").trim())
        .filter(Boolean)
        .slice(0, 4)
    );
    return { memoryCount, menuStatus, contextualControls, memoryRules };
  } finally {
    await cleanupTempMemories(page, tempBadLine);
    await cleanupTempMemories(page, tempGoodLine);
  }
});

await step("selected rewrite preview and accept", async () => {
  try {
    await selectTextById(page, "browser-smoke-research-line");
    await page.waitForSelector("#selectionMenu [data-run]", { state: "visible" });
    await page.locator("#selectionMenu [data-run]").click();
    let lastCandidateSurface = "";
    for (let attempt = 0; attempt < 90; attempt += 1) {
      const state = await page.evaluate(() => {
        const texts = Array.from(document.querySelectorAll("#candidateList .candidate-text"))
          .map((node) => (node.textContent || "").trim())
          .filter(Boolean);
        return {
          texts,
          surface: document.querySelector("#candidateList")?.textContent || "",
        };
      });
      if (state.texts.length) break;
      lastCandidateSurface = state.surface;
      if (/没有候选|质量不够|没写好|失败/.test(state.surface)) {
        throw new Error(`rewrite returned no usable candidate: ${state.surface}`);
      }
      await page.waitForTimeout(500);
    }
    if (!(await page.locator("#candidateList .candidate-text").count())) {
      throw new Error(`rewrite candidate never appeared; last surface: ${lastCandidateSurface}`);
    }
    const candidateCount = await page.locator("#candidateList .candidate-text").count();
    const resultPanel = await page.evaluate(() => ({
      sideHidden: Boolean(document.querySelector(".side")?.hidden),
      resultPanelState: document.body.dataset.resultPanel || "",
      candidateVisible: Boolean(document.querySelector("#candidateList") && !document.querySelector("#candidateList").hidden),
    }));
    if (resultPanel.sideHidden || resultPanel.resultPanelState !== "visible" || !resultPanel.candidateVisible) {
      throw new Error(`candidate result panel did not open: ${JSON.stringify(resultPanel)}`);
    }
    const candidateTexts = await page.locator("#candidateList .candidate-text").evaluateAll((nodes) =>
      nodes.map((node) => (node.textContent || "").trim()).filter(Boolean)
    );
    assertUsefulCandidates({ selectedText: tempResearchLine, candidateTexts, minCount: 3 });
    const acceptedText = (await page.locator("#candidateList .candidate-text").first().textContent()).trim();
    acceptedResearchText = acceptedText;
    const candidateSource = (await page.locator("#candidateList .candidate-head span").nth(1).textContent()).trim();
    const memoryProofLine = (await page.locator("#candidateList .memory-proof-line").textContent().catch(() => "")).trim();
    if (!memoryProofLine || !/(本次带入|本次参考).*(偏好|风格记忆)/.test(memoryProofLine)) {
      throw new Error(`memory proof line missing from rewrite result: ${memoryProofLine || "<empty>"}`);
    }
    await page.locator("#candidateList [data-save]").first().click();
    await page.waitForFunction(() => {
      const button = document.querySelector("#candidateList [data-save]");
      const note = document.querySelector("#candidateList .candidate-memory-note")?.textContent || "";
      return (button?.textContent || "").includes("已记住") && note.includes("下次优先");
    });
    const remembered = await page.evaluate(() => ({
      saveLabel: document.querySelector("#candidateList [data-save]")?.textContent || "",
      note: document.querySelector("#candidateList .candidate-memory-note")?.textContent || "",
      saveState: document.querySelector("#saveState")?.textContent || "",
    }));
    const before = await page.locator("#editor").innerText();
    await page.locator("#candidateList [data-accept]").first().click();
    await page.waitForTimeout(400);
    const after = await page.locator("#editor").innerText();
    if (before === after) throw new Error("accept did not change editor text");
    if (after.includes(tempResearchLine)) throw new Error("accept left original selected sentence in editor");
    if (!after.includes(acceptedText)) throw new Error("accepted candidate did not appear in editor");
    const selectedState = await page.locator("#selectionState").textContent();
    if (!selectedState.includes("已替换")) throw new Error(`selection state did not report replacement: ${selectedState}`);
    return {
      selected: (await page.locator("#selectedText").textContent()).slice(0, 120),
      accepted: acceptedText.slice(0, 120),
      source: candidateSource,
      memoryProof: memoryProofLine,
      remembered,
      candidateCount,
      resultPanel,
      candidateTexts: candidateTexts.slice(0, 3),
    };
  } finally {
    await cleanupTempMemories(page, tempResearchLine);
  }
});

await step("autosave survives immediate reload", async () => {
  const marker = `自动保存回写校验 ${Date.now()}`;
  await page.evaluate((text) => {
    const editor = document.querySelector("#editor");
    const node = document.createElement("p");
    node.id = "browser-smoke-autosave-line";
    node.textContent = text;
    editor.appendChild(node);
    editor.dispatchEvent(new Event("input", { bubbles: true }));
  }, marker);
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector("#editor");
  await page.waitForFunction(
    (expected) => {
      const text = document.querySelector("#editor")?.innerText || "";
      const saveState = document.querySelector("#saveState")?.textContent || "";
      return text.includes(expected) && /恢复|本地已存|工作区已存/.test(saveState);
    },
    marker,
    { timeout: 12000 }
  );
  return {
    marker,
    saveState: await page.locator("#saveState").textContent(),
    documentState: await page.locator("#documentState").textContent(),
  };
});

await step("command save writes current version to workspace", async () => {
  const marker = `快捷键保存回写校验 ${Date.now()}`;
  await page.locator("#editor").click();
  await page.keyboard.press("End");
  await page.keyboard.press("Enter");
  await page.keyboard.type(marker);
  await page.keyboard.press("Meta+S");
  await page.waitForFunction(
    () => {
      const saveState = document.querySelector("#saveState")?.textContent || "";
      const docState = document.querySelector("#documentState")?.textContent || "";
      const toast = document.querySelector("#workspaceToast")?.textContent || "";
      return saveState.includes("工作区已存") && docState.includes("已保存") && toast.includes("已保存到工作区");
    },
    null,
    { timeout: 12000 }
  );
  const saved = await page.evaluate(async (docId) => {
    const response = await fetch(`/api/document?documentId=${encodeURIComponent(docId)}`);
    if (!response.ok) throw new Error(`load failed: ${response.status}`);
    return response.json();
  }, tempDocumentId);
  if (!(saved.contentText || "").includes(marker)) {
    throw new Error("workspace save did not persist keyboard-saved marker");
  }
  if (!String(saved.contentText || "").includes("\n\n")) {
    throw new Error("workspace save flattened paragraph boundaries");
  }
  return {
    marker,
    saveState: await page.locator("#saveState").textContent(),
    documentState: await page.locator("#documentState").textContent(),
    toast: await page.locator("#workspaceToast").textContent(),
    paragraphPreserved: true,
  };
});

await step("temporary export writes current draft without manual audit", async () => {
  if (!acceptedResearchText) throw new Error("missing accepted rewrite text");
  await clickRevealed(page, "#exportMd");
  await page.waitForFunction(() => (document.querySelector("#saveState")?.textContent || "").includes("已导出 MD"));
  const exportPath = (await page.locator("#documentPath").textContent()).trim();
  if (!exportPath || !fs.existsSync(exportPath)) throw new Error(`missing export path: ${exportPath}`);
  const exported = fs.readFileSync(exportPath, "utf8");
  if (!exported.includes(acceptedResearchText.slice(0, 60))) {
    throw new Error("exported markdown does not include accepted rewrite");
  }
  if (exported.includes(tempResearchLine)) {
    throw new Error("exported markdown still includes original research line");
  }
  return { path: exportPath, acceptedStart: acceptedResearchText.slice(0, 80) };
});

await step("obsidian open-topic works from temporary document", async () => {
  const expectedPath = path.join(obsidianMirrorRoot, "Topics", tempDocumentId, "index.md");
  const state = await page.evaluate(() => {
    const fold = document.querySelector(".latest-fold");
    if (fold instanceof HTMLDetailsElement) fold.open = true;
    const button = document.querySelector("#openInObsidian");
    const rect = button?.getBoundingClientRect();
    return {
      exists: Boolean(button),
      visible: Boolean(rect && rect.width > 0 && rect.height > 0),
      disabled: Boolean(button?.disabled),
    };
  });
  if (!state.exists) {
    throw new Error("obsidian bridge control is missing");
  }
  if (!state.visible) {
    return { skipped: true, reason: "obsidian bridge hidden in lite UI" };
  }
  if (state.disabled) {
    throw new Error(`obsidian bridge control is disabled: ${JSON.stringify(state)}`);
  }
  await clickRevealed(page, "#openInObsidian");
  await page.waitForFunction(() => {
    const toast = document.querySelector("#workspaceToast")?.textContent || "";
    return toast.includes("已在 Obsidian 打开当前主题") || toast.includes("已同步到镜像");
  });
  if (!fs.existsSync(expectedPath)) {
    throw new Error(`obsidian topic note missing: ${expectedPath}`);
  }
  const body = fs.readFileSync(expectedPath, "utf8");
  if (!body.includes("浏览器交互临时稿")) {
    throw new Error("obsidian topic note does not include temporary document title");
  }
  const toast = (await page.locator("#workspaceToast").textContent()).trim();
  return {
    toast,
    path: expectedPath,
  };
});

await step("generation controls stay hidden from lite UI", async () => {
  const state = await page.evaluate(() => ({
    draftExists: Boolean(document.querySelector("[data-view='draft']")),
    progress: Boolean(document.querySelector("#generateProgress")),
    cancel: Boolean(document.querySelector("#cancelGenerate")),
    visibleAdvancedPanel: Boolean(document.querySelector(".advanced-writing-tools")),
    openGeneratePanel: Boolean(document.querySelector("#openGeneratePanel")),
    liteMode: document.body.classList.contains("lite-mode"),
    entryLabel: document.querySelector(".start-card .row span")?.textContent || "",
    generateButton: document.querySelector("#generateDraft")?.textContent || "",
    progressDetail: document.querySelector("#generateProgressDetail")?.textContent || "",
  }));
  if (
    !state.draftExists ||
    !state.progress ||
    !state.cancel ||
    state.visibleAdvancedPanel ||
    state.openGeneratePanel ||
    !state.liteMode ||
    !state.entryLabel.includes("正式写稿入口") ||
    !state.generateButton.includes("后台生成全文") ||
    !/主笔接口/.test(state.progressDetail) ||
    !/收稿检查/.test(state.progressDetail)
  ) {
    throw new Error(JSON.stringify(state));
  }
  return state;
});

await step("screenshot", async () => {
  const screenshotPath = path.join(screenshotDir, `workbench-lite-smoke-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return screenshotPath;
});

const failed = results.filter((item) => !item.ok);
const summary = {
  generatedAt: new Date().toISOString(),
  ok: failed.length === 0,
  total: results.length,
  failed: failed.length,
  url,
  interactionUrl: tempUrl,
  results,
};
fs.writeFileSync(reportPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ summary }, null, 2));

fs.rmSync(path.join(root, ".cache", "writing", "documents", `${tempDocumentId}.json`), { force: true });
fs.rmSync(path.join(root, ".cache", "writing", "documents", `${paragraphTempDocumentId}.json`), { force: true });
fs.rmSync(path.join(root, ".cache", "writing", "topic_archives", `${tempDocumentId}.json`), { force: true });
fs.rmSync(path.join(root, ".cache", "writing", "topic_archives", `${paragraphTempDocumentId}.json`), { force: true });
fs.rmSync(path.join(root, "obsidian_vault", "Topics", tempDocumentId), { recursive: true, force: true });
fs.rmSync(path.join(root, "obsidian_vault", "Topics", paragraphTempDocumentId), { recursive: true, force: true });
fs.rmSync(path.join(obsidianMirrorRoot, "Topics", tempDocumentId), { recursive: true, force: true });
fs.rmSync(path.join(obsidianMirrorRoot, "Topics", paragraphTempDocumentId), { recursive: true, force: true });

await Promise.race([
  browser.close(),
  new Promise((resolve) => setTimeout(resolve, 5000)),
]);
process.exit(failed.length ? 1 : 0);
