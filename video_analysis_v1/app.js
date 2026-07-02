const $ = (selector) => document.querySelector(selector);

const state = {
  currentJobId: "",
  sourceMode: "link",
  pollTimer: null,
  activeView: "report",
  latestDraft: null,
  savedDraft: null,
  savedDraftAvailable: false,
  historyExpanded: false,
  currentSummary: {},
  activeDeckSlideIndex: 0,
  editingDeckSlideIndex: null,
  transcriptionHealth: null,
  localVideoFile: null,
};

const nodes = {
  linkMode: $("#linkMode"),
  localMode: $("#localMode"),
  pageHint: $("#pageHint"),
  urlInput: $("#urlInput"),
  localInputWrap: $("#localInputWrap"),
  localVideoInput: $("#localVideoInput"),
  localFileName: $("#localFileName"),
  transcriptionHealth: $("#transcriptionHealth"),
  extractFrames: $("#extractFrames"),
  useBrowserCookies: $("#useBrowserCookies"),
  disableWhisperFallback: $("#disableWhisperFallback"),
  skipRewrites: $("#skipRewrites"),
  showErrors: $("#showErrors"),
  startAnalysis: $("#startAnalysis"),
  refreshJobs: $("#refreshJobs"),
  openHistory: $("#openHistory"),
  closeHistory: $("#closeHistory"),
  closeHistoryPanel: $("#closeHistoryPanel"),
  historyDrawer: $("#historyDrawer"),
  rerunJob: $("#rerunJob"),
  clearFailed: $("#clearFailed"),
  clearHistory: $("#clearHistory"),
  historyToggle: $("#historyToggle"),
  jobsMeta: $("#jobsMeta"),
  jobList: $("#jobList"),
  jobStatus: $("#jobStatus"),
  resultTitle: $("#resultTitle"),
  quickMeta: $("#quickMeta"),
  pipelineStatus: $("#pipelineStatus"),
  downloadProgress: $("#downloadProgress"),
  downloadProgressLabel: $("#downloadProgressLabel"),
  downloadProgressMeta: $("#downloadProgressMeta"),
  downloadProgressBar: $("#downloadProgressBar"),
  videoStage: $("#videoStage"),
  videoPlayer: $("#videoPlayer"),
  playbackSource: $("#playbackSource"),
  videoSummary: $(".video-summary"),
  summaryTitle: $("#summaryTitle"),
  timelineMeta: $("#timelineMeta"),
  timelineSection: $(".timeline-section"),
  timelineList: $("#timelineList"),
  coreClaim: $("#coreClaim"),
  summaryBullets: $("#summaryBullets"),
  summaryTakeaway: $("#summaryTakeaway"),
  materialAcceptance: $("#materialAcceptance"),
  acceptanceLabel: $("#acceptanceLabel"),
  acceptanceSummary: $("#acceptanceSummary"),
  acceptanceChecks: $("#acceptanceChecks"),
  summaryMore: $("#summaryMore"),
  demoDeckSection: $("#demoDeckSection"),
  demoDeckMeta: $("#demoDeckMeta"),
  demoDeckList: $("#demoDeckList"),
  demoDeckQuality: $("#demoDeckQuality"),
  generateDeck: $("#generateDeck"),
  writeDecision: $("#writeDecision"),
  anglePanel: $("#anglePanel"),
  angleList: $("#angleList"),
  writingPack: $("#writingPack"),
  refetchFrames: $("#refetchFrames"),
  saveMaterialPackage: $("#saveMaterialPackage"),
  jobFiles: $("#jobFiles"),
  jobSummary: $("#jobSummary"),
  generateDraft: $("#generateDraft"),
  draftPanel: $("#draftPanel"),
  draftHint: $("#draftHint"),
  draftStatus: $("#draftStatus"),
  draftPitch: $("#draftPitch"),
  draftPreview: $("#draftPreview"),
  deckWorkspace: $("#deckWorkspace"),
  deckFocus: $("#deckFocus"),
  deckPreview: $("#deckPreview"),
  draftMarkdownDetails: $("#draftMarkdownDetails"),
  draftEditor: $("#draftEditor"),
  draftActions: $("#draftActions"),
  draftGate: $("#draftGate"),
  draftGateLabel: $("#draftGateLabel"),
  draftEngineLabel: $("#draftEngineLabel"),
  draftGateList: $("#draftGateList"),
  polishDeck: $("#polishDeck"),
  copyDraft: $("#copyDraft"),
  regenerateDraft: $("#regenerateDraft"),
  saveDraft: $("#saveDraft"),
  saveDeckPptx: $("#saveDeckPptx"),
  saveDeckHtml: $("#saveDeckHtml"),
  sendWorkbench: $("#sendWorkbench"),
  exportLink: $("#exportLink"),
  sourcePackView: $("#sourcePackView"),
  reportView: $("#reportView"),
  briefView: $("#briefView"),
  transcriptView: $("#transcriptView"),
  tabs: document.querySelectorAll(".tab"),
  materialsDetails: $("main > details.details"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `${response.status} ${response.statusText}`);
  return data;
}

async function apiDelete(path) {
  const response = await fetch(path, { method: "DELETE" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `${response.status} ${response.statusText}`);
  return data;
}

function compact(value, limit = 120) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

function formatBytes(value = 0) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return "";
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  const fixed = index === 0 || size >= 10 ? 0 : 1;
  return `${size.toFixed(fixed)} ${units[index]}`;
}

function formatEta(seconds = null) {
  const value = Number(seconds);
  if (!Number.isFinite(value) || value < 1) return "";
  if (value < 60) return `${Math.ceil(value)} 秒`;
  const minutes = Math.floor(value / 60);
  const rest = Math.round(value % 60);
  return rest ? `${minutes} 分 ${rest} 秒` : `${minutes} 分`;
}

function formatElapsed(ms = 0) {
  const value = Number(ms);
  if (!Number.isFinite(value) || value < 1000) return "";
  const seconds = Math.floor(value / 1000);
  if (seconds < 60) return `${seconds} 秒`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  if (minutes < 60) return rest ? `${minutes} 分 ${rest} 秒` : `${minutes} 分`;
  const hours = Math.floor(minutes / 60);
  const minuteRest = minutes % 60;
  return minuteRest ? `${hours} 小时 ${minuteRest} 分` : `${hours} 小时`;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function normalizeUiSentence(value, limit = 160) {
  let text = compact(value || "", limit)
    .replace(/\s+/g, " ")
    .replace(/，，+/g, "，")
    .replace(/：，/g, "：")
    .replace(/^这条内容把重点放在/, "重点在")
    .replace(/^这条视频把重点放在/, "重点在")
    .replace(/^这条视频主要在讲/, "这条视频在讲")
    .replace(/^这条视频围绕/, "这条视频在讲")
    .replace(/把\s+/g, "把")
    .trim();
  if (!text) return "";
  if (!/[。！？]$/.test(text)) text += "。";
  return text;
}

function isInternalWritingRule(value) {
  const text = String(value || "").trim();
  if (!text) return true;
  return /先记对象|先按标题.*画面判断|先按画面|画面判断|原话转述|再分清哪一段|像证据|像转折|关键词和原话|先做证据卡|材料不足|关键缺口|先补材料再写|写稿前必须补上|回看确认|回原视频|再谈判断|别把|成语转换|重点不是|现实门槛|功能名|需补材料|后台规则|这页可以作为文章主判断|可作为文章主判断|先让观众|讲给观众听|观众应该知道|补一条证据/.test(text);
}

function cleanFrontendCopy(value, fallback = "", limit = 120) {
  let text = compact(value || "", limit);
  if (!text) return fallback;
  text = text
    .replace(/已转写/g, "已有字幕")
    .replace(/AI\s*字幕\s*\/\s*转写工具/g, "字幕工具")
    .replace(/AI\s*字幕/g, "字幕")
    .replace(/字幕弱/g, "字幕待确认")
    .replace(/转写工具/g, "字幕工具")
    .replace(/转写/g, "字幕")
    .replace(/现实门槛/g, "问题")
    .replace(/真正要看的?不是[^，。；;]{1,40}，?而是/g, "")
    .replace(/重点不是[^，。；;]+，?而是/g, "")
    .replace(/不是[^，。；;]{1,40}，?而是/g, "")
    .replace(/这是字幕工具，?它在视频里完成的任务。?/g, "看它实际完成了什么。")
    .replace(/这是一个本地视频字幕测试[，,]?现在我们要确认系统可以从视频里听到声音[，,]?并字幕。?/g, "检查视频能不能正常读出声音和字幕。")
    .replace(/先说这条视频想回答的问题。?/g, "先看这条视频要解决什么。")
    .replace(/把这一页为什么重要说清楚。?/g, "")
    .replace(/把发生了什么说清楚。?/g, "")
    .replace(/先把这一页最想让人记住的话说出来。?/g, "")
    .replace(/可以作为正文材料，但写入前还要补清楚对象、动作和结果。?/g, "")
    .replace(/^这页可以作为文章主判断[：:]?\s*/, "")
    .replace(/^可作为文章主判断[：:]?\s*/, "")
    .replace(/^这页负责讲[：:]?\s*/, "")
    .replace(/^补一条证据[：:]?\s*/, "")
    .replace(/^先让观众/, "先让人")
    .replace(/^观众应该知道[：:]?\s*/, "")
    .replace(/^观众记住[：:]?\s*/, "")
    .replace(/写稿前必须补上[^。]*。?/g, "")
    .replace(/^依据[：:]\s*/, "")
    .replace(/^可写[：:]\s*/, "")
    .replace(/^能写成什么[：:]\s*/, "")
    .replace(/^这条内容把重点放在/, "")
    .replace(/^这条视频把重点放在/, "")
    .replace(/，，+/g, "，")
    .replace(/。。+/g, "。")
    .replace(/。([，,；;])/g, "$1")
    .replace(/，。/g, "。")
    .replace(/^[，。；;：:\s]+/, "")
    .trim();
  if (!text || isInternalWritingRule(text)) return fallback;
  return text;
}

function cleanDeckTitle(value, index = 0) {
  let text = cleanFrontendCopy(value, "", 42)
    .replace(/^先看/, "")
    .replace(/^说明/, "")
    .replace(/^验证/, "检查")
    .replace(/^准备/, "准备")
    .trim();
  if (/使用场景/.test(text)) text = "使用场景";
  if (/演示目标/.test(text)) text = "演示目标";
  if (!text) text = `第 ${index + 1} 页`;
  return compact(text, 18);
}

function publicVideoCopy(value, fallback = "") {
  let text = cleanFrontendCopy(value || "", "", 120);
  if (!text || isInternalWritingRule(text)) return fallback;
  text = text
    .replace(/^(产品问题|产品判断|用途|覆盖|发生|可讲|原始证据|这一页值在哪)[：:]\s*/, "")
    .replace(/^可写成[：:]?\s*/, "")
    .replace(/完整观点稿/g, "完整稿")
    .replace(/产品判断/g, "判断")
    .replace(/观点稿/g, "短稿")
    .replace(/判断稿/g, "分析稿")
    .trim();
  text = cleanFrontendCopy(text, "", 120);
  if (!text || isInternalWritingRule(text)) return fallback;
  return text;
}

function cleanDeckLine(value, fallback = "", limit = 86) {
  let text = publicVideoCopy(value, "");
  text = cleanFrontendCopy(text, "", limit)
    .replace(/^可以记成[：:]?\s*/, "")
    .replace(/^这里讲[：:]?\s*/, "")
    .replace(/^这一步[，,]?\s*/, "")
    .replace(/观众/g, "看的人")
    .replace(/看的人看的人/g, "看的人")
    .trim();
  if (!text || isInternalWritingRule(text)) return fallback;
  return compact(text, limit);
}

function firstDeckLine(slide = {}, fields = [], fallback = "", limit = 86) {
  for (const field of fields) {
    const text = cleanDeckLine(slide[field], "", limit);
    if (text) return text;
  }
  return fallback;
}

function cleanSummaryBullet(value) {
  if (isInternalWritingRule(value)) return "";
  if (/你是不是也|主意|^\s*(你|它|这)\s*$/.test(String(value || ""))) return "";
  return compact(
    cleanFrontendCopy(String(value || ""), "", 100)
      .replace(/AI\s*字幕/g, "字幕")
      .replace(/转写/g, "字幕")
      .replace(/^重点处理/, "处理")
      .replace(/^进入面试前，/, "")
      .replace(/^可以写/, "")
      .replace(/产品判断/g, "判断")
      .replace(/判断稿/g, "分析稿")
      .replace(/观点稿/g, "短稿")
      .trim(),
    68,
  );
}

function cleanSummaryTakeaway(value) {
  if (isInternalWritingRule(value)) return "";
  return compact(
    cleanFrontendCopy(String(value || ""), "", 130)
      .replace(/AI\s*字幕/g, "字幕")
      .replace(/转写/g, "字幕")
      .replace(/^适合写成/, "")
      .replace(/^适合写[:：]\s*/, "")
      .replace(/^可以写成/, "")
      .replace(/^可写成/, "")
      .replace(/^能写成/, "")
      .replace(/^能写成什么[:：]\s*/, "")
      .replace(/^操作说明\s*\/\s*工具评测[:：]/, "操作说明或工具评测，")
      .replace(/AI 编程工具判断稿/g, "AI 编程工具分析")
      .replace(/产品判断/g, "判断")
      .replace(/判断稿/g, "分析稿")
      .replace(/观点稿/g, "短稿")
      .replace(/，，+/g, "，")
      .replace(/^，+/, "")
      .trim(),
    120,
  );
}

function cleanSummaryHeadline(value) {
  const text = cleanFrontendCopy(String(value || "").trim(), "", 120);
  if (!text) return "";
  if (isInternalWritingRule(text) || /片段\s*\d+|这条内容把重点放在|判断标准更接近真实使用成本/.test(text)) {
    return "";
  }
  return text
    .replace(/^这条视频顺着演示了一遍[:：]\s*/, "这条视频把 ")
    .replace(/^这条视频主要在讲两件事[:：]\s*/, "这条视频重点在 ")
    .replace(/^这条视频把《(.+?)》怎么跑、哪里会卡顺着演示了一遍。?$/, "这条视频把《$1》怎么跑、哪里会卡都过了一遍。")
    .replace(/^这条视频就盯着一件事讲[:：]\s*/, "这条视频就盯着 ")
    .replace(/把\s+/g, "把")
    .replace(/把 ([^。]+)(?:。)?$/, "把 $1 讲清了。")
    .replace(/重点在 ([^。]+)(?:。)?$/, "重点在 $1。")
    .replace(/盯着 ([^。]+)(?:。)?$/, "盯着 $1讲。");
}

function formatSummaryTakeaway(value) {
  const text = cleanSummaryTakeaway(value);
  if (!text) return "";
  const normalized = text
    .replace(/^操作说明\s*\/\s*工具评测[:：]?\s*/i, "操作说明或工具评测，")
    .replace(/^实测或工具评测[:：]?\s*/i, "工具评测，")
    .replace(/^短教程或工具评测[:：]?\s*/i, "短教程或工具评测，")
    .replace(/^工具评测[:：]?\s*/i, "工具评测，")
    .replace(/^操作说明[:：]?\s*/i, "操作说明，")
    .replace(/^拆成步骤说明[:：]?\s*/i, "步骤说明，")
    .replace(/^AI 编程工具分析[，,:：]?\s*/i, "")
    .replace(/^工具分析[，,:：]?\s*/i, "")
    .replace(/，，+/g, "，")
    .replace(/：，/g, "：")
    .replace(/^，+/, "")
    .replace(/。$/, "");
  const flattened = normalized.replace(/^([^：:，,。]{1,28})[：:]\s*/, "$1，");
  if (!flattened) return "";
  return flattened.endsWith("。") ? flattened : `${flattened}。`;
}

function isNoisyTakeaway(value, headline = "") {
  const text = String(value || "").trim();
  if (!text) return true;
  if (isInternalWritingRule(text)) return true;
  if (text.length > 110) return true;
  if (headline && (text === headline || text.includes(headline))) return true;
  return /这条内容|这条视频|重点放在|判断标准|更接近真实使用成本/.test(text);
}

function professionalAcceptanceCopy(acceptance = {}) {
  const status = String(acceptance.status || "").trim();
  const checks = Array.isArray(acceptance.checks) ? acceptance.checks : [];
  const failed = checks.filter((item) => item.status === "fail");
  const warned = checks.filter((item) => item.status === "warn");
  const hasVideoFailure = failed.some((item) => item.key === "video");
  const hasTranscriptFailure = failed.some((item) => item.key === "transcript");
  const hasTranscriptWarn = warned.some((item) => item.key === "transcript");
  const hasFrameIssue = [...failed, ...warned].some((item) => item.key === "screenshots" || item.key === "deck");
  if (!status && !checks.length) return null;
  if (status === "ready") {
    return null;
  }
  if (hasVideoFailure) {
    return {
      status: "blocked",
      label: "没保存成功",
      summary: "换个链接或重试。",
    };
  }
  if (hasTranscriptFailure) {
    return {
      status: "blocked",
      label: "没拿到字幕",
      summary: "可以先看视频，暂不生成稿。",
    };
  }
  if (status === "blocked") {
    return {
      status,
      label: "暂不能生成",
      summary: "视频或字幕还不完整。",
    };
  }
  if (hasTranscriptWarn) {
    return {
      status: "needs_work",
      label: "字幕待确认",
      summary: "关键片段最好回看一遍。",
    };
  }
  return {
    status: "needs_work",
    label: hasFrameIssue ? "画面偏少" : "待确认",
    summary: hasFrameIssue
      ? "已保存视频，截图还不够。"
      : "写之前回看关键句。",
  };
}

function shortSlideRole(value = "") {
  const text = String(value || "").trim();
  if (!text) return "这一页";
  if (/入口|开场/.test(text)) return "入口";
  if (/准备|材料|配置/.test(text)) return "准备";
  if (/连接|证书|失败/.test(text)) return "排错";
  if (/验证|结果|跑通/.test(text)) return "验收";
  if (/防火墙|限制|代价|门槛/.test(text)) return "门槛";
  return compact(text, 8);
}

function comparisonKey(value = "") {
  return String(value || "")
    .replace(/[：:，。、“”"'‘’！？!?\s]/g, "")
    .trim();
}

function inferTimelineValue(item = {}, index = 0) {
  const text = `${item.summary || ""} ${item.transcriptExcerpt || ""}`;
  if (index >= 4 && /六个月|未来|模型能力|为.*后.*设计/.test(text)) return "回到开头，看它押的不是今天的能力，而是下一阶段的模型。";
  if (index >= 5 && /终端|terminal|命令行|CLI/.test(text)) return "放在后半段，说明它为什么落在真实工程入口。";
  if (/六个月|未来|模型能力|为.*后.*设计/.test(text)) return "先看它押注的不是今天的能力，而是下一阶段的模型。";
  if (/终端|terminal|命令行|CLI/.test(text)) return "解释为什么入口先放在终端，而不是一上来重做界面。";
  if (/git|bash|单测|测试|项目文件|文件|团队记忆|代码/.test(text)) return "证明它不是聊天玩具，而是进入文件、命令和测试。";
  if (/开发者|门槛|真实使用|上下文|项目上下文/.test(text)) return "真正好用的前提，是把项目上下文交给它。";
  if (/低风险|重复|靠上下文推进|任务/.test(text)) return "拆成具体场景，说明它先替人处理哪些低风险动作。";
  if (/开场|背景|提出|介绍/.test(text) || index === 0) return "放在开头，先说清这条视频讨论什么问题。";
  if (/风险|失败|限制|挑战|代价|缺口/.test(text)) return "讲清条件和限制，别只写工具好用。";
  if (/总结|结论|未来|最后|所以/.test(text) || index > 5) return "收束成一个判断，别继续罗列功能。";
  return "先把这一段的人、动作和结果说清楚。";
}

function stripSentencePrefix(text, prefixes = []) {
  let value = compact(text || "", 140);
  prefixes.forEach((prefix) => {
    if (value.startsWith(prefix)) value = value.slice(prefix.length).trim();
  });
  return value.replace(/[。；;]\s*$/, "");
}

function buildEvidenceParagraph(item = {}) {
  const angle = item.writingAngle || "这段";
  const quote = stripSentencePrefix(item.quoteCandidate || item.summary || "", ["可引用："]);
  let value = stripSentencePrefix(item.writingValue || "", ["可以写", "可以", "适合"]);
  if (value.includes("：")) value = value.split("：").slice(1).join("：").trim() || value;
  const avoid = stripSentencePrefix(item.avoidWriting || "", ["不要写成", "不要"]);
  const first = quote ? `${quote}。` : `${item.summary || "这段先看发生了什么。"}。`;
  const second = value ? `重点是${value}。` : "先把谁在做、做了什么、结果怎样说清楚。";
  const third = avoid ? `别${avoid.startsWith("把") || avoid.startsWith("只") || avoid.startsWith("直接") ? avoid : `写成${avoid}`}。` : "";
  return compact(`${angle}：${first}${second}${third}`, 260);
}

function appendDraftParagraph(paragraph) {
  const current = nodes.draftEditor.value.trim();
  const next = current ? `${current}\n\n${paragraph}` : paragraph;
  setDraftText(next);
  saveDraftLocal();
  nodes.draftPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  nodes.draftEditor.focus();
}

async function appendEvidenceParagraph(item = {}, index = 0, button = null) {
  if (button) button.disabled = true;
  showDraftStatus("正在写这一段。", "running");
  try {
    const result = await api("/api/video-evidence-paragraph", {
      method: "POST",
      body: JSON.stringify({
        videoJobId: state.currentJobId || "",
        title: nodes.resultTitle.textContent.trim(),
        timelineItem: item,
      }),
    });
    appendDraftParagraph(result.paragraph || buildEvidenceParagraph(item));
    showDraftStatus(`已加入草稿：${item.timeLabel || `第 ${index + 1} 段`}`, "ready");
  } catch (error) {
    appendDraftParagraph(buildEvidenceParagraph(item));
    showDraftStatus(`已本地加入：${error.message}`, "ready");
  } finally {
    if (button) button.disabled = false;
  }
}

function slugify(value, fallback = "video-draft") {
  const slug = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return slug || fallback;
}

function draftCacheKey(jobId = state.currentJobId) {
  return `video-analysis-draft:${jobId || "scratch"}`;
}

function updateGenerateDeckButton() {
  if (!nodes.generateDeck) return;
  const showingDraft = nodes.draftPanel && !nodes.draftPanel.classList.contains("hidden");
  const label = state.savedDraftAvailable && !showingDraft ? "继续改" : "生成讲稿";
  nodes.generateDeck.textContent = label;
  if (nodes.generateDraft) nodes.generateDraft.textContent = label;
}

function resetDraftSurface({ preserveSavedDraft = false } = {}) {
  if (!preserveSavedDraft) {
    state.savedDraft = null;
    state.savedDraftAvailable = false;
  }
  state.latestDraft = null;
  state.activeDeckSlideIndex = 0;
  state.editingDeckSlideIndex = null;
  nodes.draftPanel?.classList.add("hidden");
  nodes.draftMarkdownDetails?.classList.add("hidden");
  if (nodes.draftMarkdownDetails) nodes.draftMarkdownDetails.open = false;
  nodes.draftEditor.classList.add("hidden");
  nodes.draftActions.classList.add("hidden");
  nodes.draftPitch?.classList.add("hidden");
  if (nodes.draftPitch) nodes.draftPitch.textContent = "";
  nodes.draftPreview?.classList.add("hidden");
  if (nodes.draftPreview) nodes.draftPreview.innerHTML = "";
  nodes.deckWorkspace?.classList.add("hidden");
  nodes.deckFocus?.classList.add("hidden");
  nodes.deckPreview?.classList.add("hidden");
  if (nodes.deckFocus) nodes.deckFocus.innerHTML = "";
  if (nodes.deckPreview) nodes.deckPreview.innerHTML = "";
  nodes.draftEditor.value = "";
  nodes.draftGate.classList.add("hidden");
  setDraftHint("");
  hideDraftStatus();
  updateGenerateDeckButton();
}

function resetWorkspaceSurface() {
  state.currentJobId = "";
  state.currentSummary = {};
  stopPolling();
  nodes.jobStatus.textContent = "待命";
  nodes.resultTitle.textContent = "贴一个视频链接";
  nodes.quickMeta.innerHTML = "";
  nodes.pipelineStatus.innerHTML = "";
  nodes.pipelineStatus.classList.add("hidden");
  nodes.refetchFrames?.classList.add("hidden");
  nodes.saveMaterialPackage?.classList.add("hidden");
  hideDownloadProgress();
  nodes.jobSummary.classList.add("hidden");
  nodes.jobSummary.classList.remove("failure", "pending");
  nodes.jobSummary.textContent = "";
  nodes.videoStage?.classList.add("hidden");
  if (nodes.videoPlayer) {
    nodes.videoPlayer.innerHTML = "";
    nodes.videoPlayer.classList.remove("empty");
    nodes.videoPlayer.style.backgroundImage = "";
  }
  nodes.playbackSource?.classList.add("hidden");
  if (nodes.playbackSource) nodes.playbackSource.textContent = "";
  nodes.videoSummary?.classList.add("hidden");
  if (nodes.summaryTitle) nodes.summaryTitle.textContent = "先看懂";
  if (nodes.coreClaim) nodes.coreClaim.textContent = "暂无。";
  nodes.summaryBullets?.classList.add("hidden");
  if (nodes.summaryBullets) nodes.summaryBullets.innerHTML = "";
  nodes.summaryTakeaway?.classList.add("hidden");
  if (nodes.summaryTakeaway) nodes.summaryTakeaway.textContent = "";
  nodes.materialAcceptance?.classList.add("hidden");
  nodes.summaryMore?.classList.add("hidden");
  nodes.demoDeckSection?.classList.add("hidden");
  if (nodes.demoDeckList) nodes.demoDeckList.innerHTML = "";
  nodes.demoDeckList?.classList.add("hidden");
  nodes.timelineSection?.classList.add("hidden");
  if (nodes.timelineList) nodes.timelineList.innerHTML = "";
  if (nodes.timelineMeta) nodes.timelineMeta.textContent = "等待字幕。";
  nodes.anglePanel?.classList.add("hidden");
  nodes.writeDecision?.classList.add("hidden");
  nodes.writingPack?.classList.add("hidden");
  nodes.materialsDetails?.classList.add("hidden");
  nodes.jobFiles.innerHTML = "";
  nodes.sourcePackView.textContent = "";
  nodes.reportView.textContent = "";
  nodes.briefView.textContent = "";
  nodes.transcriptView.textContent = "";
  nodes.generateDraft.disabled = true;
  nodes.generateDeck.disabled = true;
  resetDraftSurface();
}

function openSavedDraft() {
  const saved = state.savedDraft;
  if (!saved || !saved.body) return false;
  const slides = Array.isArray(saved.slides) && saved.slides.length
    ? saved.slides
    : Array.isArray(state.currentSummary?.demoDeck?.slides)
      ? state.currentSummary.demoDeck.slides
      : [];
  setDraftText(saved.body, {
    engine: "localSaved",
    model: "local",
    headline: saved.headline,
    sourceStatus: saved.sourceStatus,
    slides,
    demoDeckQuality: assessDeckQuality(slides),
  });
  nodes.draftGate.classList.add("hidden");
  setDraftHint("");
  updateGenerateDeckButton();
  return true;
}

function setActiveView(view) {
  state.activeView = view;
  nodes.tabs.forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  nodes.sourcePackView.classList.toggle("hidden", view !== "sourcePack");
  nodes.reportView.classList.toggle("hidden", view !== "report");
  nodes.briefView.classList.toggle("hidden", view !== "brief");
  nodes.transcriptView.classList.toggle("hidden", view !== "transcript");
}

function openHistoryDrawer() {
  nodes.historyDrawer.classList.remove("hidden");
  nodes.historyDrawer.setAttribute("aria-hidden", "false");
}

function closeHistoryDrawer() {
  nodes.historyDrawer.classList.add("hidden");
  nodes.historyDrawer.setAttribute("aria-hidden", "true");
}

function setSourceMode(mode = "link") {
  state.sourceMode = mode === "local" ? "local" : "link";
  nodes.linkMode?.classList.toggle("active", state.sourceMode === "link");
  nodes.localMode?.classList.toggle("active", state.sourceMode === "local");
  nodes.urlInput?.classList.toggle("hidden", state.sourceMode !== "link");
  nodes.localInputWrap?.classList.toggle("hidden", state.sourceMode !== "local");
  nodes.startAnalysis.textContent = state.sourceMode === "local" ? "分析" : "下载";
  if (state.sourceMode === "local") {
    nodes.pageHint && (nodes.pageHint.textContent = "选本地视频，抽截图，拆材料。");
    void refreshTranscriptionHealth();
  } else {
    nodes.pageHint && (nodes.pageHint.textContent = "贴链接，保存成本地视频。");
  }
}

function renderTranscriptionHealth(health = null) {
  if (!nodes.transcriptionHealth) return;
  nodes.transcriptionHealth.classList.remove("ready", "missing");
  if (!health) {
    nodes.transcriptionHealth.textContent = "转写检测中";
    return;
  }
  nodes.transcriptionHealth.textContent = health.label || (health.ok ? "转写可用" : "转写不可用");
  nodes.transcriptionHealth.classList.add(health.ok ? "ready" : "missing");
}

async function refreshTranscriptionHealth() {
  if (state.transcriptionHealth) {
    renderTranscriptionHealth(state.transcriptionHealth);
    return state.transcriptionHealth;
  }
  renderTranscriptionHealth(null);
  try {
    const health = await api("/api/video-analysis-transcription-health");
    state.transcriptionHealth = health;
    renderTranscriptionHealth(health);
    return health;
  } catch {
    const health = { ok: false, label: "转写环境未检测到" };
    state.transcriptionHealth = health;
    renderTranscriptionHealth(health);
    return health;
  }
}

function selectedLocalVideoFile() {
  if (state.localVideoFile) return state.localVideoFile;
  const files = nodes.localVideoInput?.files;
  return files && files.length ? files[0] : null;
}

function setLocalVideoFile(file = null) {
  state.localVideoFile = file || null;
  updateLocalFileName();
}

function updateLocalFileName() {
  if (!state.localVideoFile) {
    const files = nodes.localVideoInput?.files;
    state.localVideoFile = files && files.length ? files[0] : null;
  }
  const file = selectedLocalVideoFile();
  if (!nodes.localFileName) return;
  nodes.localFileName.textContent = file ? `${file.name}${file.size ? ` · ${formatBytes(file.size)}` : ""}` : "选择 mp4 / mov / mkv / webm";
}

function handleLocalDrag(event) {
  if (!nodes.localInputWrap || state.sourceMode !== "local") return;
  event.preventDefault();
  if (event.type === "dragenter" || event.type === "dragover") {
    nodes.localInputWrap.classList.add("is-drag-over");
    if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
  } else if (event.type === "dragleave") {
    nodes.localInputWrap.classList.remove("is-drag-over");
  } else if (event.type === "drop") {
    nodes.localInputWrap.classList.remove("is-drag-over");
    const file = event.dataTransfer?.files?.[0] || null;
    if (file) setLocalVideoFile(file);
  }
}

function normalizeJobKey(job) {
  const url = String(job.url || "").trim();
  if (url) {
    try {
      const parsed = new URL(url);
      parsed.searchParams.delete("utm_source");
      parsed.searchParams.delete("utm_medium");
      parsed.searchParams.delete("utm_campaign");
      parsed.searchParams.delete("spm_id_from");
      parsed.searchParams.delete("vd_source");
      return parsed.toString();
    } catch {
      return url;
    }
  }
  return String(job.title || job.id || "").trim().toLowerCase();
}

function dedupeJobs(jobs) {
  const seen = new Map();
  jobs.forEach((job) => {
    const key = normalizeJobKey(job);
    if (!seen.has(key)) {
      seen.set(key, { ...job, duplicateCount: 1 });
      return;
    }
    const current = seen.get(key);
    current.duplicateCount = (current.duplicateCount || 1) + 1;
  });
  return Array.from(seen.values());
}

function requestedJobIdFromUrl() {
  try {
    return new URL(window.location.href).searchParams.get("jobId") || "";
  } catch {
    return "";
  }
}

function writeJobIdToUrl(jobId, replace = true) {
  if (!jobId) return;
  try {
    const next = new URL(window.location.href);
    if (next.searchParams.get("jobId") === jobId) return;
    next.searchParams.set("jobId", jobId);
    const method = replace ? "replaceState" : "pushState";
    window.history[method]({}, "", next);
  } catch {
    // URL sync is a convenience; loading the job should not depend on it.
  }
}

function renderJobs(jobs) {
  const allVisibleJobs = dedupeJobs(jobs.filter((job) => nodes.showErrors.checked || job.status !== "error"));
  const visibleJobs = state.historyExpanded ? allVisibleJobs : allVisibleJobs.slice(0, 8);
  const hiddenCount = Math.max(0, allVisibleJobs.length - visibleJobs.length);
  nodes.jobsMeta.textContent = String(allVisibleJobs.length);
  nodes.historyToggle.classList.toggle("hidden", allVisibleJobs.length <= 8);
  nodes.historyToggle.textContent = state.historyExpanded ? "收起" : `更多 ${hiddenCount}`;
  nodes.jobList.innerHTML = "";
  if (!visibleJobs.length) {
    nodes.jobList.textContent = "暂无任务";
    return;
  }
  visibleJobs.forEach((job) => {
    const button = document.createElement("button");
    button.type = "button";
    const classes = ["job"];
    if (state.currentJobId === job.id) classes.push("active");
    if (jobHasLocalVideo(job)) classes.push("local-ready");
    if (isDownloadRequiredFailure(job)) classes.push("download-failed");
    button.className = classes.join(" ");
    const versionLabel = job.duplicateCount > 1 ? `版本 ${job.duplicateCount}` : "最新";
    const statusLabel = compactJobStatus(job);
    const platformLabel = jobPlatformLabel(job);
    button.innerHTML = `
      <strong>${escapeHtml(compact(job.title || job.url, 66))}</strong>
      <small>${escapeHtml([versionLabel, platformLabel, statusLabel].filter(Boolean).join(" · "))}</small>
    `;
    button.addEventListener("click", () => {
      state.currentJobId = job.id;
      closeHistoryDrawer();
      writeJobIdToUrl(job.id, false);
      void loadJob(job.id, true);
    });
    nodes.jobList.appendChild(button);
  });
}

function fileLabel(key) {
  return {
    note_path: "报告",
    transcript_md_path: "字幕",
    source_pack_path: "材料",
  }[key] || key;
}

function fileUrl(path) {
  return `/api/video-analysis-file?path=${encodeURIComponent(path)}`;
}

function downloadFileUrl(url = "") {
  if (!url) return "";
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}download=1`;
}

function renderFiles(files = {}) {
  nodes.jobFiles.innerHTML = "";
  const entries = Object.entries(files).filter(([key, value]) => ["note_path", "transcript_md_path", "source_pack_path"].includes(key) && Boolean(value));
  if (!entries.length) return;
  entries.forEach(([key, value]) => {
    const link = document.createElement("a");
    link.href = fileUrl(value);
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = fileLabel(key);
    link.title = value;
    nodes.jobFiles.appendChild(link);
  });
}

function renderAngles(angles = [], cards = []) {
  nodes.angleList.innerHTML = "";
  const displayCards = Array.isArray(cards) && cards.length
    ? cards
    : angles.slice(0, 3).map((angle, index) => ({
        label: ["切入", "冲突", "落点"][index] || "方向",
        title: angle,
        detail: "",
      }));
  if (!displayCards.length) {
    nodes.anglePanel?.classList.add("hidden");
    return;
  }
  nodes.anglePanel?.classList.add("hidden");
  displayCards.slice(0, 3).forEach((card) => {
    const item = document.createElement("li");
    item.className = "angle-card";
    const label = document.createElement("span");
    label.textContent = card.label || "方向";
    const title = document.createElement("strong");
    title.textContent = card.title || "";
    item.append(label, title);
    if (card.detail) {
      const detail = document.createElement("small");
      detail.textContent = card.detail;
      item.appendChild(detail);
    }
    nodes.angleList.appendChild(item);
  });
}

function renderWriteDecision(decision = {}) {
  const level = String(decision.level || "").trim();
  const reason = compact(String(decision.reason || "").replace(/适合进入写稿 brief/g, "可以写"), 64);
  const gaps = Array.isArray(decision.gaps)
    ? decision.gaps
        .map((item) => compact(item, 38))
        .filter((item) => item && !/(评论区|外部报道|热度和争议|社媒讨论)/.test(item))
        .slice(0, 1)
    : [];
  nodes.writeDecision.classList.toggle("hidden", !level && !reason && !gaps.length);
  if (!level && !reason && !gaps.length) {
    nodes.writeDecision.innerHTML = "";
    updateSummaryMore();
    return;
  }
  const levelText = level || "待判断";
  nodes.writeDecision.innerHTML = `
    <strong>${escapeHtml(levelText)}</strong>
    ${reason ? `<span>${escapeHtml(reason)}</span>` : ""}
    ${gaps.length ? `<small>${escapeHtml(gaps.join(" / "))}</small>` : ""}
  `;
  updateSummaryMore();
}

function renderVideoSummary(summary = {}, result = {}) {
  const card = summary.videoSummary || {};
  const materialBlocked = demoDeckBlockedByMaterial(summary);
  if (materialBlocked) {
    if (nodes.summaryTitle) nodes.summaryTitle.textContent = "先看视频";
    nodes.coreClaim.textContent = "已保存视频，没拿到字幕。";
    nodes.summaryBullets.classList.add("hidden");
    nodes.summaryBullets.innerHTML = "";
    nodes.summaryTakeaway.classList.add("hidden");
    nodes.summaryTakeaway.textContent = "";
    nodes.materialAcceptance?.classList.add("hidden");
    updateSummaryMore();
    return;
  }
  if (nodes.summaryTitle) nodes.summaryTitle.textContent = "先看懂";
  const rawHeadline = normalizeUiSentence(card.headline || summary.coreClaim || result.core_claim || "", 120);
  const headline = cleanSummaryHeadline(rawHeadline) || "先看视频讲了什么。";
  const headlineKey = comparisonKey(headline);
  const bullets = Array.isArray(card.bullets)
    ? card.bullets
        .map(cleanSummaryBullet)
        .filter(Boolean)
        .filter((item, index, list) => comparisonKey(item) !== headlineKey && list.findIndex((other) => comparisonKey(other) === comparisonKey(item)) === index)
        .slice(0, 3)
    : [];
  const takeawayRaw = normalizeUiSentence(cleanFrontendCopy(card.takeaway || "", "", 120), 96);
  const takeaway = isNoisyTakeaway(takeawayRaw, headline) ? "" : formatSummaryTakeaway(takeawayRaw);
  nodes.coreClaim.textContent = headline || "暂无。";
  nodes.summaryBullets.classList.toggle("hidden", !bullets.length);
  nodes.summaryBullets.innerHTML = bullets.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  nodes.summaryTakeaway.classList.toggle("hidden", !takeaway);
  nodes.summaryTakeaway.textContent = takeaway;
  renderMaterialAcceptance(summary.materialAcceptance || {});
}

function renderMaterialAcceptance(acceptance = {}) {
  if (!nodes.materialAcceptance) return;
  const copy = professionalAcceptanceCopy(acceptance);
  nodes.materialAcceptance.classList.toggle("hidden", !copy);
  nodes.materialAcceptance.open = false;
  nodes.materialAcceptance.dataset.status = copy?.status || "";
  nodes.acceptanceLabel.textContent = copy?.label || "";
  nodes.acceptanceSummary.textContent = copy?.summary || "";
  nodes.acceptanceChecks.innerHTML = "";
}

function renderWritingPack(pack = {}) {
  const profile = pack.discussionProfile || {};
  const rawSignals = Array.isArray(profile.signals) && profile.signals.length ? profile.signals : pack.discussionSignals;
  const signals = Array.isArray(rawSignals) ? rawSignals.map((item) => compact(item, 30)).filter(Boolean).slice(0, 4) : [];
  const discussionEvidence = Array.isArray(profile.evidence) ? profile.evidence.map((item) => compact(item, 42)).filter(Boolean).slice(0, 2) : [];
  const discussionGaps = Array.isArray(profile.gaps) ? profile.gaps.map((item) => compact(item, 42)).filter(Boolean).slice(0, 2) : [];
  const discussion = discussionEvidence.slice(0, 2);
  const gaps = Array.isArray(pack.gaps) ? pack.gaps.map((item) => compact(item, 38)).filter(Boolean).slice(0, 1) : [];
  nodes.writingPack.classList.toggle("hidden", !signals.length && !discussion.length && !gaps.length);
  if (!signals.length && !discussion.length && !gaps.length) {
    nodes.writingPack.innerHTML = "";
    updateSummaryMore();
    return;
  }
  const signalHtml = signals.length ? `<div><strong>数据</strong><small>${escapeHtml(signals.join(" / "))}</small></div>` : "";
  const discussionHtml = discussion.length ? `<div><strong>评论</strong><small>${escapeHtml(discussion.join(" / "))}</small></div>` : "";
  const gapHtml = gaps.length ? `<div><strong>缺口</strong><small>${escapeHtml(gaps.join(" / "))}</small></div>` : "";
  nodes.writingPack.innerHTML = `${signalHtml}${discussionHtml}${gapHtml}`;
  updateSummaryMore();
}

function updateSummaryMore() {
  const hasDecision = nodes.writeDecision && !nodes.writeDecision.classList.contains("hidden") && nodes.writeDecision.textContent.trim();
  const hasPack = nodes.writingPack && !nodes.writingPack.classList.contains("hidden") && nodes.writingPack.textContent.trim();
  const hasFrameAction = nodes.refetchFrames && !nodes.refetchFrames.classList.contains("hidden");
  nodes.summaryMore?.classList.toggle("hidden", !hasDecision && !hasPack && !hasFrameAction);
}

function transcriptSourceLabel(job = {}) {
  const summary = job.summary || job || {};
  const quality = summary.transcriptQuality || job.transcriptQuality || {};
  if (quality && quality.label) {
    const label = cleanFrontendCopy(String(quality.label), String(quality.label), 20);
    if (/^(无字幕|缺字幕)$/.test(label)) return "没拿到字幕";
    return label;
  }
  const source = String(summary.transcriptSource || job.transcriptSource || job.transcript_source || "").toLowerCase();
  const notes = [
    ...(Array.isArray(summary.transcriptNotes) ? summary.transcriptNotes : []),
    ...(Array.isArray(job.transcriptNotes) ? job.transcriptNotes : []),
  ].map((item) => String(item).toLowerCase());
  if (!source || source === "none") {
    if (notes.some((item) => item.includes("api-empty") || item.includes("login-required") || item.includes("not-installed"))) return "没拿到字幕";
    return "";
  }
  if (source.includes("embedded-subtitle") || source.includes("bilibili-subtitle") || source.includes("yt-dlp-captions")) return "字幕";
  if (source.includes("whisper") || source.includes("asr")) return "字幕";
  if (source.includes("video-parser") || source.includes("web-transcript")) return "字幕";
  if (notes.some((item) => item.includes("login-required"))) return "需登录";
  if (notes.some((item) => item.includes("api-empty") || item.includes("not-installed"))) return "没拿到字幕";
  return "字幕";
}

function platformFromUrl(url = "") {
  const value = String(url || "").toLowerCase();
  if (value.includes("bilibili.com") || value.includes("b23.tv")) return "bilibili";
  if (value.includes("youtube.com") || value.includes("youtu.be")) return "youtube";
  return "";
}

function platformLoginUrl(platform = "") {
  if (platform === "youtube") return "https://www.youtube.com/";
  if (platform === "bilibili") return "https://www.bilibili.com/";
  return "";
}

function jobPlatformLabel(job = {}) {
  const platform = job.summary?.platform || job.platform || platformFromUrl(job.url);
  if (platform === "local" || job.sourceType === "local") return "本地";
  if (platform === "bilibili") return "B站";
  if (platform === "youtube") return "YouTube";
  return "";
}

function jobHasLocalVideo(job = {}) {
  const summary = job.summary || {};
  const embed = summary.videoEmbed || job.videoEmbed || {};
  return embed.type === "local" && Boolean(embed.src || embed.localPath);
}

function downloadPolicyFor(jobOrSummary = {}) {
  const summary = jobOrSummary.summary || jobOrSummary || {};
  return summary.downloadPolicy && typeof summary.downloadPolicy === "object" ? summary.downloadPolicy : {};
}

function downloadAuthLabel(jobOrSummary = {}) {
  const policy = downloadPolicyFor(jobOrSummary);
  const browser = String(policy.browserCookies || "").trim();
  const auth = String(policy.auth || "").trim();
  if (browser) return browser === "chrome" ? "已用 Chrome" : `已用 ${browser}`;
  if (auth.startsWith("browser:")) {
    const source = auth.split(":")[1] || "浏览器";
    return source === "chrome" ? "已用 Chrome" : `已用 ${source}`;
  }
  if (auth === "disabled") return "";
  if (auth.startsWith("file:")) return "cookies 文件";
  return "";
}

function downloadPolicyLabel(jobOrSummary = {}) {
  const summary = jobOrSummary.summary || jobOrSummary || {};
  const policy = downloadPolicyFor(summary);
  if (policy.cacheReuse) return "本地视频";
  if (policy.status === "saved" || summary.videoEmbed?.type === "local") return "本地视频";
  if (policy.status === "failed") return "下载失败";
  return "";
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return "";
  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(mb >= 10 ? 0 : 1)}MB`;
  const kb = bytes / 1024;
  return `${Math.max(1, Math.round(kb))}KB`;
}

function compactJobStatus(job = {}) {
  if (job.status === "done") return jobHasLocalVideo(job) ? "本地视频" : "异常完成";
  if (isDownloadRequiredFailure(job)) return "下载失败";
  if (job.status === "error") return "失败";
  if (job.status === "running") return "下载中";
  if (job.status === "queued") return "待下载";
  return job.status || "待命";
}

function friendlyJobMessage(job = {}) {
  const raw = `${job.message || ""} ${job.error || ""}`.trim();
  const platform = job.summary?.platform || job.platform || platformFromUrl(job.url);
  if (job.status === "error" && /视频下载失败|没有本地视频文件|video-download|yt-dlp-video-download-failed/i.test(raw)) {
    if (/not a bot|Sign in to confirm|cookies-from-browser|需要登录|登录|bot/i.test(raw)) {
      return `${platform === "bilibili" ? "B站" : "YouTube"} 要求登录或反机器人验证，本地下载被拦下。`;
    }
    if (/Requested format is not available|No video formats|format is not available/i.test(raw)) {
      return `${platform === "bilibili" ? "B站" : "YouTube"} 没有返回可保存的视频格式，本地下载被拦下。`;
    }
    if (platform === "bilibili") return "B站视频没有保存到本地，已停止。常见原因是站点风控、登录或权限限制。";
    if (platform === "youtube") return "YouTube 视频没有保存到本地，已停止。可能是下载器、网络或权限问题。";
    return "视频没有保存到本地，已停止。";
  }
  if (job.status === "error" && !platform) return raw || "当前只支持 YouTube 和 B站链接。";
  return raw;
}

function renderMeta(job) {
  const summary = job.summary || job || {};
  const sourceLabel = downloadPolicyLabel(summary) || playbackModeLabel(summary);
  const frameCount = (summary.frames || []).length;
  const bits = [
    sourceLabel,
    frameCount ? `${frameCount} 张图` : "",
  ].filter(Boolean);
  nodes.quickMeta.classList.toggle("hidden", !bits.length);
  nodes.quickMeta.innerHTML = bits.map((item) => `<span>${escapeHtml(item)}</span>`).join("");
}

function playbackModeLabel(summary = {}) {
  const embed = summary.videoEmbed || {};
  const policy = downloadPolicyFor(summary);
  if (policy.cacheReuse) return "本地视频";
  if (embed.type === "youtube") return "未下载";
  if (embed.type === "bilibili") return "未下载";
  if (embed.type === "local") {
    const sizeText = formatBytes(embed.localBytes);
    return sizeText ? `已下载 ${sizeText}` : "已下载";
  }
  if (embed.thumbnailUrl && embed.watchUrl) return "封面预览";
  if (embed.watchUrl) return "原链接";
  return "";
}

function playbackSourceText(summary = {}) {
  const embed = summary.videoEmbed || {};
  const policy = downloadPolicyFor(summary);
  const frameCount = Array.isArray(summary.frames) ? summary.frames.length : 0;
  const frameText = frameCount ? `截图 ${frameCount} 张已保存` : "未抓到截图";
  const sizeText = formatBytes(embed.localBytes || policy.localVideoBytes);
  if (embed.type === "local" && policy.cacheReuse) return `已保存本地${sizeText ? ` · ${sizeText}` : ""} · ${frameText}`;
  if (embed.type === "local") return `已保存本地${sizeText ? ` · ${sizeText}` : ""} · ${frameText}`;
  if (embed.type === "youtube") return `未下载到本地 · YouTube 链接 · ${frameText}`;
  if (embed.type === "bilibili") return `未下载到本地 · B站链接 · ${frameText}`;
  if (embed.thumbnailUrl && embed.watchUrl) return "未下载到本地 · 仅有封面和链接";
  if (embed.watchUrl) return "未下载到本地 · 仅有链接";
  return "";
}

function compactSourceStatus(value, summary = {}) {
  const text = String(value || playbackSourceText(summary) || "").trim();
  return text
    .replace("本地视频片段播放", "本地片段播放")
    .replace("本地片段播放", "已下载到本地")
    .replace("截图已本地保存", "截图已保存")
    .replace("不是本地下载视频", "未下载")
    .replace("没有下载视频", "未下载")
    .replace("未下载视频", "未下载")
    .replace("YouTube 内嵌播放", "YouTube 链接")
    .replace("B站内嵌播放", "B站链接")
    .replace("内嵌播放", "链接预览");
}

function parseTimeLabelToSeconds(value) {
  const text = String(value || "").trim();
  if (!text) return null;
  const parts = text.split(":").map((part) => Number.parseInt(part, 10));
  if (parts.some((part) => Number.isNaN(part))) return null;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return null;
}

function demoDeckTargetSeconds(summary = {}) {
  const slides = Array.isArray(summary.demoDeck?.slides) ? summary.demoDeck.slides : [];
  const seconds = [];
  slides.forEach((slide) => {
    const value =
      Number.isFinite(Number(slide.start)) && Number(slide.start) >= 0
        ? Number(slide.start)
        : parseTimeLabelToSeconds(slide.timeLabel);
    if (value === null || Number.isNaN(value) || value < 0) return;
    const rounded = Math.round(value);
    if (!seconds.includes(rounded)) seconds.push(rounded);
  });
  return seconds.slice(0, 12);
}

function deckNeedsEvidenceFrames(summary = {}) {
  const quality = summary.demoDeck?.demoDeckQuality;
  const issues = Array.isArray(quality?.issues) ? quality.issues : [];
  return issues.some((issue) => /截图|封面|关键帧|画面/.test(String(issue)));
}

function normalizedMaterialState(summary = {}) {
  const raw = summary.materialState || {};
  const required = ["video", "transcript", "frames", "material"];
  if (required.every((key) => raw?.[key]?.label)) return raw;

  const embed = summary.videoEmbed || {};
  const policy = downloadPolicyFor(summary);
  const frames = Array.isArray(summary.frames) ? summary.frames : [];
  const transcriptQuality = summary.transcriptQuality || {};
  const transcriptCount = Number(transcriptQuality.segmentCount || 0) || 0;
  const transcriptLevel = String(transcriptQuality.level || "none");
  const slides = Array.isArray(summary.demoDeck?.slides) ? summary.demoDeck.slides : [];
  const strongSlides = Number(summary.demoDeck?.demoDeckQuality?.strongSlideCount || 0) || 0;
  const timeline = Array.isArray(summary.timeline) ? summary.timeline : [];
  const hasLocalVideo = embed.type === "local" && Boolean(embed.src);
  const localBytes = Number(embed.localBytes || policy.localVideoBytes || 0) || 0;
  const hasTranscript = transcriptQuality.usable || ["strong", "medium"].includes(transcriptLevel);

  return {
    video: {
      label: "视频",
      status: hasLocalVideo ? "ready" : "missing",
      detail: hasLocalVideo ? (formatBytes(localBytes) || "已保存") : "未保存",
    },
    transcript: {
      label: "字幕",
      status: hasTranscript ? (transcriptLevel === "weak" ? "warn" : "ready") : "missing",
      detail: transcriptCount ? `${transcriptCount} 段` : "未拿到",
    },
    frames: {
      label: "截图",
      status: frames.length >= 3 ? "ready" : frames.length ? "warn" : "missing",
      detail: frames.length ? `${frames.length} 张` : "未抓到",
    },
    material: {
      label: "材料",
      status: strongSlides >= Math.min(3, slides.length || 3) ? "ready" : (slides.length || timeline.length ? "warn" : "blocked"),
      detail: slides.length ? `${strongSlides || slides.length}/${slides.length} 页` : `${timeline.length} 段`,
    },
  };
}

function materialPillClass(status) {
  if (status === "ready") return "ok";
  if (status === "warn") return "warn";
  if (status === "blocked" || status === "missing") return "bad";
  return "";
}

function renderPipelineStatus(job) {
  const summary = job.summary || {};
  const frames = summary.frames || [];
  const visualNotes = summary.visualNotes || [];
  const frameDisabled = visualNotes.includes("frame-extraction-disabled") || job.extractFrames === false;
  const frameFailed = visualNotes.some((note) => String(note).includes("frame-extraction-failed"));
  const needsEvidenceFrames = deckNeedsEvidenceFrames(summary);
  const missingUsefulFrames = !frames.length && Boolean(job.url) && job.status === "done";
  const frameLabel = frames.length
    ? `截图 ${frames.length}`
    : job.status === "error"
      ? "无截图"
      : frameFailed
      ? "截图失败"
      : frameDisabled
        ? "未抽帧"
        : "取图中";
  const canRefetchFrames = job.status === "done" && job.url && ((!frames.length && (frameDisabled || frameFailed || missingUsefulFrames)) || needsEvidenceFrames);

  let items = [];
  if (job.status === "done") {
    const materialState = normalizedMaterialState(summary);
    items = ["video", "transcript", "frames", "material"]
      .map((key) => materialState[key])
      .filter(Boolean)
      .map((item) => ({
        label: item.detail ? `${item.label} ${item.detail}` : item.label,
        className: materialPillClass(item.status),
      }));
    if (!frames.length && canRefetchFrames && !items.some((item) => /截图/.test(item.label))) {
      items.push({ label: frameLabel, className: "warn" });
    }
  } else if (job.status === "error") {
    items = [{ label: "失败", className: "bad" }];
  }

  const shouldShowPipeline = Boolean(items.length);
  nodes.pipelineStatus.classList.toggle("hidden", !shouldShowPipeline);
  nodes.pipelineStatus.innerHTML = items
    .map((item) => `<span class="${escapeHtml(item.className || "")}">${escapeHtml(item.label)}</span>`)
    .join("");
  nodes.refetchFrames.textContent = needsEvidenceFrames && frames.length ? "补关键帧" : "补截图";
  nodes.refetchFrames.classList.toggle("hidden", !canRefetchFrames);
  nodes.saveMaterialPackage?.classList.add("hidden");
  updateSummaryMore();
}

function humanJobStatus(job) {
  const status = job.status || "queued";
  if (status === "done") return "完成";
  if (job.sourceType === "local" && status === "running") return "导入中";
  if (job.sourceType === "local" && status === "queued") return "待导入";
  if (status === "running") return "处理中";
  if (status === "queued") return "待下载";
  if (status === "error") return "失败";
  return status;
}

function renderVideoPlayer(summary = {}) {
  const embed = summary.videoEmbed || {};
  const posterUrl = videoPosterUrl(summary);
  nodes.videoPlayer.innerHTML = "";
  nodes.videoPlayer.classList.remove("empty");
  nodes.videoPlayer.style.backgroundImage = posterUrl ? `url("${posterUrl}")` : "";
  nodes.videoStage?.classList.add("hidden");
  nodes.playbackSource?.classList.add("hidden");

  const showPlayback = () => {
    nodes.videoStage?.classList.remove("hidden");
    const sourceText = playbackSourceText(summary);
    if (nodes.playbackSource) {
      nodes.playbackSource.innerHTML = "";
      const sourceLabel = document.createElement("span");
      sourceLabel.className = "playback-source-text";
      sourceLabel.textContent = sourceText;
      nodes.playbackSource.append(sourceLabel);
      if (embed.type === "local" && embed.src) {
        const downloadLink = document.createElement("a");
        downloadLink.href = downloadFileUrl(embed.src);
        downloadLink.textContent = "下载";
        downloadLink.download = "source-video.mp4";
        nodes.playbackSource.append(document.createTextNode(" "), downloadLink);
      }
      nodes.playbackSource.classList.toggle("hidden", !sourceText);
    }
  };

  if (embed.type === "youtube" || embed.type === "bilibili") {
    const iframe = document.createElement("iframe");
    iframe.src = embed.src;
    iframe.title = "视频播放器";
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.allowFullscreen = true;
    nodes.videoPlayer.appendChild(iframe);
    showPlayback();
    return;
  }
  if (embed.type === "local" && embed.src) {
    const video = document.createElement("video");
    video.controls = true;
    video.preload = "none";
    video.src = embed.src;
    if (posterUrl) video.poster = posterUrl;
    nodes.videoPlayer.appendChild(video);
    showPlayback();
    return;
  }
  if (embed.thumbnailUrl) {
    const image = document.createElement("img");
    image.src = embed.thumbnailUrl;
    image.alt = "视频封面";
    nodes.videoPlayer.appendChild(image);
    if (embed.watchUrl) {
      const link = document.createElement("a");
      link.href = embed.watchUrl;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = "打开链接";
      nodes.videoPlayer.appendChild(link);
    }
    showPlayback();
    return;
  }
  if (embed.watchUrl) {
    nodes.videoPlayer.classList.add("empty");
    const label = document.createElement("span");
    label.textContent = "没有本地视频";
    const link = document.createElement("a");
    link.href = embed.watchUrl;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "打开链接";
    nodes.videoPlayer.append(label, link);
    showPlayback();
    return;
  }
  nodes.videoPlayer.classList.add("empty");
  nodes.videoStage?.classList.add("hidden");
  if (nodes.playbackSource) {
    nodes.playbackSource.textContent = "";
    nodes.playbackSource.classList.add("hidden");
  }
}

function videoPosterUrl(summary = {}) {
  const frames = Array.isArray(summary.frames) ? summary.frames : [];
  const firstFrame = frames.find((frame) => frame?.url)?.url || "";
  const slides = Array.isArray(summary.demoDeck?.slides) ? summary.demoDeck.slides : [];
  const slideFrame = slides.find((slide) => slide?.frameUrl)?.frameUrl || "";
  return firstFrame || slideFrame || summary.videoEmbed?.thumbnailUrl || "";
}

function renderTimeline(summary = {}) {
  const timeline = summary.timeline || [];
  const transcriptLabel = transcriptSourceLabel(summary);
  nodes.timelineList.innerHTML = "";
  nodes.timelineMeta.textContent = timeline.length
    ? `${timeline.length} 段${transcriptLabel ? ` · ${transcriptLabel}` : ""}`
    : "暂无片段";
  if (!timeline.length) {
    const empty = document.createElement("div");
    empty.className = "timeline-empty";
    empty.textContent = "完成后显示片段。";
    nodes.timelineList.appendChild(empty);
    return;
  }
  timeline.forEach((item, index) => {
    const row = document.createElement("article");
    row.className = "timeline-item";
    const mediaWrap = document.createElement(item.watchAtUrl ? "a" : "div");
    mediaWrap.className = "timeline-media";
    if (item.watchAtUrl) {
      mediaWrap.href = item.watchAtUrl;
      mediaWrap.target = "_blank";
      mediaWrap.rel = "noreferrer";
      mediaWrap.title = `从 ${item.timeLabel || "00:00"} 打开链接`;
    }
    const media = document.createElement(item.frameUrl ? "img" : "div");
    media.className = item.frameUrl ? "timeline-frame" : "timeline-frame empty";
    if (item.frameUrl) {
      media.src = item.frameUrl;
      media.alt = item.frameLabel || `时间点 ${index + 1}`;
    } else {
      media.textContent = "无图";
    }
    const mediaTime = document.createElement("span");
    mediaTime.className = "timeline-media-time";
    mediaTime.textContent = item.timeLabel || "00:00";
    mediaWrap.append(media, mediaTime);
    const content = document.createElement("div");
    content.className = "timeline-content";
    const top = document.createElement("div");
    top.className = "timeline-top";
    const time = document.createElement(item.watchAtUrl ? "a" : "span");
    time.className = "timestamp";
    time.textContent = item.timeLabel || "00:00";
    if (item.watchAtUrl) {
      time.href = item.watchAtUrl;
      time.target = "_blank";
      time.rel = "noreferrer";
    }
    const label = document.createElement("span");
    label.textContent = publicVideoCopy(item.writingAngle, `第 ${index + 1} 段`);
    top.append(time, label);
    const summaryText = document.createElement("p");
    summaryText.className = "timeline-summary";
    summaryText.textContent = cleanFrontendCopy(publicVideoCopy(
      item.summary,
      publicVideoCopy(item.transcriptExcerpt, "这一段需要回看视频确认。"),
    ), "这一段需要回看视频确认。", 120);
    const valueText = document.createElement("p");
    valueText.className = "timeline-value";
    valueText.textContent = cleanFrontendCopy(publicVideoCopy(item.writingValue, inferTimelineValue(item, index)), "", 120);
    const writeButton = document.createElement("button");
    writeButton.type = "button";
    writeButton.className = "timeline-write";
    writeButton.textContent = "写一段";
    writeButton.addEventListener("click", () => {
      void appendEvidenceParagraph(item, index, writeButton);
    });
    const transcript = document.createElement("details");
    transcript.className = "timeline-transcript";
    const transcriptSummary = document.createElement("summary");
    const pseudoTranscript = /^(未拿到字幕|无字幕)/.test(item.transcriptExcerpt || "");
    transcriptSummary.textContent = pseudoTranscript ? "线索" : "摘录";
    const detailBits = [
      publicVideoCopy(item.quoteCandidate) ? `原句：${cleanFrontendCopy(publicVideoCopy(item.quoteCandidate), "", 120)}` : "",
      publicVideoCopy(item.avoidWriting) ? `避开：${String(cleanFrontendCopy(publicVideoCopy(item.avoidWriting), "", 90)).replace(/^不要(写成|只说)?/, "").trim()}` : "",
    ].filter(Boolean).join("\n");
    const detailBody = document.createElement("p");
    detailBody.textContent = detailBits;
    detailBody.classList.toggle("hidden", !detailBits);
    const transcriptBody = document.createElement("p");
    transcriptBody.textContent = cleanFrontendCopy(item.transcriptExcerpt || "", item.transcriptExcerpt || "", 280);
    transcriptBody.classList.toggle("hidden", pseudoTranscript || !item.transcriptExcerpt);
    transcript.append(transcriptSummary, detailBody, transcriptBody);
    content.append(top, summaryText, valueText, writeButton, transcript);
    row.append(mediaWrap, content);
    nodes.timelineList.appendChild(row);
  });
}

function renderDemoDeck(summary = {}) {
  const deck = summary.demoDeck || {};
  const slides = Array.isArray(deck.slides) ? deck.slides.slice(0, 6) : [];
  const evidence = deck.evidenceStatus || {};
  const backendQuality = deck.demoDeckQuality || {};
  const blockedByMaterial = demoDeckBlockedByMaterial(summary);
  const quality = {
    ...assessDeckQuality(slides),
    ...backendQuality,
  };
  const frameCount = Number(evidence.uniqueScreenshots || evidence.screenshotSlides || 0) || 0;
  nodes.demoDeckSection?.classList.toggle("hidden", blockedByMaterial || !slides.length);
  nodes.generateDeck?.classList.toggle("hidden", blockedByMaterial || !slides.length);
  if (nodes.demoDeckList) {
    nodes.demoDeckList.innerHTML = "";
    nodes.demoDeckList.classList.add("hidden");
  }
  if (blockedByMaterial) {
    nodes.demoDeckMeta.textContent = "没拿到字幕，暂不生成。";
    renderDemoDeckQuality(null, []);
    return;
  }
  const missingFrameCount = Number(evidence.missingImages || 0)
    || slides.filter((slide) => (slide.frameKind || (slide.frameUrl ? "screenshot" : "none")) === "none").length;
  const strongSlideCount = Number(quality.strongSlideCount || 0) || 0;
  const qualityText = strongSlideCount ? ` · ${strongSlideCount} 页可用` : "";
  nodes.demoDeckMeta.textContent = slides.length
    ? `${slides.length} 页${frameCount ? ` · ${frameCount} 张截图` : ""}${missingFrameCount ? ` · ${missingFrameCount} 页无图` : ""}${qualityText}`
    : "先把能讲的一页拎出来。";
  if (!slides.length) {
    renderDemoDeckQuality(null, slides);
    return;
  }
  renderDemoDeckList(slides);
  renderDemoDeckQuality(quality, slides);
}

function demoDeckBlockedByMaterial(summary = {}) {
  const transcriptQuality = summary.transcriptQuality || {};
  const acceptance = summary.materialAcceptance || {};
  const deck = summary.demoDeck || {};
  const quality = deck.demoDeckQuality || {};
  const text = [
    transcriptQuality.label,
    transcriptQuality.fallback,
    acceptance.status,
    acceptance.label,
    acceptance.summary,
    quality.status,
    quality.label,
    ...(Array.isArray(quality.issues) ? quality.issues : []),
  ].filter(Boolean).join(" ");
  return transcriptQuality.usable === false || /缺字幕|无字幕|字幕弱|missing transcript|no transcript/i.test(text);
}

function renderDemoDeckQuality(quality, slides = []) {
  if (!nodes.demoDeckQuality) return;
  nodes.demoDeckQuality.innerHTML = "";
  nodes.demoDeckQuality.classList.add("hidden");
}

function inferDeckProductDimension(slide = {}) {
  const role = String(slide.role || "");
  const title = String(slide.title || "");
  const text = `${role} ${title} ${slide.productQuestion || ""} ${slide.productAnswer || ""}`;
  if (/入口|目标|场景|是什么|排的是|先讲清/.test(text)) return "产品是什么";
  if (/准备|简历|声音源|音频|上传|配置|设备|分工|流程|步骤/.test(text)) return "核心流程";
  if (/失败|连接|地址|证书|防火墙|权限|服务|门槛|排错|卡/.test(text)) return "失败门槛";
  if (/验收|跑通|结果|转写|识别|输出|消息/.test(text)) return "跑通证据";
  if (/谁|用户|适合|不适合/.test(text)) return "谁会用";
  return "";
}

function renderDemoDeckList(slides = []) {
  if (!nodes.demoDeckList) return;
  nodes.demoDeckList.innerHTML = "";
  if (!Array.isArray(slides) || !slides.length) {
    nodes.demoDeckList.classList.add("hidden");
    return;
  }
  slides.forEach((slide, index) => {
    const card = document.createElement("article");
    card.className = "demo-card";
    const frameKind = slide.frameKind || (slide.frameUrl ? "screenshot" : "none");
    const emptyLabel = frameKind === "cover" ? "封面" : "无截图";

    const media = document.createElement(slide.watchAtUrl ? "a" : "div");
    media.className = "demo-card-media";
    if (slide.watchAtUrl) {
      media.href = slide.watchAtUrl;
      media.target = "_blank";
      media.rel = "noreferrer";
      media.title = `从 ${slide.timeLabel || "00:00"} 回看`;
    }
    if (slide.frameUrl) {
      const image = document.createElement("img");
      image.src = slide.frameUrl;
      image.alt = cleanDeckTitle(slide.title, index) || "视频截图";
      image.addEventListener("error", () => {
        image.remove();
        if (!media.querySelector(".demo-card-empty")) {
          const empty = document.createElement("div");
          empty.className = "demo-card-empty";
          empty.textContent = emptyLabel;
          media.prepend(empty);
        }
      });
      media.appendChild(image);
    } else {
      const empty = document.createElement("div");
      empty.className = "demo-card-empty";
      empty.textContent = emptyLabel;
      media.appendChild(empty);
    }
    const time = document.createElement("span");
    time.className = "demo-card-time";
    time.textContent = slide.timeLabel || "00:00";
    media.appendChild(time);

    const body = document.createElement("div");
    body.className = "demo-card-body";

    const meta = document.createElement("div");
    meta.className = "demo-card-meta";
    meta.innerHTML = `
      <span>第 ${escapeHtml(String(slide.index || index + 1))} 页</span>
    `;

    const title = document.createElement("h4");
    title.textContent = cleanDeckTitle(slide.title, index);

    const mainLine = firstDeckLine(
      slide,
      ["speakerNote", "talkTrack", "productAnswer", "audienceTakeaway", "meaning", "action", "evidence", "proof"],
      "看这一页发生了什么。",
      76,
    );
    const detailLine = firstDeckLine(
      slide,
      ["action", "evidence", "proof", "sourceQuote", "transcriptExcerpt"],
      "",
      92,
    );
    const sourceLine = firstDeckLine(slide, ["sourceQuote", "transcriptExcerpt"], "", 88);
    const product = document.createElement("p");
    product.className = "demo-card-product";
    product.textContent = mainLine;
    product.classList.toggle("hidden", !product.textContent);
    const action = document.createElement("p");
    action.className = "demo-card-line";
    action.textContent = detailLine && comparisonKey(detailLine) !== comparisonKey(mainLine) ? detailLine : "";
    action.classList.toggle("hidden", !action.textContent);
    const details = document.createElement("details");
    details.className = "demo-card-details";
    details.innerHTML = `
      <summary>原句</summary>
      <p>${escapeHtml(sourceLine || detailLine || mainLine)}</p>
    `;
    details.classList.toggle("hidden", !sourceLine && !detailLine);

    body.append(meta, title, product, action, details);

    card.append(media, body);
    nodes.demoDeckList.appendChild(card);
  });
  nodes.demoDeckList.classList.remove("hidden");
}

function showDraftStatus(text, kind = "") {
  nodes.draftStatus.classList.remove("hidden");
  nodes.draftStatus.textContent = text;
  nodes.draftStatus.dataset.kind = kind;
}

function hideDraftStatus() {
  nodes.draftStatus.classList.add("hidden");
  nodes.draftStatus.textContent = "";
  nodes.draftStatus.dataset.kind = "";
}

function setDraftHint(text = "") {
  if (!nodes.draftHint) return;
  nodes.draftHint.textContent = text;
  nodes.draftHint.classList.toggle("hidden", !text);
}

function currentVideoBrief() {
  const brief = nodes.briefView.textContent || "";
  return brief.includes("完成后") || brief.includes("暂无") ? "" : brief.trim();
}

function currentDraftText() {
  return nodes.draftEditor.value.trim();
}

function deckPitchFromSlides(slides = [], headline = "") {
  const backendSpine = state.currentSummary?.demoDeck?.deckSpine;
  if (backendSpine) return backendSpine;
  const titles = slides.map((slide) => slide.title).filter(Boolean);
  if (!titles.length) return "";
  if (/Offer IN|面试|互联|连接/.test(headline) || titles.some((title) => /证书|防火墙|转写|音频/.test(title))) {
    return "先说观众会卡在哪里，再给准备条件，接着拆排错动作，最后用结果验收。";
  }
  if (titles.some((title) => /问题|证据|结论|代价/.test(title))) {
    return "先说问题，再给证据和代价，最后收成一个判断。";
  }
  return `这一版按 ${titles.slice(0, 4).join("，")} 往下走。`;
}

function renderDraftPitch(slides = [], headline = "") {
  if (!nodes.draftPitch) return;
  nodes.draftPitch.classList.add("hidden");
  nodes.draftPitch.textContent = "";
}

function renderDraftPreview(slides = []) {
  const nextSlides = Array.isArray(slides) ? slides : [];
  renderDeckFocus(nextSlides);
  renderDeckPreview(nextSlides);
  if (!nodes.draftPreview) return;
  nodes.draftPreview.innerHTML = "";
  nodes.draftPreview.classList.toggle("hidden", !nextSlides.length);
}

function normalizeDeckSlideIndex(slides = []) {
  if (!slides.length) {
    state.activeDeckSlideIndex = 0;
    return 0;
  }
  if (typeof state.activeDeckSlideIndex !== "number" || Number.isNaN(state.activeDeckSlideIndex)) {
    state.activeDeckSlideIndex = 0;
  }
  state.activeDeckSlideIndex = Math.min(Math.max(state.activeDeckSlideIndex, 0), slides.length - 1);
  return state.activeDeckSlideIndex;
}

function renderDeckFocus(slides = []) {
  if (!nodes.deckFocus || !nodes.deckWorkspace) return;
  nodes.deckFocus.innerHTML = "";
  if (!Array.isArray(slides) || !slides.length) {
    nodes.deckWorkspace.classList.add("hidden");
    nodes.deckFocus.classList.add("hidden");
    return;
  }
  const index = normalizeDeckSlideIndex(slides);
  const slide = slides[index];
  const frameKind = slide.frameKind || (slide.frameUrl ? "screenshot" : "none");
  state.editingDeckSlideIndex = index;
  nodes.deckWorkspace.classList.remove("hidden");
  nodes.deckFocus.classList.remove("hidden");

  const shell = document.createElement("article");
  shell.className = "deck-focus-shell";

  const media = document.createElement(slide.watchAtUrl ? "a" : "div");
  media.className = "deck-focus-media";
  if (slide.watchAtUrl) {
    media.href = slide.watchAtUrl;
    media.target = "_blank";
    media.rel = "noreferrer";
    media.title = `从 ${slide.timeLabel || "00:00"} 回看`;
  }
  if (slide.frameUrl) {
    const image = document.createElement("img");
    image.src = slide.frameUrl;
    image.alt = slide.title || "视频截图";
    media.appendChild(image);
  } else {
    const empty = document.createElement("div");
    empty.className = "deck-focus-empty";
    empty.textContent = "暂无截图";
    media.appendChild(empty);
  }
  const mediaMeta = document.createElement("div");
  mediaMeta.className = "deck-focus-media-meta";
  mediaMeta.innerHTML = `
    <span>${escapeHtml(`第 ${slide.index || index + 1} 页`)}</span>
    <strong>${escapeHtml(slide.timeLabel || "00:00")}</strong>
    <em>${escapeHtml(frameKind === "screenshot" ? "截图" : frameKind === "cover" ? "封面" : "无图")}</em>
  `;
  media.appendChild(mediaMeta);

  const content = document.createElement("div");
  content.className = "deck-focus-content";
  const meta = document.createElement("div");
  meta.className = "deck-focus-meta";
  meta.innerHTML = `<span>${escapeHtml(slide.timeLabel || "00:00")}</span><span>${escapeHtml(shortSlideRole(slide.role))}</span>`;
  const title = document.createElement("h4");
  title.className = "deck-focus-title";
  title.textContent = cleanDeckTitle(slide.title, index);
  const lead = document.createElement("p");
  lead.className = "deck-focus-lead";
  lead.textContent = cleanFrontendCopy(slide.talkTrack || slide.speakerNote || "", "", 140);
  lead.classList.toggle("hidden", !lead.textContent);

  const facts = document.createElement("div");
  facts.className = "deck-focus-facts";
  const proof = document.createElement("section");
  proof.className = "deck-focus-fact";
  const proofText = document.createElement("p");
  proofText.className = "deck-focus-proof";
  const visibleAction = cleanFrontendCopy(slide.evidence || slide.action || slide.proof || "", "看这一页发生了什么。", 180);
  proofText.textContent = visibleAction;
  proof.appendChild(proofText);
  const keep = document.createElement("section");
  keep.className = "deck-focus-fact";
  const keepText = document.createElement("p");
  keepText.className = "deck-focus-meaning";
  const visibleMeaning = cleanFrontendCopy(slide.audienceTakeaway || slide.meaning || slide.proof || slide.keepReason || "", "", 180);
  keepText.textContent = visibleMeaning;
  keep.appendChild(keepText);
  if (visibleMeaning && normalizeUiSentence(visibleAction, 200) !== normalizeUiSentence(visibleMeaning, 200)) {
    facts.append(proof, keep);
  } else {
    facts.append(proof);
  }

  const editor = document.createElement("form");
  editor.className = "deck-focus-editor";
  editor.innerHTML = `
    <div class="deck-editor-head">
      <strong>改当前页</strong>
      <span>第 ${escapeHtml(String(slide.index || index + 1))} 页</span>
    </div>
    <label>标题<input name="title" value="${escapeHtml(slide.title || "")}"></label>
    <label>发生了什么<textarea name="proof" rows="3">${escapeHtml(slide.proof || slide.action || slide.evidence || "")}</textarea></label>
    <label>讲给观众听<textarea name="talkTrack" rows="3">${escapeHtml(slide.talkTrack || slide.speakerNote || "")}</textarea></label>
    <div class="deck-focus-editor-actions">
      <button class="primary" type="submit">保存这页</button>
      <button type="button" data-reset>还原</button>
    </div>
  `;
  editor.addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(editor);
    const nextSlides = currentDeckSlides().map((item, itemIndex) => {
      if (itemIndex !== index) return item;
      const titleValue = compact(form.get("title"), 80) || item.title;
      const proofValue = compact(form.get("proof"), 220) || item.proof || item.action || item.evidence;
      const talkValue = compact(form.get("talkTrack"), 180) || item.talkTrack || item.speakerNote;
      return {
        ...item,
        title: titleValue,
        proof: proofValue,
        talkTrack: talkValue,
        slideBody: compact(`${proofValue} ${talkValue} ${item.audienceTakeaway || item.meaning || ""}`, 220),
      };
    });
    setCurrentDraftSlides(nextSlides, { status: `第 ${index + 1} 页已保存。` });
  });
  editor.querySelector("[data-reset]")?.addEventListener("click", () => {
    renderDeckFocus(currentDeckSlides());
  });
  content.append(meta, title, lead, facts, editor);

  shell.append(media, content);
  nodes.deckFocus.appendChild(shell);
}

function renderDeckPreview(slides = []) {
  if (!nodes.deckPreview || !nodes.deckWorkspace) return;
  nodes.deckPreview.innerHTML = "";
  if (!Array.isArray(slides) || !slides.length) {
    nodes.deckWorkspace.classList.add("hidden");
    nodes.deckPreview.classList.add("hidden");
    return;
  }
  nodes.deckWorkspace.classList.remove("hidden");
  const activeIndex = normalizeDeckSlideIndex(slides);
  slides.slice(0, 8).forEach((slide) => {
    const slideIndex = (slide.index || 1) - 1;
    const card = document.createElement("button");
    card.type = "button";
    card.className = slideIndex === activeIndex ? "deck-slide-preview active" : "deck-slide-preview";
    card.dataset.slideIndex = String(slideIndex);
    card.addEventListener("click", () => {
      state.activeDeckSlideIndex = slideIndex;
      state.editingDeckSlideIndex = slideIndex;
      renderDeckFocus(slides);
      renderDeckPreview(slides);
    });
    const thumb = document.createElement("div");
    thumb.className = "deck-slide-thumb";
    if (slide.frameUrl) {
      const image = document.createElement("img");
      image.src = slide.frameUrl;
      image.alt = slide.title || "视频截图";
      thumb.appendChild(image);
    } else {
      const empty = document.createElement("div");
      empty.className = "deck-slide-thumb-empty";
      empty.textContent = "暂无截图";
      thumb.appendChild(empty);
    }
    const time = document.createElement("span");
    time.className = "deck-slide-time";
    time.textContent = slide.timeLabel || "00:00";
    thumb.appendChild(time);

    const index = document.createElement("span");
    index.className = "deck-slide-number";
    index.textContent = `第 ${slide.index || ""} 页`;
    const body = document.createElement("div");
    body.className = "deck-slide-body";
    const title = document.createElement("strong");
    title.textContent = slide.title || "这一页讲什么";
    const summary = document.createElement("span");
    summary.className = "deck-slide-summary";
    summary.textContent = slide.audienceTakeaway || slide.talkTrack || slide.speakerNote || slide.proof || "";
    card.title = slide.audienceTakeaway || slide.talkTrack || slide.speakerNote || slide.proof || slide.action || slide.title || "这一页";
    body.append(index, title, summary);
    card.append(thumb, body);
    nodes.deckPreview.appendChild(card);
  });
  nodes.deckPreview.classList.remove("hidden");
}

function draftHeadline() {
  return state.latestDraft?.headline
    || state.currentSummary?.demoDeck?.headline
    || nodes.resultTitle.textContent.trim()
    || "视频拆解";
}

function draftSourceStatus() {
  const value = state.latestDraft?.sourceStatus
    || state.currentSummary?.demoDeck?.sourceStatus
    || playbackSourceText(state.currentSummary || {});
  return compactSourceStatus(value, state.currentSummary || {});
}

function setCurrentDraftSlides(slides = [], { status = "已更新。" } = {}) {
  const nextSlides = slides.map((slide, index) => ({ ...slide, index: index + 1 }));
  const headline = draftHeadline();
  const source = draftSourceStatus();
  const text = deckMarkdownFromSlides(nextSlides, headline, source);
  state.latestDraft = {
    ...(state.latestDraft || {}),
    engine: state.latestDraft?.engine || "demoDeckEdit",
    model: state.latestDraft?.model || "local",
    headline,
    sourceStatus: source,
    slides: nextSlides,
    demoDeckQuality: assessDeckQuality(nextSlides),
  };
  nodes.draftEditor.value = text;
  setDraftHint("");
  renderDraftPitch(nextSlides, headline);
  renderDraftPreview(nextSlides);
  applyDeckQualityStatus(nextSlides, state.latestDraft.demoDeckQuality, "讲稿");
  saveDraftLocal({ silent: true });
  if (status) showDraftStatus(status, "ready");
}

function assessDeckQuality(slides = []) {
  const issues = [];
  const strengths = [];
  const slideChecks = [];
  if (!Array.isArray(slides) || slides.length < 3) issues.push("页数太少");
  const titles = slides.map((slide) => (slide.title || "").trim()).filter(Boolean);
  const roles = slides.map((slide) => (slide.role || "").trim()).filter(Boolean);
  const uniqueTitles = new Set(titles);
  const uniqueRoles = new Set(roles);
  if (uniqueTitles.size < titles.length) issues.push("标题重复");
  if (uniqueRoles.size < Math.min(4, slides.length)) issues.push("页面职责太像");
  const frameUrls = slides.map((slide) => slide.frameUrl || "").filter(Boolean);
  const uniqueFrames = new Set(frameUrls);
  if (!frameUrls.length) issues.push("没有截图或封面");
  if (frameUrls.length && uniqueFrames.size < Math.min(3, frameUrls.length)) issues.push("截图重复偏多");
  let strongSlideCount = 0;
  slides.forEach((slide, index) => {
    const action = (slide.action || slide.evidence || "").trim();
    const meaning = (slide.meaning || slide.proof || slide.audienceTakeaway || "").trim();
    const speaker = (slide.speakerNote || slide.talkTrack || "").trim();
    const sourceQuote = (slide.sourceQuote || slide.sourceEvidence || "").trim();
    const productQuestion = (slide.productQuestion || "").trim();
    const productAnswer = (slide.productAnswer || "").trim();
    const valueSource = [slide.title || "", slide.role || "", meaning, slide.proof || "", slide.audienceTakeaway || "", slide.keepReason || ""].join(" ");
    const checkIssues = [];
    if (!(slide.frameUrl || slide.frameKind === "cover")) checkIssues.push("缺画面");
    if (action.length < 18) checkIssues.push("缺动作");
    if (meaning.length < 18) checkIssues.push("缺意义");
    if (speaker.length < 10) checkIssues.push("缺讲法");
    if ((slide.evidenceMode || "") !== "visual-only" && sourceQuote.length < 16) checkIssues.push("缺原始证据");
    if ((slide.templateKey === "tutorial" || slide.templateKey === "demo" || slide.templateKey === "review")
      && (productQuestion.length < 6 || productAnswer.length < 16)) checkIssues.push("缺产品判断");
    if (!/(为什么|值钱|值得|关键|门槛|卡住|风险|代价|成本|结果|验收|判断|选择|适合|不适合|证明|说明|避免|排查|复现|回看|能不能|该不该|别把|不要只|不是.+而是|为.+做|核心理念|经验|服务谁|谁会用|替代方案|选择标准|连接失败|连不上|跑通|防火墙|证书|音频源|声音源|适合谁|不适合)/.test(`${valueSource} ${sourceQuote}`)) {
      checkIssues.push("缺可写价值");
    }
    if (!checkIssues.length) strongSlideCount += 1;
    slideChecks.push({
      index: slide.index || index + 1,
      title: slide.title || `第 ${index + 1} 页`,
      ok: !checkIssues.length,
      issues: checkIssues,
    });
  });
  if (slideChecks.some((item) => item.issues.includes("缺动作"))) issues.push("有的页没有把发生的动作说清");
  if (slideChecks.some((item) => item.issues.includes("缺意义"))) issues.push("有的页没有说明为什么值得留下");
    if (slideChecks.some((item) => item.issues.includes("缺讲法"))) issues.push("有的页缺少可直接讲的一句话");
    if (slideChecks.some((item) => item.issues.includes("缺原始证据"))) issues.push("有的页缺少原字幕或画面证据");
  if (slideChecks.some((item) => item.issues.includes("缺产品判断"))) issues.push("有的页没有回答产品问题");
  if (slideChecks.some((item) => item.issues.includes("缺可写价值"))) issues.push("有的页没有说明这段材料能写出什么判断");
  if (slides.filter((slide) => /这页证明|保留它|观众带走|这一页先|可以写|适合写/.test(
    [slide.proof, slide.talkTrack, slide.audienceTakeaway, slide.keepReason].filter(Boolean).join(" "),
  )).length >= 2) issues.push("讲法有模板味");
  if (uniqueRoles.size) strengths.push(`${uniqueRoles.size} 个角色`);
  if (uniqueFrames.size) strengths.push(`${uniqueFrames.size} 张图`);
  if (strongSlideCount) strengths.push(`${strongSlideCount} 页可讲`);
  return {
    status: issues.length ? "needs_work" : "ready",
    label: issues.length ? "需补证据" : "可用",
    issues: issues.slice(0, 3),
    strengths: strengths.slice(0, 2),
    nextBestUse: issues.length
      ? "先补材料，再生成讲稿。"
      : uniqueFrames.size
        ? "这组卡片可以继续整理。"
        : "先整理文字，再补画面。",
    slideChecks,
    strongSlideCount,
    score: Math.round((strongSlideCount / Math.max(1, slides.length)) * 100) / 100,
  };
}

function applyDeckQualityStatus(slides = [], backendQuality = null, prefix = "讲稿") {
  const quality = backendQuality && typeof backendQuality === "object" ? backendQuality : assessDeckQuality(slides);
  const issues = Array.isArray(quality.issues)
    ? quality.issues.map(formatDeckIssue).filter(Boolean)
    : [];
  if (quality.status === "ready" || !issues.length) {
    const frameCount = new Set(slides.map((slide) => slide.frameUrl).filter(Boolean)).size;
    const bits = [`${slides.length} 页`];
    if (frameCount) bits.push(`${frameCount} 图`);
    const nextBestUse = compact(quality.nextBestUse || "", 50);
    showDraftStatus(`可用 · ${bits.join(" · ")}`, "ready");
    nodes.draftStatus.title = nextBestUse;
    return quality;
  }
  showDraftStatus(`需补 · ${issues.length} 项`, "warn");
  nodes.draftStatus.title = issues.join("；");
  return quality;
}

function formatDeckIssue(value = "") {
  const text = compact(String(value || "").trim(), 80);
  if (!text) return "";
  return text
    .replace(/^有页面讲法太短.*$/, "有的页还差一句能直接讲的话")
    .replace(/^画面证明太短.*$/, "有的页证据还不够")
    .replace(/^截图重复偏多.*$/, "截图还不够散")
    .replace(/^标题重复.*$/, "几页标题太像")
    .replace(/^页面职责太像.*$/, "几页在说同一件事")
    .replace(/^没有截图或封面.*$/, "还缺图")
    .replace(/^页数太少.*$/, "页数还少")
    .replace(/^讲法有模板味.*$/, "讲法有点像模板")
    .replace(/^有的页没有回答产品问题.*$/, "有的页还没说清适合谁")
    .replace(/^有的页没有说明这段材料能写出什么判断.*$/, "有的页还没说清为什么留下");
}

function setDraftText(text, result = null) {
  nodes.draftPanel?.classList.remove("hidden");
  nodes.draftMarkdownDetails?.classList.remove("hidden");
  if (nodes.draftMarkdownDetails) nodes.draftMarkdownDetails.open = false;
  nodes.draftEditor.classList.remove("hidden");
  nodes.draftActions.classList.remove("hidden");
  nodes.draftEditor.value = text || "";
  state.latestDraft = result || state.latestDraft;
  const slides = Array.isArray(result?.slides)
    ? result.slides
    : Array.isArray(state.currentSummary?.demoDeck?.slides)
      ? state.currentSummary.demoDeck.slides
      : [];
  setDraftHint("");
  renderDraftPitch(slides, draftHeadline());
  renderDraftPreview(slides);
  updateGenerateDeckButton();
  return applyDeckQualityStatus(slides, result?.demoDeckQuality || result?.qualityGate || state.currentSummary?.demoDeck?.demoDeckQuality, "讲稿");
}

function deckMarkdownFromSlides(slides = [], headline = "视频拆解", source = "") {
  const lines = [`# ${headline}`, ""];
  if (source) lines.push(`> ${source}`);
  lines.push("> 每页一张画面，一句能讲的话。", "");
  slides.forEach((slide) => {
    const title = cleanDeckTitle(slide.title, Number(slide.index || 1) - 1);
    const action = cleanFrontendCopy(slide.action || slide.proof || slide.evidence || "", "", 220);
    const meaning = cleanFrontendCopy(slide.audienceTakeaway || slide.meaning || slide.keepReason || slide.proof || "", "", 220);
    const talk = cleanFrontendCopy(slide.talkTrack || slide.speakerNote || slide.audienceTakeaway || "", "", 180);
    lines.push("---", "", `## 第 ${slide.index || ""} 页｜${title || "这一页"}`, "");
    lines.push(`时间：${slide.timeLabel || "00:00"}`);
    if (slide.role) lines.push(`位置：${slide.role}`);
    if (slide.frameUrl) lines.push("", `![${title || "视频截图"}](${slide.frameUrl})`);
    if (slide.watchAtUrl) lines.push("", `[回看这一段](${slide.watchAtUrl})`);
    lines.push("");
    if (action) lines.push(`- 画面：${action}`);
    if (meaning) lines.push(`- 这页留下：${meaning}`);
    if (talk) lines.push(`- 讲法：${talk}`);
    lines.push("");
  });
  return `${lines.join("\n").trim()}\n`;
}

function fallbackDeckMarkdown() {
  const title = nodes.resultTitle.textContent.trim() || "视频拆解";
  const summary = state.currentSummary || {};
  const deck = summary.demoDeck || {};
  if (deck.deckMarkdown) return deck.deckMarkdown;
  const slides = Array.isArray(deck.slides) ? deck.slides : [];
  if (!slides.length) return `# ${title}\n\n> 还没有可用画面。\n`;
  return deckMarkdownFromSlides(slides, deck.headline || title, compactSourceStatus(deck.sourceStatus, summary));
}

function saveDraftLocal({ silent = false } = {}) {
  const title = nodes.resultTitle.textContent.trim() || "未命名稿件";
  const body = currentDraftText();
  if (!body) {
    if (!silent) showDraftStatus("还没有讲稿。", "error");
    return;
  }
  const saved = {
    title,
    body,
    slides: state.latestDraft?.slides || [],
    headline: state.latestDraft?.headline || draftHeadline(),
    sourceStatus: state.latestDraft?.sourceStatus || draftSourceStatus(),
    deckVersion: Number(state.currentSummary?.demoDeckVersion || 0) || 0,
    summaryVersion: Number(state.currentSummary?.videoSummaryVersion || 0) || 0,
    savedAt: new Date().toISOString(),
    jobId: state.currentJobId,
  };
  state.savedDraft = saved;
  state.savedDraftAvailable = Boolean(body.trim());
  updateGenerateDeckButton();
  window.localStorage.setItem(draftCacheKey(), JSON.stringify(saved));
  if (!silent) showDraftStatus("已保存。", "ready");
}

function shouldDiscardSavedDraft(saved = {}) {
  const currentDeckVersion = Number(state.currentSummary?.demoDeckVersion || 0) || 0;
  if (!currentDeckVersion) return false;
  const savedDeckVersion = Number(saved.deckVersion || 0) || 0;
  if (!Array.isArray(saved.slides) || !saved.slides.length) return false;
  if (!savedDeckVersion && currentDeckVersion >= 23) return true;
  return savedDeckVersion > 0 && savedDeckVersion < currentDeckVersion;
}

function loadSavedDraft(jobId) {
  const raw = window.localStorage.getItem(draftCacheKey(jobId));
  if (!raw) {
    resetDraftSurface();
    return;
  }
  try {
    const saved = JSON.parse(raw);
    if (shouldDiscardSavedDraft(saved)) {
      window.localStorage.removeItem(draftCacheKey(jobId));
      resetDraftSurface();
      return;
    }
    resetDraftSurface({ preserveSavedDraft: true });
    if (saved.body) {
      state.savedDraft = saved;
      state.savedDraftAvailable = true;
      updateGenerateDeckButton();
      return;
    }
    resetDraftSurface();
  } catch {
    window.localStorage.removeItem(draftCacheKey(jobId));
    resetDraftSurface();
  }
}

function collectDraftIssues(result = {}) {
  const gate = result.qualityGate || {};
  const surface = result.surfaceAudit || {};
  const issues = [];
  (gate.reasons || []).forEach((reason) => issues.push(String(reason)));
  (surface.findings || [])
    .filter((item) => item && item.kind !== "pass")
    .slice(0, 3)
    .forEach((item) => {
      const label = item.label || item.kind || "快审";
      const detail = item.text || item.message || item.detail || "";
      issues.push(detail ? `${label}：${detail}` : label);
    });
  return [...new Set(issues.map((item) => compact(item, 120)).filter(Boolean))].slice(0, 4);
}

function renderDraftGate(result = {}) {
  const gate = result.qualityGate || {};
  const issues = collectDraftIssues(result);
  if (!issues.length) {
    nodes.draftGate.classList.add("hidden");
    nodes.draftGateList.innerHTML = "";
    nodes.draftGateLabel.textContent = "";
    nodes.draftEngineLabel.textContent = "";
    return;
  }
  nodes.draftGate.classList.remove("hidden");
  nodes.draftGateLabel.textContent = gate.status === "allow" ? "可用" : gate.status === "block" ? "需改" : "草稿";
  nodes.draftEngineLabel.textContent = [result.engine, result.model, result.thinking && result.thinking !== "disabled" ? "thinking" : ""].filter(Boolean).join(" · ");
  nodes.draftGateList.innerHTML = "";
  issues.forEach((issue) => {
    const item = document.createElement("li");
    item.textContent = issue;
    nodes.draftGateList.appendChild(item);
  });
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function failureDiagnosis(job = {}) {
  const raw = `${job.message || ""} ${job.error || ""}`;
  const needsLoginFromRaw = /not a bot|Sign in to confirm|cookies-from-browser|需要登录|登录|bot/i.test(raw);
  const platform = job.summary?.platform || job.platform || platformFromUrl(job.url);
  const chromeAlreadyUsed = String(job.cookiesFromBrowser || "").toLowerCase() === "chrome";
  if (job.failure && typeof job.failure === "object") {
    const needsLogin = needsLoginFromRaw;
    const noFormat = /Requested format is not available|No video formats|format is not available/i.test(raw);
    if (job.failure.kind === "download_required" && (needsLogin || noFormat)) {
      const backendActions = Array.isArray(job.failure.nextActions) ? job.failure.nextActions.filter(Boolean).slice(0, 4) : [];
      return {
        title: job.failure.title || (needsLogin ? "平台要求登录验证" : "没有可下载格式"),
        reason: job.failure.reason || friendlyJobMessage(job) || "没有拿到本地视频文件，所以不继续生成总结和拆解。",
        kind: job.failure.kind,
        needsLogin,
        platform,
        chromeAlreadyUsed,
        canRetry: job.failure.canRetry !== false,
        nextActions: backendActions.length
          ? backendActions
          : needsLogin
            ? ["先在浏览器登录平台", "用 Chrome 登录态重跑", "换一个公开视频"]
            : ["重跑这个链接", "换一个公开可播放的视频", "确认视频能正常播放"],
      };
    }
    return {
      title: job.failure.title || "处理失败",
      reason: job.failure.reason || friendlyJobMessage(job) || "这个任务没有成功完成。",
      kind: job.failure.kind || "unknown",
      needsLogin: needsLoginFromRaw,
      platform,
      chromeAlreadyUsed,
      canRetry: job.failure.canRetry !== false,
      nextActions: Array.isArray(job.failure.nextActions) ? job.failure.nextActions.filter(Boolean).slice(0, 4) : [],
    };
  }
  if (/超过 \d+ 秒|timeout|timed out|停止等待/i.test(raw)) {
    return {
      title: chromeAlreadyUsed ? "保存视频超时" : "下载超时",
      reason: chromeAlreadyUsed ? "已经尝试使用浏览器登录状态，但等待时间用完了。" : "等待时间用完了，任务已停止。",
      kind: "timeout",
      canRetry: true,
      nextActions: chromeAlreadyUsed
        ? ["重跑一次", "换一个更短的视频验证链路", "换网络后重试", "改用本地视频上传"]
        : ["重跑一次", "换一个更短或更稳定的视频", "确认网络和平台访问正常"],
    };
  }
  if (/视频下载失败|没有本地视频文件|没有保存到本地|video-download|yt-dlp-video-download-failed/i.test(raw)) {
    const needsLogin = /not a bot|Sign in to confirm|cookies-from-browser|需要登录|登录|bot/i.test(raw);
    const noFormat = /Requested format is not available|No video formats|format is not available/i.test(raw);
    return {
      title: needsLogin ? "平台要求登录验证" : noFormat ? "没有可下载格式" : "没有下载到本地视频",
      reason: friendlyJobMessage(job) || "没有拿到本地视频文件，所以不继续生成总结和拆解。",
      kind: "download_required",
      needsLogin,
      platform,
      chromeAlreadyUsed,
      canRetry: true,
      nextActions: needsLogin
        ? ["先在浏览器登录平台", "用 Chrome 登录态重跑", "换一个公开视频"]
        : ["重跑这个链接", "换一个公开可播放的视频", "确认视频能正常播放"],
    };
  }
  if (job.status === "error") {
    return {
      title: "处理失败",
      reason: friendlyJobMessage(job) || "这个任务没有成功完成。",
      kind: "unknown",
      needsLogin: needsLoginFromRaw,
      platform,
      chromeAlreadyUsed,
      canRetry: true,
      nextActions: ["重跑一次", "换一个 YouTube 或 B站链接"],
    };
  }
  return null;
}

function isDownloadRequiredFailure(job = {}) {
  const diagnosis = failureDiagnosis(job);
  if (diagnosis?.kind === "download_required") return true;
  const raw = `${job.message || ""} ${job.error || ""}`;
  return job.status === "error" && /视频下载失败|没有本地视频文件|video-download|yt-dlp-video-download-failed/i.test(raw);
}

function renderJobFailure(job = {}) {
  state.currentSummary = {};
  const diagnosis = failureDiagnosis(job) || {
    title: "处理失败",
    reason: friendlyJobMessage(job) || "这个任务没有成功完成。",
    canRetry: true,
    nextActions: ["重跑一次", "换一个 YouTube 或 B站链接"],
  };
  const actions = diagnosis.nextActions?.length
    ? `<ul>${diagnosis.nextActions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "";
  const loginUrl = diagnosis.needsLogin ? platformLoginUrl(diagnosis.platform || platformFromUrl(job.url)) : "";
  const loginLabel = diagnosis.platform === "bilibili" ? "打开 B站登录" : "打开 YouTube 登录";
  const actionButtons = diagnosis.needsLogin
    ? `
      <div class="failure-actions">
        ${loginUrl ? `<button type="button" data-video-action="open-platform-login">${escapeHtml(loginLabel)}</button>` : ""}
        <button type="button" data-video-action="rerun-with-chrome">${diagnosis.chromeAlreadyUsed ? "重新读取 Chrome 登录态" : "用 Chrome 登录态重跑"}</button>
      </div>
    `
    : diagnosis.canRetry
      ? `<div class="failure-actions"><button type="button" data-video-action="rerun">重跑</button></div>`
      : "";
  nodes.jobSummary.classList.remove("hidden");
  nodes.jobSummary.classList.add("failure");
  nodes.jobSummary.innerHTML = `
    <strong>${escapeHtml(diagnosis.title)}</strong>
    <span>${escapeHtml(diagnosis.reason)}</span>
    ${actions}
    ${actionButtons}
    <small>${diagnosis.canRetry ? "可以重跑；本次没有继续分析。" : "这个链接不能继续处理。"}</small>
  `;
  nodes.quickMeta.classList.remove("hidden");
  nodes.quickMeta.innerHTML = `<span>${escapeHtml(diagnosis.title)}</span>`;
  nodes.pipelineStatus.innerHTML = "";
  nodes.pipelineStatus.classList.add("hidden");
  hideDownloadProgress();
  nodes.refetchFrames?.classList.add("hidden");
  nodes.saveMaterialPackage?.classList.add("hidden");
  nodes.videoStage?.classList.add("hidden");
  if (nodes.videoPlayer) nodes.videoPlayer.innerHTML = "";
  nodes.playbackSource?.classList.add("hidden");
  if (nodes.playbackSource) nodes.playbackSource.textContent = "";
  nodes.videoSummary?.classList.add("hidden");
  if (nodes.coreClaim) nodes.coreClaim.textContent = "";
  if (nodes.summaryBullets) nodes.summaryBullets.innerHTML = "";
  nodes.summaryBullets?.classList.add("hidden");
  nodes.summaryTakeaway?.classList.add("hidden");
  if (nodes.summaryTakeaway) nodes.summaryTakeaway.textContent = "";
  nodes.summaryMore?.classList.add("hidden");
  nodes.demoDeckSection?.classList.add("hidden");
  if (nodes.demoDeckList) nodes.demoDeckList.innerHTML = "";
  nodes.timelineSection?.classList.add("hidden");
  if (nodes.timelineList) nodes.timelineList.innerHTML = "";
  if (nodes.timelineMeta) nodes.timelineMeta.textContent = "";
  nodes.anglePanel?.classList.add("hidden");
  nodes.writeDecision?.classList.add("hidden");
  nodes.writingPack?.classList.add("hidden");
  nodes.materialsDetails?.classList.add("hidden");
  nodes.jobFiles.innerHTML = "";
  nodes.sourcePackView.textContent = "";
  nodes.reportView.textContent = "";
  nodes.briefView.textContent = "";
  nodes.transcriptView.textContent = "";
  nodes.generateDraft.disabled = true;
  nodes.generateDeck.disabled = true;
  nodes.draftPanel?.classList.add("hidden");
  setDraftHint("任务失败，不能生成。");
}

function renderDownloadRequiredError(job = {}) {
  renderJobFailure(job);
}

function latestDownloadProgress(job = {}) {
  const events = Array.isArray(job.events) ? job.events : [];
  const event = [...events].reverse().find((item) => {
    const extra = item && typeof item.extra === "object" ? item.extra : {};
    return item?.stage === "download" && extra.progressKind === "download";
  });
  if (event?.extra) return event.extra;
  if (job.progressKind === "download") return job;
  return null;
}

function activeStageStartedAt(job = {}) {
  const events = Array.isArray(job.events) ? job.events : [];
  const event = [...events].reverse().find((item) => ["download", "fetch", "transcript", "frames", "analysis"].includes(String(item?.stage || "")));
  const stamp = event?.at || job.updatedAt || job.createdAt || "";
  const time = Date.parse(stamp);
  return Number.isFinite(time) ? time : 0;
}

function hideDownloadProgress() {
  nodes.downloadProgress?.classList.add("hidden");
  if (nodes.downloadProgressBar) {
    nodes.downloadProgressBar.style.width = "0%";
    nodes.downloadProgressBar.removeAttribute("data-indeterminate");
    nodes.downloadProgressBar.parentElement?.classList.add("hidden");
  }
  if (nodes.downloadProgressLabel) nodes.downloadProgressLabel.textContent = "";
  if (nodes.downloadProgressMeta) nodes.downloadProgressMeta.textContent = "";
}

function pendingStage(job = {}, progress = null) {
  if (job.sourceType === "local") {
    if (job.status === "queued") return { step: "download", label: "等待导入", meta: "排队中" };
    const currentStage = String(job.stage || "");
    if (currentStage === "frames" || currentStage === "analysis") return { step: "frames", label: "正在截图", meta: "提取关键画面" };
    if (currentStage === "materials" || currentStage === "report") return { step: "materials", label: "正在整理", meta: "生成材料卡" };
    return { step: "download", label: "正在导入", meta: "保存本地视频" };
  }
  if (job.status === "queued") {
    return { step: "download", label: "排队中", meta: "等待开始" };
  }
  const downloadStatus = String(progress?.downloadStatus || "");
  if (downloadStatus === "finished") {
    return { step: "frames", label: "保存完成", meta: "处理中" };
  }
  const events = Array.isArray(job.events) ? job.events : [];
  const stages = events.map((item) => String(item?.stage || ""));
  if (stages.includes("frames") || stages.includes("frame") || stages.includes("analysis")) {
    return { step: "frames", label: "处理中", meta: "" };
  }
  if (stages.includes("transcript")) {
    return { step: "transcript", label: "取字幕", meta: "" };
  }
  if (job.status === "queued") return { step: "queued", label: "等待中", meta: "" };
  return { step: "download", label: "保存视频", meta: "" };
}

function renderDownloadProgress(job = {}) {
  const progress = latestDownloadProgress(job);
  const isActive = job.status === "running" || job.status === "queued";
  if (!isActive) {
    hideDownloadProgress();
    return;
  }
  nodes.downloadProgress?.classList.remove("hidden");
  const status = String(progress?.downloadStatus || "");
  const downloaded = Number(progress?.downloadedBytes || 0);
  const total = Number(progress?.totalBytes || 0);
  const percent = Number(progress?.percent || 0);
  const hasPercent = Number.isFinite(percent) && percent >= 0 && total > 0;
  const speedText = formatBytes(progress?.speedBytesPerSecond) ? `${formatBytes(progress.speedBytesPerSecond)}/s` : "";
  const etaText = formatEta(progress?.etaSeconds);
  const downloadedText = formatBytes(downloaded);
  const totalText = formatBytes(total);
  const fragmentIndex = Number(progress?.fragmentIndex || 0);
  const fragmentCount = Number(progress?.fragmentCount || 0);
  const stage = pendingStage(job, progress);
  const label = stage.label;
  const pieces = [];
  if (hasPercent) pieces.push(`${Math.round(percent)}%`);
  if (downloadedText && totalText) pieces.push(`${downloadedText} / ${totalText}`);
  else if (downloadedText) pieces.push(`已下载 ${downloadedText}`);
  if (fragmentIndex && fragmentCount) pieces.push(`分片 ${fragmentIndex}/${fragmentCount}`);
  if (speedText) pieces.push(speedText);
  if (etaText && status !== "finished") pieces.push(`剩 ${etaText}`);
  if (!pieces.length) {
    const startedAt = activeStageStartedAt(job);
    const elapsed = startedAt ? formatElapsed(Date.now() - startedAt) : "";
    if (elapsed) pieces.push(`已等待 ${elapsed}`);
  }
  nodes.downloadProgressLabel.textContent = label;
  nodes.downloadProgressMeta.textContent = pieces.join(" · ") || stage.meta || "连接中";
  if (nodes.downloadProgressBar) {
    const track = nodes.downloadProgressBar.parentElement;
    if (hasPercent) {
      nodes.downloadProgressBar.removeAttribute("data-indeterminate");
      nodes.downloadProgressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
      track?.classList.remove("hidden");
    } else {
      nodes.downloadProgressBar.removeAttribute("data-indeterminate");
      nodes.downloadProgressBar.style.width = "0%";
      track?.classList.add("hidden");
    }
  }
}

function renderJobPending(job = {}) {
  state.currentSummary = {};
  const isLocal = job.sourceType === "local";
  nodes.jobSummary.classList.add("hidden");
  nodes.jobSummary.classList.remove("failure", "pending");
  nodes.jobSummary.textContent = "";
  nodes.quickMeta.classList.add("hidden");
  nodes.quickMeta.innerHTML = "";
  nodes.pipelineStatus.classList.add("hidden");
  nodes.pipelineStatus.innerHTML = "";
  renderDownloadProgress(job);
  nodes.refetchFrames?.classList.add("hidden");
  nodes.saveMaterialPackage?.classList.add("hidden");
  nodes.videoStage?.classList.add("hidden");
  if (nodes.videoPlayer) {
    nodes.videoPlayer.innerHTML = "";
    nodes.videoPlayer.classList.remove("empty");
    nodes.videoPlayer.style.backgroundImage = "";
  }
  nodes.playbackSource?.classList.add("hidden");
  if (nodes.playbackSource) nodes.playbackSource.textContent = "";
  nodes.videoSummary?.classList.add("hidden");
  nodes.summaryMore?.classList.add("hidden");
  nodes.demoDeckSection?.classList.add("hidden");
  nodes.timelineSection?.classList.add("hidden");
  nodes.anglePanel?.classList.add("hidden");
  nodes.writeDecision?.classList.add("hidden");
  nodes.writingPack?.classList.add("hidden");
  nodes.materialsDetails?.classList.add("hidden");
  nodes.draftPanel?.classList.add("hidden");
  if (nodes.timelineList) nodes.timelineList.innerHTML = "";
  if (nodes.timelineMeta) nodes.timelineMeta.textContent = "";
  nodes.jobFiles.innerHTML = "";
  nodes.generateDraft.disabled = true;
  nodes.generateDeck.disabled = true;
  setDraftHint(isLocal ? "导入完成后可生成。" : "视频保存完成后可生成。");
}

async function waitForDraftJob(jobId) {
  let count = 0;
  while (true) {
    const job = await api(`/api/full-draft-job/${encodeURIComponent(jobId)}`);
    if (job.status === "done") {
      if (!job.result) throw new Error("写完了，但没有返回正文。");
      return job.result;
    }
    if (job.status === "error") {
      throw new Error(job.error || "写稿失败。");
    }
    count += 1;
    showDraftStatus(count > 30 ? "还在写。" : "正在写。", "running");
    await sleep(2500);
  }
}

function renderJob(job) {
  state.currentJobId = job.id;
  const summary = job.summary || {};
  const renderSummary = {
    ...summary,
    platform: summary.platform || job.platform || platformFromUrl(job.url),
    videoEmbed: summary.videoEmbed || (job.url ? { type: "link", watchUrl: job.url } : undefined),
  };
  state.currentSummary = renderSummary;
  const result = job.result || {};
  nodes.jobStatus.textContent = humanJobStatus(job);
  nodes.resultTitle.textContent = result.title || job.title || compact(job.url, 80) || "任务详情";
  nodes.jobSummary.classList.remove("failure");
  if (job.status === "error") {
    renderJobFailure(job);
    return;
  }
  if (job.status === "queued" || job.status === "running") {
    renderJobPending(job);
    return;
  }
  if (isDownloadRequiredFailure(job)) {
    renderDownloadRequiredError(job);
    return;
  }
  if (job.status === "done" && !jobHasLocalVideo({ ...job, summary: renderSummary })) {
    renderDownloadRequiredError({
      ...job,
      status: "error",
      error: "视频没有保存到本地，已停止。",
      message: "视频没有保存到本地，已停止。",
    });
    return;
  }
  nodes.videoSummary?.classList.remove("hidden");
  nodes.timelineSection?.classList.remove("hidden");
  nodes.materialsDetails?.classList.remove("hidden");
  nodes.pipelineStatus?.classList.remove("hidden");
  const shouldShowStatus = job.status === "queued" || job.status === "running" || job.status === "error";
  nodes.jobSummary.classList.toggle("hidden", !shouldShowStatus);
  nodes.jobSummary.textContent = shouldShowStatus ? friendlyJobMessage(job) : "";
  hideDownloadProgress();
  renderVideoSummary(renderSummary, result);
  renderWriteDecision(summary.editorialDecision || {});
  renderAngles(summary.angles || result.repurpose_angles || [], summary.writingCards || []);
  renderWritingPack(summary.writingPack || {});
  renderPipelineStatus({ ...job, summary: renderSummary });
  renderVideoPlayer(renderSummary);
  renderDemoDeck(renderSummary);
  renderTimeline(renderSummary);
  renderFiles(job.files || {});
  renderMeta({ ...job, summary: renderSummary, transcriptSource: renderSummary.transcriptSource });
  nodes.sourcePackView.textContent = summary.sourcePackMarkdown || "完成后显示材料。";
  nodes.reportView.textContent = job.noteMarkdown || "完成后显示报告。";
  nodes.briefView.textContent = summary.editorialDecision?.brief || "完成后显示卡片。";
  nodes.transcriptView.textContent = job.transcriptMarkdown || "完成后显示原文。";
  nodes.generateDraft.disabled = job.status !== "done";
  nodes.generateDeck.disabled = job.status !== "done";
  setDraftHint(job.status === "done" ? "" : "分析完成后可生成。");
  loadSavedDraft(job.id);
}

async function refreshJobs() {
  const jobs = await api("/api/video-analysis-jobs");
  renderJobs(jobs);
  const requestedJobId = requestedJobIdFromUrl();
  const stillShowingEmptyState = nodes.resultTitle.textContent.trim() === "贴一个视频链接";
  if (requestedJobId && (requestedJobId !== state.currentJobId || stillShowingEmptyState)) {
    state.currentJobId = requestedJobId;
    try {
      const fullJob = await api(`/api/video-analysis-job/${encodeURIComponent(requestedJobId)}`);
      renderJob(fullJob);
      return;
    } catch (error) {
      showDraftStatus(`载入失败：${error.message}`, "error");
      state.currentJobId = "";
    }
  }
}

async function loadJob(jobId, keepPolling = false) {
  const job = await api(`/api/video-analysis-job/${encodeURIComponent(jobId)}`);
  writeJobIdToUrl(job.id || jobId, true);
  renderJob(job);
  const shouldPoll = job.status === "queued" || job.status === "running";
  if (keepPolling && shouldPoll) startPolling(job.id);
  if (!shouldPoll) stopPolling();
  await refreshJobs();
}

function stopPolling() {
  if (state.pollTimer) window.clearInterval(state.pollTimer);
  state.pollTimer = null;
}

function startPolling(jobId) {
  stopPolling();
  state.pollTimer = window.setInterval(() => {
    void loadJob(jobId, true);
  }, 1600);
}

async function startAnalysis() {
  if (state.sourceMode === "local") {
    await startLocalAnalysis();
    return;
  }
  const url = nodes.urlInput.value.trim();
  if (!url) {
    nodes.urlInput.focus();
    return;
  }
  const platform = platformFromUrl(url);
  if (!["youtube", "bilibili"].includes(platform)) {
    nodes.jobSummary.classList.remove("hidden");
    nodes.jobSummary.classList.remove("failure");
    nodes.jobSummary.textContent = "只支持 YouTube 和 B站链接。";
    nodes.urlInput.focus();
    return;
  }
  resetWorkspaceSurface();
  nodes.urlInput.value = url;
  nodes.startAnalysis.disabled = true;
  nodes.jobSummary.classList.add("hidden");
  nodes.jobSummary.classList.remove("failure", "pending");
  nodes.jobSummary.textContent = "";
  renderDownloadProgress({ status: "running", stage: "fetch", createdAt: new Date().toISOString() });
  try {
    const job = await api("/api/video-analysis-request", {
      method: "POST",
      body: JSON.stringify({
        url,
        analysisBackend: "rules",
        requireLocalVideo: true,
        extractFrames: true,
        cookiesFromBrowser: nodes.useBrowserCookies.checked ? "chrome" : "none",
        disableWhisperFallback: nodes.disableWhisperFallback.checked,
        disableVideoParser: false,
        skipRewrites: nodes.skipRewrites.checked,
        frameIntervalSeconds: 180,
        maxFrames: 8,
      }),
    });
    renderJob(job);
    await refreshJobs();
    startPolling(job.id);
  } catch (error) {
    hideDownloadProgress();
    nodes.jobSummary.classList.remove("hidden");
    nodes.jobSummary.classList.remove("failure");
    nodes.jobSummary.textContent = `失败：${error.message}`;
  } finally {
    nodes.startAnalysis.disabled = false;
  }
}

async function startLocalAnalysis() {
  const file = selectedLocalVideoFile();
  if (!file) {
    nodes.localVideoInput?.focus();
    if (nodes.jobSummary) {
      nodes.jobSummary.classList.remove("hidden", "failure");
      nodes.jobSummary.textContent = "先选择一个本地视频。";
    }
    return;
  }
  if (!nodes.disableWhisperFallback.checked) {
    const health = await refreshTranscriptionHealth();
    if (!health?.ok) {
      nodes.jobSummary.classList.remove("hidden");
      nodes.jobSummary.classList.add("failure");
      nodes.jobSummary.textContent = health?.label || "转写环境不可用。";
      return;
    }
  }
  resetWorkspaceSurface();
  nodes.startAnalysis.disabled = true;
  nodes.jobSummary.classList.add("hidden");
  nodes.jobSummary.classList.remove("failure", "pending");
  nodes.jobSummary.textContent = "";
  renderDownloadProgress({ status: "running", sourceType: "local", stage: "import" });
  try {
    const form = new FormData();
    form.append("video", file);
    form.append("title", file.name.replace(/\.[^.]+$/, ""));
    form.append("analysisBackend", "rules");
    form.append("extractFrames", "1");
    form.append("disableWhisperFallback", nodes.disableWhisperFallback.checked ? "1" : "0");
    form.append("skipRewrites", nodes.skipRewrites.checked ? "1" : "0");
    form.append("frameIntervalSeconds", "180");
    form.append("maxFrames", "8");
    const response = await fetch("/api/video-analysis-local-file", {
      method: "POST",
      body: form,
    });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || `${response.status} ${response.statusText}`);
    renderJob(job);
    await refreshJobs();
    startPolling(job.id);
  } catch (error) {
    nodes.jobSummary.classList.remove("hidden");
    nodes.jobSummary.classList.add("failure");
    nodes.jobSummary.textContent = `失败：${error.message}`;
    hideDownloadProgress();
  } finally {
    nodes.startAnalysis.disabled = false;
  }
}

async function refetchCurrentWithFrames() {
  if (!state.currentJobId) return;
  const current = await api(`/api/video-analysis-job/${encodeURIComponent(state.currentJobId)}`);
  const url = current.url || current.result?.url || current.summary?.videoEmbed?.watchUrl || "";
  if (!url) {
    nodes.jobSummary.classList.remove("hidden");
    nodes.jobSummary.classList.remove("failure");
    nodes.jobSummary.textContent = "没有找到视频链接。";
    return;
  }
  nodes.refetchFrames.disabled = true;
  nodes.jobSummary.classList.remove("hidden");
  nodes.jobSummary.classList.remove("failure");
  const targetFrameSeconds = demoDeckTargetSeconds(current.summary || state.currentSummary || {});
  const qualityRefetch = deckNeedsEvidenceFrames(current.summary || state.currentSummary || {});
  nodes.jobSummary.textContent = qualityRefetch ? "正在按演示页补关键帧。" : "已提交补截图任务。";
  try {
    const job = await api("/api/video-analysis-request", {
      method: "POST",
      body: JSON.stringify({
        url,
        analysisBackend: current.analysisBackend || "rules",
        requireLocalVideo: true,
        extractFrames: true,
        cookiesFromBrowser: current.cookiesFromBrowser || (nodes.useBrowserCookies.checked ? "chrome" : "none"),
        disableWhisperFallback: Boolean(current.disableWhisperFallback),
        disableVideoParser: Boolean(current.disableVideoParser),
        skipRewrites: Boolean(current.skipRewrites ?? true),
        frameIntervalSeconds: qualityRefetch ? 60 : 180,
        maxFrames: qualityRefetch ? Math.max(12, targetFrameSeconds.length || 0) : 8,
        targetFrameSeconds: qualityRefetch ? targetFrameSeconds : [],
        qualityRefetch,
      }),
    });
    renderJob(job);
    await refreshJobs();
    startPolling(job.id);
  } catch (error) {
    nodes.jobSummary.textContent = `补截图失败：${error.message}`;
  } finally {
    nodes.refetchFrames.disabled = false;
  }
}

function generateDraft() {
  if (nodes.draftPanel?.classList.contains("hidden") && openSavedDraft()) {
    nodes.draftPanel?.scrollIntoView({ behavior: "smooth", block: "start" });
    showDraftStatus("已恢复上次保存的讲稿。", "ready");
    return;
  }
  const deck = state.currentSummary?.demoDeck || {};
  const slides = Array.isArray(deck.slides) ? deck.slides : [];
  if (demoDeckBlockedByMaterial(state.currentSummary || {})) {
    showDraftStatus("没拿到字幕，暂不生成。", "error");
    return;
  }
  if (!slides.length) {
    showDraftStatus("还没有拆解。", "error");
    return;
  }
  nodes.generateDraft.disabled = true;
  nodes.regenerateDraft.disabled = true;
  try {
    state.activeDeckSlideIndex = 0;
    state.editingDeckSlideIndex = null;
    const text = fallbackDeckMarkdown();
    setDraftText(text, {
      engine: "demoDeck",
      model: "local",
      slides,
      demoDeckQuality: deck.demoDeckQuality,
    });
    saveDraftLocal({ silent: true });
    nodes.draftGate.classList.add("hidden");
    nodes.draftPanel?.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showDraftStatus(`生成失败：${error.message}`, "error");
  } finally {
    nodes.generateDraft.disabled = false;
    nodes.regenerateDraft.disabled = false;
  }
}

function polishedSlideTitle(slide = {}, index = 0) {
  const titleText = slide.title || "";
  const text = `${titleText} ${slide.proof || ""} ${slide.talkTrack || ""} ${slide.audienceTakeaway || ""}`;
  const tutorialTitles = [
    "这条视频排的是连接失败",
    "设备和音频源决定能不能复现",
    "地址和证书是第一关",
    "跑通要看真实结果",
    "防火墙是最后一层门槛",
    "最后收成操作清单",
  ];
  if (/演示目标|正常流程|排的是连接失败/.test(titleText) || index === 0) return "这条视频排的是连接失败";
  if (/准备简历|音频|声音源|设备/.test(titleText)) return "设备和音频源决定能不能复现";
  if (/安装连接证书|地址和证书/.test(titleText)) return "地址和证书是第一关";
  if (/验证转写|跑通|结果/.test(titleText)) return "跑通要看真实结果";
  if (/排查防火墙|防火墙/.test(titleText)) return "防火墙是最后一层门槛";
  if (/防火墙|服务状态|最后门槛/.test(text)) return "补上真实使用的最后门槛";
  if (/转写|消息列表|结果验收|跑通/.test(text)) return "用结果证明已经跑通";
  if (/证书|连接失败|地址访问|重装/.test(text)) return "把失败拆成可检查动作";
  if (/简历|音频|声音来源|输入材料/.test(text)) return "把输入材料先交代清楚";
  if (/演示目标|正常流程|排什么坑|连接失败/.test(text)) return "这条视频排的是连接失败";
  return tutorialTitles[Math.min(index, tutorialTitles.length - 1)] || slide.title || `第 ${index + 1} 页`;
}

function polishSlide(slide = {}, index = 0) {
  const title = polishedSlideTitle(slide, index);
  const proof = slide.proof || slide.action || slide.evidence || "";
  const talk = slide.talkTrack || slide.speakerNote || "";
  const remember = slide.audienceTakeaway || slide.meaning || "";
  const tunedProof = proof
    .replace(/^这页证明/, "这里要看")
    .replace(/不是玄学/g, "不是靠猜")
    .replace(/不只是点开就能用/g, "不是点开就结束");
  const tunedTalk = talk
    ? talk.replace(/^先说/, "讲的时候先说").replace(/^先把/, "讲的时候先把")
    : "讲的时候先把画面里的动作压成一句话。";
  const tunedRemember = remember
    ? remember.replace(/^这一步照做以后，/, "观众应该知道：")
    : "观众应该知道这一页放在这里的理由。";
  return {
    ...slide,
    index: index + 1,
    title,
    proof: tunedProof,
    talkTrack: tunedTalk,
    audienceTakeaway: tunedRemember,
    slideBody: compact(`${tunedProof} ${tunedTalk} ${tunedRemember}`, 180),
  };
}

function polishDeck() {
  const baseSlides = currentDeckSlides();
  if (!baseSlides.length) {
    showDraftStatus("还没有讲稿。", "error");
    return;
  }
  state.editingDeckSlideIndex = null;
  const deck = state.currentSummary?.demoDeck || {};
  const headline = deck.headline || nodes.resultTitle.textContent.trim() || "视频演示拆解";
  const source = deck.sourceStatus || playbackSourceText(state.currentSummary || {});
  const polishedSlides = baseSlides.slice(0, 8).map((slide, index) => polishSlide(slide, index));
  const text = deckMarkdownFromSlides(polishedSlides, `${headline}｜顺稿`, source);
  setDraftText(text, {
    engine: "demoDeckPolish",
    model: "codex-local",
    slides: polishedSlides,
    demoDeckQuality: assessDeckQuality(polishedSlides),
  });
  saveDraftLocal({ silent: true });
  nodes.draftGate.classList.add("hidden");
  showDraftStatus("已顺一版。", "ready");
}

async function copyDraft() {
  const text = currentDraftText();
  if (!text) {
    showDraftStatus("还没有讲稿。", "error");
    return;
  }
  await navigator.clipboard.writeText(text);
  showDraftStatus("已复制。", "ready");
}

function downloadDraftMarkdown() {
  const text = currentDraftText();
  if (!text) {
    showDraftStatus("还没有讲稿。", "error");
    return;
  }
  const title = nodes.resultTitle.textContent.trim() || "video-deck";
  const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(title, "video-deck")}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  showDraftStatus("已下载 Markdown。", "ready");
}

async function downloadDeckPptx() {
  const slides = currentDeckSlides();
  if (!slides.length) {
    showDraftStatus("还没有演示页。", "error");
    return;
  }
  const title = draftHeadline() || nodes.resultTitle.textContent.trim() || "video-deck";
  const sourceStatus = draftSourceStatus() || playbackSourceText(state.currentSummary || {});
  if (nodes.saveDeckPptx) nodes.saveDeckPptx.disabled = true;
    showDraftStatus("正在导出 PPTX。", "running");
  try {
    const response = await fetch("/api/video-deck-pptx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, sourceStatus, slides }),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${slugify(title, "video-deck")}.pptx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    showDraftStatus("已下载 PPTX。", "ready");
  } catch (error) {
    showDraftStatus(`PPTX 失败：${error.message}`, "error");
  } finally {
    if (nodes.saveDeckPptx) nodes.saveDeckPptx.disabled = false;
  }
}

function absoluteAssetUrl(url) {
  if (!url) return "";
  try {
    return new URL(url, window.location.origin).href;
  } catch {
    return "";
  }
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("read image failed"));
    reader.readAsDataURL(blob);
  });
}

async function inlineAssetUrl(url) {
  const absolute = absoluteAssetUrl(url);
  if (!absolute) return "";
  try {
    const response = await fetch(absolute);
    if (!response.ok) return absolute;
    const blob = await response.blob();
    if (!blob.type.startsWith("image/") || blob.size > 4 * 1024 * 1024) return absolute;
    return await blobToDataUrl(blob);
  } catch {
    return absolute;
  }
}

function currentDeckSlides() {
  if (Array.isArray(state.latestDraft?.slides) && state.latestDraft.slides.length) {
    return state.latestDraft.slides;
  }
  if (Array.isArray(state.currentSummary?.demoDeck?.slides) && state.currentSummary.demoDeck.slides.length) {
    return state.currentSummary.demoDeck.slides;
  }
  return [];
}

async function buildDeckHtmlDocument({ inlineImages = false } = {}) {
  const summary = state.currentSummary || {};
  const deck = summary.demoDeck || {};
  const slides = currentDeckSlides();
  const title = deck.headline || nodes.resultTitle.textContent.trim() || "视频演示拆解";
  const source = deck.sourceStatus || playbackSourceText(summary);
  const deckDate = new Date().toLocaleDateString("zh-CN");
  const firstFrame = slides.find((slide) => slide.frameUrl)?.frameUrl || "";
  const coverImage = inlineImages ? await inlineAssetUrl(firstFrame) : absoluteAssetUrl(firstFrame);
  const slideParts = await Promise.all(
    slides.map(async (slide, index) => {
      const imageUrl = inlineImages ? await inlineAssetUrl(slide.frameUrl) : absoluteAssetUrl(slide.frameUrl);
      const watchUrl = absoluteAssetUrl(slide.watchAtUrl);
      return `<section class="slide">
        <div class="media">${imageUrl ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(slide.title || "视频截图")}">` : `<div class="empty">${escapeHtml(slide.timeLabel || "00:00")}</div>`}</div>
        <div class="copy">
          <p class="kicker">第 ${escapeHtml(String(slide.index || ""))} 页 · ${escapeHtml(slide.timeLabel || "00:00")}</p>
          <h2>${escapeHtml(slide.title || "这一页讲什么")}</h2>
          <p class="label">画面</p>
          <p class="action">${escapeHtml(slide.proof || slide.action || slide.evidence || "")}</p>
          <p class="label">讲这一页</p>
          <p class="meaning">${escapeHtml(slide.talkTrack || slide.speakerNote || "")}</p>
          <p class="line">${escapeHtml(slide.audienceTakeaway || slide.meaning || "")}</p>
          ${watchUrl ? `<a class="watch" href="${escapeHtml(watchUrl)}">回看这一段</a>` : ""}
        </div>
        <footer>${escapeHtml(title)} · ${index + 1}/${slides.length}</footer>
      </section>`;
    }),
  );
  const slideHtml = slideParts.join("\n");
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)}</title>
<style>
  :root { --ink:#181612; --muted:#706b61; --line:#ded6c8; --accent:#137f63; --paper:#f7f3eb; --panel:#fffdf8; }
  * { box-sizing: border-box; }
  html { scroll-snap-type:y mandatory; background:#e7e0d4; }
  body { margin:0; background:#e7e0d4; color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",Arial,sans-serif; }
  main { width:min(1280px, calc(100vw - 48px)); margin:28px auto; }
  .cover, .slide { position:relative; min-height:min(720px, calc(100vh - 56px)); aspect-ratio:16/9; margin:0 auto 28px; padding:52px; border:1px solid rgba(80,70,56,.18); border-radius:28px; background:var(--panel); box-shadow:0 26px 70px rgba(43,36,24,.12); scroll-snap-align:start; page-break-after:always; overflow:hidden; }
  .cover { display:grid; grid-template-columns: 1fr 42%; gap:44px; align-items:end; }
  .cover:before { content:""; position:absolute; inset:0; background:radial-gradient(circle at 82% 18%, rgba(19,127,99,.16), transparent 32%); pointer-events:none; }
  .cover-copy { position:relative; z-index:1; }
  .cover h1 { margin:0 0 20px; font-size:56px; line-height:1.04; letter-spacing:0; max-width:780px; }
  .cover p { margin:0; color:var(--muted); font-size:17px; line-height:1.7; max-width:680px; }
  .cover-meta { margin-top:38px; display:flex; gap:10px; flex-wrap:wrap; }
  .chip { border:1px solid var(--line); border-radius:999px; padding:7px 12px; color:var(--muted); background:rgba(255,255,255,.7); font-size:13px; font-weight:700; }
  .cover-image { position:relative; z-index:1; border-radius:22px; overflow:hidden; aspect-ratio:16/10; background:#ded6c8; align-self:center; }
  .cover-image img { width:100%; height:100%; object-fit:cover; display:block; }
  .slide { display:grid; grid-template-columns: 58% 1fr; gap:42px; align-items:center; }
  .media { overflow:hidden; border-radius:22px; background:#e3ded4; aspect-ratio:16/9; display:grid; place-items:center; box-shadow:0 14px 32px rgba(43,36,24,.12); }
  .media img { width:100%; height:100%; object-fit:cover; display:block; }
  .empty { color:var(--muted); font-weight:700; }
  .kicker { margin:0 0 10px; color:var(--accent); font-size:14px; font-weight:800; }
  h2 { margin:0 0 18px; font-size:44px; line-height:1.1; letter-spacing:0; }
  .label { margin:18px 0 6px; color:var(--muted); font-size:13px; font-weight:800; }
  .action { margin:0 0 14px; font-size:22px; line-height:1.45; font-weight:700; }
  .meaning { margin:0 0 18px; color:var(--muted); font-size:17px; line-height:1.65; }
  .line { display:inline-block; margin:0; padding:9px 12px; border-radius:999px; background:rgba(19,127,99,.09); color:var(--accent); font-size:15px; line-height:1.5; }
  .watch { display:block; margin-top:18px; color:var(--accent); text-decoration:none; font-weight:700; }
  footer { position:absolute; left:52px; right:52px; bottom:24px; display:flex; justify-content:flex-end; color:var(--muted); font-size:12px; }
  @page { size: 16in 9in landscape; margin:0; }
  @media print {
    html, body { background:#fff; }
    main { width:100%; margin:0; }
    .cover, .slide { width:16in; height:9in; min-height:9in; margin:0; border:0; border-radius:0; box-shadow:none; }
  }
  @media (max-width: 900px) {
    main { width:calc(100vw - 24px); }
    .cover, .slide { aspect-ratio:auto; min-height:0; padding:28px; border-radius:20px; }
    .cover, .slide { grid-template-columns:1fr; }
    .cover h1 { font-size:34px; }
    h2 { font-size:30px; }
    footer { position:static; margin-top:24px; justify-content:flex-start; }
  }
</style>
</head>
<body>
<main>
  <section class="cover">
    <div class="cover-copy">
      <h1>${escapeHtml(title)}</h1>
      <p>${escapeHtml(source)}</p>
      <div class="cover-meta">
        <span class="chip">${escapeHtml(String(slides.length || 0))} 页拆解</span>
        <span class="chip">${escapeHtml(deckDate)}</span>
        <span class="chip">视频截图</span>
      </div>
    </div>
    <div class="cover-image">${coverImage ? `<img src="${escapeHtml(coverImage)}" alt="视频封面">` : `<div class="empty">视频拆解</div>`}</div>
  </section>
  ${slideHtml || "<p>还没有可用画面。</p>"}
</main>
</body>
</html>`;
}

async function downloadDeckHtml() {
  const slides = currentDeckSlides();
  if (!slides.length) {
    showDraftStatus("还没有演示页。", "error");
    return;
  }
  if (nodes.saveDeckHtml) nodes.saveDeckHtml.disabled = true;
  showDraftStatus("正在整理页面。", "running");
  const title = nodes.resultTitle.textContent.trim() || "video-deck";
  try {
    const html = await buildDeckHtmlDocument({ inlineImages: true });
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${slugify(title, "video-deck")}.html`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    showDraftStatus("已下载页面。", "ready");
  } catch (error) {
    showDraftStatus(`下载失败：${error.message}`, "error");
  } finally {
    if (nodes.saveDeckHtml) nodes.saveDeckHtml.disabled = false;
  }
}

function downloadMaterialPackage() {
  if (!state.currentJobId) {
    showDraftStatus("没有可保存的任务。", "error");
    return;
  }
  const link = document.createElement("a");
  link.href = `/api/video-analysis-package/${encodeURIComponent(state.currentJobId)}`;
  link.download = "video-material.zip";
  document.body.appendChild(link);
  link.click();
  link.remove();
  showDraftStatus("已开始保存材料包。", "ready");
}

function draftTextToHtml(text) {
  return text
    .split(/\n\s*\n+/)
    .map((block, index) => {
      const escaped = escapeHtml(block.trim()).replace(/\n/g, "<br>");
      return index === 0 ? `<h2>${escaped}</h2>` : `<p>${escaped}</p>`;
    })
    .join("\n");
}

async function sendToWorkbench() {
  const text = currentDraftText();
  if (!text) {
    showDraftStatus("还没有讲稿。", "error");
    return;
  }
  const title = text.split(/\n/).find(Boolean)?.trim() || nodes.resultTitle.textContent.trim() || "视频草稿";
  const documentId = slugify(`video_${state.currentJobId || title}`, `video-${Date.now()}`);
  nodes.sendWorkbench.disabled = true;
  showDraftStatus("写入写作台。", "running");
  try {
    await api("/api/document", {
      method: "POST",
      body: JSON.stringify({
        documentId,
        title,
        contentText: text,
        contentHtml: draftTextToHtml(text),
        documentType: "experiment",
      }),
    });
    const url = `/v2/?documentId=${encodeURIComponent(documentId)}`;
    nodes.exportLink.classList.remove("hidden");
    nodes.exportLink.innerHTML = `<a href="${url}" target="_blank" rel="noreferrer">打开写作台</a>`;
    showDraftStatus("已写入。", "ready");
  } catch (error) {
    showDraftStatus(`写入失败：${error.message}`, "error");
  } finally {
    nodes.sendWorkbench.disabled = false;
  }
}

async function rerunCurrentJob() {
  if (!state.currentJobId) return;
  const job = await api(`/api/video-analysis-rerun/${encodeURIComponent(state.currentJobId)}`, { method: "POST", body: "{}" });
  closeHistoryDrawer();
  renderJob(job);
  await refreshJobs();
  startPolling(job.id);
}

async function rerunCurrentJobWithChrome() {
  if (!state.currentJobId) return;
  const current = await api(`/api/video-analysis-job/${encodeURIComponent(state.currentJobId)}`);
  const url = current.url || current.result?.url || current.summary?.videoEmbed?.watchUrl || nodes.urlInput.value.trim();
  if (!url) return;
  nodes.useBrowserCookies.checked = true;
  nodes.urlInput.value = url;
  const job = await api("/api/video-analysis-request", {
    method: "POST",
    body: JSON.stringify({
      url,
      analysisBackend: current.analysisBackend || "rules",
      requireLocalVideo: true,
      extractFrames: true,
      cookiesFromBrowser: "chrome",
      disableWhisperFallback: Boolean(current.disableWhisperFallback ?? nodes.disableWhisperFallback.checked),
      disableVideoParser: Boolean(current.disableVideoParser),
      skipRewrites: Boolean(current.skipRewrites ?? nodes.skipRewrites.checked),
      frameIntervalSeconds: Number(current.frameIntervalSeconds || 180),
      maxFrames: Number(current.maxFrames || 8),
    }),
  });
  renderJob(job);
  await refreshJobs();
  startPolling(job.id);
}

async function clearJobs(path) {
  await apiDelete(path);
  resetWorkspaceSurface();
  try {
    const next = new URL(window.location.href);
    next.searchParams.delete("jobId");
    window.history.replaceState({}, "", next);
  } catch {
    // URL cleanup is only for a cleaner entry state.
  }
  await refreshJobs();
}

nodes.tabs.forEach((button) => button.addEventListener("click", () => setActiveView(button.dataset.view)));
nodes.refreshJobs.addEventListener("click", refreshJobs);
nodes.startAnalysis.addEventListener("click", startAnalysis);
nodes.linkMode?.addEventListener("click", () => setSourceMode("link"));
nodes.localMode?.addEventListener("click", () => setSourceMode("local"));
nodes.localVideoInput?.addEventListener("change", () => {
  state.localVideoFile = null;
  updateLocalFileName();
});
["dragenter", "dragover", "dragleave", "drop"].forEach((type) => {
  nodes.localInputWrap?.addEventListener(type, handleLocalDrag);
});
nodes.openHistory.addEventListener("click", openHistoryDrawer);
nodes.closeHistory.addEventListener("click", closeHistoryDrawer);
nodes.closeHistoryPanel.addEventListener("click", closeHistoryDrawer);
nodes.showErrors.addEventListener("change", refreshJobs);
nodes.historyToggle.addEventListener("click", () => {
  state.historyExpanded = !state.historyExpanded;
  void refreshJobs();
});
nodes.generateDraft.addEventListener("click", () => {
  generateDraft();
});
nodes.generateDeck.addEventListener("click", () => {
  generateDraft();
});
nodes.refetchFrames.addEventListener("click", () => {
  void refetchCurrentWithFrames();
});
nodes.saveMaterialPackage?.addEventListener("click", downloadMaterialPackage);
nodes.regenerateDraft.addEventListener("click", () => {
  generateDraft();
});
nodes.polishDeck.addEventListener("click", () => {
  polishDeck();
});
nodes.copyDraft.addEventListener("click", () => {
  void copyDraft();
});
nodes.saveDraft.addEventListener("click", downloadDraftMarkdown);
nodes.saveDeckPptx.addEventListener("click", () => {
  void downloadDeckPptx();
});
nodes.saveDeckHtml.addEventListener("click", downloadDeckHtml);
nodes.sendWorkbench.addEventListener("click", () => {
  void sendToWorkbench();
});
nodes.draftEditor.addEventListener("input", () => {
  const saved = {
    title: nodes.resultTitle.textContent.trim() || "未命名稿件",
    body: nodes.draftEditor.value,
    slides: state.latestDraft?.slides || [],
    headline: state.latestDraft?.headline || draftHeadline(),
    sourceStatus: state.latestDraft?.sourceStatus || draftSourceStatus(),
    deckVersion: Number(state.currentSummary?.demoDeckVersion || 0) || 0,
    summaryVersion: Number(state.currentSummary?.videoSummaryVersion || 0) || 0,
    savedAt: new Date().toISOString(),
    jobId: state.currentJobId,
  };
  state.savedDraft = saved;
  state.savedDraftAvailable = Boolean(saved.body.trim());
  updateGenerateDeckButton();
  window.localStorage.setItem(draftCacheKey(), JSON.stringify(saved));
});
nodes.rerunJob.addEventListener("click", () => {
  void rerunCurrentJob().catch((error) => showDraftStatus(`重跑失败：${error.message}`, "error"));
});
nodes.jobSummary.addEventListener("click", (event) => {
  const button = event.target instanceof HTMLElement ? event.target.closest("[data-video-action]") : null;
  if (!button) return;
  const action = button.getAttribute("data-video-action") || "";
  if (action === "open-platform-login") {
    const platform = platformFromUrl(nodes.urlInput.value);
    const loginUrl = platformLoginUrl(platform);
    if (loginUrl) window.open(loginUrl, "_blank", "noopener");
    return;
  }
  if (action === "rerun-with-chrome") {
    button.setAttribute("disabled", "true");
    void rerunCurrentJobWithChrome().catch((error) => {
      button.removeAttribute("disabled");
      showDraftStatus(`重跑失败：${error.message}`, "error");
    });
    return;
  }
  if (action === "rerun") {
    button.setAttribute("disabled", "true");
    void rerunCurrentJob().catch((error) => {
      button.removeAttribute("disabled");
      showDraftStatus(`重跑失败：${error.message}`, "error");
    });
  }
});
nodes.clearFailed.addEventListener("click", () => {
  void clearJobs("/api/video-analysis-jobs?status=error").catch((error) => showDraftStatus(`清理失败：${error.message}`, "error"));
});
nodes.clearHistory.addEventListener("click", () => {
  void clearJobs("/api/video-analysis-jobs").catch((error) => showDraftStatus(`清理失败：${error.message}`, "error"));
});
nodes.urlInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    void startAnalysis();
  }
});
window.addEventListener("popstate", () => {
  const requestedJobId = requestedJobIdFromUrl();
  if (!requestedJobId || requestedJobId === state.currentJobId) return;
  void loadJob(requestedJobId, false).catch((error) => showDraftStatus(`载入失败：${error.message}`, "error"));
});

setSourceMode("link");
updateLocalFileName();
setActiveView("report");
const initialJobId = requestedJobIdFromUrl();
if (initialJobId) {
  void loadJob(initialJobId, false).catch((error) => {
    state.currentJobId = "";
    showDraftStatus(`载入失败：${error.message}`, "error");
    void refreshJobs();
  });
} else {
  void refreshJobs();
}
