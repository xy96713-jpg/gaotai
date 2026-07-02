const editor = document.querySelector("#editor");
const paper = document.querySelector(".paper");
const sideNode = document.querySelector(".side");
const titleInput = document.querySelector("#documentTitle");
const documentStateNode = document.querySelector("#documentState");
const documentPathNode = document.querySelector("#documentPath");
const documentListNode = document.querySelector("#documentList");
const documentSearchInput = document.querySelector("#documentSearch");
const documentFilterButtons = document.querySelectorAll("[data-document-filter]");
const selectionMenu = document.querySelector("#selectionMenu");
const selectionMenuStatusNode = document.querySelector("#selectionMenuStatus");
const draftBriefInput = document.querySelector("#draftBrief");
const draftClaimInput = document.querySelector("#draftClaim");
const draftSourcesInput = document.querySelector("#draftSources");
const draftReaderObjectionInput = document.querySelector("#draftReaderObjection");
const draftAvoidShapeInput = document.querySelector("#draftAvoidShape");
const draftAuthorTakeInput = document.querySelector("#draftAuthorTake");
const draftNoInventInput = document.querySelector("#draftNoInvent");
const fillStartCardButton = document.querySelector("#fillStartCard");
const startCardHintNode = document.querySelector("#startCardHint");
const draftPromptModeInput = document.querySelector("#draftPromptMode");
const draftProviderInput = document.querySelector("#draftProvider");
const currentDraftPreviewNode = document.querySelector("#currentDraftPreview");
const cleanAiTasteInput = document.querySelector("#cleanAiTaste");
const cowriteSeedInput = document.querySelector("#cowriteSeed");
const buildCowritePlanButton = document.querySelector("#buildCowritePlan");
const composeCowriteDraftButton = document.querySelector("#composeCowriteDraft");
const cowriteStateNode = document.querySelector("#cowriteState");
const cowriteProgressLabelNode = document.querySelector("#cowriteProgressLabel");
const cowriteProgressFillNode = document.querySelector("#cowriteProgressFill");
const cowriteThesisStateNode = document.querySelector("#cowriteThesisState");
const cowriteThesisNode = document.querySelector("#cowriteThesis");
const cowriteBeatListNode = document.querySelector("#cowriteBeatList");
const cowriteActiveBeatNode = document.querySelector("#cowriteActiveBeat");
const cowriteCurrentJobNode = document.querySelector("#cowriteCurrentJob");
const cowriteCurrentMustNode = document.querySelector("#cowriteCurrentMust");
const cowriteSectionSeedInput = document.querySelector("#cowriteSectionSeed");
const writeCowriteSectionButton = document.querySelector("#writeCowriteSection");
const cowriteSectionDraftNode = document.querySelector("#cowriteSectionDraft");
const insertCowriteSectionButton = document.querySelector("#insertCowriteSection");
const saveCowriteSectionButton = document.querySelector("#saveCowriteSection");
const clearCowriteSectionButton = document.querySelector("#clearCowriteSection");
const generateOpeningsButton = document.querySelector("#generateOpenings");
const generateDraftButton = document.querySelector("#generateDraft");
const generateProgressNode = document.querySelector("#generateProgress");
const generateProgressTitleNode = document.querySelector("#generateProgressTitle");
const generateElapsedNode = document.querySelector("#generateElapsed");
const generateProgressBarNode = document.querySelector("#generateProgressBar");
const generateProgressDetailNode = document.querySelector("#generateProgressDetail");
const cancelGenerateButton = document.querySelector("#cancelGenerate");
const runPreflightButton = document.querySelector("#runPreflight");
const refreshStyleCardButton = document.querySelector("#refreshStyleCard");
const sessionStyleCardNode = document.querySelector("#sessionStyleCard");
const preflightPreviewNode = document.querySelector("#preflightPreview");
const editorialHandoffPreviewNode = document.querySelector("#editorialHandoffPreview");
const generateStateNode = document.querySelector("#generateState");
const openingStateNode = document.querySelector("#openingState");
const openingListNode = document.querySelector("#openingList");
const generatedTitleNode = document.querySelector("#generatedTitle");
const generatedPreviewNode = document.querySelector("#generatedPreview");
const generatedModeHintNode = document.querySelector("#generatedModeHint");
const generatedProvenanceNode = document.querySelector("#generatedProvenance");
const generationAuditNode = document.querySelector("#generationAudit");
const compliancePreviewNode = document.querySelector("#compliancePreview");
const loadGeneratedButton = document.querySelector("#loadGenerated");
const showRawDraftButton = document.querySelector("#showRawDraft");
const showCleanDraftButton = document.querySelector("#showCleanDraft");
const draftNoticeNode = document.querySelector("#draftNotice");
const draftStatsNode = document.querySelector("#draftStats");
const provenanceStateNode = document.querySelector("#provenanceState");
const workspaceToastNode = document.querySelector("#workspaceToast");
const leftStatusNode = document.querySelector("#leftStatus");
const rightStatusNode = document.querySelector("#rightStatus");
const syncLatestButton = document.querySelector("#syncLatest");
const loadGeneratedTopButton = document.querySelector("#loadGeneratedTop");
const openInObsidianButton = document.querySelector("#openInObsidian");
const topicFoldNode = document.querySelector("#topicFold");
const topicManageFoldNode = document.querySelector("#topicManageFold");
const latestFoldNode = document.querySelector(".latest-fold");
const latestFoldSummaryNode = latestFoldNode?.querySelector("summary") || null;
const topicArchiveListNode = document.querySelector("#topicArchiveList");
const refreshTopicArchiveButton = document.querySelector("#refreshTopicArchive");
const openingBadgeNode = document.querySelector("#openingBadge");
const draftBadgeNode = document.querySelector("#draftBadge");
const bodyBadgeNode = document.querySelector("#bodyBadge");
const quickAuditButton = document.querySelector("#quickAuditButton");
const finalReviewButton = document.querySelector("#finalReviewButton");
const auditSummaryNode = document.querySelector("#auditSummary");
const auditScoreNode = document.querySelector("#auditScore");
const auditListNode = document.querySelector("#auditList");
const auditFoldNode = auditListNode.closest("details");
const panelTabs = document.querySelectorAll(".panel-tab");
const panelViews = document.querySelectorAll(".panel-view");
const selectionBlockNode = document.querySelector(".selection-block");
const selectedTextNode = document.querySelector("#selectedText");
const selectionStateNode = document.querySelector("#selectionState");
const rewriteContextNode = document.querySelector(".rewrite-context");
const rewriteIssueNode = document.querySelector("#rewriteIssue");
const rewriteProgressNode = document.querySelector("#rewriteProgress");
const nextAuditIssueButton = document.querySelector("#nextAuditIssue");
const bridgeStatusNode = document.querySelector("#bridgeStatus");
const runRewriteButton = document.querySelector("#runRewrite");
const quickRewriteAction = document.querySelector("#quickRewriteAction");
const quickRecordAction = document.querySelector("#quickRecordAction");
const aiFlavorAction = document.querySelector("#aiFlavorAction");
const quickAuditAction = document.querySelector("#quickAuditAction");
const saveBadButton = document.querySelector("#saveBad");
const saveGoodButton = document.querySelector("#saveGood");
const paragraphAssistBlockNode = document.querySelector(".paragraph-assist-block");
const paragraphAssistAction = document.querySelector("#paragraphAssistAction");
const paragraphAssistStateNode = document.querySelector("#paragraphAssistState");
const paragraphAssistHintNode = document.querySelector("#paragraphAssistHint");
const paragraphAssistPromptInput = document.querySelector("#paragraphAssistPromptInput");
const candidateListNode = document.querySelector("#candidateList");
const actionDetailNode = document.querySelector(".action-detail");
const jobStateNode = document.querySelector("#jobState");
const memoryListNode = document.querySelector("#memoryList");
const memoryCountNode = document.querySelector("#memoryCount");
const memorySummaryNode = document.querySelector("#memorySummary");
const memoryFoldNode = memoryListNode.closest("details");

if (latestFoldNode) {
  latestFoldNode.open = false;
}
const saveStateNode = document.querySelector("#saveState");
const exportMenuNode = document.querySelector(".toolbar-menu");
const rerunAuditButton = document.querySelector("#rerunAudit");
const tasteAuditButton = document.querySelector("#tasteAuditButton");
const deepReviewAction = document.querySelector("#deepReviewAction");
const refreshWorkbenchContextButton = document.querySelector("#refreshWorkbenchContext");
const proofFoldNode = document.querySelector("#proofFold");
const proofSummaryNode = document.querySelector("#proofSummary");
const styleProofPanel = document.querySelector("#styleProofPanel");
const aiFlavorFoldNode = document.querySelector("#aiFlavorFold");
const aiFlavorSummaryNode = document.querySelector("#aiFlavorSummary");
const aiFlavorPanelNode = document.querySelector("#aiFlavorPanel");
const deliveryStatusNode = document.querySelector("#deliveryStatus");
const contextContractNode = document.querySelector("#contextContract");
const contextStyleNode = document.querySelector("#contextStyle");
const contextDemoNode = document.querySelector("#contextDemo");
const contextGoldNode = document.querySelector("#contextGold");
const contextAmiNode = document.querySelector("#contextAmi");
const advancedFoldNode = document.querySelector(".advanced-fold");
const returnLiteModeButton = document.querySelector("#returnLiteMode");
const projectPackNameInput = document.querySelector("#projectPackName");
const projectPackPathInput = document.querySelector("#projectPackPath");
const projectPackNotesInput = document.querySelector("#projectPackNotes");
const buildProjectPackButton = document.querySelector("#buildProjectPack");
const loadProjectPackButton = document.querySelector("#loadProjectPack");
const projectPackPreviewNode = document.querySelector("#projectPackPreview");
const newTopicDraftButton = document.querySelector("#newTopicDraft");
const presentDraftButton = document.querySelector("#presentDraft");
const presentationModeNode = document.querySelector("#presentationMode");
const presentationTitleNode = document.querySelector("#presentationTitle");
const presentationViewportNode = document.querySelector("#presentationViewport");
const presentationTextNode = document.querySelector("#presentationText");
const presentationFontSizeInput = document.querySelector("#presentationFontSize");
const presentationSpeedInput = document.querySelector("#presentationSpeed");
const presentationFontValueNode = document.querySelector("#presentationFontValue");
const presentationSpeedValueNode = document.querySelector("#presentationSpeedValue");
const presentationPlayButton = document.querySelector("#presentationPlay");
const presentationResetButton = document.querySelector("#presentationReset");
const presentationCloseButton = document.querySelector("#presentationClose");
const presentationStatsNode = document.querySelector("#presentationStats");

const legacyDraftKey = "codex-inline-editor-v2-html";
const legacyTitleKey = "codex-inline-editor-v2-title";
const draftCacheKeyPrefix = "codex-inline-editor-v2-doc-cache::";
const pendingJobKey = "codex-inline-editor-v2-pending-job";
const currentDocumentKey = "codex-inline-editor-v2-document-id";
const generatedDraftKey = "codex-inline-editor-v2-generated-draft";
const openingPackKey = "codex-inline-editor-v2-opening-pack";
const cowritePlanKey = "codex-inline-editor-v2-cowrite-plan";
const cowriteActiveBeatKey = "codex-inline-editor-v2-cowrite-active-beat";
const bodySourceKey = "codex-inline-editor-v2-body-source";
const promptModeKey = "codex-inline-editor-v2-prompt-mode";
const draftProviderKey = "codex-inline-editor-v2-provider";
const presentationFontSizeKey = "codex-inline-editor-v2-presentation-font-size";
const presentationSpeedKey = "codex-inline-editor-v2-presentation-speed";
const rewriteEngine = "deepseek";
const apiBase = window.location.protocol === "file:" ? "http://127.0.0.1:8766" : "";
const scratchDocumentId = "__scratch__";
const documentAliasMap = {
  "ai-best": "first_video_concise_strengthened_20260617",
  "best-writing": "first_video_concise_strengthened_20260617",
  first_video_kimi_thinking_new_frontend_20260622: "first_video_concise_strengthened_20260617",
};

let activeRange = null;
let activeSelection = null;
let activeCaretRange = null;
let activePromptParagraph = null;
let activeMode = "rewrite";
let autosaveTimer = null;
let activeJobTimer = null;
let suppressSelectionCaptureUntil = 0;
let editorUndoStack = [];
let editorRedoStack = [];
let isRestoringEditorUndo = false;
const PROGRAMMATIC_SELECTION_COOLDOWN_MS = 220;
const EDITOR_UNDO_LIMIT = 80;
function normalizeDraftProvider(value) {
  return value === "deepseek" || value === "hybrid" || value === "kimi" ? value : "deepseek";
}

function draftProviderLabel(provider, compact = false) {
  if (provider === "hybrid") return compact ? "主笔+复核" : "主笔接口 + 复核接口";
  if (provider === "kimi") return compact ? "旧主笔路线" : "旧主笔路线";
  return compact ? "默认主笔" : "默认主笔接口";
}

const DOCUMENT_TYPE_LABELS = {
  formal: "正式稿",
  experiment: "实验稿",
};

function normalizeDocumentType(value) {
  return value === "experiment" ? "experiment" : "formal";
}

function documentTypeLabel(value) {
  return DOCUMENT_TYPE_LABELS[normalizeDocumentType(value)] || DOCUMENT_TYPE_LABELS.formal;
}

function modelChainLabel(value) {
  const normalized = String(value || "");
  if (normalized.includes("kimi") && normalized.includes("codex")) return "旧主笔路线";
  if (normalized.includes("kimi")) return "旧主笔路线";
  if (normalized.includes("deepseek")) return "默认主笔接口";
  if (normalized.includes("codex")) return "审稿流程";
  return "";
}

function routeLabel(value) {
  const normalized = String(value || "");
  if (normalized === "event_hot_analysis") return "事件/热点";
  if (normalized === "workbench_method") return "工作台/SOP";
  return normalized.replace(/_/g, "/");
}

function reviewStatusLabel(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "ready") return "已收稿";
  if (normalized === "needs_work") return "需再修";
  if (normalized === "blocked") return "未通过";
  return normalized;
}

function formatDocumentProvenance(metadata = {}, { compact = false } = {}) {
  if (!metadata || typeof metadata !== "object") return "";
  const parts = [
    modelChainLabel(metadata.model_chain),
    routeLabel(metadata.route),
    reviewStatusLabel(metadata.review_status),
  ].filter(Boolean);
  if (!parts.length) return "";
  return compact ? parts.slice(0, 2).join(" · ") : parts.join(" · ");
}

let providerEngine = normalizeDraftProvider(window.localStorage.getItem(draftProviderKey));
let currentDocumentId = window.localStorage.getItem(currentDocumentKey) || "";
let currentWorkspaceUpdatedAt = "";
let currentDocumentType = "formal";
let currentDocumentMetadata = {};
let currentDocumentFilter = "formal";
let documentSearchQuery = "";
let documentRefreshSeq = 0;
let selectedOpeningIndex = -1;
let latestAuditResult = null;
let currentAuditIndex = -1;
let currentAuditIssue = null;
let auditFlowDone = false;
let rewriteRunId = 0;
let paragraphAssistRunId = 0;
let paragraphAssistRecentlyAppliedUntil = 0;
let paragraphAssistRecentlyActivatedUntil = 0;
let generatedDraftView = "clean";
let cowritePlan = null;
let activeCowriteBeatId = window.localStorage.getItem(cowriteActiveBeatKey) || "";
let latestCowriteSection = "";
let generateTimer = null;
let activeGenerateController = null;
let activeGenerateJobId = "";
let generateStartedAt = 0;
let deliveryState = "unchecked";
let latestProjectPackDocumentId = "";
let activeWorkspaceSavePromise = null;
let latestTopicArchiveEntries = [];
let workspaceToastTimer = null;
let rewriteInvalidatedToastAt = 0;
let presentationPlaying = false;
let presentationFrame = 0;
let presentationLastFrameAt = 0;
let presentationScrollPosition = 0;
let finalReviewIgnoredKeys = new Set();
let documentHydrating = true;
const maxRewriteSelectionChars = 240;
const maxRewriteSelectionParagraphs = 2;

function clampNumber(value, min, max, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(min, Math.min(max, number));
}

function restorePresentationPrefs() {
  if (presentationFontSizeInput) {
    presentationFontSizeInput.value = String(
      clampNumber(
        window.localStorage.getItem(presentationFontSizeKey),
        Number(presentationFontSizeInput.min || 28),
        Number(presentationFontSizeInput.max || 88),
        Number(presentationFontSizeInput.value || 48)
      )
    );
  }
  if (presentationSpeedInput) {
    presentationSpeedInput.value = String(
      clampNumber(
        window.localStorage.getItem(presentationSpeedKey),
        Number(presentationSpeedInput.min || 0),
        Number(presentationSpeedInput.max || 200),
        Number(presentationSpeedInput.value || 100)
      )
    );
  }
}

function setDocumentHydrating(value) {
  documentHydrating = value === true;
  if (finalReviewButton) finalReviewButton.disabled = documentHydrating;
}

function savePresentationPrefs() {
  if (presentationFontSizeInput) window.localStorage.setItem(presentationFontSizeKey, String(presentationFontSizeInput.value));
  if (presentationSpeedInput) window.localStorage.setItem(presentationSpeedKey, String(presentationSpeedInput.value));
}

const sampleHtml = editor.innerHTML;
const sampleTitle = titleInput.value;

function parseTimeValue(value) {
  const ts = Date.parse(String(value || ""));
  return Number.isFinite(ts) ? ts : 0;
}

function normalizeText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .replace(/哪[。.．]里/g, "哪里")
    .replace(/([。！？!?；;])\1+/g, "$1")
    .replace(/[，,]\s*([。！？!?；;])/g, "$1")
    .replace(/([。！？!?；;])\s*[，,]/g, "$1")
    .trim();
}

function sanitizeVisibleModelText(value) {
  return normalizeText(value)
    .replace(/Kimi\s*(?:thinking\s*)?/gi, "写作助手")
    .replace(/DeepSeek\s*(?:thinking\s*)?/gi, "写作助手")
    .replace(/DS\s*(?=改句|复核|主笔|返回|正在|已生成)/gi, "写作助手")
    .replace(/deepseek[-_\w.]*/gi, "写作助手")
    .replace(/kimi[-_\w.]*/gi, "写作助手")
    .replace(/写作助手\s*正在结合上下段补写/g, "写作助手正在结合上下段补写")
    .replace(/写作助手\s*仍在整理候选/g, "写作助手仍在整理候选")
    .replace(/写作助手\s*正在生成候选/g, "写作助手正在生成候选")
    .replace(/\s+/g, " ")
    .trim();
}

function sanitizeVisibleModelDom(root = document) {
  [
    jobStateNode,
    paragraphAssistStateNode,
    paragraphAssistHintNode,
    rewriteProgressNode,
    candidateListNode,
  ].forEach((node) => {
    if (!node) return;
    node.querySelectorAll?.(".rewrite-loading-title, .rewrite-loading-detail, .rewrite-loading-meta, .candidate-meta, .candidate-proof").forEach((child) => {
      const clean = sanitizeVisibleModelText(child.textContent || "");
      if (clean) child.textContent = clean;
    });
    if (!node.children?.length) {
      const clean = sanitizeVisibleModelText(node.textContent || "");
      if (clean) node.textContent = clean;
    }
  });
  root.querySelectorAll?.("[data-progress]").forEach((node) => {
    const clean = sanitizeVisibleModelText(node.dataset.progress || "");
    if (clean) node.dataset.progress = clean;
  });
}

function storageDocumentId(documentId = currentDocumentId) {
  return normalizeText(documentId) || scratchDocumentId;
}

function freshTopicDocumentId() {
  const stamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}Z$/, "")
    .replace("T", "_");
  return `topic_${stamp}_${Math.random().toString(36).slice(2, 6)}`;
}

function draftCacheKey(documentId = currentDocumentId) {
  return `${draftCacheKeyPrefix}${storageDocumentId(documentId)}`;
}

function clearLegacyDraftCache() {
  window.localStorage.removeItem(legacyDraftKey);
  window.localStorage.removeItem(legacyTitleKey);
}

function readDraftSnapshot(documentId = currentDocumentId) {
  const raw = window.localStorage.getItem(draftCacheKey(documentId));
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") {
      parsed.contentHtml = stripParagraphAssistSlotsFromHtml(parsed.contentHtml || "");
      return parsed;
    }
    return null;
  } catch (error) {
    console.warn("draft snapshot parse failed", error);
    return null;
  }
}

function stripParagraphAssistSlotsFromHtml(html = "") {
  const raw = String(html || "");
  if (!raw || !raw.includes("data-paragraph-assist-slot")) return raw;
  const shell = document.createElement("div");
  shell.innerHTML = raw;
  shell.querySelectorAll('p[data-paragraph-assist-slot="1"]').forEach((node) => {
    node.remove();
  });
  return shell.innerHTML;
}

function editorHistoryHtml() {
  return String(editor?.innerHTML || "");
}

function trimEditorUndoStack() {
  if (editorUndoStack.length > EDITOR_UNDO_LIMIT) {
    editorUndoStack = editorUndoStack.slice(editorUndoStack.length - EDITOR_UNDO_LIMIT);
  }
}

function resetEditorUndoHistory() {
  editorUndoStack = [];
  editorRedoStack = [];
}

function recordEditorUndoBoundary() {
  if (!editor || isRestoringEditorUndo) return;
  const html = editorHistoryHtml();
  const previous = editorUndoStack[editorUndoStack.length - 1];
  if (html && html !== previous) {
    editorUndoStack.push(html);
    trimEditorUndoStack();
  }
  editorRedoStack = [];
}

function placeCaretAtEditorEnd() {
  if (!editor) return;
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  const selection = window.getSelection();
  if (!selection) return;
  suppressSelectionCaptureUntil = Date.now() + PROGRAMMATIC_SELECTION_COOLDOWN_MS;
  selection.removeAllRanges();
  selection.addRange(range);
  activeCaretRange = range.cloneRange();
  activePromptParagraph = null;
  updateParagraphAssistState();
}

function restoreEditorHistoryHtml(html) {
  isRestoringEditorUndo = true;
  try {
    editor.innerHTML = String(html || "");
    syncAllParagraphAssistSlots();
    updateDraftStats();
    updateCurrentDraftPreview();
    setDeliveryStatus("unchecked");
    setBodySource("edited");
    scheduleSave();
    placeCaretAtEditorEnd();
    scheduleParagraphAssistInlineBarSync();
  } finally {
    isRestoringEditorUndo = false;
  }
}

function undoEditorChange() {
  if (!editorUndoStack.length) return false;
  const current = editorHistoryHtml();
  let previous = editorUndoStack.pop();
  while (previous === current && editorUndoStack.length) {
    previous = editorUndoStack.pop();
  }
  if (previous === current) return false;
  editorRedoStack.push(current);
  restoreEditorHistoryHtml(previous);
  return true;
}

function redoEditorChange() {
  if (!editorRedoStack.length) return false;
  const current = editorHistoryHtml();
  const next = editorRedoStack.pop();
  if (next === current) return false;
  editorUndoStack.push(current);
  trimEditorUndoStack();
  restoreEditorHistoryHtml(next);
  return true;
}

function handleEditorUndoShortcut(event) {
  if (!editor || !(event.metaKey || event.ctrlKey) || event.altKey) return;
  const key = event.key.toLowerCase();
  if (key !== "z" && key !== "y") return;
  if (!isInsideEditor(document.activeElement)) return;
  const handled = key === "y" || event.shiftKey ? redoEditorChange() : undoEditorChange();
  if (!handled) return;
  event.preventDefault();
  event.stopPropagation();
}

function currentDraftSnapshot(options = {}) {
  const workspaceDocumentId =
    options.workspaceDocumentId !== undefined ? normalizeText(options.workspaceDocumentId) : normalizeText(currentDocumentId);
  return {
    documentId: storageDocumentId(workspaceDocumentId || options.documentId),
    workspaceDocumentId,
    title: String(options.title ?? titleInput.value ?? ""),
    contentHtml: stripParagraphAssistSlotsFromHtml(String(options.contentHtml ?? editor.innerHTML ?? "")),
    updatedAt: String(options.updatedAt || new Date().toISOString()),
    workspaceUpdatedAt:
      options.workspaceUpdatedAt !== undefined ? String(options.workspaceUpdatedAt || "") : String(currentWorkspaceUpdatedAt || ""),
    dirty: options.dirty !== undefined ? Boolean(options.dirty) : true,
  };
}

function persistDraftSnapshot(snapshot) {
  const key = draftCacheKey(snapshot.workspaceDocumentId || snapshot.documentId);
  window.localStorage.setItem(key, JSON.stringify(snapshot));
}

function persistCurrentDraft(options = {}) {
  const snapshot = currentDraftSnapshot(options);
  persistDraftSnapshot(snapshot);
  if (!snapshot.workspaceDocumentId) {
    window.localStorage.setItem(legacyDraftKey, snapshot.contentHtml);
    window.localStorage.setItem(legacyTitleKey, snapshot.title);
  } else {
    clearLegacyDraftCache();
  }
  return snapshot;
}

function migrateLegacyDraft(documentId = currentDocumentId) {
  const existing = readDraftSnapshot(documentId);
  if (existing) return existing;
  const legacyDocumentId = normalizeText(window.localStorage.getItem(currentDocumentKey));
  const targetDocumentId = normalizeText(documentId);
  if (targetDocumentId && legacyDocumentId && legacyDocumentId !== targetDocumentId) return null;
  const saved = window.localStorage.getItem(legacyDraftKey);
  const savedTitle = window.localStorage.getItem(legacyTitleKey);
  if (!saved && !savedTitle) return null;
  const snapshot = {
    documentId: storageDocumentId(documentId),
    workspaceDocumentId: normalizeText(documentId),
    title: savedTitle || currentTitle(),
    contentHtml: saved || "",
    updatedAt: new Date().toISOString(),
    workspaceUpdatedAt: "",
    dirty: true,
  };
  persistDraftSnapshot(snapshot);
  return snapshot;
}

function applyDraftSnapshot(snapshot, options = {}) {
  if (!snapshot) return false;
  editor.innerHTML = stripParagraphAssistSlotsFromHtml(snapshot.contentHtml || "");
  resetEditorUndoHistory();
  titleInput.value = snapshot.title || "未命名稿件";
  currentWorkspaceUpdatedAt = snapshot.workspaceUpdatedAt || currentWorkspaceUpdatedAt || "";
  if (options.saveStateText) setSaveStateText(options.saveStateText, { quiet: Boolean(options.saveStateQuiet) });
  updateDraftStats();
  updateCurrentDraftPreview();
  return true;
}

function setSaveStateText(text = "", options = {}) {
  if (!saveStateNode) return;
  saveStateNode.textContent = text || "";
  if (options.quiet) {
    saveStateNode.dataset.quiet = "1";
  } else {
    delete saveStateNode.dataset.quiet;
  }
}

function hasLocalDraftChanges(snapshot, documentData) {
  if (!snapshot || snapshot.dirty === false) return false;
  const localTitle = normalizeText(snapshot.title);
  const remoteTitle = normalizeText(documentData?.title);
  const localHtml = stripParagraphAssistSlotsFromHtml(String(snapshot.contentHtml || "")).trim();
  const remoteHtml = stripParagraphAssistSlotsFromHtml(String(documentData?.contentHtml || "")).trim();
  const localTs = parseTimeValue(snapshot.updatedAt);
  const remoteTs = parseTimeValue(documentData?.updatedAt);
  const snapshotWorkspaceTs = parseTimeValue(snapshot.workspaceUpdatedAt);
  if (snapshotWorkspaceTs && remoteTs && remoteTs > snapshotWorkspaceTs) return false;
  const contentChanged = localTitle !== remoteTitle || localHtml !== remoteHtml;
  if (!contentChanged) return false;
  if (localTs && remoteTs) return localTs >= remoteTs;
  return true;
}

function selectedParagraphCount(text) {
  return String(text || "").split(/\n\s*\n+/).filter((part) => normalizeText(part)).length;
}

function selectionProblem(text) {
  const normalized = normalizeText(text);
  if (!normalized) return "先选一句。";
  if (normalized.length > maxRewriteSelectionChars || selectedParagraphCount(text) > maxRewriteSelectionParagraphs) {
    return "选区太长。改句只处理一句或一小段；整段问题先缩短选区。";
  }
  return "";
}

function hasUsableSelection() {
  return Boolean(activeSelection?.text && !selectionProblem(activeSelection.text));
}

function extractParagraphPrompt(text) {
  const raw = String(text || "").trim();
  if (!raw) return "";
  const patterns = [
    /^(待写|待补|补写|写段|补段|补写段|补)\s*[:：]\s*/i,
    /^(【\s*(?:待写|补段|写段)\s*】|\[\s*(?:待写|补段|写段)\s*\])\s*/i,
    /^(这里)?(补|写)(一段)?\s*[:：，,\s]+/i,
    /^(这段)?(想写|要写)\s*[:：，,\s]+/i,
    /^(写一些|写一段|补一些|补一段|加一些|加一段|展开写|继续写|解释一下|解释清楚|调研一下|研究一下|查一下|搜一下)\s*/i,
    /^todo\s*[:：]\s*/i,
    /^\/\/\s*/,
  ];
  for (const pattern of patterns) {
    if (pattern.test(raw)) return raw.replace(pattern, "").trim();
  }
  return "";
}

function manualParagraphAssistPrompt() {
  return normalizeText(paragraphAssistPromptInput?.value || "");
}

function setSelectionSummary(text = "", state = "待选", options = {}) {
  const idle = Boolean(options.idle);
  if (selectedTextNode) {
    selectedTextNode.textContent = text || "";
    selectedTextNode.hidden = idle || !text;
  }
  if (selectionStateNode) {
    selectionStateNode.textContent = state || "";
    selectionStateNode.hidden = idle || !state;
    selectionStateNode.dataset.state = idle ? "idle" : "active";
  }
  if (selectionBlockNode) selectionBlockNode.dataset.idle = idle ? "1" : "0";
}

function isParagraphAssistSlot(node) {
  return Boolean(node?.dataset?.paragraphAssistSlot === "1");
}

function paragraphAssistSlots() {
  return Array.from(editor.querySelectorAll('p[data-paragraph-assist-slot="1"]'));
}

function paragraphAssistSlotText(slot) {
  return normalizeText(slot?.innerText || "");
}

function pruneParagraphAssistSlots(preferredSlot = null) {
  const slots = paragraphAssistSlots();
  if (!slots.length) return null;
  const keep =
    (preferredSlot && slots.includes(preferredSlot) && preferredSlot) ||
    slots.find((slot) => paragraphAssistSlotText(slot)) ||
    null;
  if (!keep) {
    slots.forEach((slot) => slot.remove());
    return null;
  }
  slots.forEach((slot) => {
    if (slot === keep) return;
    if (!paragraphAssistSlotText(slot)) slot.remove();
  });
  return keep;
}

function editorBlockForNode(node) {
  let current = node && node.nodeType === Node.TEXT_NODE ? node.parentNode : node;
  while (current && current !== editor) {
    if (current.nodeType === Node.ELEMENT_NODE && /^(P|H2|LI|BLOCKQUOTE)$/i.test(current.tagName || "")) {
      return current;
    }
    current = current.parentNode;
  }
  return null;
}

function editorAllBlockNodes() {
  return Array.from(editor.querySelectorAll("p, h2, li, blockquote"));
}

function editorBlockNodes() {
  return editorAllBlockNodes().filter((node) => normalizeText(node.innerText || ""));
}

function paragraphGapTargetFromClientY(clientY) {
  const blocks = editorAllBlockNodes();
  for (let index = 0; index < blocks.length - 1; index += 1) {
    const currentRect = blocks[index].getBoundingClientRect();
    const nextRect = blocks[index + 1].getBoundingClientRect();
    if (clientY > currentRect.bottom && clientY < nextRect.top) {
      return { afterBlock: blocks[index], beforeBlock: blocks[index + 1], index };
    }
  }
  return null;
}

function neighboringParagraphText(blocks, startIndex, direction) {
  for (let index = startIndex + direction; index >= 0 && index < blocks.length; index += direction) {
    const text = normalizeText(blocks[index]?.innerText || "");
    if (text) return text;
  }
  return "";
}

function blockOffsets(node) {
  if (!node) return { start: -1, end: -1 };
  const range = document.createRange();
  range.selectNodeContents(node);
  return getTextOffsets(range);
}

function promptParagraphStateFromRange(range) {
  if (!range || !isInsideEditor(range.commonAncestorContainer)) return null;
  const block = editorBlockForNode(range.startContainer);
  if (!block) return null;
  const blockText = normalizeText(block.innerText || "");
  const isAssistSlot = isParagraphAssistSlot(block);
  const prompt = isAssistSlot ? blockText : extractParagraphPrompt(blockText);
  const blocks = editorAllBlockNodes();
  const paragraphIndex = blocks.indexOf(block);
  const offsets = blockOffsets(block);
  return {
    block,
    blockText,
    prompt,
    isAssistSlot,
    paragraphIndex,
    blockStart: offsets.start,
    blockEnd: offsets.end,
    previousParagraph: neighboringParagraphText(blocks, paragraphIndex, -1),
    nextParagraph: neighboringParagraphText(blocks, paragraphIndex, 1),
  };
}

function paragraphIndexFromRange(range) {
  if (!range || !isInsideEditor(range.commonAncestorContainer)) return -1;
  const block = editorBlockForNode(range.startContainer);
  if (!block) return -1;
  const blocks = editorAllBlockNodes();
  const paragraphIndex = blocks.indexOf(block);
  return paragraphIndex >= 0 ? paragraphIndex + 1 : -1;
}

function clearStaleAuditIssueForRange(range) {
  if (!currentAuditIssue || !Number.isInteger(currentAuditIssue.paragraphIndex)) return;
  const paragraphIndex = paragraphIndexFromRange(range);
  if (!Number.isInteger(paragraphIndex) || paragraphIndex <= 0) return;
  if (paragraphIndex === currentAuditIssue.paragraphIndex) return;
  currentAuditIssue = null;
  currentAuditIndex = -1;
  auditFlowDone = false;
  updateAuditIssueUi();
}

function hasUsablePromptParagraph() {
  return Boolean(activePromptParagraph?.prompt);
}

function isBlankParagraphAssistTarget() {
  return Boolean(activePromptParagraph?.block && activePromptParagraph?.isAssistSlot && !normalizeText(activePromptParagraph?.blockText || ""));
}

function isEmptyEditorParagraph(block) {
  return Boolean(
    block &&
    block.tagName === "P" &&
    !isParagraphAssistSlot(block) &&
    !normalizeText(block.innerText || "")
  );
}

function syncParagraphAssistSlotVisual(slot) {
  if (!slot || !isParagraphAssistSlot(slot)) return;
  const text = normalizeText(slot.innerText || "");
  const runState = slot.dataset.runState || "";
  slot.classList.add("paragraph-assist-slot");
  slot.dataset.empty = text ? "0" : "1";
  if (runState === "running") {
    slot.dataset.label = "补写中";
  } else if (runState === "ready") {
    slot.dataset.label = "有候选";
  } else if (runState === "failed") {
    slot.dataset.label = "失败";
  } else {
    slot.dataset.label = text ? "写作需求" : "待写段";
  }
  slot.dataset.placeholder = "写一句需求，按回车生成。例：这里接一下前后两段，补一个具体例子。";
}

function clearParagraphAssistSlotRunState(slot) {
  if (!slot || !isParagraphAssistSlot(slot)) return;
  delete slot.dataset.runState;
  delete slot.dataset.progress;
  slot.classList.remove("is-running", "is-ready", "is-failed");
  syncParagraphAssistSlotVisual(slot);
}

function setParagraphAssistSlotRunState(slot, state = "idle", message = "") {
  if (!slot || !isParagraphAssistSlot(slot)) return;
  slot.classList.remove("is-running", "is-ready", "is-failed");
  if (!state || state === "idle") {
    clearParagraphAssistSlotRunState(slot);
    return;
  }
  slot.dataset.runState = state;
  if (message) slot.dataset.progress = sanitizeVisibleModelText(message);
  else delete slot.dataset.progress;
  if (state === "running") slot.classList.add("is-running");
  if (state === "ready") slot.classList.add("is-ready");
  if (state === "failed") slot.classList.add("is-failed");
  syncParagraphAssistSlotVisual(slot);
}

function syncAllParagraphAssistSlots() {
  pruneParagraphAssistSlots(activePromptParagraph?.isAssistSlot ? activePromptParagraph.block : null);
  editor.querySelectorAll('p[data-paragraph-assist-slot="1"]').forEach((slot) => {
    syncParagraphAssistSlotVisual(slot);
  });
}

function currentParagraphAssistSlot() {
  const activeBlock = activePromptParagraph?.block;
  if (activeBlock && activePromptParagraph?.isAssistSlot && editor.contains(activeBlock)) return activeBlock;
  return null;
}

function briefParagraphAssistPrompt(prompt, max = 18) {
  const text = normalizeText(prompt || "");
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function setParagraphAssistPanel(state, hint) {
  if (paragraphAssistStateNode) paragraphAssistStateNode.textContent = sanitizeVisibleModelText(state || "");
  if (paragraphAssistHintNode) paragraphAssistHintNode.textContent = sanitizeVisibleModelText(hint || "");
}

function sanitizeParagraphAssistPromptText(value) {
  return String(value || "")
    .replace(/\r\n?/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/\n+/g, " ")
    .trim();
}

function normalizeClipboardText(value) {
  return String(value || "")
    .replace(/\r\n?/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    .trim();
}

function clipboardParagraphParts(value) {
  const text = normalizeClipboardText(value);
  if (!text) return [];
  const roughParts = text.includes("\n\n")
    ? text.split(/\n\s*\n+/)
    : text.split(/\n+/).filter((line) => normalizeText(line).length > 0);
  return roughParts.map((part) => normalizeText(part)).filter(Boolean);
}

function insertTextAtEditorSelection(text) {
  const content = String(text || "");
  if (!content) return false;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return false;
  const range = selection.getRangeAt(0);
  if (!isInsideEditor(range.commonAncestorContainer)) return false;
  range.deleteContents();
  const node = document.createTextNode(content);
  range.insertNode(node);
  range.setStartAfter(node);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
  return true;
}

function insertPlainTextAtEditorSelection(rawText) {
  const parts = clipboardParagraphParts(rawText);
  if (!parts.length) return false;
  if (parts.length === 1) return insertTextAtEditorSelection(parts[0]);
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return false;
  const range = selection.getRangeAt(0);
  if (!isInsideEditor(range.commonAncestorContainer)) return false;
  const block = editorBlockForNode(range.startContainer);
  const nodes = parts.map((part) => {
    const paragraph = document.createElement("p");
    paragraph.textContent = part;
    return paragraph;
  });
  recordEditorUndoBoundary();
  const selectedWholeBlock =
    block && !range.collapsed && normalizeText(range.toString()) === normalizeText(block.innerText || "");
  if (block && block !== editor && (selectedWholeBlock || normalizeText(block.innerText || "") === "")) {
    block.replaceWith(...nodes);
  } else if (block && /^(P|H2|LI|BLOCKQUOTE)$/i.test(block.tagName || "")) {
    range.deleteContents();
    const firstText = document.createTextNode(parts[0]);
    range.insertNode(firstText);
    let anchor = block;
    nodes.slice(1).forEach((node) => {
      anchor.insertAdjacentElement("afterend", node);
      anchor = node;
    });
  } else {
    range.deleteContents();
    const fragment = document.createDocumentFragment();
    nodes.forEach((node) => fragment.appendChild(node));
    range.insertNode(fragment);
  }
  const lastNode = nodes[nodes.length - 1];
  const nextRange = document.createRange();
  nextRange.selectNodeContents(lastNode);
  nextRange.collapse(false);
  selection.removeAllRanges();
  selection.addRange(nextRange);
  activeCaretRange = nextRange.cloneRange();
  return true;
}

function paragraphAssistSlotFromContext(target = null) {
  const eventSlot = target?.closest?.('p[data-paragraph-assist-slot="1"]');
  if (eventSlot && editor.contains(eventSlot)) return eventSlot;
  const selection = window.getSelection();
  if (selection?.rangeCount) {
    const block = editorBlockForNode(selection.getRangeAt(0).startContainer);
    if (isParagraphAssistSlot(block)) return block;
  }
  const currentSlot = currentParagraphAssistSlot();
  if (currentSlot) return currentSlot;
  const slots = paragraphAssistSlots();
  if (slots.length === 1 && document.activeElement === editor) return slots[0];
  return null;
}

function syncParagraphAssistPanelVisibility() {
  if (!paragraphAssistBlockNode) return;
  paragraphAssistBlockNode.hidden = true;
}

function dismissEmptyParagraphAssistSlots(options = {}) {
  const persist = Boolean(options.persist);
  let removed = false;
  paragraphAssistSlots().forEach((slot) => {
    if (paragraphAssistSlotText(slot)) return;
    if (activePromptParagraph?.block === slot) {
      activePromptParagraph = null;
      activeCaretRange = null;
    }
    slot.remove();
    removed = true;
  });
  if (!removed) return false;
  hideParagraphAssistInlineBar();
  syncParagraphAssistPanelVisibility();
  if (persist) {
    markDraftChanged({ clearRewrite: false });
    scheduleSave();
  }
  return true;
}

function syncStyleProofVisibility(show = false) {
  if (!proofFoldNode) return;
  proofFoldNode.hidden = !show;
  if (!show) proofFoldNode.open = false;
}

function setAuditSummary(text = "", state = "") {
  if (!auditSummaryNode) return;
  auditSummaryNode.textContent = text || "";
  if (state) auditSummaryNode.dataset.state = state;
  else delete auditSummaryNode.dataset.state;
}

function hideParagraphAssistInlineBar() {
  return;
}

function syncParagraphAssistInlineBar() {
  return;
}

function scheduleParagraphAssistInlineBarSync() {
  return;
}

function updateSelectionActionState() {
  const enabled = hasUsableSelection();
  if (selectionBlockNode) {
    selectionBlockNode.hidden = true;
    selectionBlockNode.dataset.visible = "0";
  }
  [quickRewriteAction, runRewriteButton, saveBadButton, saveGoodButton].forEach((button) => {
    if (!button) return;
    button.disabled = !enabled;
    button.setAttribute("aria-disabled", enabled ? "false" : "true");
  });
  refreshRewriteSurface();
}

function rewriteSurfaceHasContent() {
  if (!candidateListNode) return false;
  if (candidateListNode.classList.contains("is-loading")) return true;
  if (candidateListNode.querySelector(".candidate, .rewrite-loading-card, .candidate-label")) return true;
  const text = normalizeText(candidateListNode.textContent || "");
  return Boolean(text) && text !== "暂无候选。";
}

function refreshRewriteSurface() {
  const hasCandidateSurface = rewriteSurfaceHasContent();
  const showActionDetail = false;
  const showRewriteContext = Boolean(currentAuditIssue);
  document.body.dataset.resultPanel = hasCandidateSurface ? "visible" : "hidden";
  if (sideNode) sideNode.hidden = !hasCandidateSurface;
  if (actionDetailNode) {
    actionDetailNode.hidden = !showActionDetail;
    if (!showActionDetail) actionDetailNode.removeAttribute("open");
  }
  if (rewriteContextNode) rewriteContextNode.hidden = !showRewriteContext;
  if (candidateListNode) candidateListNode.hidden = !hasCandidateSurface;
}

function updateParagraphAssistState() {
  if (!paragraphAssistAction || !paragraphAssistStateNode || !paragraphAssistHintNode) return;
  syncAllParagraphAssistSlots();
  syncParagraphAssistPanelVisibility();
  editor.querySelectorAll(".paragraph-assist-slot").forEach((slot) => slot.classList.remove("is-active"));
  if (Date.now() < paragraphAssistRecentlyAppliedUntil && paragraphAssistStateNode.textContent === "已补段") {
    if (paragraphAssistPromptInput) paragraphAssistPromptInput.hidden = true;
    paragraphAssistAction.disabled = true;
    hideParagraphAssistInlineBar();
    return;
  }
  const blankTarget = isBlankParagraphAssistTarget();
  if (paragraphAssistPromptInput) paragraphAssistPromptInput.hidden = true;
  if (!activeCaretRange || !activePromptParagraph) {
    paragraphAssistAction.disabled = true;
    setParagraphAssistPanel("待写段", "双击正文空白插一段。");
    scheduleParagraphAssistInlineBarSync();
    return;
  }
  if (blankTarget) {
    paragraphAssistAction.disabled = true;
    setParagraphAssistPanel("写需求", "在正文里写需求。");
    activePromptParagraph.block?.classList.add("is-active");
    scheduleParagraphAssistInlineBarSync();
    return;
  }
  if (activePromptParagraph?.isAssistSlot) {
    paragraphAssistAction.disabled = false;
    setParagraphAssistPanel("可补写", `将结合上下段补写：${briefParagraphAssistPrompt(activePromptParagraph.prompt)}`);
    activePromptParagraph.block?.classList.add("is-active");
    scheduleParagraphAssistInlineBarSync();
    return;
  }
  if (!activePromptParagraph.prompt) {
    paragraphAssistAction.disabled = true;
    setParagraphAssistPanel("待写段", "把光标点进待写段。");
    activePromptParagraph.block?.classList.remove("is-active");
    hideParagraphAssistInlineBar();
    return;
  }
  paragraphAssistAction.disabled = false;
  setParagraphAssistPanel("可补写", `将结合上下段补写：${briefParagraphAssistPrompt(activePromptParagraph.prompt)}`);
  activePromptParagraph.block?.classList.remove("is-active");
  hideParagraphAssistInlineBar();
}

function maybeDismissIdleParagraphAssist(event) {
  const slots = paragraphAssistSlots();
  if (!slots.length) return;
  const target = event.target;
  const insideSlot = slots.some((slot) => slot.contains(target));
  const insideAssistPanel = paragraphAssistBlockNode?.contains(target);
  if (insideSlot || insideAssistPanel) return;
  window.setTimeout(() => {
    if (Date.now() < paragraphAssistRecentlyActivatedUntil) return;
    if (!dismissEmptyParagraphAssistSlots({ persist: true })) return;
    updateParagraphAssistState();
  }, 220);
}

function clearActiveSelection({ clearPending = false } = {}) {
  activeRange = null;
  activeSelection = null;
  selectionMenu.hidden = true;
  updateSelectionActionState();
  updateParagraphAssistState();
  if (clearPending) window.localStorage.removeItem(pendingJobKey);
}

function clearCandidateSurfaceForNewSelection(nextText = "") {
  if (!candidateListNode) return;
  const next = normalizeText(nextText);
  const previous = normalizeText(candidateListNode.dataset.selectedText || "");
  const hasRewriteSurface = candidateListNode.dataset.surface === "rewrite" && rewriteSurfaceHasContent();
  if (!hasRewriteSurface && !previous) return;
  if (previous && previous === next) return;
  rewriteRunId += 1;
  window.clearInterval(activeJobTimer);
  window.localStorage.removeItem(pendingJobKey);
  setBusy(false);
  candidateListNode.dataset.surface = "idle";
  delete candidateListNode.dataset.selectedText;
  candidateListNode.textContent = "暂无候选。";
  if (jobStateNode) jobStateNode.textContent = "";
  refreshRewriteSurface();
}

function candidateRepeatsBadFrame(candidateText, selectedText) {
  const candidate = normalizeText(candidateText);
  const selected = normalizeText(selectedText);
  if (!candidate) return true;
  const structural = candidate.replace(/[。；;，,\s`"'“”]/g, "");
  if (!structural) return true;
  if (candidate.includes("\\")) return true;
  if (/\\["']|["']\s*[,}\]]/.test(candidate)) return true;
  if (/["']$/.test(candidate.trim())) return true;
  if (/^[{}\[\]():：,]+$/.test(structural)) return true;
  if (/^[{}\[\],]/.test(candidate)) return true;
  if (/^["“”']?(variants|variant|move|label|text|reason|schema|task|json_example)["“”']?\s*[:：]/i.test(candidate)) return true;
  if (
    !/[\u4e00-\u9fff]/.test(candidate) &&
    /^[A-Za-z0-9_"'{}\[\],:：\s.-]+$/.test(candidate)
  ) {
    return true;
  }
  if (selected && candidate === selected) return true;
  if (selected && candidate.includes(selected) && candidate.length <= selected.length + 12) return true;
  if (/这句还缺|把抽象判断|避免像孤立金句|先回答一个具体问题|先移除提示语|先把人、动作和后果|先让这句话接住|接回上下文/.test(candidate)) return true;
  if (/\b(concretize|oralize|source-ground|workflow|style memory|gate)\b/i.test(candidate)) return true;
  if (/^(打开它|点开它|看这句|这句话|这个系统|这套系统|这个工作台|这套工作台)[，,]/.test(candidate) && !/^(打开它|点开它)/.test(selected)) return true;
  if (
    candidate.length <= 24 &&
    !/[。！？!?；;]/.test(candidate) &&
    /(工作台|系统|流程|能力|入口|动作|判断|记录|偏好|风格库)$/.test(candidate) &&
    !/(做|搭|放|记|改|写|用|看|选|点|拦|救|收进|变成)/.test(candidate)
  ) {
    return true;
  }
  if (/(补出读者能看到的对象|动作或结果|不像正文|像半句|没落正文|下次怎么避开|下次优先)/.test(candidate)) return true;
  if (selected.includes("往往") && candidate.includes("往往")) return true;
  if (selected.includes("第一屏") && candidate.includes("第一屏")) return true;
  if (
    selected.includes("第一屏") &&
    /(问题|麻烦).{0,8}(出现在|发生在|从).{0,8}(开头|第一段|第一步)/.test(candidate)
  ) {
    return true;
  }
  return false;
}

function candidateSimilarity(left, right) {
  const compact = (value) => normalizeText(value).replace(/[^\w\u4e00-\u9fff]+/g, "");
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
}

function candidateTooSimilar(candidateText, acceptedTexts = []) {
  return acceptedTexts.some((text) => candidateSimilarity(candidateText, text) >= 0.82);
}

function candidateRepeatsLede(candidateText, acceptedTexts = [], prefixChars = 6) {
  const candidate = normalizeText(candidateText);
  if (!candidate || candidate.length < prefixChars) return false;
  const lede = candidate.slice(0, prefixChars);
  return acceptedTexts.some((text) => normalizeText(text).startsWith(lede));
}

function candidateIsSelectedFragment(candidateText, selectedText) {
  const candidate = normalizeText(candidateText);
  const selected = normalizeText(selectedText);
  if (!candidate || !selected) return false;
  return selected.includes(candidate) && candidate.length < Math.max(24, selected.length * 0.72);
}

function candidateTooCloseToSelected(candidateText, selectedText) {
  const candidate = normalizeText(candidateText);
  const selected = normalizeText(selectedText);
  if (!candidate || !selected) return false;
  const similarity = candidateSimilarity(candidate, selected);
  if (selected.length >= 80) return similarity >= 0.86;
  if (selected.length >= 35) return similarity >= 0.92;
  return similarity >= 0.96;
}

function usefulCandidates(variants = [], selectedText = "") {
  const seen = new Set();
  const accepted = [];
  return variants.filter((variant) => {
    const text = normalizeText(variant?.text || "");
    if (candidateRepeatsBadFrame(text, selectedText)) return false;
    if (candidateIsSelectedFragment(text, selectedText)) return false;
    if (candidateTooCloseToSelected(text, selectedText)) return false;
    if (candidateTooSimilar(text, accepted)) return false;
    if (candidateRepeatsLede(text, accepted)) return false;
    if (seen.has(text)) return false;
    seen.add(text);
    accepted.push(text);
    return true;
  });
}

function relaxedCandidates(variants = [], selectedText = "") {
  const selected = normalizeText(selectedText);
  const seen = new Set();
  const accepted = [];
  return (variants || []).filter((variant) => {
    const text = normalizeText(variant?.text || "");
    if (!text) return false;
    if (candidateRepeatsBadFrame(text, selectedText)) return false;
    if (candidateIsSelectedFragment(text, selectedText)) return false;
    if (selected && text === selected) return false;
    if (seen.has(text)) return false;
    if (accepted.some((item) => candidateSimilarity(text, item) >= 0.94)) return false;
    seen.add(text);
    accepted.push(text);
    return true;
  });
}

function displayMove(move = "") {
  const labels = {
    "plain-language": "说人话",
    "de-jargon": "少术语",
    "change-frame": "换说法",
    rewrite: "换说法",
    replace: "换说法",
    concretize: "变清楚",
    oralize: "更顺口",
    "less-ai": "去套话",
    "source-ground": "接前后文",
    "reader-action": "补动作",
    mechanism: "说清楚",
    compress: "压缩",
    split: "拆段",
    sharpen: "压出态度",
  };
  return labels[move] || "候选";
}

function plainText() {
  const shell = editor.cloneNode(true);
  shell.querySelectorAll?.('p[data-paragraph-assist-slot="1"]').forEach((node) => node.remove());
  return shell.innerText || "";
}

function bodyParagraphText() {
  const paragraphs = Array.from(editor.querySelectorAll("p"))
    .filter((node) => !isParagraphAssistSlot(node))
    .map((node) => normalizeText(node.innerText || ""))
    .filter(Boolean);
  return paragraphs.join("\n\n") || plainText();
}

function draftCharacterCount(text = bodyParagraphText()) {
  return normalizeText(text).replace(/\s/g, "").length;
}

function estimatedSpeechMinutes(charCount) {
  if (!charCount) return 0;
  return Math.max(1, Math.round(charCount / 180));
}

function draftStatsLabel() {
  const count = draftCharacterCount();
  const minutes = estimatedSpeechMinutes(count);
  return minutes ? `${count} 字 · 约 ${minutes} 分钟` : "0 字";
}

function updateDraftStats() {
  if (!draftStatsNode) return;
  draftStatsNode.textContent = draftStatsLabel();
}

function setDeliveryStatus(state = "unchecked", detail = "") {
  deliveryState = state;
  if (!deliveryStatusNode) return;
  const labels = {
    unchecked: "未查",
    checking: "检查中",
    blocked: "有硬伤",
    review: "快检完成",
  };
  deliveryStatusNode.className = `delivery-status ${state}`;
  deliveryStatusNode.textContent = detail ? `${labels[state] || labels.unchecked} · ${detail}` : labels[state] || labels.unchecked;
  deliveryStatusNode.hidden = state === "unchecked";
}

function deliveryStateFromAudits(tasteResult, aiResult) {
  const findings = [
    ...((tasteResult && tasteResult.findings) || []),
    ...((aiResult && aiResult.findings) || []),
  ].filter((item) => item && item.kind !== "pass");
  const high = findings.filter((item) => item.level === "high").length;
  const medium = findings.filter((item) => item.level === "medium").length;
  const needsDemo = findings.some((item) => String(item.kind || "").startsWith("missing-demo"));
  if (needsDemo) return { state: "blocked", detail: "需要补演示" };
  if (high > 0) return { state: "blocked", detail: `${high} 条高风险` };
  if (medium > 0) return { state: "blocked", detail: `${medium} 条中风险` };
  return { state: "review", detail: "未扫到明显硬伤" };
}

function clearRewriteResults(message = "暂无候选。", options = {}) {
  if (options.invalidate !== false) rewriteRunId += 1;
  window.clearInterval(activeJobTimer);
  window.localStorage.removeItem(pendingJobKey);
  setBusy(false);
  candidateListNode.textContent = message;
  if (options.jobMessage) jobStateNode.textContent = options.jobMessage;
  if (options.clearSelection) {
    clearActiveSelection();
    setSelectionSummary("选一句。", "待选", { idle: true });
  } else {
    updateSelectionActionState();
  }
}

function markDraftChanged(options = {}) {
  updateDraftStats();
  setDeliveryStatus("unchecked");
  clearAuditMarks();
  renderStyleProof(null);
  if (options.clearRewrite !== false) {
    const hadCandidateSurface = candidateListNode?.dataset?.surface !== "idle" && rewriteSurfaceHasContent();
    clearRewriteResults(options.rewriteMessage || "暂无候选。", {
      clearSelection: Boolean(options.clearSelection),
      jobMessage: options.jobMessage || "",
    });
    if (options.notifyInvalidated && hadCandidateSurface) {
      const now = Date.now();
      if (now - rewriteInvalidatedToastAt > 1800) {
        rewriteInvalidatedToastAt = now;
        showWorkspaceToast("正文已改，旧候选已失效。");
      }
    }
  }
}

function updateCurrentDraftPreview() {
  if (!currentDraftPreviewNode) return;
  const text = bodyParagraphText();
  currentDraftPreviewNode.textContent = text ? `${currentTitle()}\n\n${text}` : "当前还没有正文。";
}

function currentTitle() {
  return normalizeText(titleInput.value) || "未命名稿件";
}

function presentationParagraphs() {
  return bodyParagraphText()
    .split(/\n{2,}/)
    .map((item) => normalizeText(item))
    .filter(Boolean);
}

function presentationSpeedValue() {
  return Math.max(0, Number(presentationSpeedInput?.value || 0));
}

function presentationSpeedFactor() {
  return presentationSpeedValue() / 100;
}

function presentationPixelsPerSecond() {
  const factor = presentationSpeedFactor();
  if (factor <= 0) return 0;
  const fontSize = Number(presentationFontSizeInput?.value || 48);
  const basePixelsPerSecond = Math.max(30, Math.min(54, fontSize * 0.82));
  return Math.round(basePixelsPerSecond * factor);
}

function presentationSpeedLabel() {
  const factor = presentationSpeedFactor();
  if (factor <= 0) return "停";
  return `${factor.toFixed(1)}x`;
}

function updatePresentationStats() {
  const fontSize = Number(presentationFontSizeInput?.value || 48);
  if (presentationFontValueNode) presentationFontValueNode.textContent = String(fontSize);
  if (presentationSpeedValueNode) presentationSpeedValueNode.textContent = presentationSpeedLabel();
  if (!presentationStatsNode) return;
  const charCount = draftCharacterCount();
  const pixelsPerSecond = presentationPixelsPerSecond();
  const scrollDistance = presentationViewportNode
    ? Math.max(0, presentationViewportNode.scrollHeight - presentationViewportNode.clientHeight)
    : 0;
  const roughMinutes = pixelsPerSecond && scrollDistance
    ? Math.max(1, Math.round(scrollDistance / pixelsPerSecond / 60))
    : 0;
  presentationStatsNode.textContent = roughMinutes ? `${charCount} 字 · 约 ${roughMinutes} 分钟` : `${charCount} 字`;
}

function updatePresentationSettings() {
  if (!presentationModeNode) return;
  const fontSize = Number(presentationFontSizeInput?.value || 48);
  presentationModeNode.style.setProperty("--presentation-font-size", `${fontSize}px`);
  updatePresentationStats();
}

function setPresentationPlaying(nextPlaying) {
  presentationPlaying = Boolean(nextPlaying);
  if (presentationPlayButton) presentationPlayButton.textContent = presentationPlaying ? "暂停" : "开始";
  if (presentationPlaying) {
    presentationLastFrameAt = performance.now();
    presentationScrollPosition = Number(presentationViewportNode?.scrollTop || 0);
    window.cancelAnimationFrame(presentationFrame);
    presentationFrame = window.requestAnimationFrame(stepPresentationScroll);
  } else {
    window.cancelAnimationFrame(presentationFrame);
    presentationFrame = 0;
  }
}

function stepPresentationScroll(timestamp) {
  if (!presentationPlaying || !presentationViewportNode) return;
  const deltaSeconds = Math.max(0, (timestamp - presentationLastFrameAt) / 1000);
  presentationLastFrameAt = timestamp;
  const pixelsPerSecond = presentationPixelsPerSecond();
  if (pixelsPerSecond > 0) {
    presentationScrollPosition += pixelsPerSecond * deltaSeconds;
    presentationViewportNode.scrollTop = presentationScrollPosition;
  }
  const atEnd = presentationViewportNode.scrollTop + presentationViewportNode.clientHeight >= presentationViewportNode.scrollHeight - 4;
  if (atEnd) {
    setPresentationPlaying(false);
    return;
  }
  presentationFrame = window.requestAnimationFrame(stepPresentationScroll);
}

function resetPresentationScroll() {
  presentationScrollPosition = 0;
  if (presentationViewportNode) presentationViewportNode.scrollTop = presentationScrollPosition;
  presentationLastFrameAt = performance.now();
}

function renderPresentationText() {
  if (!presentationTextNode) return false;
  const title = currentTitle();
  const paragraphs = presentationParagraphs();
  presentationTextNode.replaceChildren();
  const heading = document.createElement("h1");
  heading.textContent = title;
  presentationTextNode.append(heading);
  paragraphs.forEach((paragraph) => {
    const node = document.createElement("p");
    node.textContent = paragraph;
    presentationTextNode.append(node);
  });
  if (presentationTitleNode) presentationTitleNode.textContent = title;
  updatePresentationStats();
  return paragraphs.length > 0;
}

async function enterPresentationMode() {
  if (!presentationModeNode) return;
  if (!renderPresentationText()) {
    showWorkspaceToast("正文为空，先写稿再演示。", "error");
    return;
  }
  updatePresentationSettings();
  presentationModeNode.hidden = false;
  presentationModeNode.setAttribute("aria-hidden", "false");
  resetPresentationScroll();
  try {
    if (presentationModeNode.requestFullscreen && !document.fullscreenElement) {
      await presentationModeNode.requestFullscreen();
    }
  } catch (_) {
    // Fullscreen may be blocked by the browser; the fixed overlay still works.
  }
  setPresentationPlaying(false);
  presentationPlayButton?.focus({ preventScroll: true });
}

function exitPresentationMode() {
  if (!presentationModeNode) return;
  setPresentationPlaying(false);
  presentationModeNode.hidden = true;
  presentationModeNode.setAttribute("aria-hidden", "true");
  if (document.fullscreenElement === presentationModeNode) {
    void document.exitFullscreen().catch(() => {});
  }
}

function handlePresentationKeydown(event) {
  if (!presentationModeNode || presentationModeNode.hidden) return;
  if (event.key === " " || event.code === "Space") {
    event.preventDefault();
    setPresentationPlaying(!presentationPlaying);
  }
  if (event.key === "Escape") {
    event.preventDefault();
    exitPresentationMode();
  }
  if (event.key === "Home") {
    event.preventDefault();
    resetPresentationScroll();
  }
}

function cowriteDraftText() {
  return "value" in cowriteSectionDraftNode
    ? cowriteSectionDraftNode.value
    : cowriteSectionDraftNode.textContent || "";
}

function setCowriteDraftText(text = "", placeholder = "还没有段落稿。") {
  latestCowriteSection = text;
  if ("value" in cowriteSectionDraftNode) {
    cowriteSectionDraftNode.value = text;
    cowriteSectionDraftNode.placeholder = placeholder;
  } else {
    cowriteSectionDraftNode.textContent = text || placeholder;
  }
}

function startCardInputs() {
  return [
    draftBriefInput,
    draftClaimInput,
    draftSourcesInput,
    draftReaderObjectionInput,
    draftAvoidShapeInput,
    draftAuthorTakeInput,
    draftNoInventInput,
  ].filter(Boolean);
}

function startCardHasUserText() {
  return startCardInputs().some((input) => normalizeText(input.value || ""));
}

function inferredStartCard() {
  const title = currentTitle();
  const body = bodyParagraphText();
  const context = `${title}\n${body}`;
  const isWritingWorkbench = /AI\s*写作|写作工作台|写作系统|去\s*AI\s*味|ai味|风格库|Kimi|DeepSeek|Codex/i.test(context);
  if (isWritingWorkbench) {
    return {
      brief: "写一篇视频稿：从一句 AI 直写坏句、一个删不掉的开头，或一次划选改句进入。先说 AI 写作为什么经常不好用，再查原因和主流解法，紧接着引出我的写作工作台怎么把这些解法落地。",
      claim: "好稿不是靠一次生成，而是先把判断、材料和退稿权放到模型前面。",
      sources: "失败样本：AI 直写常见套话，比如“当前行业正在快速发展，创作者需要积极拥抱变化，提升自身竞争力”；研究锚点：79 篇实证研究、96 项自动写作评估、Axios 2026、STORM、PaperDebugger、CoAuthor；前后对比样本：直出版坏句 -> 被拦原因 -> 修后版本；读者代价：不用这套系统，最常见的是整篇返工、找不到该删哪一句、最后只能整段重写；当前工作台动作：划选改句、风格库、后台审计、导出、主笔接口 / 改句接口 / 收稿检查分工。",
      readerObjection: "读者会觉得写文章不该这么费劲，也会怀疑这是不是又一套复杂提示词。",
      avoidShape: "不能写成 AI 写作技巧合集、产品说明书、模型排行，也不能只讲按钮功能。",
      authorTake: "我的态度是少相信一键生成，把写作前的判断、写作中的退稿、写作后的风格记忆固定下来。",
      noInvent: "不要编用户数据、测试数据、论文年份、模型结论、读者反馈。",
    };
  }
  return {
    brief: `围绕「${title}」写一篇个人 IP 稿：先给具体问题，再查材料和反对意见，最后落到我的判断。`,
    claim: "先给出一个能被反驳、能被验证的判断，不写成泛泛总结。",
    sources: body.length > 240 ? "当前正文和已保存材料；如涉及最新事实，先由 Codex 补来源。" : "待补：3 个具体材料、例子、原句、数据或经历。",
    readerObjection: "读者可能会问：这和我有什么关系？证据够不够？为什么现在要听这个？",
    avoidShape: "不能写成新闻稿、百科总结、工具说明书、空泛方法论或 AI 味金句。",
    authorTake: "我的态度要明确：哪些值得做，哪些先别跟风，读者看完能做一个小判断。",
    noInvent: "不要编数据、私人经历、评论反馈、测试结果或不存在的来源。",
  };
}

function fillStartCard({ force = false } = {}) {
  if (!force && startCardHasUserText()) {
    if (startCardHintNode) startCardHintNode.textContent = "已有起点卡内容；不会自动覆盖。需要重填可点“Codex 先填”。";
    return false;
  }
  const card = inferredStartCard();
  draftBriefInput.value = card.brief;
  draftClaimInput.value = card.claim;
  draftSourcesInput.value = card.sources;
  if (draftReaderObjectionInput) draftReaderObjectionInput.value = card.readerObjection;
  if (draftAvoidShapeInput) draftAvoidShapeInput.value = card.avoidShape;
  if (draftAuthorTakeInput) draftAuthorTakeInput.value = card.authorTake;
  draftNoInventInput.value = card.noInvent;
  if (startCardHintNode) startCardHintNode.textContent = "已按当前主题填好；你只需要确认或微调。";
  return true;
}

function fullDraftMaterialCard() {
  return {
    brief: draftBriefInput.value.trim(),
    claim: draftClaimInput.value.trim(),
    sources: draftSourcesInput.value.trim(),
    readerObjection: draftReaderObjectionInput?.value.trim() || "",
    avoidShape: draftAvoidShapeInput?.value.trim() || "",
    authorTake: draftAuthorTakeInput?.value.trim() || "",
    noInvent: draftNoInventInput.value.trim(),
  };
}

function fullDraftBriefText(card = fullDraftMaterialCard()) {
  return [
    card.brief ? `写作目标：${card.brief}` : "",
    card.claim ? `一句话判断：${card.claim}` : "",
    card.sources ? `具体材料：${card.sources}` : "",
    card.readerObjection ? `读者反驳：${card.readerObjection}` : "",
    card.avoidShape ? `不能写成：${card.avoidShape}` : "",
    card.authorTake ? `作者态度：${card.authorTake}` : "",
    card.noInvent ? `不能编：${card.noInvent}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

function styleCardTopic() {
  return [currentTitle(), fullDraftBriefText()].filter(Boolean).join("\n");
}

function setDocumentMeta({ state = "", path = "", documentType = currentDocumentType, showType = true, metadata = currentDocumentMetadata } = {}) {
  currentDocumentType = normalizeDocumentType(documentType || currentDocumentType);
  if (metadata && typeof metadata === "object") currentDocumentMetadata = metadata;
  if (state) {
    documentStateNode.textContent = showType ? `${documentTypeLabel(currentDocumentType)} · ${state}` : state;
  }
  if (path || currentDocumentId) documentPathNode.textContent = path || `当前文档：${currentDocumentId}`;
  if (provenanceStateNode) {
    provenanceStateNode.textContent = formatDocumentProvenance(currentDocumentMetadata);
  }
}

function isInsideEditor(node) {
  return node && (node === editor || editor.contains(node));
}

function getTextOffsets(range) {
  const pre = range.cloneRange();
  pre.selectNodeContents(editor);
  pre.setEnd(range.startContainer, range.startOffset);
  const start = pre.toString().length;
  return { start, end: start + range.toString().length };
}

function setBusy(isBusy) {
  runRewriteButton.disabled = isBusy;
  quickRewriteAction.disabled = isBusy || !hasUsableSelection();
  if (paragraphAssistAction) paragraphAssistAction.disabled = isBusy || !hasUsablePromptParagraph();
  candidateListNode.classList.toggle("is-loading", isBusy);
  quickRewriteAction.classList.toggle("is-loading", isBusy);
  runRewriteButton.classList.toggle("is-loading", isBusy);
  quickRewriteAction.textContent = isBusy ? "改句中..." : "改句";
  runRewriteButton.textContent = isBusy ? "模型改写中..." : "按当前方式改";
  document.querySelectorAll(".mode").forEach((button) => {
    button.disabled = isBusy;
  });
  scheduleParagraphAssistInlineBarSync();
  refreshRewriteSurface();
}

function setGenerateBusy(isBusy, stateText = "") {
  generateOpeningsButton.disabled = isBusy;
  generateDraftButton.disabled = isBusy;
  if (runPreflightButton) runPreflightButton.disabled = isBusy;
  loadGeneratedButton.disabled = isBusy;
  if (loadGeneratedTopButton) loadGeneratedTopButton.disabled = isBusy || !latestGeneratedPayload();
  if (syncLatestButton) syncLatestButton.disabled = isBusy;
  if (stateText) generateStateNode.textContent = stateText;
}

function setGenerateProgress({ status = "idle", title = "生成空闲", detail = "", elapsed = 0, progress = 0, cancellable = false } = {}) {
  if (!generateProgressNode) return;
  generateProgressNode.className = `generation-status ${status}`;
  generateProgressTitleNode.textContent = title;
  generateElapsedNode.textContent = `${Math.max(0, Math.round(elapsed))}s`;
  generateProgressDetailNode.textContent =
    detail || "后台链路：整理任务书 / 主笔接口写稿 / 自动收稿检查。";
  generateProgressBarNode.style.width = `${Math.max(0, Math.min(100, progress))}%`;
  cancelGenerateButton.hidden = !cancellable;
}

function stopGenerateTimer() {
  window.clearInterval(generateTimer);
  generateTimer = null;
}

function startGenerateTimer({ provider, promptMode }) {
  stopGenerateTimer();
  generateStartedAt = Date.now();
  const providerLabel = draftProviderLabel(provider);
  const modeLabel = promptMode === "pure_ds" ? "自由提示" : "工作台约束";
  setGenerateProgress({
    status: "running",
    title: "正在生成全文",
    detail: `${providerLabel} · ${modeLabel}。前 30 秒正常，超过 90 秒会提示慢任务。`,
    elapsed: 0,
    progress: 8,
    cancellable: true,
  });
  generateTimer = window.setInterval(() => {
    const elapsed = Math.round((Date.now() - generateStartedAt) / 1000);
    let status = "running";
    let title = "正在生成全文";
    let detail = `${providerLabel} · ${modeLabel}。正在等主笔接口返回。`;
    let progress = Math.min(88, 10 + elapsed * 1.15);
    if (elapsed >= 30) {
      detail = "还在跑。深度思考可能会慢，可以继续等，也可以取消前端等待。";
      progress = Math.min(92, 45 + elapsed * 0.45);
    }
    if (elapsed >= 90) {
      status = "warn";
      title = "生成较慢";
      detail = "已经超过 90 秒。主笔接口还在返回；可以继续等，也可以取消前端等待，稍后取回。";
      progress = 94;
    }
    setGenerateProgress({ status, title, detail, elapsed, progress, cancellable: true });
  }, 1000);
}

function finishGenerateProgress(result, provider, promptMode) {
  stopGenerateTimer();
  const elapsed = generateStartedAt ? Math.round((Date.now() - generateStartedAt) / 1000) : 0;
  const providerLabel = draftProviderLabel(provider, true);
  const modeLabel = promptMode === "pure_ds" ? "自由提示" : "工作台约束";
  const modelFailed = Boolean(result?.externalModelFailed || result?.modelError);
  const codexGateStatus = String(result?.codexGate?.status || "");
  const gateStatus = codexGateStatus === "pending" ? "终审中" : result?.qualityGate?.status === "allow" ? "通过" : "未过";
  setGenerateProgress({
    status: modelFailed ? "error" : codexGateStatus === "pending" ? "running" : result?.qualityGate?.status === "allow" ? "done" : "warn",
    title: modelFailed ? "主笔失败：没有正文" : `生成完成：${gateStatus}`,
    detail: modelFailed
      ? `${providerLabel} · ${modeLabel}。${result?.supportError || result?.modelError || "外部模型没有返回正文。"}`
      : codexGateStatus === "pending"
        ? `${providerLabel} · ${modeLabel} · ${result?.model || "model"} · thinking ${result?.thinking || "unknown"}。正文已载入，Codex 正在后台终审。`
        : `${providerLabel} · ${modeLabel} · ${result?.model || "model"} · thinking ${result?.thinking || "unknown"}。${result?.qualityGate?.status === "allow" ? "已载入正文。" : "未载入正文，先看细节。"}`,
    elapsed,
    progress: codexGateStatus === "pending" ? 96 : 100,
    cancellable: false,
  });
}

function failGenerateProgress(error) {
  stopGenerateTimer();
  const elapsed = generateStartedAt ? Math.round((Date.now() - generateStartedAt) / 1000) : 0;
  const message = error?.name === "AbortError" ? "已取消前端等待。后台若已发出请求，稍后可点“版本 / 刷新”取回。" : `生成失败：${error?.message || error}`;
  setGenerateProgress({
    status: error?.name === "AbortError" ? "warn" : "error",
    title: error?.name === "AbortError" ? "已取消等待" : "生成失败",
    detail: message,
    elapsed,
    progress: error?.name === "AbortError" ? 55 : 100,
    cancellable: false,
  });
}

function formatGeneratedProvenance(payload) {
  if (!payload) return "来源：未生成。";
  if (payload.externalModelFailed || payload.modelError) {
    return `来源：主笔失败 / ${payload.supportError || payload.modelError || "没有正文"}`;
  }
  const engine = String(payload.engine || "");
  const thinking = String(payload.thinking || "unknown");
  const role = engine === "hybrid"
    ? "主笔接口写稿 / 复核接口改句 / 收稿检查"
    : engine === "kimi"
      ? "旧主笔路线 / 收稿检查"
      : "主笔接口写稿 / 收稿检查";
  const gate = payload.codexGate?.status === "pending"
    ? "终审中"
    : payload.qualityGate?.status === "allow"
      ? "通过"
      : "未过";
  const thinkingLabel = thinking === "enabled" ? " · 深度思考" : "";
  return `来源：${role}${thinkingLabel} · 门槛${gate}`;
}

function sleepWithSignal(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }
    const timer = window.setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true }
    );
  });
}

async function waitForFullDraftJob(jobId, signal) {
  let pollCount = 0;
  while (true) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    const job = await api(`/api/full-draft-job/${encodeURIComponent(jobId)}`, { signal });
    const elapsed = generateStartedAt ? Math.round((Date.now() - generateStartedAt) / 1000) : 0;
    if (job.status === "done") {
      if (!job.result) throw new Error("后台生成结束，但没有返回正文。");
      return job.result;
    }
    if (job.status === "error") {
      throw new Error(job.error || "后台生成失败。");
    }
    pollCount += 1;
    setGenerateProgress({
      status: elapsed >= 90 ? "warn" : "running",
      title: elapsed >= 90 ? "后台仍在生成" : "后台生成中",
      detail: `任务 ${jobId} · ${job.status || "running"}。可以取消前端等待，后台会继续跑。`,
      elapsed,
      progress: Math.min(96, 32 + pollCount * 3),
      cancellable: true,
    });
    await sleepWithSignal(2500, signal);
  }
}

async function waitForFinalReviewJob(jobId) {
  let pollCount = 0;
  const startedAt = Date.now();
  while (true) {
    const job = await api(`/api/final-review-job/${encodeURIComponent(jobId)}`);
    const elapsed = Math.round((Date.now() - startedAt) / 1000);
    if (job.status === "done") {
      if (!job.result) throw new Error("Codex 收稿结束，但没有返回结果。");
      return job.result;
    }
    if (job.status === "error") {
      throw new Error(job.error || "Codex 收稿失败。");
    }
    pollCount += 1;
    setAuditSummary(elapsed >= 120 ? "Codex 仍在收稿" : "Codex 收稿中", "checking");
    jobStateNode.textContent = `Codex 通篇收稿中 · ${elapsed}s · 任务 ${jobId}。先等它跑完，不用本地结果冒充终审。`;
    await sleepWithSignal(Math.min(5000, 1800 + pollCount * 250));
  }
}

async function continueDeferredCodexGate(jobId, provider, promptMode) {
  if (!jobId) return;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 4000));
    let job = null;
    try {
      job = await api(`/api/full-draft-job/${encodeURIComponent(jobId)}`);
    } catch (_) {
      continue;
    }
    const result = job?.result;
    const gateStatus = String(result?.codexGate?.status || "");
    if (!result || !gateStatus || gateStatus === "pending") {
      continue;
    }
    window.localStorage.setItem(generatedDraftKey, JSON.stringify(result));
    renderGeneratedDraft(result);
    if (gateStatus === "allow" && result.qualityGate?.status === "allow") {
      generateStateNode.textContent = "终审通过";
      draftNoticeNode.textContent = "Codex 终审已放行；可继续人工细修或导出。";
      finishGenerateProgress(result, provider, promptMode);
      return;
    }
    if (gateStatus === "review" || gateStatus === "block" || result.qualityGate?.status === "block") {
      generateStateNode.textContent = "终审未过";
      draftNoticeNode.textContent = "Codex 终审未放行，先看右侧细节。";
      setGenerateProgress({
        status: "warn",
        title: "Codex 终审未过",
        detail: (result.qualityGate?.reasons || [result.codexGate?.summary || "需要继续修改。"]).slice(0, 2).join(" / "),
        elapsed: generateStartedAt ? Math.round((Date.now() - generateStartedAt) / 1000) : 0,
        progress: 100,
        cancellable: false,
      });
      return;
    }
    if (gateStatus === "unavailable") {
      generateStateNode.textContent = "终审待补";
      draftNoticeNode.textContent = "正文已载入；Codex 终审这次没有及时返回，先按本地门槛继续看稿。";
      setGenerateProgress({
        status: "warn",
        title: "Codex 终审暂不可用",
        detail: result.codexGate?.summary || "本次没有拿到 Codex 终审结果。",
        elapsed: generateStartedAt ? Math.round((Date.now() - generateStartedAt) / 1000) : 0,
        progress: 100,
        cancellable: false,
      });
      return;
    }
  }
}

function bodySource() {
  return window.localStorage.getItem(bodySourceKey) || "sample";
}

function latestGeneratedPayload() {
  const raw = window.localStorage.getItem(generatedDraftKey);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}

function normalizedEditorBody() {
  return normalizeText(editor.innerText || "");
}

function normalizedGeneratedBody(payload = latestGeneratedPayload()) {
  if (!payload) return "";
  return normalizeText(generatedDraftText(payload));
}

function generatedBodyCandidates(payload = latestGeneratedPayload()) {
  if (!payload) return [];
  return [payload.rawBody, payload.minimalBody, payload.body]
    .map((item) => normalizeText(item || ""))
    .filter(Boolean);
}

function isEditorSyncedWithGenerated(payload = latestGeneratedPayload()) {
  if (!payload) return false;
  const titleMatches = normalizeText(titleInput.value) === normalizeText(payload.title || "");
  const body = normalizedEditorBody();
  const candidates = generatedBodyCandidates(payload);
  return Boolean(
    titleMatches &&
      body &&
      candidates.some((generated) => generated && body.includes(generated.slice(0, Math.min(160, generated.length))))
  );
}

function setBodySource(source) {
  window.localStorage.setItem(bodySourceKey, source);
  renderWorkflowState();
}

function preferredGeneratedView() {
  return cleanAiTasteInput?.checked ? "clean" : "raw";
}

function renderWorkflowState() {
  const generated = latestGeneratedPayload();
  const synced = isEditorSyncedWithGenerated(generated);
  openingBadgeNode.textContent = selectedOpeningIndex >= 0 ? `开头 ${selectedOpeningIndex + 1}` : "开头";
  draftBadgeNode.textContent = generated ? (synced ? "已同步" : "未同步") : "未生成";
  const current = bodySource();
  const bodyMap = {
    sample: "正文：样稿",
    latest_generated: "正文：最新全文",
    generated_loaded: "正文：生成稿",
    workspace_loaded: "正文：工作区稿",
    workspace_saved: "正文：已保存",
    edited: "正文：已修改",
    blank: "正文：新稿",
  };
  bodyBadgeNode.textContent = bodyMap[current] || "当前稿";
  if (leftStatusNode) {
    leftStatusNode.textContent = `当前：${currentTitle()}`;
    leftStatusNode.classList.toggle("unsynced", Boolean(generated && !synced));
  }
  if (rightStatusNode) {
    rightStatusNode.textContent = generated ? `最新：${generated.title || "未命名稿件"}` : "最新：未取回";
    rightStatusNode.classList.toggle("unsynced", Boolean(generated && !synced));
  }
  if (latestFoldNode) {
    const showLatestEntry = Boolean(generated && !synced);
    const showTopicArchive = latestTopicArchiveEntries.length > 0 || Boolean(currentDocumentId);
    latestFoldNode.hidden = document.body.classList.contains("lite-mode") ? !(showLatestEntry || showTopicArchive) : false;
    if (!showLatestEntry && !showTopicArchive) latestFoldNode.open = false;
    if (leftStatusNode) leftStatusNode.hidden = !showLatestEntry;
    if (rightStatusNode) rightStatusNode.hidden = !showLatestEntry;
    if (syncLatestButton) syncLatestButton.hidden = !showLatestEntry;
    if (loadGeneratedTopButton) loadGeneratedTopButton.hidden = !showLatestEntry;
  }
  if (latestFoldSummaryNode) {
    latestFoldSummaryNode.textContent = generated && !synced ? "版本" : "存档";
  }
  if (openInObsidianButton) openInObsidianButton.disabled = !currentDocumentId;
  if (loadGeneratedTopButton) loadGeneratedTopButton.disabled = !generated || synced;
  if (loadGeneratedButton) loadGeneratedButton.disabled = !generated || synced;
}

function closeLatestFold() {
  if (latestFoldNode) latestFoldNode.open = false;
}

function canonicalizeWorkbenchUrl() {
  if (!window.history?.replaceState) return;
  const canonicalPath = "/v2/";
  const canonicalSearch = currentDocumentId ? `?documentId=${encodeURIComponent(currentDocumentId)}` : "";
  if (window.location.pathname === canonicalPath && window.location.search === canonicalSearch && !window.location.hash) return;
  window.history.replaceState({}, "", `${canonicalPath}${canonicalSearch}`);
}

function resolveDocumentAlias(documentId) {
  const value = normalizeText(documentId);
  return documentAliasMap[value] || value;
}

function applyGeneratedToEditor(payload, source = "latest_generated") {
  if (!payload) return false;
  generatedDraftView = preferredGeneratedView();
  renderGeneratedDraft(payload);
  titleInput.value = payload.title || titleInput.value;
  const html = generatedDraftHtml(payload);
  if (html) editor.innerHTML = html;
  resetEditorUndoHistory();
  saveDraft();
  setBodySource(source);
  markDraftChanged();
  documentStateNode.textContent = "最新";
  documentPathNode.textContent = payload.title || "";
  draftNoticeNode.textContent = "已载入最新。";
  renderWorkflowState();
  return true;
}

function formatAuditIssue(item) {
  if (!item) return "待改句。";
  const head = item.category || item.kind || "问题";
  const reason = item.reason || "这段需要继续收。";
  return `当前在修：${head} · ${reason}`;
}

function locatableAuditIndexes() {
  const findings = latestAuditResult?.findings || [];
  return findings
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => Number.isInteger(item.paragraphIndex))
    .map(({ index }) => index);
}

function findNextAuditIndex(fromIndex) {
  const indexes = locatableAuditIndexes();
  return indexes.find((index) => index > fromIndex) ?? -1;
}

function currentAuditOrder() {
  const indexes = locatableAuditIndexes();
  const order = indexes.indexOf(currentAuditIndex);
  return {
    order: order >= 0 ? order + 1 : 0,
    total: indexes.length,
  };
}

function updateAuditListActive() {
  auditListNode.querySelectorAll(".audit-item").forEach((node) => {
    const itemIndex = Number(node.dataset.auditIndex || "-1");
    node.classList.toggle("active", itemIndex === currentAuditIndex && !auditFlowDone);
  });
}

function updateAuditIssueUi() {
  const { order, total } = currentAuditOrder();
  if (auditFlowDone && total > 0) {
    rewriteIssueNode.textContent = "本轮可定位问题已经走完。";
    rewriteProgressNode.textContent = `本轮进度 ${total}/${total}`;
  } else {
    rewriteIssueNode.textContent = formatAuditIssue(currentAuditIssue);
    rewriteProgressNode.textContent = total > 0 ? (order > 0 ? `${order}/${total}` : `${total} 条可定位`) : "待检查。";
  }
  const hasNext = findNextAuditIndex(currentAuditIndex) !== -1;
  nextAuditIssueButton.disabled = !hasNext || auditFlowDone;
  updateAuditListActive();
  refreshRewriteSurface();
}

function clearAuditMarks() {
  editor.querySelectorAll(".audit-inline-mark").forEach((mark) => {
    const parent = mark.parentNode;
    if (!parent) return;
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
    mark.remove();
    parent.normalize();
  });
  editor.querySelectorAll(".audit-mark").forEach((node) => {
    node.classList.remove("audit-mark");
    node.classList.remove("audit-mark-high");
    node.classList.remove("audit-mark-medium");
    node.classList.remove("audit-mark-low");
    node.removeAttribute("data-audit-label");
    node.removeAttribute("data-audit-paragraph");
    node.removeAttribute("title");
    node.onclick = null;
  });
}

function applyAuditMarks(result) {
  clearAuditMarks();
  const findings = result?.findings || [];
  const paragraphs = Array.from(editor.querySelectorAll("p"));
  const levelRank = { low: 1, medium: 2, high: 3 };
  const paragraphIssueCounts = new Map();
  const paragraphIssueLevels = new Map();
  findings.forEach((item) => {
    if (!Number.isInteger(item.paragraphIndex)) return;
    paragraphIssueCounts.set(item.paragraphIndex, (paragraphIssueCounts.get(item.paragraphIndex) || 0) + 1);
    const level = item.level || "low";
    const previous = paragraphIssueLevels.get(item.paragraphIndex) || "low";
    paragraphIssueLevels.set(
      item.paragraphIndex,
      (levelRank[level] || 1) > (levelRank[previous] || 1) ? level : previous,
    );
  });
  findings.forEach((item, index) => {
    if (!Number.isInteger(item.paragraphIndex)) return;
    const target = paragraphs[Math.max(0, item.paragraphIndex - 1)];
    if (!target) return;
    const level = paragraphIssueLevels.get(item.paragraphIndex) || item.level || "low";
    let inlineMark = target.querySelector(":scope > .audit-inline-mark");
    if (!inlineMark) {
      inlineMark = document.createElement("span");
      inlineMark.className = "audit-inline-mark";
      while (target.firstChild) inlineMark.appendChild(target.firstChild);
      target.appendChild(inlineMark);
    }
    inlineMark.classList.add(`audit-inline-${level}`);
    inlineMark.title = `${item.category || item.kind || "问题"}：${item.reason || "这段需要检查。"}`;
    inlineMark.onclick = (event) => {
      event.stopPropagation();
      jumpToParagraph(item.paragraphIndex, item, index);
    };
    target.classList.add("audit-mark");
    target.classList.add(`audit-mark-${level}`);
    const issueCount = paragraphIssueCounts.get(item.paragraphIndex) || 1;
    target.dataset.auditParagraph = issueCount > 1 ? `第 ${item.paragraphIndex} 段 · ${issueCount} 条` : `第 ${item.paragraphIndex} 段`;
    target.title = `${item.category || item.kind || "问题"}：${item.reason || "这段需要检查。"}`;
    target.onclick = () => jumpToParagraph(item.paragraphIndex, item, index);
  });
}

function finalReviewLocationLabel(item) {
  if (!Number.isInteger(item?.paragraphIndex)) return "全文";
  const mergedSuffix = item.mergedCount > 1 ? ` · ${item.mergedCount} 项` : "";
  return `第 ${item.paragraphIndex} 段${mergedSuffix}`;
}

function finalReviewButtonLabel(item) {
  if (!Number.isInteger(item?.paragraphIndex)) return item?.actionLabel || "看说明";
  if (item?.autoRewrite === true) return item?.actionLabel || "改这句";
  return `定位第 ${item.paragraphIndex} 段`;
}

function renderAuditResult(result) {
  if (auditFoldNode && result) auditFoldNode.open = true;
  latestAuditResult = result || null;
  currentAuditIndex = -1;
  currentAuditIssue = null;
  auditFlowDone = false;
  updateAuditIssueUi();
  if (!result) {
    clearAuditMarks();
    auditScoreNode.textContent = "--";
    setAuditSummary("", "");
    auditListNode.textContent = "点“扫硬伤”。";
    return;
  }
  auditScoreNode.textContent = String(result.score ?? "--");
  auditListNode.innerHTML = "";
  const findings = result.findings || [];
  const summaryBuckets = Array.isArray(result.summaryBuckets) ? result.summaryBuckets : [];
  const summaryLine =
    result.summaryLine ||
    (summaryBuckets.length ? summaryBuckets.map((item) => `${item.label} ${item.count}`).join(" / ") : "");
  const compactSummary = ["检查通过", "通过"].includes(normalizeText(summaryLine))
    ? "未扫到明显硬伤"
    : summaryLine;
  setAuditSummary(compactSummary || (findings.length ? `发现 ${findings.length} 条` : "未扫到明显硬伤"), findings.length ? "issues" : "pass");
  if (!findings.length) {
    clearAuditMarks();
    auditListNode.textContent = "没有返回问题。";
    return;
  }
  findings.forEach((item, index) => {
    const node = document.createElement("button");
    node.type = "button";
    node.className = `audit-item ${item.level || "low"}`;
    node.dataset.auditIndex = String(index);
    const label = item.category || item.kind || "问题";
    const risk = item.levelLabel || item.level || "";
    node.innerHTML = `<strong>${risk ? `${label} · ${risk}` : label}</strong><p>${item.reason || ""}</p>`;
    if (Number.isInteger(item.paragraphIndex)) {
      node.addEventListener("click", () => jumpToParagraph(item.paragraphIndex, item, index));
    } else {
      node.disabled = true;
    }
    auditListNode.appendChild(node);
  });
  applyAuditMarks(result);
  updateAuditIssueUi();
}

function finalReviewItemKey(item, index = 0) {
  return [
    item?.kind || "",
    item?.category || "",
    item?.paragraphIndex ?? "",
    normalizeText(item?.text || "").slice(0, 42),
    index,
  ].join("|");
}

function renderFinalReviewResult(result) {
  if (!candidateListNode) return;
  const auditResult = result?.auditResult || result?.audit || null;
  if (auditResult) renderAuditResult(auditResult);
  const rawItems = Array.isArray(result?.items) ? result.items : [];
  const allItems = rawItems.filter((item, index) => !finalReviewIgnoredKeys.has(finalReviewItemKey(item, index)));
  const items = allItems.slice(0, 3);
  const totalItemCount = Number.isFinite(Number(result?.totalItemCount)) ? Number(result.totalItemCount) : rawItems.length;
  const hiddenCount = Math.max(0, Math.max(totalItemCount, allItems.length) - items.length);
  candidateListNode.innerHTML = "";
  candidateListNode.dataset.surface = "final-review";
  delete candidateListNode.dataset.selectedText;

  const head = document.createElement("div");
  head.className = "final-review-head";
  const statusLabel = result?.statusLabel || (items.length ? "建议再收" : "可以人工通读");
  const codexStatus = normalizeText(result?.codexReview?.status || "");
  const reviewTitle = codexStatus === "applied"
    ? "Codex 收稿"
    : codexStatus === "fallback"
      ? "本地收稿定位"
      : "收稿定位";
  const summary = hiddenCount > 0
    ? `收稿发现 ${Math.max(totalItemCount, allItems.length)} 处建议，先定位最该修的 ${items.length} 处；不自动改正文。`
    : result?.summary || (items.length ? `还有 ${items.length} 处建议处理。` : "没有扫到明显交稿问题。");
  head.innerHTML = `
    <span></span>
    <strong></strong>
    <p></p>
  `;
  head.querySelector("span").textContent = reviewTitle;
  head.querySelector("strong").textContent = statusLabel;
  head.querySelector("p").textContent = summary;
  candidateListNode.appendChild(head);

  if (!items.length) {
    const pass = document.createElement("div");
    pass.className = "final-review-empty";
    pass.textContent = "没有必须立刻处理的问题。建议你最后自己通读一遍口播节奏。";
    candidateListNode.appendChild(pass);
    refreshRewriteSurface();
    return { summary, statusLabel, visibleCount: 0, hiddenCount };
  }

  items.forEach((item, index) => {
    const key = finalReviewItemKey(item, rawItems.indexOf(item));
    const showDirectRewrite = item.autoRewrite === true;
    const primarySuggestion = showDirectRewrite
      ? item.previewText || item.suggestion || "先定位，再决定是否局部改句。"
      : item.suggestion || item.previewText || "先定位，再决定是否局部改句。";
    const secondarySuggestion = showDirectRewrite
      ? item.previewReason || (item.suggestion && item.suggestion !== item.previewText ? item.suggestion : "")
      : item.previewText && item.previewText !== item.suggestion
        ? `定位到正文后，可先看：${item.previewText}`
        : item.previewReason || "";
    const card = document.createElement("div");
    card.className = `final-review-item ${item.level || "low"}`;
    if (item.actionType) card.dataset.actionType = item.actionType;
    card.dataset.reviewMode = showDirectRewrite ? "rewrite" : "locate";
    card.innerHTML = `
      <div class="final-review-item-head">
        <span></span>
        <strong class="final-review-location"></strong>
      </div>
      <p class="final-review-reason"></p>
      <p class="final-review-suggestion"></p>
      <p class="final-review-preview-reason" hidden></p>
      <div class="candidate-actions">
        <button type="button" data-fix>改这句</button>
        <button type="button" data-ignore>忽略</button>
      </div>
    `;
    card.querySelector(".final-review-item-head span").textContent = item.category || item.kind || `问题 ${index + 1}`;
    card.querySelector(".final-review-item-head strong").textContent = finalReviewLocationLabel(item);
    card.querySelector(".final-review-reason").textContent = item.reason || "这处建议再看一眼。";
    card.querySelector(".final-review-suggestion").textContent = primarySuggestion;
    const previewReasonNode = card.querySelector(".final-review-preview-reason");
    if (secondarySuggestion) {
      previewReasonNode.hidden = false;
      previewReasonNode.textContent = secondarySuggestion;
    }
    const fixButton = card.querySelector("[data-fix]");
    fixButton.textContent = finalReviewButtonLabel(item);
    if (Number.isInteger(item.paragraphIndex)) {
      fixButton.addEventListener("click", () => {
        jumpToParagraph(item.paragraphIndex, item, rawItems.indexOf(item), { autoRewrite: item.autoRewrite === true });
      });
    } else {
      if (item.actionType === "outline") {
        fixButton.hidden = true;
      } else {
        fixButton.disabled = true;
      }
    }
    card.querySelector("[data-ignore]").addEventListener("click", () => {
      finalReviewIgnoredKeys.add(key);
      renderFinalReviewResult(result);
      jobStateNode.textContent = "已忽略这一条收稿建议。";
    });
    candidateListNode.appendChild(card);
  });
  if (hiddenCount > 0) {
    const overflow = document.createElement("p");
    overflow.className = "candidate-label final-review-overflow";
    overflow.textContent = `其余 ${hiddenCount} 处先不展开，先把这 ${items.length} 处处理掉。`;
    candidateListNode.appendChild(overflow);
  }
  refreshRewriteSurface();
  return { summary, statusLabel, visibleCount: items.length, hiddenCount };
}

async function runFinalReview() {
  if (documentHydrating) {
    jobStateNode.textContent = "正文还在载入，等它完全展开后再收稿。";
    return null;
  }
  finalReviewIgnoredKeys = new Set();
  clearRewriteResults("Codex 收稿中...", { invalidate: false });
  candidateListNode.dataset.surface = "final-review";
  refreshRewriteSurface();
  setDeliveryStatus("checking");
  setAuditSummary("Codex 收稿中", "checking");
  jobStateNode.textContent = "正在交给 Codex 通篇收稿：只找问题，不自动改正文。";
  try {
    const job = await api("/api/final-review-job", {
      method: "POST",
      body: JSON.stringify({
        title: currentTitle(),
        body: bodyParagraphText(),
      }),
    });
    const jobId = job.jobId || "";
    if (!jobId) throw new Error("后台没有返回收稿任务号。");
    jobStateNode.textContent = `Codex 收稿任务已开始：${jobId}`;
    const result = await waitForFinalReviewJob(jobId);
    const reviewView = renderFinalReviewResult(result) || {};
    setDeliveryStatus(result.status === "ready" ? "review" : "blocked", result.statusLabel || "");
    setAuditSummary(result.statusLabel || "收稿完成", result.status === "ready" ? "pass" : "issues");
    jobStateNode.textContent = reviewView.summary || result.summary || "收稿检查完成。";
    return result;
  } catch (error) {
    candidateListNode.dataset.surface = "final-review";
    candidateListNode.innerHTML = `<div class="candidate">收稿检查失败：${error.message}</div>`;
    refreshRewriteSurface();
    setDeliveryStatus("blocked", "收稿失败");
    setAuditSummary("收稿失败", "issues");
    jobStateNode.textContent = `收稿检查失败：${error.message}`;
    return null;
  }
}

function jumpToParagraph(paragraphIndex, auditItem = null, auditIndex = -1, options = {}) {
  const autoRewrite = options.autoRewrite === true;
  const paragraphs = Array.from(editor.querySelectorAll("p"));
  const target = paragraphs[Math.max(0, paragraphIndex - 1)];
  if (!target) return;
  const targetText = normalizeText(target.innerText || "");
  currentAuditIndex = auditIndex;
  currentAuditIssue = auditItem;
  auditFlowDone = false;
  updateAuditIssueUi();
  activatePanel("rewrite");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  const previous = editor.querySelector(".audit-focus");
  if (previous) previous.classList.remove("audit-focus");
  target.classList.add("audit-focus");
  activeSelection = targetText ? { text: targetText, start: 0, end: targetText.length } : activeSelection;
  setSelectionSummary(targetText, "已定位");
  updateSelectionActionState();
  try {
    editor.focus({ preventScroll: true });
    const range = document.createRange();
    range.selectNodeContents(target);
    const selection = window.getSelection();
    suppressSelectionCaptureUntil = Date.now() + PROGRAMMATIC_SELECTION_COOLDOWN_MS;
    selection.removeAllRanges();
    selection.addRange(range);
    activeRange = range.cloneRange();
    activeSelection = {
      text: targetText,
      start: 0,
      end: targetText.length,
    };
    setSelectionSummary(targetText, "已定位");
    updateSelectionActionState();
    const issueName = auditItem?.category || auditItem?.kind || "";
    const routeHint = autoRewrite
      ? "正在按这条建议直接改写。"
      : auditItem?.actionType === "locate"
        ? "这条更像段落顺序问题，先看这一段，再决定怎么拆或重排。"
        : "需要改写时点“改句”。";
    jobStateNode.textContent = `已定位到问题段落。${issueName ? `当前问题：${issueName}。` : ""}${routeHint}`;
  } catch (_) {}
  window.setTimeout(() => target.classList.remove("audit-focus"), 2200);
  if (autoRewrite) {
    window.setTimeout(() => {
      void runRewrite({ fromAudit: true, auditIssue: auditItem, keepAuditSelection: true });
    }, 40);
  }
}

function renderOpenings(payload) {
  openingListNode.innerHTML = "";
  const openings = payload?.openings || [];
  if (!openings.length) {
    openingListNode.textContent = "可以先生成开头，也可以直接生成全文。";
    openingStateNode.textContent = "未生成";
    return;
  }
  openings.forEach((item, index) => {
    const node = document.createElement("button");
    node.type = "button";
    node.className = index === selectedOpeningIndex ? "opening-item active" : "opening-item";
    node.innerHTML = `<strong>${item.label || `开头 ${index + 1}`}</strong><p>${item.text || ""}</p>`;
    node.addEventListener("click", () => {
      selectedOpeningIndex = index;
      window.localStorage.setItem(openingPackKey, JSON.stringify({ ...payload, selectedOpeningIndex }));
      renderOpenings(payload);
      openingStateNode.textContent = `已选 ${index + 1}`;
      draftNoticeNode.textContent = "已选开头。";
      renderWorkflowState();
    });
    openingListNode.appendChild(node);
  });
}

function restoreOpeningPack() {
  const raw = window.localStorage.getItem(openingPackKey);
  if (!raw) return null;
  try {
    const payload = JSON.parse(raw);
    selectedOpeningIndex = Number.isInteger(payload.selectedOpeningIndex) ? payload.selectedOpeningIndex : -1;
    renderOpenings(payload);
    if (selectedOpeningIndex >= 0) openingStateNode.textContent = `已选 ${selectedOpeningIndex + 1}`;
    renderWorkflowState();
    return payload;
  } catch (_) {
    return null;
  }
}

function activatePanel(panelName) {
  const visiblePanelName = panelName === "draft" ? "rewrite" : panelName;
  panelTabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.panel === visiblePanelName);
  });
  panelViews.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === visiblePanelName);
  });
  document.body.classList.toggle("is-cowrite", visiblePanelName === "cowrite");
  document.body.classList.remove("is-workflow-stage");
}

function enterLiteMode() {
  document.body.classList.add("lite-mode");
  activatePanel("rewrite");
}

function openAdvancedPanel(panelName) {
  if (panelName === "draft") {
    enterLiteMode();
    if (draftNoticeNode) draftNoticeNode.textContent = "全文生成入口已收起；需要新稿时直接告诉 Codex 主题。";
    return;
  }
  document.body.classList.remove("lite-mode");
  activatePanel(panelName);
}

function syncGeneratedDraftModeButtons() {
  showRawDraftButton.classList.toggle("active", generatedDraftView === "raw");
  showCleanDraftButton.classList.toggle("active", generatedDraftView === "clean");
  if (generatedModeHintNode) {
    generatedModeHintNode.textContent = generatedDraftView === "raw"
      ? "原稿"
      : "编辑稿";
  }
}

function generatedDraftText(payload) {
  if (!payload) return "";
  return generatedDraftView === "clean" ? (payload.minimalBody || payload.body || payload.rawBody || "") : (payload.rawBody || payload.body || "");
}

function generatedDraftHtml(payload) {
  if (!payload) return "";
  if (generatedDraftView === "clean") {
    return (
      payload.minimalContentHtml ||
      payload.contentHtml ||
      articleTextToHtmlLocal(payload.title || "未命名稿件", generatedDraftText(payload))
    );
  }
  const rawBody = payload.rawBody || payload.body || "";
  return articleTextToHtmlLocal(payload.title || "未命名稿件", rawBody);
}

function renderGenerationAudit(payload) {
  if (!generationAuditNode) return;
  if (!payload) {
    generationAuditNode.textContent = "还没有审计结果。";
    return;
  }
  if (payload.externalModelFailed || payload.modelError) {
    generationAuditNode.textContent = `主笔失败：${payload.supportError || payload.modelError || "外部模型没有返回正文"}`;
    return;
  }
  const audit = payload.draftAudit || {};
  const after = payload.minimalEditAudit || {};
  const edits = payload.minimalEdits || [];
  const gate = payload.qualityGate || {};
  const codexGate = payload.codexGate || {};
  const workflow = payload.workflow || {};
  const surface = payload.surfaceAudit || {};
  const model = payload.model || "deepseek";
  const findings = audit.findings || [];
  const gateText = gate.status ? ` · ${gate.status}${gate.reasons?.length ? `：${gate.reasons.join(" / ")}` : ""}` : "";
  const codexText = codexGate.status ? ` · Codex ${codexGate.status}` : "";
  const rhythmText = Number.isInteger(gate.paragraphCount)
    ? ` · 段 ${gate.paragraphCount} / 长 ${gate.longParagraphCount || 0} / 最长 ${gate.maxParagraphLength || 0}`
    : "";
  const paragraphingText = payload.paragraphing?.changed ? " · 已分段" : "";
  const surfaceText = Number.isInteger(surface.score) ? ` · 检查 ${surface.score}/${surface.findings?.length || 0}` : "";
  const workflowText = workflow.fullSop ? " · 全SOP" : " · 草稿门槛";
  generationAuditNode.textContent = `${model}${workflowText} · 原稿 ${audit.count ?? findings.length ?? 0} · 编辑稿 ${after.count ?? 0} · 改 ${edits.length}${paragraphingText}${rhythmText}${surfaceText}${codexText}${gateText}`;
}

function renderPreflight(preflight) {
  if (!preflightPreviewNode) return;
  if (!preflight) {
    preflightPreviewNode.textContent = "还没预检。";
    renderEditorialHandoff(null);
    return;
  }
  const failed = (preflight.checks || []).filter((item) => !item.ok).map((item) => item.label);
  const route = preflight.provider === "hybrid" ? "主笔+复核" : preflight.provider === "kimi" ? "旧主笔路线" : "默认主笔";
  preflightPreviewNode.textContent = `${preflight.label || preflight.status} · ${route}${failed.length ? ` · 缺：${failed.slice(0, 3).join(" / ")}` : " · 材料可用"}`;
  renderEditorialHandoff(preflight.editorialHandoff);
}

function renderEditorialHandoff(handoff) {
  if (!editorialHandoffPreviewNode) return;
  if (!handoff) {
    editorialHandoffPreviewNode.textContent = "生成前会先整理选题、材料和结构。";
    return;
  }
  const summary = Array.isArray(handoff.summary) ? handoff.summary.filter(Boolean) : [];
  const checks = Array.isArray(handoff.checks)
    ? handoff.checks.filter((item) => item && item.ok === false).map((item) => item.label).filter(Boolean)
    : [];
  editorialHandoffPreviewNode.textContent = [
    `状态：${handoff.status || "ready"}`,
    ...summary.slice(0, 7),
    checks.length ? `待补：${checks.slice(0, 3).join(" / ")}` : "已整理成主笔任务书",
  ].join("\n");
}

function renderCompliance(payload) {
  if (!compliancePreviewNode) return;
  const compliance = payload?.compliance;
  if (!compliance) {
    compliancePreviewNode.textContent = "还没有遵守情况。";
    return;
  }
  const findings = compliance.codexFindings || [];
  const self = compliance.modelSelfReport || {};
  const kept = Array.isArray(self.kept) ? self.kept.length : 0;
  const risks = Array.isArray(self.risks) ? self.risks.length : 0;
  compliancePreviewNode.textContent = `${compliance.status === "pass" ? "遵守通过" : "需要修"} · 模型自报 ${kept} 项 / 风险 ${risks} 项 · Codex问题 ${findings.length} 条`;
}

function articleTextToHtmlLocal(title, body) {
  const blocks = String(body || "")
    .split(/\n\s*\n+/)
    .map((block) => normalizeText(block))
    .filter(Boolean);
  const paragraphs = blocks.map((block) => `<p>${escapeHtmlLocal(block)}</p>`).join("\n");
  return `<h2>${escapeHtmlLocal(title)}</h2>\n${paragraphs}`;
}

function escapeHtmlLocal(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;");
}

function bodyTextToParagraphHtmlLocal(body) {
  return String(body || "")
    .split(/\n\s*\n+/)
    .map((block) => normalizeText(block))
    .filter(Boolean)
    .map((block) => `<p>${escapeHtmlLocal(block)}</p>`)
    .join("\n");
}

function renderGeneratedDraft(payload) {
  const text = generatedDraftText(payload);
  if (!payload || (!payload.contentHtml && !payload.minimalContentHtml && !text)) {
    generatedTitleNode.textContent = "还没有生成结果";
    generatedPreviewNode.textContent = "暂无。";
    if (generatedProvenanceNode) generatedProvenanceNode.textContent = "来源：未生成。";
    if (sessionStyleCardNode) sessionStyleCardNode.textContent = "生成前可先查看主笔接口会参考哪些偏好。";
    renderGenerationAudit(null);
    syncGeneratedDraftModeButtons();
    renderWorkflowState();
    return;
  }
  generatedTitleNode.textContent = payload.title || "未命名稿件";
  generatedPreviewNode.textContent = text || "没有正文。";
  if (generatedProvenanceNode) generatedProvenanceNode.textContent = formatGeneratedProvenance(payload);
  if (sessionStyleCardNode && payload.sessionStyleCard) {
    sessionStyleCardNode.textContent = payload.sessionStyleCard;
  }
  renderPreflight(payload.preflight);
  renderCompliance(payload);
  if (payload.promptMode && draftPromptModeInput) {
    draftPromptModeInput.value = payload.promptMode;
  }
  renderGenerationAudit(payload);
  renderEditorialHandoff(payload.editorialHandoff || payload.preflight?.editorialHandoff);
  syncGeneratedDraftModeButtons();
  renderWorkflowState();
}

async function runWritingPreflight() {
  const materialCard = fullDraftMaterialCard();
  const brief = fullDraftBriefText(materialCard);
  if (!brief) {
    generateStateNode.textContent = "缺材料";
    draftBriefInput.focus();
    return null;
  }
  if (preflightPreviewNode) preflightPreviewNode.textContent = "预检中...";
  const result = await api("/api/writing-preflight", {
    method: "POST",
    body: JSON.stringify({
      title: currentTitle(),
      brief,
      materialCard,
      promptMode: draftPromptModeInput?.value || "guided",
      provider: normalizeDraftProvider(draftProviderInput?.value || providerEngine),
      cleanAiTaste: cleanAiTasteInput.checked,
    }),
  });
  renderPreflight(result);
  return result;
}

async function refreshSessionStyleCard() {
  if (!sessionStyleCardNode) return null;
  const topic = styleCardTopic();
  if (!topic) {
    sessionStyleCardNode.textContent = "先写标题或需求。";
    return null;
  }
  sessionStyleCardNode.textContent = "读取中...";
  const query = new URLSearchParams({ topic }).toString();
  const data = await api(`/api/session-style-card?${query}`);
  sessionStyleCardNode.textContent = data.sessionStyleCard || "没有找到相关风格记忆。";
  return data;
}

function renderContextList(node, items, fallback = "暂无。") {
  if (!node) return;
  const list = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!list.length) {
    node.textContent = fallback;
    return;
  }
  node.innerHTML = "";
  list.slice(0, 5).forEach((item) => {
    const line = document.createElement("p");
    line.textContent = String(item || "").trim();
    node.appendChild(line);
  });
}

function structureHighlights(records = []) {
  return records.slice(-3).reverse().map((record) => {
    const beats = Array.isArray(record.beats)
      ? record.beats.slice(0, 6).map((beat) => beat.job || beat.label || beat.index).filter(Boolean).join(" -> ")
      : "";
    const title = record.title || "成功结构";
    return beats ? `${title}：${beats}` : title;
  });
}

async function refreshWorkbenchContext() {
  const topic = styleCardTopic() || `${currentTitle()}\n${bodyParagraphText().slice(0, 800)}`;
  if (contextContractNode) contextContractNode.textContent = "读取中...";
  if (contextStyleNode) contextStyleNode.textContent = "读取中...";
  if (contextDemoNode) contextDemoNode.textContent = "读取中...";
  if (contextGoldNode) contextGoldNode.textContent = "读取中...";
  if (contextAmiNode) contextAmiNode.textContent = "读取中...";
  const query = new URLSearchParams({ topic }).toString();
  const data = await api(`/api/workbench-context?${query}`);
  renderContextList(contextContractNode, data.executionContract?.highlights, "暂无执行合同。");
  const styleLines = [];
  if (data.styleProof?.summary) styleLines.push(data.styleProof.summary);
  if (data.styleMemorySummary?.compactLine) styleLines.push(data.styleMemorySummary.compactLine);
  styleLines.push(...(data.styleHighlights || data.summary || []));
  renderContextList(contextStyleNode, styleLines, "暂无相关偏好。");
  renderContextList(contextDemoNode, data.beforeAfter?.highlights, "暂无反例对比。");
  const gold = [
    ...(data.goldenSamples?.highlights || []),
    ...structureHighlights(data.successStructures || []),
  ];
  renderContextList(contextGoldNode, gold, "暂无黄金样本。");
  renderContextList(contextAmiNode, data.amiRoute?.highlights, "暂无参考节奏。");
  return data;
}

function renderStyleProof(proof) {
  if (!styleProofPanel) return;
  if (!proof) {
    syncStyleProofVisibility(false);
    styleProofPanel.hidden = true;
    styleProofPanel.textContent = "检查后显示本次用了哪些偏好。";
    if (proofSummaryNode) proofSummaryNode.textContent = "偏好：待检查";
    return;
  }
  syncStyleProofVisibility(true);
  const counts = proof.memoryCounts || {};
  const focus = proof.focus || {};
  const hardBans = proof.memoryHits?.hardBans || [];
  const approved = proof.memoryHits?.approved || [];
  const usedThisRun = proof.memoryHits?.usedThisRun || [];
  const compiledRules = proof.compiledRules?.rules || [];
  const usedCount = usedThisRun.length || counts.related || 0;
  const bannedFindings = Number(counts.currentBannedFindings ?? 0);
  if (proofSummaryNode) {
    if (bannedFindings > 0) {
      proofSummaryNode.textContent = `踩禁 ${bannedFindings} · 已带入 ${usedCount}`;
    } else if (usedCount > 0) {
      proofSummaryNode.textContent = `已带入 ${usedCount} 条偏好`;
    } else {
      proofSummaryNode.textContent = "偏好待检查";
    }
  }
  const lines = [];
  const memoryLine = memoryProofLine({
    ...proof,
    counts: {
      hardBans: counts.hardBans ?? 0,
      approved: counts.approved ?? 0,
      rewritePairs: counts.rewritePairs ?? 0,
    },
  });
  if (memoryLine) lines.push(memoryLine);
  lines.push(bannedFindings > 0 ? `这篇踩中 ${bannedFindings} 条讨厌项。` : "这篇没有踩中讨厌库。");
  lines.push(`库里现有：讨厌 ${counts.hardBans ?? 0} / 喜欢 ${counts.approved ?? 0} / 改法 ${counts.rewritePairs ?? 0}`);
  if (focus.hardBanLine && focus.hardBanLine !== "暂无稳定硬禁结构。") {
    lines.push(`避开：${focus.hardBanLine}`);
  }
  if (focus.approvalLine && focus.approvalLine !== "暂无稳定喜欢模式。") {
    lines.push(`靠近：${focus.approvalLine}`);
  }
  if (focus.rewriteLine && focus.rewriteLine !== "暂无稳定改法。") {
    lines.push(`改法：${focus.rewriteLine}`);
  }
  if (compiledRules.length) {
    lines.push(`这轮规则：${compiledRules.slice(0, 2).map((item) => item.label).join(" / ")}`);
  }
  const proofSamples = [];
  const addProofSample = (entry, prefix = "") => {
    if (!entry) return;
    const text = `${prefix || entry.typeLabel || "记忆"}：${entry.sourceText || entry.reason || entry.id}`;
    if (!proofSamples.includes(text)) proofSamples.push(text);
  };
  addProofSample(usedThisRun.find((entry) => entry.typeLabel === "改写对"), "改写");
  addProofSample(usedThisRun.find((entry) => entry.typeLabel === "硬禁句"), "避开");
  addProofSample(usedThisRun.find((entry) => entry.typeLabel === "喜欢表达"), "参考");
  usedThisRun.slice(0, 3).forEach((entry) => addProofSample(entry));
  hardBans.slice(0, 1).forEach((entry) => addProofSample(entry, "避开"));
  approved.slice(0, 1).forEach((entry) => addProofSample(entry, "参考"));
  const sampleLines = proofSamples.slice(0, 4);
  styleProofPanel.hidden = false;
  styleProofPanel.innerHTML = "";
  lines.forEach((text) => {
    const line = document.createElement("p");
    line.textContent = text;
    styleProofPanel.appendChild(line);
  });
  if (sampleLines.length) {
    const list = document.createElement("div");
    list.className = "proof-samples";
    sampleLines.forEach((text) => {
      const item = document.createElement("span");
      item.textContent = text;
      list.appendChild(item);
    });
    styleProofPanel.appendChild(list);
  }
}

async function runStyleProof() {
  syncStyleProofVisibility(true);
  if (styleProofPanel) {
    styleProofPanel.hidden = false;
    styleProofPanel.textContent = "读取偏好中。";
  }
  if (proofSummaryNode) proofSummaryNode.textContent = "偏好：检查中";
  jobStateNode.textContent = "检查偏好。";
  try {
    const proof = await api("/api/style-proof", {
      method: "POST",
      body: JSON.stringify({
        title: currentTitle(),
        brief: styleCardTopic(),
        body: bodyParagraphText(),
      }),
    });
    renderStyleProof(proof);
    const count = proof.memoryCounts?.related ?? 0;
    const findings = proof.memoryCounts?.currentBannedFindings ?? 0;
    jobStateNode.textContent = `偏好 ${count} / 踩禁 ${findings}`;
    return proof;
  } catch (error) {
    if (styleProofPanel) styleProofPanel.textContent = `证明失败：${error.message}`;
    if (proofSummaryNode) proofSummaryNode.textContent = "偏好：失败";
    jobStateNode.textContent = `偏好检查失败：${error.message}`;
    return null;
  }
}

function renderAiFlavorAudit(result, options = {}) {
  if (!aiFlavorPanelNode) return;
  const shouldOpen = options.openPanel !== false;
  if (!result) {
    aiFlavorPanelNode.hidden = true;
    aiFlavorPanelNode.textContent = "扫硬伤时会一起检查文本痕迹。";
    if (aiFlavorSummaryNode) aiFlavorSummaryNode.textContent = "痕迹：未查";
    return;
  }
  aiFlavorPanelNode.hidden = false;
  if (aiFlavorFoldNode) aiFlavorFoldNode.open = shouldOpen;
  if (aiFlavorSummaryNode) {
    aiFlavorSummaryNode.textContent = `痕迹：${result.risk || "--"} · ${result.score ?? "--"}分`;
  }
  const reasons = Array.isArray(result.mainReasons) ? result.mainReasons : [];
  const actions = Array.isArray(result.nextActions) ? result.nextActions : [];
  const detectors = Array.isArray(result.externalDetectors) ? result.externalDetectors : [];
  aiFlavorPanelNode.innerHTML = "";

  const head = document.createElement("div");
  head.className = "ai-flavor-head";
  head.innerHTML = `<strong>${result.label || "已检测"}</strong><span>${result.counts?.findings ?? 0} 条问题</span>`;
  aiFlavorPanelNode.appendChild(head);

  const summary = document.createElement("p");
  summary.textContent = result.summary || "没有扫到明显硬伤。";
  aiFlavorPanelNode.appendChild(summary);

  const detail = document.createElement("div");
  detail.className = "ai-flavor-grid";
  detail.innerHTML = `
    <span>高风险 ${result.counts?.high ?? 0}</span>
    <span>中风险 ${result.counts?.medium ?? 0}</span>
    <span>字数 ${result.counts?.chars ?? 0}</span>
  `;
  aiFlavorPanelNode.appendChild(detail);

  if (reasons.length) {
    const reasonList = document.createElement("ul");
    reasonList.className = "ai-flavor-list";
    reasons.slice(0, 3).forEach((item) => {
      const line = document.createElement("li");
      line.textContent = item;
      reasonList.appendChild(line);
    });
    aiFlavorPanelNode.appendChild(reasonList);
  }

  if (actions.length) {
    const actionList = document.createElement("div");
    actionList.className = "ai-flavor-actions-text";
    actions.slice(0, 2).forEach((item) => {
      const line = document.createElement("p");
      line.textContent = item;
      actionList.appendChild(line);
    });
    aiFlavorPanelNode.appendChild(actionList);
  }

  const externalFold = document.createElement("details");
  externalFold.className = "external-detectors-fold";
  const externalSummary = document.createElement("summary");
  externalSummary.textContent = "外部检测";
  externalFold.appendChild(externalSummary);
  const external = document.createElement("div");
  external.className = "external-detectors";
  const copyButton = document.createElement("button");
  copyButton.type = "button";
  copyButton.className = "mini-button";
  copyButton.textContent = "复制全文";
  copyButton.addEventListener("click", async () => {
    const text = `${currentTitle()}\n\n${bodyParagraphText()}`.trim();
    try {
      await navigator.clipboard.writeText(text);
      jobStateNode.textContent = "已复制全文，可粘到外部检测站复核。";
    } catch (_) {
      jobStateNode.textContent = "复制失败；可以手动全选正文。";
    }
  });
  external.appendChild(copyButton);
  detectors.slice(0, 4).forEach((detector) => {
    const link = document.createElement("a");
    link.href = detector.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = detector.name;
    external.appendChild(link);
  });
  externalFold.appendChild(external);
  aiFlavorPanelNode.appendChild(externalFold);

  const warning = document.createElement("p");
  warning.className = "ai-flavor-warning";
  warning.textContent = result.warning || "外部检测只作参考。";
  aiFlavorPanelNode.appendChild(warning);
}

async function runAiFlavorAudit(options = {}) {
  const shouldRenderToAudit = options.renderToAudit !== false;
  const shouldOpen = options.openPanel !== false;
  const shouldAnnounce = options.announce !== false;
  if (aiFlavorPanelNode) {
    aiFlavorPanelNode.hidden = false;
    aiFlavorPanelNode.textContent = "检测中...";
  }
  if (aiFlavorSummaryNode) aiFlavorSummaryNode.textContent = "痕迹：检测中";
  if (aiFlavorFoldNode) aiFlavorFoldNode.open = shouldOpen;
  if (shouldAnnounce) jobStateNode.textContent = "检查文本痕迹。";
  try {
    const result = await api("/api/ai-flavor-audit", {
      method: "POST",
      body: JSON.stringify({
        title: currentTitle(),
        body: bodyParagraphText(),
      }),
    });
    renderAiFlavorAudit(result, { openPanel: shouldOpen });
    if (shouldRenderToAudit) renderAuditResult(result);
    if (shouldAnnounce) jobStateNode.textContent = `痕迹 ${result.risk || "--"} · ${result.counts?.findings ?? 0} 条`;
    return result;
  } catch (error) {
    if (aiFlavorPanelNode) aiFlavorPanelNode.textContent = `检测失败：${error.message}`;
    if (aiFlavorSummaryNode) aiFlavorSummaryNode.textContent = "痕迹：失败";
    if (shouldAnnounce) jobStateNode.textContent = `痕迹检查失败：${error.message}`;
    return null;
  }
}

function restoreGeneratedDraft() {
  const raw = window.localStorage.getItem(generatedDraftKey);
  if (!raw) return;
  try {
    renderGeneratedDraft(JSON.parse(raw));
  } catch (_) {}
}

async function loadLatestGeneratedDraft(options = {}) {
  const shouldApply = Boolean(options.apply);
  try {
    const latest = await api("/api/latest-full-draft");
    window.localStorage.setItem(generatedDraftKey, JSON.stringify(latest));
    if (latest.qualityGate?.status === "block") {
      generatedDraftView = preferredGeneratedView();
      renderGeneratedDraft(latest);
      draftNoticeNode.textContent = "最新稿未过门槛，未载入正文。";
    } else if (shouldApply) {
      applyGeneratedToEditor(latest, "latest_generated");
    } else {
      renderGeneratedDraft(latest);
      if (!currentDocumentId) {
        draftNoticeNode.textContent = "已取回最新生成稿，尚未载入正文。";
      }
    }
    return latest;
  } catch (_) {
    return null;
  }
}

async function recoverLatestFullDraft() {
  const latest = await loadLatestGeneratedDraft({ apply: true });
  if (!latest) return null;
  activatePanel("draft");
  generateStateNode.textContent = "最新";
  saveStateNode.textContent = "已载入最新";
  documentStateNode.textContent = "最新";
  documentPathNode.textContent = latest.title || "";
  draftNoticeNode.textContent = "已载入最新。";
  return latest;
}

async function refreshLatestGeneratedDraft() {
  const latest = await loadLatestGeneratedDraft({ apply: false });
  if (!latest) {
    generateStateNode.textContent = "无最新";
    draftNoticeNode.textContent = "没有取回最新生成稿。";
    return null;
  }
  activatePanel("draft");
  generateStateNode.textContent = "已刷新";
  saveStateNode.textContent = "最新生成稿已取回";
  documentStateNode.textContent = bodySource() === "blank" ? "新稿未保存" : "当前稿";
  documentPathNode.textContent = latest.title || "";
  draftNoticeNode.textContent = "已取回最新生成稿。点“载入”会替换到正文区。";
  renderWorkflowState();
  return latest;
}

function loadGeneratedIntoEditor() {
  const raw = window.localStorage.getItem(generatedDraftKey);
  if (!raw) return;
  const payload = JSON.parse(raw);
  generatedDraftView = "clean";
  renderGeneratedDraft(payload);
  titleInput.value = payload.title || titleInput.value;
  editor.innerHTML = generatedDraftHtml(payload) || editor.innerHTML;
  resetEditorUndoHistory();
  saveDraft();
  const modeLabel = "编辑稿";
  draftNoticeNode.textContent = `已载入${modeLabel}。`;
  saveStateNode.textContent = `已载入${modeLabel}`;
  documentStateNode.textContent = "已载入";
  documentPathNode.textContent = payload.title || "";
  setBodySource("generated_loaded");
  markDraftChanged();
  renderWorkflowState();
  activatePanel("rewrite");
  void runQuickAudit();
}

async function api(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `${response.status} ${response.statusText}`);
  return data;
}

function saveDraft() {
  persistCurrentDraft();
  saveStateNode.textContent = `本地已存 ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
  updateCurrentDraftPreview();
}

function scheduleSave() {
  window.clearTimeout(autosaveTimer);
  saveStateNode.textContent = "本地暂存中...";
  documentStateNode.textContent = currentDocumentId ? "有未保存改动" : "新稿未保存";
  if (bodySource() !== "blank") setBodySource("edited");
  autosaveTimer = window.setTimeout(saveDraft, 400);
}

function showWorkspaceToast(message, kind = "ok") {
  if (!workspaceToastNode) return;
  window.clearTimeout(workspaceToastTimer);
  workspaceToastNode.textContent = message;
  workspaceToastNode.hidden = false;
  workspaceToastNode.classList.toggle("toast-error", kind === "error");
  workspaceToastNode.classList.add("show");
  workspaceToastTimer = window.setTimeout(() => {
    workspaceToastNode.classList.remove("show");
    workspaceToastTimer = window.setTimeout(() => {
      workspaceToastNode.hidden = true;
      workspaceToastNode.classList.remove("toast-error");
    }, 180);
  }, kind === "error" ? 2200 : 1200);
}

function showSelectionMenuStatus(message = "", state = "ok") {
  if (!selectionMenuStatusNode) return;
  selectionMenuStatusNode.textContent = message;
  selectionMenuStatusNode.hidden = !message;
  selectionMenuStatusNode.dataset.state = state;
}

function restoreDraft() {
  const snapshot = readDraftSnapshot(currentDocumentId) || migrateLegacyDraft(currentDocumentId);
  if (!snapshot) return false;
  return applyDraftSnapshot(snapshot, { saveStateText: "已恢复本地草稿" });
}

function flushAutosave() {
  window.clearTimeout(autosaveTimer);
  persistCurrentDraft();
  updateCurrentDraftPreview();
}

function syncHeadingFromTitle() {
  const heading = editor.querySelector("h2");
  if (!heading) return;
  const nextTitle = currentTitle();
  if (heading.textContent !== nextTitle) heading.textContent = nextTitle;
}

function captureCaret() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || !selection.isCollapsed) return false;
  const range = selection.getRangeAt(0);
  if (!isInsideEditor(range.commonAncestorContainer)) {
    activeCaretRange = null;
    activePromptParagraph = null;
    updateParagraphAssistState();
    return false;
  }
  activeCaretRange = range.cloneRange();
  activePromptParagraph = promptParagraphStateFromRange(range);
  selectionMenu.hidden = true;
  updateParagraphAssistState();
  return true;
}

function captureSelection() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    selectionMenu.hidden = true;
    captureCaret();
    return;
  }
  if (selection.isCollapsed) {
    selectionMenu.hidden = true;
    captureCaret();
    return;
  }
  const range = selection.getRangeAt(0);
  if (!isInsideEditor(range.commonAncestorContainer)) {
    selectionMenu.hidden = true;
    captureCaret();
    return;
  }
  const text = normalizeText(selection.toString());
  if (!text) {
    selectionMenu.hidden = true;
    captureCaret();
    return;
  }
  clearStaleAuditIssueForRange(range);
  const problem = selectionProblem(text);
  if (problem) {
    clearActiveSelection();
    setSelectionSummary(text.slice(0, 120), "选区不适合改句");
    jobStateNode.textContent = problem;
    return;
  }
  activeRange = range.cloneRange();
  activeCaretRange = null;
  activeSelection = { text, ...getTextOffsets(range) };
  clearCandidateSurfaceForNewSelection(text);
  setSelectionSummary(text, "已选");
  updateSelectionActionState();
  updateParagraphAssistState();
  activatePanel("rewrite");
  const rect = range.getBoundingClientRect();
  const top = Math.min(window.innerHeight - 54, Math.max(12, rect.bottom + 8));
  const left = Math.min(window.innerWidth - 250, Math.max(12, rect.left));
  selectionMenu.style.top = `${top}px`;
  selectionMenu.style.left = `${left}px`;
  showSelectionMenuStatus("");
  selectionMenu.hidden = false;
}

function syncActiveSelectionFromWindow({ updateUi = true } = {}) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    return Boolean(activeSelection?.text);
  }
  const range = selection.getRangeAt(0);
  if (!isInsideEditor(range.commonAncestorContainer)) return Boolean(activeSelection?.text);
  const text = normalizeText(selection.toString());
  if (!text || selectionProblem(text)) return Boolean(activeSelection?.text);
  clearStaleAuditIssueForRange(range);
  activeRange = range.cloneRange();
  activeCaretRange = null;
  activeSelection = { text, ...getTextOffsets(range) };
  if (updateUi) {
    clearCandidateSurfaceForNewSelection(text);
    setSelectionSummary(text, "已选");
    updateSelectionActionState();
    updateParagraphAssistState();
  }
  return true;
}

function restoreRange() {
  if (!activeRange) return false;
  if (!isInsideEditor(activeRange.commonAncestorContainer)) return false;
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(activeRange);
  return true;
}

function boundaryFromTextOffset(offset) {
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  let cursor = 0;
  let lastTextNode = null;
  while (current) {
    const length = current.nodeValue.length;
    if (offset <= cursor + length) {
      return { node: current, offset: Math.max(0, Math.min(length, offset - cursor)) };
    }
    cursor += length;
    lastTextNode = current;
    current = walker.nextNode();
  }
  if (lastTextNode) return { node: lastTextNode, offset: lastTextNode.nodeValue.length };
  return null;
}

function rangeFromTextOffsets(start, end) {
  if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start) return null;
  const startPoint = boundaryFromTextOffset(start);
  const endPoint = boundaryFromTextOffset(end);
  if (!startPoint || !endPoint) return null;
  const range = document.createRange();
  range.setStart(startPoint.node, startPoint.offset);
  range.setEnd(endPoint.node, endPoint.offset);
  return range;
}

function rangeFromExactText(text) {
  const normalized = normalizeText(text || "");
  if (!normalized) return null;
  const content = editor.textContent || "";
  let index = content.indexOf(normalized);
  if (index < 0 && activeSelection?.start >= 0) {
    const tail = content.slice(activeSelection.start);
    const tailIndex = tail.indexOf(normalized);
    if (tailIndex >= 0) index = activeSelection.start + tailIndex;
  }
  if (index < 0) return null;
  return rangeFromTextOffsets(index, index + normalized.length);
}

function replacementTargetRange(originalText) {
  if (restoreRange()) {
    const selection = window.getSelection();
    if (selection.rangeCount) {
      const range = selection.getRangeAt(0);
      const rangeText = normalizeText(range.toString());
      if (isInsideEditor(range.commonAncestorContainer) && rangeText && (!originalText || rangeText === normalizeText(originalText))) {
        return range;
      }
    }
  }
  const offsetRange = rangeFromTextOffsets(activeSelection?.start, activeSelection?.end);
  if (offsetRange && normalizeText(offsetRange.toString()) === normalizeText(originalText || activeSelection?.text || "")) {
    return offsetRange;
  }
  return rangeFromExactText(originalText || activeSelection?.text || "");
}

function selectAcceptedNode(node) {
  const selection = window.getSelection();
  const nextRange = document.createRange();
  nextRange.selectNodeContents(node);
  suppressSelectionCaptureUntil = Date.now() + PROGRAMMATIC_SELECTION_COOLDOWN_MS;
  selection.removeAllRanges();
  selection.addRange(nextRange);
  activeRange = nextRange.cloneRange();
  activeSelection = { text: node.textContent || "", ...getTextOffsets(nextRange) };
}

function selectedPayload() {
  const all = plainText();
  const start = activeSelection?.start ?? all.indexOf(activeSelection?.text || "");
  const end = activeSelection?.end ?? start + (activeSelection?.text || "").length;
  return {
    documentId: currentDocumentId || "inline-editor-v2",
    threadId: bridgeStatusNode.dataset.threadId || "",
    engine: rewriteEngine,
    action: activeMode,
    selectedText: activeSelection?.text || "",
    contextBefore: start >= 0 ? all.slice(Math.max(0, start - 500), start) : "",
    contextAfter: end >= 0 ? all.slice(end, Math.min(all.length, end + 500)) : "",
    documentText: all,
    selection: { start, end },
    auditIssue: currentAuditIssue
      ? {
          kind: currentAuditIssue.kind || "",
          category: currentAuditIssue.category || "",
          reason: currentAuditIssue.reason || "",
          paragraphIndex: currentAuditIssue.paragraphIndex,
          suggestion: currentAuditIssue.suggestion || "",
          previewText: currentAuditIssue.previewText || "",
          previewReason: currentAuditIssue.previewReason || "",
          previewMove: currentAuditIssue.previewMove || "",
        }
      : null,
  };
}

function promptParagraphPayload() {
  const livePromptParagraph = refreshPromptParagraphFromEditor();
  const promptText = livePromptParagraph?.prompt || "";
  if (!promptText) return null;
  const all = plainText();
  const start = livePromptParagraph.blockStart ?? all.indexOf(livePromptParagraph.blockText || "");
  const end = livePromptParagraph.blockEnd ?? start + (livePromptParagraph.blockText || "").length;
  return {
    documentId: currentDocumentId || "inline-editor-v2",
    title: currentTitle(),
    promptText,
    promptParagraphText: livePromptParagraph.blockText || "",
    previousParagraph: livePromptParagraph.previousParagraph || "",
    nextParagraph: livePromptParagraph.nextParagraph || "",
    contextBefore: start >= 0 ? all.slice(Math.max(0, start - 1200), start) : "",
    contextAfter: end >= 0 ? all.slice(end, Math.min(all.length, end + 1200)) : "",
    documentText: all,
    insertion: {
      start,
      end,
      paragraphIndex: livePromptParagraph.paragraphIndex,
    },
  };
}

function promptNeedsResearch(promptText) {
  const text = normalizeText(promptText || "");
  return /(调研|研究|查一下|搜一下|找一下|搜几个|举例|例子|最新|主流|报道|论文|评论|说法|最爱怎么说|常见句子|AI味|套话)/i.test(text);
}

function focusParagraphAssistPromptInput() {
  if (!activePromptParagraph?.block || !editor.contains(activePromptParagraph.block)) return;
  placeCaretInParagraph(activePromptParagraph.block);
}

function placeCaretInParagraph(node) {
  if (!node || !editor.contains(node)) return false;
  const range = document.createRange();
  range.selectNodeContents(node);
  range.collapse(true);
  const selection = window.getSelection();
  suppressSelectionCaptureUntil = Date.now() + 220;
  selection.removeAllRanges();
  selection.addRange(range);
  activeCaretRange = range.cloneRange();
  activePromptParagraph = promptParagraphStateFromRange(range);
  updateParagraphAssistState();
  return true;
}

function activateParagraphAssistSlot(slot, message = "已新开待写段。", options = {}) {
  if (!slot || !editor.contains(slot)) return false;
  paragraphAssistRecentlyActivatedUntil = Date.now() + 360;
  syncParagraphAssistSlotVisual(slot);
  placeCaretInParagraph(slot);
  if (!options.silent && message) jobStateNode.textContent = message;
  scheduleParagraphAssistInlineBarSync();
  return true;
}

function materializeParagraphAssistSlot(block, message = "已定位到待写段。") {
  if (!block || !editor.contains(block)) return false;
  recordEditorUndoBoundary();
  const existing = pruneParagraphAssistSlots();
  if (existing) {
    if (existing === block) {
      activateParagraphAssistSlot(existing, message);
      return true;
    }
    if (paragraphAssistSlotText(existing)) {
      activateParagraphAssistSlot(existing, "已经有一段待写需求，先写完或清空它。");
      return true;
    }
    block.replaceWith(existing);
    syncParagraphAssistSlotVisual(existing);
    window.requestAnimationFrame(() => {
      existing.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    activateParagraphAssistSlot(existing, "已把待写段移到这里。");
    markDraftChanged();
    scheduleSave();
    return true;
  }
  block.innerHTML = "<br>";
  block.dataset.paragraphAssistSlot = "1";
  block.dataset.empty = "1";
  block.dataset.label = "待写段";
  block.dataset.placeholder = "写一句需求，按回车生成。例：这里接一下前后两段，补一个具体例子。";
  block.className = "paragraph-assist-slot is-fresh";
  activateParagraphAssistSlot(block, message);
  window.setTimeout(() => activateParagraphAssistSlot(block, message), 0);
  window.setTimeout(() => activateParagraphAssistSlot(block, message), 90);
  window.setTimeout(() => block.classList.remove("is-fresh"), 320);
  markDraftChanged();
  scheduleSave();
  return true;
}

function createParagraphAssistSlotAfter(block) {
  if (!block || !editor.contains(block)) return false;
  recordEditorUndoBoundary();
  const existing = pruneParagraphAssistSlots();
  if (existing) {
    if (existing === block.nextElementSibling) {
      activateParagraphAssistSlot(existing, "继续写这一段。");
      return true;
    }
    if (paragraphAssistSlotText(existing)) {
      activateParagraphAssistSlot(existing, "已经有一段待写需求，先写完或清空它。");
      return true;
    }
    block.insertAdjacentElement("afterend", existing);
    syncParagraphAssistSlotVisual(existing);
    window.requestAnimationFrame(() => {
      existing.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    activateParagraphAssistSlot(existing, "已把待写段移到这里。");
    return true;
  }
  const slot = document.createElement("p");
  slot.appendChild(document.createElement("br"));
  slot.dataset.paragraphAssistSlot = "1";
  slot.dataset.empty = "1";
  slot.dataset.label = "待写段";
  slot.dataset.placeholder = "写一句需求，按回车生成。例：这里接一下前后两段，补一个具体例子。";
  slot.className = "paragraph-assist-slot is-fresh";
  block.insertAdjacentElement("afterend", slot);
  window.requestAnimationFrame(() => {
    slot.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  activateParagraphAssistSlot(slot);
  window.setTimeout(() => activateParagraphAssistSlot(slot, "已定位到待写段。"), 0);
  window.setTimeout(() => activateParagraphAssistSlot(slot, "已定位到待写段。"), 90);
  window.setTimeout(() => slot.classList.remove("is-fresh"), 320);
  markDraftChanged();
  scheduleSave();
  return true;
}

function handleParagraphAssistDblclick(event) {
  const gapTarget = paragraphGapTargetFromClientY(event.clientY);
  if (gapTarget?.afterBlock) {
    event.preventDefault();
    createParagraphAssistSlotAfter(gapTarget.afterBlock);
    return;
  }
  const selection = window.getSelection();
  const selectedText = normalizeText(selection?.toString() || "");
  if (selectedText) return;
  if (isBlankParagraphAssistTarget()) {
    activateParagraphAssistSlot(activePromptParagraph.block, "继续写这段。");
    return;
  }
  const block =
    editorBlockForNode(event.target) ||
    editorBlockForNode(selection?.anchorNode) ||
    activePromptParagraph?.block ||
    null;
  if (!block) return;
  if (isParagraphAssistSlot(block)) {
    activateParagraphAssistSlot(block, "继续写这段。");
    return;
  }
  if (isEmptyEditorParagraph(block)) {
    event.preventDefault();
    materializeParagraphAssistSlot(block);
  }
}

function handleParagraphAssistClick(event) {
  const slot = event.target.closest?.('p[data-paragraph-assist-slot="1"]');
  if (!slot || !editor.contains(slot)) return;
  window.setTimeout(() => {
    const selection = window.getSelection();
    if (selection?.rangeCount) {
      const range = selection.getRangeAt(0);
      const block = editorBlockForNode(range.startContainer);
      if (block === slot) {
        activeCaretRange = range.cloneRange();
        activePromptParagraph = promptParagraphStateFromRange(range);
        updateParagraphAssistState();
        return;
      }
    }
    activateParagraphAssistSlot(slot, "", { silent: true });
  }, 0);
}

function handleParagraphAssistPaste(event) {
  const slot = paragraphAssistSlotFromContext(event.target);
  const rawText = event.clipboardData?.getData("text/plain") || "";
  if (!normalizeClipboardText(rawText)) return;
  event.preventDefault();
  if (slot) {
    const text = sanitizeParagraphAssistPromptText(rawText);
    const selection = window.getSelection();
    const block = selection?.rangeCount ? editorBlockForNode(selection.getRangeAt(0).startContainer) : null;
    if (block !== slot) {
      activateParagraphAssistSlot(slot, "", { silent: true });
    }
    recordEditorUndoBoundary();
    if (!insertTextAtEditorSelection(text)) {
      slot.textContent = text;
      activateParagraphAssistSlot(slot, "", { silent: true });
    }
  } else if (!insertPlainTextAtEditorSelection(rawText)) {
    return;
  }
  editor.dispatchEvent(
    new InputEvent("input", {
      bubbles: true,
      data: normalizeClipboardText(rawText),
      inputType: "insertFromPaste",
    })
  );
}

function paragraphNodesFromText(text) {
  const parts = String(text || "")
    .split(/\n\s*\n+/)
    .map((part) => normalizeText(part))
    .filter(Boolean);
  if (!parts.length) return [];
  return parts.map((part) => {
    const node = document.createElement("p");
    node.textContent = part;
    return node;
  });
}

function promptParagraphTarget() {
  if (activePromptParagraph?.block && editor.contains(activePromptParagraph.block)) {
    return activePromptParagraph;
  }
  if (activePromptParagraph?.isAssistSlot) {
    const block = editor.querySelector('p[data-paragraph-assist-slot="1"]');
    if (!block) return null;
    const range = document.createRange();
    range.selectNodeContents(block);
    return promptParagraphStateFromRange(range);
  }
  const promptText = normalizeText(activePromptParagraph?.blockText || "");
  if (!promptText) return null;
  const block = editorBlockNodes().find((node) => normalizeText(node.innerText || "") === promptText);
  if (!block) return null;
  const range = document.createRange();
  range.selectNodeContents(block);
  return promptParagraphStateFromRange(range);
}

function refreshPromptParagraphFromEditor() {
  const selection = window.getSelection();
  if (selection?.rangeCount) {
    const range = selection.getRangeAt(0);
    if (isInsideEditor(range.commonAncestorContainer)) {
      const live = promptParagraphStateFromRange(range);
      if (live) {
        activeCaretRange = range.cloneRange();
        activePromptParagraph = live;
        return live;
      }
    }
  }
  const filledSlot = paragraphAssistSlots().find((slot) => paragraphAssistSlotText(slot));
  if (!filledSlot) return activePromptParagraph;
  const range = document.createRange();
  range.selectNodeContents(filledSlot);
  const fallback = promptParagraphStateFromRange(range);
  if (fallback) {
    activePromptParagraph = fallback;
    return fallback;
  }
  return activePromptParagraph;
}

function replacePromptParagraph(text) {
  const target = promptParagraphTarget();
  if (!target?.block) {
    jobStateNode.textContent = "待写段位置找不到了，请把光标重新点进那一段。";
    setParagraphAssistPanel("待定位", "重新点回那一段。");
    updateParagraphAssistState();
    return;
  }
  const nodes = paragraphNodesFromText(text);
  if (!nodes.length) {
    jobStateNode.textContent = "模型没有返回可插入的新段。";
    return;
  }
  recordEditorUndoBoundary();
  const fragment = document.createDocumentFragment();
  nodes.forEach((node) => fragment.appendChild(node));
  target.block.replaceWith(fragment);
  const firstInserted = nodes[0];
  selectAcceptedNode(firstInserted);
  activePromptParagraph = null;
  paragraphAssistRecentlyAppliedUntil = Date.now() + 1800;
  setSelectionSummary(`已补段：${normalizeText(firstInserted.textContent || "").slice(0, 80)}`, "已补段");
  setParagraphAssistPanel("已补段", "这一段已写回正文。");
  hideParagraphAssistInlineBar();
  updateSelectionActionState();
  updateParagraphAssistState();
  jobStateNode.textContent = "已把新段写回正文。";
  markDraftChanged();
  scheduleSave();
}

function replaceSelection(text, options = {}) {
  const continueAudit = Boolean(options.continueAudit);
  const originalText = activeSelection?.text || "";
  if (continueAudit) {
    rewriteRunId += 1;
    window.clearInterval(activeJobTimer);
    window.localStorage.removeItem(pendingJobKey);
  }
  const range = replacementTargetRange(originalText);
  if (!range) {
    setSelectionSummary("没有命中原选句，请重新划选。", "替换失败");
    jobStateNode.textContent = "选区已经失效，正文没有改动。";
    updateSelectionActionState();
    return;
  }
  recordEditorUndoBoundary();
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  const normalizedReplacement = normalizeText(text);
  const replacementParagraphs = normalizedReplacement
    .split(/\n\s*\n+/)
    .map((part) => normalizeText(part))
    .filter(Boolean);
  const blockTarget =
    range.commonAncestorContainer.nodeType === Node.ELEMENT_NODE
      ? range.commonAncestorContainer.closest?.("p")
      : range.commonAncestorContainer.parentElement?.closest?.("p");
  if (replacementParagraphs.length > 1 && blockTarget && normalizeText(blockTarget.innerText || "") === normalizeText(activeSelection?.text || "")) {
    const inserted = replacementParagraphs.map((part) => {
      const paragraph = document.createElement("p");
      paragraph.className = "accepted-change";
      paragraph.textContent = part;
      return paragraph;
    });
    blockTarget.replaceWith(...inserted);
    const nextRange = document.createRange();
    nextRange.selectNodeContents(inserted[0]);
    suppressSelectionCaptureUntil = Date.now() + PROGRAMMATIC_SELECTION_COOLDOWN_MS;
    selection.removeAllRanges();
    selection.addRange(nextRange);
    activeRange = nextRange.cloneRange();
    activeSelection = { text: inserted[0].textContent || "", ...getTextOffsets(nextRange) };
    setSelectionSummary(`已替换：${inserted.map((node) => node.textContent).join(" / ")}`, "已替换");
    updateSelectionActionState();
    jobStateNode.textContent = continueAudit ? "已接受这条改法，准备跳到下一条问题。" : "已接受当前改法。";
    markDraftChanged();
    scheduleSave();
    if (continueAudit) {
      window.setTimeout(() => {
        jumpToNextAuditIssue();
      }, 260);
    }
    return;
  }
  range.deleteContents();
  const node = document.createElement("span");
  node.className = "accepted-change";
  node.textContent = normalizedReplacement;
  range.insertNode(node);
  const next = node.nextSibling;
  if (next && next.nodeType === Node.TEXT_NODE && /[。！？!?；;]$/.test(node.textContent || "")) {
    next.textContent = next.textContent.replace(/^[，,。！？!?；;]+/, "");
  }
  selectAcceptedNode(node);
  setSelectionSummary(`已替换：${node.textContent}`, "已替换");
  updateSelectionActionState();
  jobStateNode.textContent = continueAudit ? "已接受这条改法，准备跳到下一条问题。" : "已接受当前改法。";
  markDraftChanged();
  scheduleSave();
  if (continueAudit) {
    window.setTimeout(() => {
      jumpToNextAuditIssue();
    }, 260);
  }
}

function renderRewriteLoading(message = "正在用模型改句...", options = {}) {
  candidateListNode.dataset.surface = options.surface || "rewrite";
  candidateListNode.innerHTML = "";

  const card = document.createElement("div");
  card.className = "rewrite-loading-card";
  card.setAttribute("role", "status");
  card.setAttribute("aria-live", "polite");

  const spinner = document.createElement("span");
  spinner.className = "rewrite-spinner";
  spinner.setAttribute("aria-hidden", "true");

  const copy = document.createElement("div");
  copy.className = "rewrite-loading-copy";

  const title = document.createElement("strong");
  title.className = "rewrite-loading-title";
  title.textContent = sanitizeVisibleModelText(message);
  copy.appendChild(title);

  if (options.detail) {
    const detail = document.createElement("p");
    detail.className = "rewrite-loading-detail";
    detail.textContent = sanitizeVisibleModelText(options.detail);
    copy.appendChild(detail);
  }

  const meta = document.createElement("span");
  meta.className = "rewrite-loading-meta";
  meta.textContent = sanitizeVisibleModelText(options.meta || "0s");
  copy.appendChild(meta);

  card.appendChild(spinner);
  card.appendChild(copy);
  candidateListNode.appendChild(card);
  refreshRewriteSurface();
}

function renderParagraphAssistLoading(message = "正在结合上下文补这一段...", options = {}) {
  renderRewriteLoading(message, {
    surface: "paragraph-assist",
    detail: options.detail,
    meta: options.meta,
  });
}

function renderCandidates(variants, options = {}) {
  candidateListNode.innerHTML = "";
  const selectedText = options.selectedText ?? activeSelection?.text ?? "";
  const paragraphAssist = Boolean(options.paragraphAssist);
  candidateListNode.dataset.surface = paragraphAssist ? "paragraph-assist" : "rewrite";
  if (paragraphAssist) delete candidateListNode.dataset.selectedText;
  else candidateListNode.dataset.selectedText = normalizeText(selectedText);
  let filtered = usefulCandidates(variants || [], selectedText);
  const weakButUsable = !filtered.length ? relaxedCandidates(variants || [], selectedText) : [];
  if (!filtered.length && weakButUsable.length) {
    filtered = weakButUsable;
    options = { ...options, weakCandidates: true };
  }
  if (!filtered.length) {
    const originalCount = Array.isArray(variants) ? variants.length : 0;
    candidateListNode.textContent = paragraphAssist
      ? "这段没写好，已拦下。"
      : originalCount
        ? "这组候选像原句换皮，已拦下。请重新生成或换一小段选区。"
        : "没有候选。";
    if (originalCount) jobStateNode.textContent = paragraphAssist ? "这段没写好，换一组再试。" : "候选质量不够，已拦下。";
    refreshRewriteSurface();
    return;
  }
  if (options.issueLabel) {
    const label = document.createElement("p");
    label.className = "candidate-label";
    label.textContent = `这组候选正在修：${options.issueLabel}`;
    candidateListNode.appendChild(label);
  }
  if (paragraphAssist) appendParagraphAssistProof(options.assistProof);
  else appendMemoryProof(options.memoryProof);
  if (options.weakCandidates) {
    const weakLabel = document.createElement("p");
    weakLabel.className = "candidate-label weak-candidate-line";
    weakLabel.textContent = "这组改动偏弱，先展示给你判断；记住改法后会反向训练下一轮。";
    candidateListNode.appendChild(weakLabel);
  }
  filtered.forEach((variant, index) => {
    const item = document.createElement("div");
    item.className = options.preview ? "candidate preview" : "candidate";
    item.innerHTML = `
      <div class="candidate-head"><span></span><span></span></div>
      <p class="candidate-text"></p>
      <p class="candidate-reason"></p>
      <p class="candidate-memory-note" hidden></p>
      <div class="candidate-actions">
        <button type="button" data-accept>接受</button>
        <button type="button" data-save>记住改法</button>
      </div>
    `;
    item.querySelector(".candidate-head span:first-child").textContent = paragraphAssist
      ? variant.label || `候选 ${index + 1}`
      : `候选 ${index + 1}`;
    item.querySelector(".candidate-head span:last-child").textContent = options.preview
      ? "本地"
      : paragraphAssist
        ? `候选 ${index + 1}`
        : "";
    if (options.preview || paragraphAssist) item.querySelector(".candidate-head span:last-child").className = "candidate-source";
    item.querySelector(".candidate-text").textContent = variant.text || "";
    const reasonNode = item.querySelector(".candidate-reason");
    const memoryNoteNode = item.querySelector(".candidate-memory-note");
    reasonNode.textContent = paragraphAssist ? "" : variant.reason || "";
    reasonNode.hidden = paragraphAssist || !variant.reason;
    item.querySelector("[data-accept]").addEventListener("click", () => {
      if (paragraphAssist) {
        replacePromptParagraph(variant.text || "");
        return;
      }
      replaceSelection(variant.text || "", { continueAudit: Boolean(currentAuditIssue) });
    });
    item.querySelector("[data-save]").addEventListener("click", async () => {
      const saveButton = item.querySelector("[data-save]");
      if (!saveButton) return;
      const previousLabel = saveButton.textContent || "记住改法";
      saveButton.disabled = true;
      saveButton.textContent = "记忆中...";
      try {
        const entry = await saveMemory(
          "rewrite_pair",
          variant.text || "",
          variant.reason || (paragraphAssist ? "用户在 V2 候选中保存补段改法" : "用户在 V2 候选中保存改法"),
          paragraphAssist ? "rewrite_pair,v2,paragraph_assist" : "rewrite_pair,v2",
          "example",
          {
            variantMove: variant.move || "",
            variantLabel: variant.label || "",
            paragraphAssist,
            sourcePrompt: paragraphAssist ? activePromptParagraph?.prompt || "" : "",
          }
        );
        const feedback = entry ? memoryToastLine(entry) : "已记住改法";
        const ruleLine = entry ? memoryEntryRuleLine(entry) : "";
        if (memoryNoteNode) {
          memoryNoteNode.textContent = ruleLine || feedback;
          memoryNoteNode.hidden = !(ruleLine || feedback);
        }
        saveButton.textContent = "已记住";
        saveButton.dataset.saved = "true";
        showWorkspaceToast(feedback || "已记住改法");
        await refreshMemory();
      } catch (error) {
        saveButton.disabled = false;
        saveButton.textContent = previousLabel;
        if (memoryNoteNode) {
          memoryNoteNode.textContent = `记忆失败：${error.message}`;
          memoryNoteNode.hidden = false;
        }
        showWorkspaceToast(`记忆失败：${error.message}`, "error");
      }
    });
    candidateListNode.appendChild(item);
  });
  refreshRewriteSurface();
}

function resetRewritePanel() {
  clearActiveSelection();
  if (paragraphAssistPromptInput) paragraphAssistPromptInput.hidden = true;
  candidateListNode.dataset.surface = "idle";
  candidateListNode.textContent = "暂无候选。";
  setSelectionSummary("选一句。", "待选", { idle: true });
  jobStateNode.textContent = "";
  refreshRewriteSurface();
}

function clearStalePendingRewriteForDocument(documentId) {
  try {
    const pending = JSON.parse(window.localStorage.getItem(pendingJobKey) || "{}");
    if (pending.documentId && pending.documentId !== documentId) {
      window.localStorage.removeItem(pendingJobKey);
    }
  } catch (_) {
    window.localStorage.removeItem(pendingJobKey);
  }
}

async function pollJob(responseUrl, runId) {
  const issueLabel = currentAuditIssue?.category || currentAuditIssue?.kind || "";
  const startedAt = Date.now();
  window.clearInterval(activeJobTimer);
  activeJobTimer = window.setInterval(() => {
    if (runId !== rewriteRunId) return;
    const seconds = Math.round((Date.now() - startedAt) / 1000);
    jobStateNode.textContent = `后台改写中：${seconds}s`;
  }, 1000);

  for (let attempt = 0; attempt < 90; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, attempt < 4 ? 300 : 800));
    const data = await api(responseUrl);
    if (data.status === "done") {
      if (runId !== rewriteRunId) return data;
      window.clearInterval(activeJobTimer);
      window.localStorage.removeItem(pendingJobKey);
      renderCandidates(data.variants || [], { issueLabel, selectedText: activeSelection?.text || "", memoryProof: data.memoryProof });
      jobStateNode.textContent = `完成：改句助手返回 ${data.variants?.length || 0} 个候选`;
      setSelectionSummary(activeSelection?.text || selectedTextNode?.textContent || "", "有候选");
      return data;
    }
    if (data.status === "error") {
      if (runId !== rewriteRunId) return data;
      window.clearInterval(activeJobTimer);
      window.localStorage.removeItem(pendingJobKey);
      jobStateNode.textContent = `失败：${data.error || "unknown error"}`;
      setSelectionSummary(activeSelection?.text || selectedTextNode?.textContent || "", "失败");
      return data;
    }
  }
  window.clearInterval(activeJobTimer);
  jobStateNode.textContent = "后台超时。任务可能仍在队列里，可以稍后刷新。";
  return null;
}

async function runRewrite(options = {}) {
  const fromAudit = Boolean(options.fromAudit);
  const keepAuditSelection = Boolean(options.keepAuditSelection);
  const auditContext = options.auditIssue || currentAuditIssue || null;
  const issueLabel = auditContext?.category || auditContext?.kind || "";
  const runId = ++rewriteRunId;
  const rewriteStartedAt = Date.now();
  const waitDetail = issueLabel
    ? `当前问题：${issueLabel}。${fromAudit ? "已按收稿定位到这一段。" : "只改这一句，"}不自动改正文。`
    : "只改当前选句，保留原意，返回 2 到 3 个候选。";
  const syncRewriteStatus = (progressText = "") => {
    if (auditContext) rewriteIssueNode.textContent = formatAuditIssue(auditContext);
    if (progressText) rewriteProgressNode.textContent = progressText;
  };
  const updateRewriteProgress = (seconds = 0) => {
    const title =
      seconds <= 0
        ? "已发送给改句助手"
        : seconds < 6
          ? "改句助手正在生成候选"
          : "改句助手仍在返回";
    renderRewriteLoading(title, {
      surface: "rewrite",
      detail: waitDetail,
      meta: `${seconds}s`,
    });
    syncRewriteStatus(seconds <= 0 ? "正在取候选" : `改句中 · ${seconds}s`);
    jobStateNode.textContent = sanitizeVisibleModelText(`改句中 · ${title} · ${seconds}s`);
  };
  if (keepAuditSelection) restoreRange();
  syncActiveSelectionFromWindow({ updateUi: !keepAuditSelection });
  if (!activeSelection?.text) {
    setSelectionSummary("先选一句。", "未选");
    updateSelectionActionState();
    return;
  }
  const problem = selectionProblem(activeSelection.text);
  if (problem) {
    setSelectionSummary(activeSelection.text, "选区不适合改句");
    jobStateNode.textContent = problem;
    updateSelectionActionState();
    return;
  }
  selectionMenu.hidden = true;
  updateRewriteProgress(0);
  setBusy(true);
  window.clearInterval(activeJobTimer);
  activeJobTimer = window.setInterval(() => {
    if (runId !== rewriteRunId) {
      window.clearInterval(activeJobTimer);
      return;
    }
    const seconds = Math.max(0, Math.round((Date.now() - rewriteStartedAt) / 1000));
    updateRewriteProgress(seconds);
  }, 1000);
  try {
    const data = await api("/api/rewrite-selection", {
      method: "POST",
      body: JSON.stringify(selectedPayload()),
    });
    if (runId !== rewriteRunId) return;
    window.clearInterval(activeJobTimer);
    window.localStorage.removeItem(pendingJobKey);
    renderCandidates(data.variants || [], { issueLabel, selectedText: activeSelection?.text || "", memoryProof: data.memoryProof });
    syncRewriteStatus(`已出 ${data.variants?.length || 0} 个候选`);
    jobStateNode.textContent = `完成：改句助手返回 ${data.variants?.length || 0} 个候选`;
    setSelectionSummary(activeSelection?.text || selectedTextNode?.textContent || "", "有候选");
  } catch (error) {
    if (runId !== rewriteRunId) return;
    syncRewriteStatus("改句失败");
    jobStateNode.textContent = `失败：${error.message}`;
    try {
      const fallback = await api("/api/rewrite-selection", {
        method: "POST",
        body: JSON.stringify({ ...selectedPayload(), engine: "heuristic" }),
      });
      if (runId !== rewriteRunId) return;
      if (fallback?.variants?.length) {
        renderCandidates(fallback.variants, { preview: true, issueLabel, memoryProof: fallback.memoryProof });
        syncRewriteStatus(`已出 ${fallback.variants.length} 个候选`);
        jobStateNode.textContent = "模型改写失败，已显示本地兜底候选。";
      } else {
        candidateListNode.innerHTML = '<div class="candidate">没有返回候选。</div>';
        syncRewriteStatus("没有返回候选");
      }
    } catch (_) {
      candidateListNode.innerHTML = '<div class="candidate">没有返回候选。</div>';
      syncRewriteStatus("没有返回候选");
    }
  } finally {
    if (runId === rewriteRunId) {
      window.clearInterval(activeJobTimer);
      setBusy(false);
    }
  }
}

async function runParagraphAssist() {
  const livePromptParagraph = refreshPromptParagraphFromEditor() || activePromptParagraph;
  const promptPayload = promptParagraphPayload();
  const runId = ++paragraphAssistRunId;
  const promptSlot = livePromptParagraph?.isAssistSlot
    ? livePromptParagraph.block
    : currentParagraphAssistSlot() || paragraphAssistSlotFromContext() || editor.querySelector('p[data-paragraph-assist-slot="1"]');
  if (!promptPayload?.promptText) {
    setParagraphAssistPanel("待写段", "先写一句需求。");
    jobStateNode.textContent = "还没有待写段。";
    updateParagraphAssistState();
    return;
  }
  selectionMenu.hidden = true;
  const wantsResearch = promptNeedsResearch(promptPayload.promptText);
  const paragraphAssistStartedAt = Date.now();
  const promptSummary = briefParagraphAssistPrompt(promptPayload.promptText, 36);
  const updateParagraphAssistProgress = (seconds = 0) => {
    const title = wantsResearch
      ? seconds <= 0
        ? "已发送给写作助手"
        : seconds < 6
          ? "写作助手正在先找线索"
          : "写作助手仍在整理候选"
      : seconds <= 0
        ? "已发送给写作助手"
        : seconds < 6
          ? "写作助手正在结合上下段补写"
          : "写作助手仍在整理候选";
    renderParagraphAssistLoading(title, {
      detail: `需求：${promptSummary || "补这一段"}`,
      meta: `${seconds}s`,
    });
    const visibleProgress = sanitizeVisibleModelText(`${title} · ${seconds}s`);
    setParagraphAssistSlotRunState(promptSlot, "running", visibleProgress);
    setParagraphAssistPanel("补写中", visibleProgress);
    jobStateNode.textContent = sanitizeVisibleModelText(`补段中 · ${visibleProgress}`);
  };
  updateParagraphAssistProgress(0);
  setBusy(true);
  window.clearInterval(activeJobTimer);
  activeJobTimer = window.setInterval(() => {
    if (runId !== paragraphAssistRunId) {
      window.clearInterval(activeJobTimer);
      return;
    }
    const seconds = Math.max(0, Math.round((Date.now() - paragraphAssistStartedAt) / 1000));
    updateParagraphAssistProgress(seconds);
  }, 1000);
  try {
    const data = await api("/api/paragraph-assist", {
      method: "POST",
      body: JSON.stringify(promptPayload),
    });
    if (runId !== paragraphAssistRunId) return;
    window.clearInterval(activeJobTimer);
    renderCandidates(data.variants || [], {
      paragraphAssist: true,
      selectedText: "",
      issueLabel: `补这一段：${promptPayload.promptText}`,
      assistProof: data.assistProof,
    });
    setParagraphAssistPanel("有候选", "选一个候选，直接写回正文。");
    const researchNote = data.researchUsed ? `，参考了 ${data.researchHits || 0} 条线索` : "";
    setParagraphAssistSlotRunState(
      promptSlot,
      "ready",
      `已生成 ${data.variants?.length || 0} 个候选，右侧选一个写回正文${researchNote || ""}。`
    );
    jobStateNode.textContent = sanitizeVisibleModelText(data.assistProof?.summaryLine || "") || `完成：写作助手返回 ${data.variants?.length || 0} 个段落候选${researchNote}`;
  } catch (error) {
    if (runId !== paragraphAssistRunId) return;
    window.clearInterval(activeJobTimer);
    setParagraphAssistSlotRunState(promptSlot, "failed", `补段失败：${error.message}`);
    setParagraphAssistPanel("失败", `补段失败：${error.message}`);
    jobStateNode.textContent = `补段失败：${error.message}`;
    candidateListNode.innerHTML = '<div class="candidate">这一段没有生成成功。</div>';
  } finally {
    if (runId === paragraphAssistRunId) {
      window.clearInterval(activeJobTimer);
      setBusy(false);
      if (!["有候选", "已补段", "失败"].includes(paragraphAssistStateNode?.textContent || "")) {
        updateParagraphAssistState();
      }
    }
  }
}

async function recoverLatestResult() {
  try {
    const pending = JSON.parse(window.localStorage.getItem(pendingJobKey) || "{}");
    const documentId = currentDocumentId || "inline-editor-v2";
    if (pending.documentId && pending.documentId !== documentId) {
      window.localStorage.removeItem(pendingJobKey);
    } else if (pending.responseUrl) {
      const data = await api(pending.responseUrl);
      if (data.status === "done") {
        window.localStorage.removeItem(pendingJobKey);
        renderCandidates(data.variants || [], {
          issueLabel: currentAuditIssue?.category || currentAuditIssue?.kind || "",
          selectedText: pending.selectedText || activeSelection?.text || "",
          memoryProof: data.memoryProof || data.memory_proof,
        });
        jobStateNode.textContent = `已取回：改句助手返回 ${data.variants?.length || 0} 个候选`;
        setSelectionSummary(pending.selectedText || activeSelection?.text || selectedTextNode?.textContent || "", "有候选");
        return data;
      }
      jobStateNode.textContent = `任务仍在后台：${pending.id || data.request_id || ""}`;
      return data;
    }
    const latest = await api(`/api/latest-selection-response?documentId=${encodeURIComponent(documentId)}`);
    renderCandidates(latest.variants || [], {
      issueLabel: currentAuditIssue?.category || currentAuditIssue?.kind || "",
      selectedText: latest.selected_text || activeSelection?.text || "",
      memoryProof: latest.memoryProof || latest.memory_proof,
    });
    jobStateNode.textContent = `已取回最近结果：改句助手返回 ${latest.variants?.length || 0} 个候选`;
    setSelectionSummary(latest.selected_text || activeSelection?.text || selectedTextNode?.textContent || "", "有候选");
    return latest;
  } catch (error) {
    jobStateNode.textContent = `没有可取回结果：${error.message}`;
    return null;
  }
}

function focusRecordActions() {
  if (actionDetailNode) {
    actionDetailNode.hidden = false;
    actionDetailNode.setAttribute("open", "");
  }
  const feedbackRow = document.querySelector(".feedback-row");
  if (!feedbackRow) return;
  feedbackRow.scrollIntoView({ behavior: "smooth", block: "center" });
  if (activeSelection?.text) {
    jobStateNode.textContent = "选讨厌或喜欢，会记进风格库。";
  } else {
    jobStateNode.textContent = "先划选一句，再记录喜欢或讨厌。";
  }
  document.querySelector("#saveBad")?.focus({ preventScroll: true });
}

async function saveMemory(kind, replacementText = "", reason = "", tags = "", strength = "soft", meta = {}) {
  syncActiveSelectionFromWindow();
  if (!activeSelection?.text) {
    setSelectionSummary("先选一句。", "未选");
    updateSelectionActionState();
    return null;
  }
  const selectedText = activeSelection.text;
  const entry = await api("/api/memory", {
    method: "POST",
    body: JSON.stringify({
      kind,
      sourceText: selectedText,
      replacementText,
      reason,
      tags,
      strength,
      origin: "inline-editor-v2",
      auditIssue: currentAuditIssue || null,
      ...meta,
    }),
  });
  const label = entry.kind === "banned_line" ? "讨厌库" : entry.kind === "approved_line" ? "喜欢库" : "改法库";
  const shortWhy = memoryEntryUiSummary(entry);
  setSelectionSummary(selectedText, shortWhy ? `已记：${shortWhy}` : `已记入${label}`);
  const why = memoryToastLine(entry);
  const ruleLine = memoryEntryRuleLine(entry);
  const companionRuleLine = entry?.companionRule ? memoryEntryRuleLine(entry.companionRule, { withPrefix: false }) : "";
  const reasonLine = memoryEntryReason(entry);
  jobStateNode.textContent = companionRuleLine
    ? `规则已更新：${companionRuleLine}`
    : ruleLine
      ? `${label}：${ruleLine}`
      : reasonLine
        ? `已记入${label}：${reasonLine}`
        : why
          ? `${label}：${why}`
          : `已记入${label}：${entry.id}`;
  if (companionRuleLine) {
    draftNoticeNode.textContent = `已同步风格规则：${companionRuleLine}`;
  }
  if (memoryFoldNode) memoryFoldNode.open = true;
  void refreshWorkbenchContext();
  return entry;
}

function memoryEntryRule(entry) {
  const meta = entry?.meta && typeof entry.meta === "object" ? entry.meta : {};
  const directRule = normalizeText(meta?.derivedRule || "");
  if (directRule) return directRule;
  if (normalizeText(entry?.kind || "") === "rule") {
    const sourceRule = normalizeText(entry?.source_text || entry?.sourceText || "");
    if (sourceRule) return sourceRule;
  }
  if (Array.isArray(meta?.principles)) {
    const first = meta.principles.map((item) => normalizeText(item)).find(Boolean);
    if (first) return first;
  }
  return "";
}

function memoryRulePrefix(entry) {
  const meta = entry?.meta && typeof entry.meta === "object" ? entry.meta : {};
  const feedbackClass = normalizeText(meta?.feedbackClass || "");
  if (feedbackClass === "avoid" || entry?.kind === "banned_line") return "下次怎么避开";
  if (feedbackClass === "prefer" || entry?.kind === "approved_line") return "下次怎么借";
  if (feedbackClass === "repair" || entry?.kind === "rewrite_pair") return "下次优先";
  if (feedbackClass === "rule" || entry?.kind === "rule") return "规则";
  return "下次怎么用";
}

function memoryEntryRuleLine(entry, options = {}) {
  const rule = memoryEntryRule(entry);
  if (!rule) return "";
  if (options.withPrefix === false) return rule;
  return `${memoryRulePrefix(entry)}：${rule}`;
}

function shortStatusLine(value, maxLength = 28) {
  const text = normalizeText(value || "");
  if (!text) return "";
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
}

function memoryEntryUiSummary(entry) {
  const meta = entry?.meta && typeof entry.meta === "object" ? entry.meta : {};
  const label = normalizeText(meta?.variantLabel || meta?.variantMove || "");
  if (entry?.kind === "rewrite_pair" && label) return label;
  const problemLabels = memoryProblemLabels(entry).slice(0, 2);
  if (problemLabels.length) return problemLabels.join(" / ");
  const tags = Array.isArray(entry?.tags) ? entry.tags.map(memoryTagShortLabel).filter(Boolean) : [];
  const primaryTags = tags.filter((tag) => !/^(banned|approved|rewrite_pair|v2|hard|soft|example)$/i.test(tag)).slice(0, 3);
  if (primaryTags.length) return primaryTags.join(" / ");
  if (label) return label;
  const rule = memoryEntryRule(entry);
  if (rule) return shortStatusLine(rule, 22);
  return normalizeText(entry?.reason || "").replace(/^这句的问题在|这句成立，是因为|这次改法主要在/, "").replace(/[。.]$/, "");
}

function memoryEntryReason(entry) {
  const value = normalizeText(entry?.reason || "");
  if (!value) return "";
  return value.length > 48 ? `${value.slice(0, 48)}…` : value;
}

function memoryEntryMetaLine(entry) {
  const parts = [];
  const meta = entry?.meta && typeof entry.meta === "object" ? entry.meta : {};
  const label = normalizeText(meta?.variantLabel || "");
  const move = normalizeText(meta?.variantMove || "");
  const audit = normalizeText(meta?.audit?.category || meta?.auditCategory || meta?.auditIssue?.category || "");
  if (label) parts.push(label);
  else if (move) parts.push(move);
  if (audit) parts.push(`触发：${audit}`);
  if (meta?.paragraphAssist) parts.push("补段");
  if (Number(entry?.usage_count || 0) > 0) parts.push(`命中 ${Number(entry.usage_count)} 次`);
  return parts.join(" / ");
}

function memoryToastLine(entry) {
  const summary = memoryEntryUiSummary(entry);
  if (summary) return `已记：${summary}`;
  const rule = memoryEntryRuleLine(entry);
  if (rule) return shortStatusLine(rule, 26);
  return "";
}
function memoryTagShortLabel(tag) {
  const value = normalizeText(tag);
  if (!value) return "";
  const parts = value.split(":");
  return parts.length > 1 ? parts.slice(1).join(":") : value;
}

function memoryProblemLabels(entry) {
  const meta = entry?.meta && typeof entry.meta === "object" ? entry.meta : {};
  const profile = meta?.problemProfile && typeof meta.problemProfile === "object" ? meta.problemProfile : {};
  const labels = Array.isArray(profile.labels) ? profile.labels.map((item) => normalizeText(item)).filter(Boolean) : [];
  if (labels.length) return labels;
  const keys = Array.isArray(profile.keys) ? profile.keys.map((item) => normalizeText(item)).filter(Boolean) : [];
  return keys.map((key) =>
    ({
      macro_subject_soft_verb: "大主语软动词",
      false_agency: "假主语假动作",
      pseudo_oral: "伪口语",
      source_pileup: "资料罗列",
      binary_reversal: "二段反转",
      cheap_suspense_hook: "空悬念",
      blank_judgment: "空泛判断",
      half_sentence_note: "像半句",
      report_voice: "报告腔",
      abstract_noun_load: "抽象词过多",
      looks_complete_but_hollow: "外观看似完整",
      engineering_register: "工程腔",
      meta_opening: "解释题目",
      light_heavy_contrast: "轻重对照",
      no_object_or_action: "缺对象动作",
      no_real_scene: "缺真实场景",
      no_writing_action: "缺写作动作",
      fake_depth: "假深刻",
      not_body_ready: "没落正文",
      no_grounding: "没落地",
    }[key] || key)
  );
}

function memoryProofLine(proof) {
  if (!proof || proof.status === "empty") return "";
  const counts = proof.counts || {};
  const total = Number(counts.hardBans || 0) + Number(counts.approved || 0) + Number(counts.rewritePairs || 0);
  const applied = proof.applied && typeof proof.applied === "object" ? proof.applied : {};
  const parts = [];
  [
    ["avoid", "避开"],
    ["prefer", "靠近"],
    ["repair", "改法"],
  ].forEach(([key, label]) => {
    const item = applied[key] && typeof applied[key] === "object" ? applied[key] : null;
    const value = normalizeText(item?.label || item?.rule || "");
    if (value) parts.push(`${label}${value}`);
  });
  if (parts.length) return `本次带入 ${total || parts.length} 条偏好：${parts.slice(0, 3).join(" / ")}`;
  const focusLine = normalizeText(proof.focusLine || "");
  if (focusLine) return focusLine;
  const summary = normalizeText(proof.summary || "");
  if (summary) return summary;
  return total ? `本次带入 ${total} 条偏好。` : "";
}

function appendMemoryProof(proof) {
  const line = memoryProofLine(proof);
  if (!line) return;
  const label = document.createElement("p");
  label.className = "candidate-label memory-proof-line";
  label.textContent = line;
  candidateListNode.appendChild(label);
}

function appendParagraphAssistProof(proof) {
  if (!proof || typeof proof !== "object") return;
  const lines = [normalizeText(proof.summaryLine || ""), normalizeText(proof.focusLine || "")]
    .filter(Boolean)
    .slice(0, 2);
  lines.forEach((line, index) => {
    const label = document.createElement("p");
    label.className = `candidate-label paragraph-assist-proof-line${index ? " secondary" : ""}`;
    label.textContent = line;
    candidateListNode.appendChild(label);
  });
}

function memoryKindLabel(kind) {
  return {
    banned_line: "讨厌句",
    approved_line: "喜欢句",
    rewrite_pair: "改法",
    rule: "规则",
  }[kind] || kind;
}

function renderMemorySummary(summary) {
  if (!memorySummaryNode) return;
  if (!summary) {
    memorySummaryNode.textContent = "硬禁 / 喜欢 / 改法：暂无。";
    return;
  }
  const line = summary.compactLine || summary.line || "暂无稳定反感模式。";
  memorySummaryNode.textContent = line;
}

function renderMemory(entries) {
  memoryCountNode.textContent = `${entries.length} 条`;
  memoryListNode.innerHTML = "";
  if (!entries.length) {
    memoryListNode.textContent = "暂无记录。";
    return;
  }
  const ordered = [...entries].sort((left, right) =>
    String(right.last_used_at || right.updated_at || "").localeCompare(String(left.last_used_at || left.updated_at || ""))
  );
  ordered.slice(0, 8).forEach((entry) => {
    const item = document.createElement("div");
    item.className = `memory-entry ${entry.kind}`;
    item.innerHTML = "<strong></strong><p class=\"memory-text\"></p><p class=\"memory-meta\"></p><p class=\"memory-rule\"></p><p class=\"memory-detail\"></p>";
    item.querySelector("strong").textContent = `${memoryKindLabel(entry.kind)} · ${entry.strength}`;
    item.querySelector(".memory-text").textContent = entry.replacement_text
      ? `${entry.source_text} -> ${entry.replacement_text}`
      : entry.source_text;
    const meta = [];
    const shortWhy = memoryEntryUiSummary(entry);
    const metaLine = memoryEntryMetaLine(entry);
    if (shortWhy) meta.push(shortWhy);
    if (metaLine) meta.push(metaLine);
    item.querySelector(".memory-meta").textContent = meta.join(" · ");
    const ruleLine = memoryEntryRuleLine(entry);
    item.querySelector(".memory-rule").textContent = ruleLine;
    item.querySelector(".memory-rule").hidden = !ruleLine;
    item.querySelector(".memory-detail").textContent = memoryEntryReason(entry);
    item.querySelector(".memory-detail").hidden = !entry.reason;
    memoryListNode.appendChild(item);
  });
}

function documentFilterApiParams() {
  const params = new URLSearchParams();
  if (documentSearchQuery) params.set("q", documentSearchQuery);
  if (currentDocumentFilter === "deleted") {
    params.set("deleted", "1");
  } else if (currentDocumentFilter === "formal" || currentDocumentFilter === "experiment") {
    params.set("type", currentDocumentFilter);
  }
  return params.toString();
}

function syncDocumentFilterButtons() {
  documentFilterButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.documentFilter === currentDocumentFilter);
  });
}

function topicManagementMode() {
  return Boolean(topicManageFoldNode?.open);
}

function renderDocuments(entries) {
  if (!documentListNode) return;
  documentListNode.innerHTML = "";
  syncDocumentFilterButtons();
  const managementMode = topicManagementMode();
  if (!entries.length) {
    documentListNode.textContent = currentDocumentFilter === "deleted"
      ? "暂无已删除主题。"
      : currentDocumentFilter === "formal"
        ? managementMode
          ? "暂无正式主题。"
          : "暂无正式主题。实验稿和已删除主题在“管理主题”里。"
        : "暂无匹配主题。";
    return;
  }
  const deletedMode = currentDocumentFilter === "deleted";
  const orderedEntries = currentDocumentId
    ? [...entries.filter((entry) => entry.documentId === currentDocumentId), ...entries.filter((entry) => entry.documentId !== currentDocumentId)]
    : entries;
  const visibleEntries = managementMode ? orderedEntries.slice(0, 20) : orderedEntries.slice(0, 6);
  visibleEntries.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "document-item";
    item.dataset.documentId = entry.documentId || "";
    if (entry.documentId === currentDocumentId) item.classList.add("is-current");
    if (deletedMode) item.classList.add("is-deleted");
    item.innerHTML = `
      <div class="doc-head">
        <strong></strong>
        <span class="doc-kind"></span>
      </div>
      <p class="doc-updated"></p>
      <p class="doc-provenance"></p>
      <div class="doc-actions">
        ${
          deletedMode
            ? '<button type="button" class="doc-restore">恢复</button>'
            : '<button type="button" class="doc-open">打开</button><button type="button" class="doc-delete">删除</button>'
        }
      </div>
    `;
    item.querySelector("strong").textContent = entry.title || entry.documentId;
    item.querySelector(".doc-kind").textContent = documentTypeLabel(entry.documentType);
    item.querySelector(".doc-updated").textContent = `${deletedMode ? "删除前更新" : "更新"}：${entry.updatedAt || "未知"}`;
    item.querySelector(".doc-provenance").textContent = formatDocumentProvenance(entry.metadata, { compact: true });
    if (deletedMode) {
      item.querySelector(".doc-restore").addEventListener("click", async () => {
        const title = entry.title || entry.documentId || "这个主题";
        await api("/api/document/restore", {
          method: "POST",
          body: JSON.stringify({ documentId: entry.documentId }),
        });
        showWorkspaceToast(`已恢复主题：${title}`);
        currentDocumentFilter = normalizeDocumentType(entry.documentType) || "formal";
        await refreshDocuments();
      });
    } else {
      item.querySelector(".doc-open").addEventListener("click", async () => {
        await openDocument(entry.documentId);
        if (topicFoldNode) topicFoldNode.open = false;
      });
      const deleteButton = item.querySelector(".doc-delete");
      if (deleteButton) {
        deleteButton.addEventListener("click", async () => {
          const title = entry.title || entry.documentId || "这个主题";
          const confirmed = window.confirm(`从主题列表删除「${title}」？\n\n会移到本地 deleted_documents 里，不会直接清空正文。`);
          if (!confirmed) return;
          const isFormal = normalizeDocumentType(entry.documentType) === "formal";
          if (isFormal) {
            const formalConfirmed = window.confirm(`「${title}」是正式稿。\n\n确认移到已删除主题？`);
            if (!formalConfirmed) return;
          }
          const confirmParam = isFormal ? "&confirmFormal=1" : "";
          await api(`/api/document?documentId=${encodeURIComponent(entry.documentId)}${confirmParam}`, { method: "DELETE" });
          showWorkspaceToast(`已移出主题列表：${title}`);
          await refreshDocuments();
        });
      }
    }
    documentListNode.appendChild(item);
  });
}

async function refreshDocuments() {
  const seq = ++documentRefreshSeq;
  const query = documentFilterApiParams();
  const documents = await api(`/api/documents${query ? `?${query}` : ""}`);
  if (seq !== documentRefreshSeq) return;
  renderDocuments(documents);
}

function closeTopicFold(options = {}) {
  if (options.closeManage !== false && topicManageFoldNode) topicManageFoldNode.open = false;
  if (topicFoldNode) topicFoldNode.open = false;
}

function topicArchiveDisplayTitle(archive, entries) {
  const placeholderTitles = new Set(["主稿", "正文", "未命名稿件", "当前主题稿", "新主题稿"]);
  const candidates = [
    currentTitle(),
    archive?.title,
    ...(entries || []).map((entry) => entry?.title),
  ];
  const title = candidates.find((candidate) => {
    const value = normalizeText(candidate);
    return value && !placeholderTitles.has(value);
  });
  return title || "当前主题稿";
}

function topicArchiveProofText(entry) {
  const proof = entry?.styleProofSummary;
  if (!proof || typeof proof !== "object") return "";
  const lines = [];
  const summaryLine = normalizeText(proof.summaryLine);
  const focusLine = normalizeText(proof.focusLine);
  if (summaryLine) lines.push(summaryLine);
  if (focusLine) lines.push(focusLine);
  return lines.join(" · ");
}

function renderTopicArchive(archive) {
  latestTopicArchiveEntries = Array.isArray(archive?.entries) ? archive.entries.slice(0, 5) : [];
  if (!topicArchiveListNode) return;
  topicArchiveListNode.innerHTML = "";
  if (!currentDocumentId) {
    topicArchiveListNode.textContent = "保存后开始记录。";
    renderWorkflowState();
    return;
  }
  if (!latestTopicArchiveEntries.length) {
    topicArchiveListNode.textContent = "暂无存档。";
    renderWorkflowState();
    return;
  }
  const topic = document.createElement("details");
  topic.className = "topic-archive-topic";
  const summaryNode = document.createElement("summary");
  const summaryTitle = document.createElement("strong");
  const summaryMeta = document.createElement("span");
  const topicTitle = topicArchiveDisplayTitle(archive, latestTopicArchiveEntries);
  summaryTitle.textContent = topicTitle;
  summaryMeta.textContent = `最近 ${latestTopicArchiveEntries.length} 次`;
  summaryNode.append(summaryTitle, summaryMeta);
  const versionList = document.createElement("div");
  versionList.className = "topic-archive-version-list";
  latestTopicArchiveEntries.forEach((entry, index) => {
    const item = document.createElement("div");
    item.className = "topic-archive-entry";
    const meta = document.createElement("div");
    const title = document.createElement("strong");
    const summary = document.createElement("span");
    const proof = document.createElement("span");
    const time = document.createElement("span");
    const button = document.createElement("button");
    const updatedAt = entry.updatedAt ? new Date(entry.updatedAt) : null;
    const changeSummary = normalizeText(entry.changeSummary);
    const proofText = topicArchiveProofText(entry);
    title.textContent = changeSummary === "当前保存版"
      ? "当前保存版"
      : changeSummary.startsWith("备份")
        ? "备份"
        : `历史 ${index + 1}`;
    summary.textContent = changeSummary === "当前保存版"
      ? "已保存版本"
      : changeSummary.startsWith("备份：")
        ? changeSummary.replace(/^备份：/, "")
        : entry.changeSummary || entry.title || "有修改";
    proof.className = "topic-archive-proof";
    proof.textContent = proofText;
    proof.hidden = !proofText;
    time.textContent = updatedAt && !Number.isNaN(updatedAt.getTime())
      ? updatedAt.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
      : entry.updatedAt || "";
    button.type = "button";
    button.textContent = "载入";
    button.addEventListener("click", () => loadTopicArchiveEntry(entry));
    if (proofText) {
      item.title = `${summary.textContent}\n${proofText}`;
    }
    meta.append(title, summary, proof, time);
    item.append(meta, button);
    versionList.appendChild(item);
  });
  topic.append(summaryNode, versionList);
  topicArchiveListNode.appendChild(topic);
  renderWorkflowState();
}

async function refreshTopicArchive() {
  if (!topicArchiveListNode) return null;
  if (!currentDocumentId) {
    renderTopicArchive({ entries: [] });
    return null;
  }
  try {
    const archive = await api(`/api/topic-archive?documentId=${encodeURIComponent(currentDocumentId)}`);
    renderTopicArchive(archive);
    return archive;
  } catch (error) {
    topicArchiveListNode.textContent = `存档读取失败：${error.message}`;
    return null;
  }
}

async function openCurrentTopicInObsidian() {
  if (!currentDocumentId) {
    showWorkspaceToast("先保存正文，再打开 Obsidian。", "error");
    return;
  }
  if (openInObsidianButton) openInObsidianButton.disabled = true;
  try {
    const result = await api("/api/obsidian/open-topic", {
      method: "POST",
      body: JSON.stringify({
        documentId: currentDocumentId,
        title: currentTitle(),
      }),
    });
    showWorkspaceToast(result.message || "已在 Obsidian 打开当前主题");
  } catch (error) {
    showWorkspaceToast(`打开 Obsidian 失败：${error.message}`, "error");
  } finally {
    if (openInObsidianButton) openInObsidianButton.disabled = !currentDocumentId;
  }
}

function loadTopicArchiveEntry(entry) {
  if (!entry) return;
  titleInput.value = entry.title || titleInput.value || "未命名稿件";
  const html = String(entry.contentHtml || "").trim();
  const text = String(entry.contentText || "").trim();
  if (html) {
    editor.innerHTML = stripParagraphAssistSlotsFromHtml(html);
  } else if (text) {
    editor.innerHTML = text
      .split(/\n{2,}/)
      .map((paragraph) => `<p>${paragraph.replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]))}</p>`)
      .join("");
  }
  editor.innerHTML = stripParagraphAssistSlotsFromHtml(editor.innerHTML);
  resetEditorUndoHistory();
  resetRewritePanel();
  markDraftChanged();
  setBodySource("edited");
  setSaveStateText("已载入历史，保存后生效");
  draftNoticeNode.textContent = "已载入一版主题存档，保存后会成为当前稿。";
  updateCurrentDraftPreview();
}

async function saveToWorkspace(source = "manual") {
  if (activeWorkspaceSavePromise) return activeWorkspaceSavePromise;
  activeWorkspaceSavePromise = (async () => {
  syncHeadingFromTitle();
  flushAutosave();
  saveStateNode.textContent = "正在保存...";
  documentStateNode.textContent = currentDocumentId ? "保存中..." : "新稿保存中...";
  const previousDocumentId = currentDocumentId;
  try {
    const result = await api("/api/document", {
      method: "POST",
      body: JSON.stringify({
        documentId: currentDocumentId,
        title: currentTitle(),
        styleBrief: styleCardTopic(),
        contentHtml: editor.innerHTML,
        contentText: bodyParagraphText(),
        documentType: currentDocumentType,
        metadata: currentDocumentMetadata,
      }),
    });
    currentDocumentId = result.documentId;
    currentWorkspaceUpdatedAt = result.updatedAt || "";
    currentDocumentType = normalizeDocumentType(result.documentType || currentDocumentType);
    window.localStorage.setItem(currentDocumentKey, currentDocumentId);
    if (!previousDocumentId && currentDocumentId) {
      window.localStorage.removeItem(draftCacheKey(""));
      clearLegacyDraftCache();
    }
    persistCurrentDraft({
      dirty: false,
      updatedAt: result.updatedAt || new Date().toISOString(),
      workspaceUpdatedAt: result.updatedAt || "",
    });
    setDocumentMeta({
      state: "已保存",
      path: result.path,
      documentType: currentDocumentType,
      metadata: currentDocumentMetadata,
    });
    documentPathNode.textContent = result.path;
    const savedAt = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    const savedMessage = source === "shortcut" ? `Command+S 已保存到工作区 · ${savedAt}` : `已保存到工作区 · ${savedAt}`;
    draftNoticeNode.textContent = savedMessage;
    saveStateNode.textContent = `工作区已存 ${savedAt}`;
    canonicalizeWorkbenchUrl();
    showWorkspaceToast(savedMessage);
    setBodySource("workspace_saved");
    await refreshDocuments();
    await refreshTopicArchive();
    return result;
  } catch (error) {
    documentStateNode.textContent = "保存失败";
    saveStateNode.textContent = `保存失败：${error.message}`;
    showWorkspaceToast(`保存失败：${error.message}`, "error");
    throw error;
  } finally {
    activeWorkspaceSavePromise = null;
  }
  })();
  return activeWorkspaceSavePromise;
}

function handleWorkspaceSaveShortcut(event) {
  if (event.isComposing) return;
  const key = String(event.key || "").toLowerCase();
  if (key !== "s" || event.altKey || !(event.metaKey || event.ctrlKey)) return;
  event.preventDefault();
  void saveToWorkspace("shortcut");
}

function renderProjectPackPreview(result) {
  if (!projectPackPreviewNode) return;
  const route = result?.primaryRoute || result?.classification?.primary || {};
  const angles = Array.isArray(result?.angles) ? result.angles : [];
  const questions = Array.isArray(result?.questions) ? result.questions : [];
  const summary = [
    `<p><strong>主路由：${escapeHtmlLocal(route.label || "未判断")}</strong></p>`,
    `<p>${escapeHtmlLocal(route.description || "已生成项目写作包。")}</p>`,
  ];
  if (angles.length) {
    summary.push(`<p>可写方向：${angles.slice(0, 3).map(escapeHtmlLocal).join(" / ")}</p>`);
  }
  if (questions.length) {
    summary.push(`<p>先补：${questions.slice(0, 2).map(escapeHtmlLocal).join("；")}</p>`);
  }
  projectPackPreviewNode.innerHTML = summary.join("");
}

async function buildProjectPack() {
  if (!projectPackNameInput || !projectPackPreviewNode) return null;
  const name = projectPackNameInput.value.trim();
  if (!name) {
    projectPackPreviewNode.textContent = "先填项目名。";
    return null;
  }
  buildProjectPackButton.disabled = true;
  projectPackPreviewNode.textContent = "正在整理项目动机和可写方向...";
  try {
    const result = await api("/api/project-story-pack", {
      method: "POST",
      body: JSON.stringify({
        name,
        path: projectPackPathInput?.value || "",
        notes: projectPackNotesInput?.value || "",
      }),
    });
    latestProjectPackDocumentId = result?.document?.documentId || "";
    renderProjectPackPreview(result);
    if (loadProjectPackButton) {
      loadProjectPackButton.hidden = !latestProjectPackDocumentId;
    }
    jobStateNode.textContent = latestProjectPackDocumentId ? "项目写作包已生成，可载入正文。" : "项目写作包已生成。";
    return result;
  } catch (error) {
    projectPackPreviewNode.textContent = `生成失败：${error.message}`;
    jobStateNode.textContent = "项目写作包生成失败。";
    return null;
  } finally {
    buildProjectPackButton.disabled = false;
  }
}

function activeCowriteBeat() {
  const beats = cowritePlan?.beats || [];
  return beats.find((beat) => beat.id === activeCowriteBeatId) || beats[0] || null;
}

function saveCowritePlan() {
  if (!cowritePlan) return;
  window.localStorage.setItem(cowritePlanKey, JSON.stringify(cowritePlan));
  if (activeCowriteBeatId) window.localStorage.setItem(cowriteActiveBeatKey, activeCowriteBeatId);
}

function saveActiveCowriteDraft() {
  const beat = activeCowriteBeat();
  if (!beat) return false;
  const text = cowriteDraftText().trim();
  latestCowriteSection = text;
  beat.draft = text;
  beat.status = text ? "saved" : "";
  if (!text) {
    beat.source = "";
    beat.model = "";
    beat.thinking = "";
  }
  saveCowritePlan();
  renderCowritePlan(cowritePlan);
  return true;
}

function advanceCowriteBeat() {
  const beats = cowritePlan?.beats || [];
  const index = beats.findIndex((beat) => beat.id === activeCowriteBeatId);
  const next = beats.slice(index + 1).find((beat) => !String(beat.draft || "").trim()) || beats[index + 1];
  if (!next) return false;
  activeCowriteBeatId = next.id;
  latestCowriteSection = next.draft || "";
  cowriteSectionSeedInput.value = "";
  setCowriteDraftText(latestCowriteSection, "还没有段落稿。");
  cowriteActiveBeatNode.textContent = next.label || next.id;
  saveCowritePlan();
  renderCowritePlan(cowritePlan);
  return true;
}

function renderCowritePlan(plan = cowritePlan) {
  cowritePlan = plan;
  if (!cowriteBeatListNode) return;
  if (!plan) {
    cowriteThesisStateNode.textContent = "未定";
    cowriteThesisNode.textContent = "暂无。";
    cowriteBeatListNode.textContent = "还没有段落任务。";
    cowriteActiveBeatNode.textContent = "未选";
    cowriteCurrentJobNode.textContent = "先定主线。";
    cowriteCurrentMustNode.textContent = "";
    cowriteProgressLabelNode.textContent = "0/0";
    cowriteProgressFillNode.style.width = "0%";
    return;
  }
  const beats = plan.beats || [];
  if (!beats.some((beat) => beat.id === activeCowriteBeatId)) {
    activeCowriteBeatId = beats[0]?.id || "";
  }
  const activeIndex = Math.max(0, beats.findIndex((beat) => beat.id === activeCowriteBeatId));
  const doneCount = beats.filter((beat) => String(beat.draft || "").trim()).length;
  const progressBase = beats.length ? Math.max(doneCount, activeIndex + 1) : 0;
  const progressValue = beats.length ? Math.round((progressBase / beats.length) * 100) : 0;
  cowriteProgressLabelNode.textContent = beats.length ? `${activeIndex + 1}/${beats.length}` : "0/0";
  cowriteProgressFillNode.style.width = `${progressValue}%`;
  cowriteThesisStateNode.textContent = beats.length ? `${beats.length} 段` : "未定";
  cowriteThesisNode.textContent = plan.thesis || "暂无。";
  cowriteBeatListNode.innerHTML = "";
  beats.forEach((beat, index) => {
    const item = document.createElement("button");
    item.type = "button";
    const isActive = beat.id === activeCowriteBeatId;
    const isDone = Boolean(String(beat.draft || "").trim());
    item.className = ["cowrite-beat", isActive ? "active" : "", isDone ? "done" : ""].filter(Boolean).join(" ");
    item.innerHTML = `
      <strong></strong>
      <p class="cowrite-job"></p>
      <p class="cowrite-excerpt"></p>
      <p class="cowrite-status"></p>
    `;
    item.querySelector("strong").textContent = `${index + 1}. ${beat.label || beat.id}`;
    item.querySelector(".cowrite-job").textContent = beat.job || "";
    const excerptNode = item.querySelector(".cowrite-excerpt");
    const draftText = String(beat.draft || "").trim();
    excerptNode.textContent = draftText ? draftText.slice(0, 72) : "";
    excerptNode.hidden = !draftText;
    item.querySelector(".cowrite-status").textContent = beat.draft
      ? `已写${beat.source === "kimi" ? " · 写作助手" : beat.source ? " · 回退" : ""}`
      : beat.mustHave || "";
    item.addEventListener("click", () => {
      activeCowriteBeatId = beat.id;
      latestCowriteSection = beat.draft || "";
      setCowriteDraftText(latestCowriteSection, "还没有段落稿。");
      cowriteActiveBeatNode.textContent = beat.label || beat.id;
      saveCowritePlan();
      renderCowritePlan(cowritePlan);
    });
    cowriteBeatListNode.appendChild(item);
  });
  const active = activeCowriteBeat();
  cowriteActiveBeatNode.textContent = active ? active.label || active.id : "未选";
  cowriteCurrentJobNode.textContent = active?.job || "先写这一节。";
  cowriteCurrentMustNode.textContent = active?.mustHave ? `要点：${active.mustHave}` : "";
  if (active?.draft) {
    setCowriteDraftText(active.draft, "还没有段落稿。");
  } else {
    setCowriteDraftText("", "还没有段落稿。");
  }
  saveCowritePlan();
}

function restoreCowritePlan() {
  const raw = window.localStorage.getItem(cowritePlanKey);
  if (!raw) return;
  try {
    cowritePlan = JSON.parse(raw);
    renderCowritePlan(cowritePlan);
  } catch (_) {}
}

function buildWorkbenchCowritePlanFromEditor() {
  const title = currentTitle();
  const topic = `${title}\n${bodyParagraphText()}`;
  const isWorkbenchTopic = /AI\s*写作|写作工作台|写作系统|写作\s*SOP|写稿/i.test(topic);
  if (!isWorkbenchTopic) return null;

  const paragraphs = Array.from(editor.querySelectorAll("p"))
    .map((node) => normalizeText(node.innerText || ""))
    .filter(Boolean);
  const join = (items) => items.filter(Boolean).join("\n\n");
  const beats = [
    {
      id: "pain",
      label: "发现问题",
      job: "从 AI 写稿常见但不好用进入：AI 味、不说人话、中文稿抓不住重点。",
      mustHave: "先讲返工痛点，不提前讲工作台。",
      draft: join(paragraphs.slice(0, 3)),
    },
    {
      id: "research-question",
      label: "研究原因",
      job: "第二步先查原因：为什么 AI 会写句子，却常常写不出好文章。",
      mustHave: "这里必须先问原因，不能跳到工作台。",
      draft: join(paragraphs.slice(3, 5)),
    },
    {
      id: "research-answer",
      label: "主流解法",
      job: "写清楚主流解决办法：pre-writing、source map、human-in-the-loop、anti-slop、风格记忆。",
      mustHave: "每个资料点都落到一个写作动作。",
      draft: join(paragraphs.slice(5, 9)),
    },
    {
      id: "solution",
      label: "我的工作台",
      job: "再引出工作台：它把研究里的解法变成具体操作。",
      mustHave: "这里才说系统，不要提前抢戏。",
      draft: join(paragraphs.slice(9, 11)),
    },
    {
      id: "frontend",
      label: "前端演示",
      job: "讲清楚定主线、按节写、删除/保存/下一节、最后合成。",
      mustHave: "让观众知道页面怎么用，不写成说明书。",
      draft: join([...paragraphs.slice(11, 14), paragraphs[18]]),
    },
    {
      id: "workflow",
      label: "写作链路",
      job: "主笔接口写稿，收稿检查负责审计和退稿。",
      mustHave: "说清楚岗位，不堆模型名。",
      draft: join(paragraphs.slice(14, 15)),
    },
    {
      id: "contrast",
      label: "用和不用",
      job: "展示没加流程和加流程之后的差别。",
      mustHave: "必须有坏句、追问、改后效果。",
      draft: join(paragraphs.slice(15, 18)),
    },
    {
      id: "boundary",
      label: "边界收束",
      job: "承认它不能保证好文章，只是减少废稿和返工。",
      mustHave: "结尾落到作者判断。",
      draft: join(paragraphs.slice(19)),
    },
  ].map((beat) => ({
    ...beat,
    status: beat.draft ? "saved" : "empty",
    source: beat.draft ? "workspace" : "",
  }));

  return {
    title,
    thesis: "我发现 AI 写稿常常完整但不好用；第二步先查原因和主流解法，再把这些解法落成一个会退稿的写作工作台。",
    beats,
    styleCard: "",
    documentId: currentDocumentId,
    updatedAt: new Date().toISOString(),
  };
}

function syncCowritePlanFromCurrentDocument() {
  const plan = buildWorkbenchCowritePlanFromEditor();
  if (!plan) return false;
  cowritePlan = plan;
  activeCowriteBeatId = plan.beats?.[0]?.id || "";
  latestCowriteSection = plan.beats?.[0]?.draft || "";
  setCowriteDraftText(latestCowriteSection, "还没有段落稿。");
  window.localStorage.setItem(cowritePlanKey, JSON.stringify(cowritePlan));
  window.localStorage.setItem(cowriteActiveBeatKey, activeCowriteBeatId);
  renderCowritePlan(cowritePlan);
  cowriteStateNode.textContent = "已按当前文档同步共写主线";
  return true;
}

async function buildCowritePlan() {
  const materialCard = fullDraftMaterialCard();
  const brief = fullDraftBriefText(materialCard) || bodyParagraphText().slice(0, 1200);
  const seed = cowriteSeedInput.value.trim() || brief;
  cowriteStateNode.textContent = "定主线中...";
  const plan = await api("/api/cowrite-plan", {
    method: "POST",
    body: JSON.stringify({
      title: currentTitle(),
      brief,
      seed,
      materialCard,
    }),
  });
  cowritePlan = plan;
  activeCowriteBeatId = plan.beats?.[0]?.id || "";
  setCowriteDraftText("", "选一段后写。");
  renderCowritePlan(plan);
  cowriteStateNode.textContent = "已定主线，从第一节开始写";
  draftNoticeNode.textContent = "共写模式：按节写完，最后合成全文。";
  return plan;
}

async function writeCowriteSection() {
  if (!cowritePlan) {
    await buildCowritePlan();
  }
  const beat = activeCowriteBeat();
  if (!beat) {
    cowriteStateNode.textContent = "没有段落任务";
    return null;
  }
  cowriteStateNode.textContent = `写作助手正在写：${beat.label || beat.id}`;
  setCowriteDraftText("", "写作助手正在写这一段，通常要等一会儿。");
  const result = await api("/api/cowrite-section", {
    method: "POST",
    body: JSON.stringify({
      title: currentTitle(),
      thesis: cowritePlan.thesis || "",
      beat,
      seed: cowriteSectionSeedInput.value.trim(),
      previous: bodyParagraphText().slice(-1000),
      provider: "kimi",
    }),
  });
  latestCowriteSection = result.body || "";
  beat.draft = latestCowriteSection;
  beat.status = result.audit?.score >= 80 ? "drafted" : "needs_review";
  beat.source = result.source || "";
  beat.model = result.model || "";
  beat.thinking = result.thinking || "";
  setCowriteDraftText(latestCowriteSection, "没有段落稿。");
  const sourceLabel = result.source === "kimi"
    ? "写作助手"
    : result.source === "kimi_failure"
      ? "写作助手失败"
      : "本地回退";
  const scoreLabel = Number.isInteger(result.audit?.score) ? ` · ${result.audit.score}` : "";
  const errorLabel = result.modelError ? " · 未生成段落" : "";
  cowriteStateNode.textContent = `${result.audit?.score >= 80 ? "本节可用" : "本节需审"} · ${sourceLabel}${scoreLabel}${errorLabel}`;
  renderCowritePlan(cowritePlan);
  return result;
}

function insertCowriteSection() {
  if (!saveActiveCowriteDraft()) {
    cowriteStateNode.textContent = "没有可保存的本节";
    return;
  }
  if (!latestCowriteSection.trim()) {
    cowriteStateNode.textContent = "本节是空的，先写内容再进入下一节";
    return;
  }
  const advanced = advanceCowriteBeat();
  cowriteStateNode.textContent = advanced ? "已保存本节，进入下一节" : "全部章节已保存，可以合成全文";
}

function saveCurrentCowriteSection() {
  if (!saveActiveCowriteDraft()) {
    cowriteStateNode.textContent = "没有可保存段落";
    return;
  }
  cowriteStateNode.textContent = "已保存本节";
}

function clearCurrentCowriteSection() {
  const beat = activeCowriteBeat();
  if (!beat) {
    cowriteStateNode.textContent = "没有可清空的本节";
    return;
  }
  latestCowriteSection = "";
  beat.draft = "";
  beat.status = "";
  beat.source = "";
  beat.model = "";
  beat.thinking = "";
  cowriteSectionSeedInput.value = "";
  setCowriteDraftText("", "还没有段落稿。");
  saveCowritePlan();
  renderCowritePlan(cowritePlan);
  cowriteStateNode.textContent = "已清空本节";
}

function composeCowriteDraft() {
  if (!cowritePlan?.beats?.length) {
    cowriteStateNode.textContent = "先定段落";
    return;
  }
  const missing = cowritePlan.beats.filter((beat) => !String(beat.draft || "").trim());
  if (missing.length) {
    cowriteStateNode.textContent = `还有 ${missing.length} 段没写，先别合成`;
    return;
  }
  const body = cowritePlan.beats.map((beat) => beat.draft || "").filter(Boolean).join("\n\n");
  if (!body) {
    cowriteStateNode.textContent = "还没有段落稿";
    return;
  }
  titleInput.value = cowritePlan.title || currentTitle();
  editor.innerHTML = articleTextToHtmlLocal(titleInput.value, body);
  resetEditorUndoHistory();
  scheduleSave();
  setBodySource("edited");
  markDraftChanged();
  activatePanel("rewrite");
  cowriteStateNode.textContent = "已合成全文";
  draftNoticeNode.textContent = "已合成全文，可以检查或改句。";
}

async function generateFullDraft() {
  const materialCard = fullDraftMaterialCard();
  const brief = fullDraftBriefText(materialCard);
  if (!brief) {
    generateStateNode.textContent = "缺材料";
    draftBriefInput.focus();
    return;
  }
  const openingPayload = restoreOpeningPack();
  const opening = openingPayload?.openings?.[selectedOpeningIndex]?.text || "";
  syncHeadingFromTitle();
  setGenerateBusy(true, "生成中");
  draftNoticeNode.textContent = opening
    ? "按选中开头生成。"
    : "生成全文。";
  saveStateNode.textContent = "等待写作链路...";
  try {
    const promptMode = draftPromptModeInput?.value || "guided";
    const provider = normalizeDraftProvider(draftProviderInput?.value || providerEngine);
    activeGenerateController = new AbortController();
    startGenerateTimer({ provider, promptMode });
    await refreshWorkbenchContext();
    setGenerateProgress({
      status: "running",
      title: "正在整理交接单",
      detail: "先把选题、材料、结构、禁句和风格库整理成写稿任务书。",
      elapsed: Math.round((Date.now() - generateStartedAt) / 1000),
      progress: 16,
      cancellable: true,
    });
    await runWritingPreflight();
    setGenerateProgress({
      status: "running",
      title: "正在写第一版",
      detail: provider === "hybrid"
        ? "主笔接口正在按任务书写第一版，复核接口会处理改句和证据检查。"
        : provider === "kimi"
          ? "写作助手正在按任务书写第一版。"
          : "主笔接口正在按任务书写第一版。",
      elapsed: Math.round((Date.now() - generateStartedAt) / 1000),
      progress: 28,
      cancellable: true,
    });
    const job = await api("/api/full-draft-job", {
      method: "POST",
      signal: activeGenerateController.signal,
      body: JSON.stringify({
        title: currentTitle(),
        brief,
        materialCard,
        opening,
        promptMode,
        provider,
        cleanAiTaste: cleanAiTasteInput.checked,
      }),
    });
    activeGenerateJobId = job.jobId || "";
    setGenerateProgress({
      status: "running",
      title: "后台已接单",
      detail: activeGenerateJobId ? `任务 ${activeGenerateJobId} 已开始。前端只轮询结果，不再卡死。` : "后台已开始生成。",
      elapsed: Math.round((Date.now() - generateStartedAt) / 1000),
      progress: 34,
      cancellable: true,
    });
    const result = await waitForFullDraftJob(activeGenerateJobId, activeGenerateController.signal);
    window.localStorage.setItem(promptModeKey, promptMode);
    window.localStorage.setItem(draftProviderKey, provider);
    providerEngine = provider;
    window.localStorage.setItem(generatedDraftKey, JSON.stringify(result));
    if (sessionStyleCardNode && result.sessionStyleCard) {
      sessionStyleCardNode.textContent = result.sessionStyleCard;
    }
    renderPreflight(result.preflight);
    renderCompliance(result);
    if (result.qualityGate?.status === "allow") {
      applyGeneratedToEditor(result, "latest_generated");
    } else {
      generatedDraftView = preferredGeneratedView();
      renderGeneratedDraft(result);
      if (advancedFoldNode) advancedFoldNode.open = true;
    }
    renderWorkflowState();
    resetRewritePanel();
    const providerLabel = draftProviderLabel(provider, true);
    const modeLabel = `${providerLabel} · ${promptMode === "pure_ds" ? "纯提示" : "工作台约束"}`;
    generateStateNode.textContent = result.qualityGate?.status === "allow" ? "草稿通过" : "未通过";
    saveStateNode.textContent =
      result.qualityGate?.status === "allow" ? `已载入${generatedDraftView === "raw" ? "原稿" : "编辑稿"}` : "已生成，未载入";
    documentStateNode.textContent = result.qualityGate?.status === "allow" ? "最新" : "未载入";
    documentPathNode.textContent = modeLabel;
    if (result.codexGate?.status === "pending" && result.qualityGate?.status === "allow") {
      draftNoticeNode.textContent = "草稿已载入；Codex 终审继续在后台跑，不再堵住生成返回。";
    } else {
      draftNoticeNode.textContent = result.qualityGate?.status === "allow" ? "草稿已载入；全 SOP 需跑报告。" : "生成稿未过门槛，先看细节。";
    }
    if (result.qualityGate?.status === "allow") {
      editor.scrollIntoView({ behavior: "smooth", block: "start" });
      if (result.codexGate?.status === "pending") {
        finishGenerateProgress(result, provider, promptMode);
        const deferredJobId = activeGenerateJobId;
        void continueDeferredCodexGate(deferredJobId, provider, promptMode);
      } else {
        setGenerateProgress({
          status: "running",
          title: "正在自动终审",
          detail: "正文已载入，Codex 正在检查主线、硬伤、AI 味和风格库命中。",
          elapsed: Math.round((Date.now() - generateStartedAt) / 1000),
          progress: 96,
          cancellable: false,
        });
        const review = await runTasteAuditWithProof({
          label: "生成后自动终审中。",
          passPrefix: "自动终审通过",
          blockPrefix: "自动终审未过",
        });
        if (review?.delivery?.state === "blocked") {
          generateStateNode.textContent = "终审未过";
          saveStateNode.textContent = "已载入，需修改";
          documentStateNode.textContent = "需修改";
          draftNoticeNode.textContent = "主笔接口已生成并载入，但自动终审未过，先改标黄处。";
          setGenerateProgress({
            status: "warn",
            title: "生成完成：终审未过",
            detail: `已载入正文，但需要修改：${review.delivery.detail}`,
            elapsed: Math.round((Date.now() - generateStartedAt) / 1000),
            progress: 100,
            cancellable: false,
          });
        } else {
          draftNoticeNode.textContent = "主笔接口已生成，自动终审通过；可继续人工细修或导出。";
          finishGenerateProgress(result, provider, promptMode);
        }
      }
    } else {
      finishGenerateProgress(result, provider, promptMode);
    }
  } catch (error) {
    generateStateNode.textContent = "失败";
    saveStateNode.textContent = error.name === "AbortError" ? "已取消前端等待，后台继续" : `生成失败：${error.message}`;
    draftNoticeNode.textContent = error.name === "AbortError" ? "已取消等待，可稍后刷新最新稿。" : "生成失败。";
    failGenerateProgress(error);
  } finally {
    activeGenerateController = null;
    activeGenerateJobId = "";
    setGenerateBusy(false);
  }
}

async function generateOpenings() {
  const brief = fullDraftBriefText();
  if (!brief) {
    openingStateNode.textContent = "缺材料";
    draftBriefInput.focus();
    return;
  }
  syncHeadingFromTitle();
  selectedOpeningIndex = -1;
  setGenerateBusy(true, "开头生成中");
  openingStateNode.textContent = "生成中";
  openingListNode.textContent = "正在生成 3 个开头...";
  try {
    const result = await api("/api/opening-pack", {
      method: "POST",
      body: JSON.stringify({
        title: currentTitle(),
        brief,
      }),
    });
    window.localStorage.setItem(openingPackKey, JSON.stringify({ ...result, selectedOpeningIndex: -1 }));
    renderOpenings(result);
    openingStateNode.textContent = "请选择";
    draftNoticeNode.textContent = "已生成开头。";
    renderWorkflowState();
  } catch (error) {
    openingStateNode.textContent = "失败";
    openingListNode.textContent = `开头生成失败：${error.message}。可以再点一次；如果还是不行，我会回退到本地候选。`;
  } finally {
    setGenerateBusy(false);
  }
}

async function exportDraft(format) {
  syncHeadingFromTitle();
  const result = await api("/api/export", {
    method: "POST",
    body: JSON.stringify({
      documentId: currentDocumentId || currentTitle(),
      title: currentTitle(),
      contentHtml: editor.innerHTML,
      contentText: bodyParagraphText(),
      format,
    }),
  });
  documentStateNode.textContent = `已导出 ${format.toUpperCase()}`;
  documentPathNode.textContent = result.path;
  saveStateNode.textContent = `已导出 ${format.toUpperCase()}`;
  if (exportMenuNode) exportMenuNode.open = false;
  await refreshDocuments();
  return result;
}

async function runQuickAudit() {
  clearRewriteResults("暂无候选。");
  setAuditSummary("检查中", "checking");
  setDeliveryStatus("checking");
  jobStateNode.textContent = "正在扫明显硬伤。";
  try {
    const result = await api("/api/quick-audit", {
      method: "POST",
      body: JSON.stringify({
        title: currentTitle(),
        body: bodyParagraphText(),
      }),
    });
    renderAuditResult(result);
    const delivery = deliveryStateFromAudits(result, null);
    setDeliveryStatus(delivery.state, delivery.detail);
    const firstAuditIndex = locatableAuditIndexes()[0];
    const summaryLine =
      result.summaryLine ||
      ((result.summaryBuckets || []).length
        ? result.summaryBuckets.map((item) => `${item.label} ${item.count}`).join(" / ")
        : `${result.findings.length} 条问题`);
    if (Number.isInteger(firstAuditIndex)) {
      jobStateNode.textContent = `硬伤检查：${summaryLine}，已在正文标出。点标黄处再改。`;
    } else {
      jobStateNode.textContent = result.findings?.length
        ? `硬伤检查：${summaryLine}。`
        : "硬伤检查：未扫到明显硬伤，但这不等于文章已经写好。";
    }
    return result;
  } catch (error) {
    renderAuditResult({
      score: "--",
      summary: `检查失败：${error.message}`,
      findings: [],
    });
    setDeliveryStatus("blocked", "检查失败");
    jobStateNode.textContent = `检查失败：${error.message}`;
    return null;
  }
}

async function runTasteAudit() {
  clearRewriteResults("暂无候选。");
  setAuditSummary("检查中", "checking");
  jobStateNode.textContent = "正在检查并标黄：主线、动作、反例和 AI 味。";
  try {
    const result = await api("/api/taste-audit", {
      method: "POST",
      body: JSON.stringify({
        title: currentTitle(),
        body: bodyParagraphText(),
      }),
    });
    renderAuditResult(result);
    const firstAuditIndex = locatableAuditIndexes()[0];
    if (Number.isInteger(firstAuditIndex)) {
      jobStateNode.textContent = `查到 ${result.findings.length} 条问题，已在正文标出。点标黄处再改。`;
    } else {
      jobStateNode.textContent = result.findings?.length ? `标出 ${result.findings.length} 条问题。` : "检查通过。";
    }
    return result;
  } catch (error) {
    renderAuditResult({
      score: "--",
      summary: `检查失败：${error.message}`,
      findings: [],
    });
    jobStateNode.textContent = `检查失败：${error.message}`;
    return null;
  }
}

async function runTasteAuditWithProof(options = {}) {
  const config = options && typeof options === "object" && !("type" in options) ? options : {};
  const label = config.label || "深度终审中。";
  const blockPrefix = config.blockPrefix || "不可交付";
  setDeliveryStatus("checking");
  jobStateNode.textContent = label;
  const aiResult = await runAiFlavorAudit({ renderToAudit: false, openPanel: false, announce: false });
  const result = await runTasteAudit();
  await runStyleProof();
  const delivery = deliveryStateFromAudits(result, aiResult);
  setDeliveryStatus(delivery.state, delivery.detail);
  if (delivery.state === "blocked") {
    jobStateNode.textContent = `${blockPrefix}：${delivery.detail}`;
  } else {
    jobStateNode.textContent = "";
  }
  return { result, delivery, aiResult };
}

async function runHardCheckWithProof() {
  setDeliveryStatus("checking");
  jobStateNode.textContent = "正在扫明显硬伤。";
  const aiResult = await runAiFlavorAudit({ renderToAudit: false, openPanel: false, announce: false });
  const result = await runQuickAudit();
  await runStyleProof();
  const delivery = deliveryStateFromAudits(result, aiResult);
  setDeliveryStatus(delivery.state, delivery.detail);
  if (delivery.state === "blocked") {
    jobStateNode.textContent = `硬伤未过：${delivery.detail}`;
  } else {
    jobStateNode.textContent = "";
  }
  return result;
}

function jumpToNextAuditIssue() {
  const findings = latestAuditResult?.findings || [];
  if (!findings.length) return;
  const nextIndex = findNextAuditIndex(currentAuditIndex);
  if (nextIndex !== -1) {
    const item = findings[nextIndex];
    jumpToParagraph(item.paragraphIndex, item, nextIndex);
    return;
  }
  auditFlowDone = true;
  currentAuditIssue = null;
  updateAuditIssueUi();
  jobStateNode.textContent = "本轮已走完。可以再检查。";
}

async function openDocument(documentId, options = {}) {
  setDocumentHydrating(true);
  try {
    const documentData = await api(`/api/document?documentId=${encodeURIComponent(documentId)}`);
    currentDocumentId = documentData.documentId;
    currentWorkspaceUpdatedAt = documentData.updatedAt || "";
    currentDocumentType = normalizeDocumentType(documentData.documentType || currentDocumentType);
    currentDocumentMetadata = documentData.metadata && typeof documentData.metadata === "object" ? documentData.metadata : {};
    clearStalePendingRewriteForDocument(currentDocumentId);
    window.localStorage.setItem(currentDocumentKey, currentDocumentId);
    const localSnapshot = options.preferRemote
      ? null
      : readDraftSnapshot(currentDocumentId) || migrateLegacyDraft(currentDocumentId);
    if (hasLocalDraftChanges(localSnapshot, documentData)) {
      applyDraftSnapshot(localSnapshot, { saveStateText: "已恢复本地未保存改动" });
      setDocumentMeta({
        state: "有未保存改动",
        path: documentData.path || "",
        documentType: currentDocumentType,
        metadata: currentDocumentMetadata,
      });
      draftNoticeNode.textContent = "已恢复本地未保存改动。";
      setBodySource("edited");
    } else {
      titleInput.value = documentData.title || "未命名稿件";
      editor.innerHTML = stripParagraphAssistSlotsFromHtml(documentData.contentHtml || "");
      resetEditorUndoHistory();
      persistCurrentDraft({
        dirty: false,
        updatedAt: documentData.updatedAt || new Date().toISOString(),
        workspaceUpdatedAt: documentData.updatedAt || "",
      });
      setDocumentMeta({
        state: "已打开工作区文档",
        path: documentData.path || "",
        documentType: currentDocumentType,
        metadata: currentDocumentMetadata,
      });
      setSaveStateText("已载入", { quiet: true });
      draftNoticeNode.textContent = `已打开${documentTypeLabel(currentDocumentType)}。`;
      setBodySource("workspace_loaded");
    }
    documentPathNode.textContent = documentData.path || "";
    resetRewritePanel();
    markDraftChanged();
    syncCowritePlanFromCurrentDocument();
    await refreshTopicArchive();
    updateCurrentDraftPreview();
  } finally {
    setDocumentHydrating(false);
  }
}

function newDraft() {
  currentDocumentId = freshTopicDocumentId();
  currentWorkspaceUpdatedAt = "";
  currentDocumentType = "formal";
  currentDocumentMetadata = {};
  window.localStorage.setItem(currentDocumentKey, currentDocumentId);
  editor.innerHTML = [
    "<h2>新主题稿</h2>",
    "<p>这篇想讲：</p>",
    "<p>我的判断：</p>",
    "<p>已有材料/例子：</p>",
    "<p>不想写成：</p>",
  ].join("");
  resetEditorUndoHistory();
  titleInput.value = "新主题稿";
  persistCurrentDraft({ dirty: true, workspaceUpdatedAt: "" });
  resetRewritePanel();
  renderTopicArchive({ entries: [] });
  setDocumentMeta({ state: "新主题未保存", path: `当前主题：${currentDocumentId}`, documentType: currentDocumentType, metadata: currentDocumentMetadata });
  documentPathNode.textContent = `当前主题：${currentDocumentId}`;
  setSaveStateText("已新建主题");
  draftNoticeNode.textContent = "已新建独立主题。先改标题，再写材料。";
  setBodySource("blank");
  markDraftChanged();
  updateCurrentDraftPreview();
  titleInput.focus();
  titleInput.select();
  showWorkspaceToast("已新建独立主题。先改标题，再保存。");
  setDocumentHydrating(false);
}

async function refreshMemory() {
  const [entries, summary] = await Promise.all([api("/api/memory"), api("/api/memory-summary")]);
  renderMemorySummary(summary);
  renderMemory(entries);
}

async function loadHealth() {
  try {
    const health = await api("/api/health");
    bridgeStatusNode.dataset.threadId = health.thread_id || "";
    providerEngine = normalizeDraftProvider(window.localStorage.getItem(draftProviderKey));
    window.localStorage.setItem(draftProviderKey, providerEngine);
    if (draftProviderInput) draftProviderInput.value = providerEngine;
    const activeConfigured = providerEngine === "hybrid"
      ? health.hybrid_configured
      : providerEngine === "kimi"
        ? health.kimi_configured
        : health.deepseek_configured;
    const keyLabel = !activeConfigured ? " · Key未配" : "";
    const modelLabel = providerEngine === "hybrid"
      ? "主笔+复核"
      : providerEngine === "kimi"
        ? "旧主笔路线"
        : "默认主笔接口";
    const fullThinkingLabel = providerEngine === "hybrid"
      ? " · 写稿/复核已配置"
      : providerEngine === "kimi"
        ? " · 旧路线已配置"
        : ` · 全文 ${health.deepseek_full_thinking === "enabled" ? "深度思考" : "标准模式"}`;
    const rewriteThinkingLabel = ` · 改句 ${health.deepseek_rewrite_thinking === "enabled" ? "深度思考" : "标准模式"}`;
    bridgeStatusNode.textContent = `${modelLabel}${fullThinkingLabel}${rewriteThinkingLabel}${keyLabel} · ${health.thread_id || "workspace"}`;
  } catch (error) {
    bridgeStatusNode.textContent = `offline: ${error.message}`;
  }
}

document.addEventListener("selectionchange", () => {
  if (Date.now() < suppressSelectionCaptureUntil) return;
  if (document.activeElement === paragraphAssistPromptInput) return;
  window.clearTimeout(window.__v2SelectionTimer);
  window.__v2SelectionTimer = window.setTimeout(() => {
    const selection = window.getSelection();
    if (selection?.isCollapsed) {
      captureCaret();
      return;
    }
    captureSelection();
  }, 80);
});

selectionMenu.addEventListener("mousedown", (event) => event.preventDefault());
selectionMenu.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.run !== undefined) await runRewrite();
  if (button.dataset.ban !== undefined) {
    button.disabled = true;
    showSelectionMenuStatus("记录中...", "busy");
    try {
      const entry = await saveMemory("banned_line", "", "用户在 V2 浮层标记为讨厌句式", "banned,v2", "hard");
      if (entry) {
        const feedback = memoryToastLine(entry) || "已记入讨厌库";
        showSelectionMenuStatus(feedback, "ok");
        showWorkspaceToast(feedback);
      }
      await refreshMemory();
    } catch (error) {
      showSelectionMenuStatus("记录失败", "error");
      showWorkspaceToast(`记录失败：${error.message}`, "error");
    } finally {
      button.disabled = false;
    }
  }
  if (button.dataset.like !== undefined) {
    button.disabled = true;
    showSelectionMenuStatus("记录中...", "busy");
    try {
      const entry = await saveMemory("approved_line", "", "用户在 V2 浮层标记为喜欢句式", "approved,v2", "example");
      if (entry) {
        const feedback = memoryToastLine(entry) || "已记入喜欢库";
        showSelectionMenuStatus(feedback, "ok");
        showWorkspaceToast(feedback);
      }
      await refreshMemory();
    } catch (error) {
      showSelectionMenuStatus("记录失败", "error");
      showWorkspaceToast(`记录失败：${error.message}`, "error");
    } finally {
      button.disabled = false;
    }
  }
});

document.querySelectorAll(".mode").forEach((button) => {
  button.addEventListener("click", () => {
    activeMode = button.dataset.mode || "rewrite";
    document.querySelectorAll(".mode").forEach((item) => item.classList.toggle("active", item === button));
  });
});

panelTabs.forEach((button) => {
  button.addEventListener("click", () => {
    const panelName = button.dataset.panel || "rewrite";
    if (panelName === "rewrite") {
      enterLiteMode();
    } else {
      openAdvancedPanel(panelName);
    }
  });
});

document.querySelectorAll("[data-open-panel]").forEach((button) => {
  button.addEventListener("click", () => openAdvancedPanel(button.dataset.openPanel || "draft"));
});
returnLiteModeButton?.addEventListener("click", enterLiteMode);
buildProjectPackButton?.addEventListener("click", buildProjectPack);
loadProjectPackButton?.addEventListener("click", async () => {
  if (!latestProjectPackDocumentId) {
    jobStateNode.textContent = "还没有可载入的项目写作包。";
    return;
  }
  await openDocument(latestProjectPackDocumentId);
});
fillStartCardButton?.addEventListener("click", () => fillStartCard({ force: true }));

runRewriteButton.addEventListener("click", runRewrite);
quickRewriteAction?.addEventListener("click", () => runRewrite());
paragraphAssistAction?.addEventListener("click", runParagraphAssist);
paragraphAssistPromptInput?.addEventListener("input", updateParagraphAssistState);
paragraphAssistPromptInput?.addEventListener("keydown", (event) => {
  if (event.isComposing || event.keyCode === 229) return;
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "enter") {
    event.preventDefault();
    runParagraphAssist();
  }
});
editor?.addEventListener("dblclick", handleParagraphAssistDblclick);
editor?.addEventListener("click", handleParagraphAssistClick);
editor?.addEventListener("paste", handleParagraphAssistPaste);
editor?.addEventListener("beforeinput", (event) => {
  if (event.inputType === "historyUndo" || event.inputType === "historyRedo") return;
  recordEditorUndoBoundary();
});
editor?.addEventListener("keydown", handleEditorUndoShortcut);
document.addEventListener("pointerdown", maybeDismissIdleParagraphAssist, true);
editor?.addEventListener("keydown", (event) => {
  if (!activePromptParagraph?.isAssistSlot) return;
  if (event.isComposing || event.keyCode === 229) return;
  const isModifierEnter = (event.metaKey || event.ctrlKey) && event.key === "Enter";
  const isPlainEnter = !event.metaKey && !event.ctrlKey && !event.shiftKey && event.key === "Enter";
  if (!isModifierEnter && !isPlainEnter) return;
  event.preventDefault();
  runParagraphAssist();
});
quickRecordAction?.addEventListener("click", focusRecordActions);
aiFlavorAction?.addEventListener("click", () => runAiFlavorAudit());
quickAuditAction?.addEventListener("click", runHardCheckWithProof);
deepReviewAction?.addEventListener("click", runTasteAuditWithProof);
document.querySelector("#saveBad").addEventListener("click", async () => {
  await saveMemory("banned_line", "", "用户在 V2 面板标记为讨厌句式", "banned,v2", "hard");
  await refreshMemory();
});
document.querySelector("#saveGood").addEventListener("click", async () => {
  await saveMemory("approved_line", "", "用户在 V2 面板标记为喜欢句式", "approved,v2", "example");
  await refreshMemory();
});
document.querySelector("#refreshMemory").addEventListener("click", refreshMemory);
document.querySelector("#refreshDocuments")?.addEventListener("click", refreshDocuments);
document.querySelector("#refreshDocumentsTop")?.addEventListener("click", refreshDocuments);
documentSearchInput?.addEventListener("input", async () => {
  documentSearchQuery = normalizeText(documentSearchInput.value);
  await refreshDocuments();
});
topicManageFoldNode?.addEventListener("toggle", async () => {
  if (topicManageFoldNode.open) {
    await refreshDocuments();
    return;
  }
  currentDocumentFilter = "formal";
  documentSearchQuery = "";
  if (documentSearchInput) documentSearchInput.value = "";
  await refreshDocuments();
});
topicFoldNode?.addEventListener("toggle", async () => {
  if (topicFoldNode.open) {
    closeLatestFold();
    await refreshDocuments();
    return;
  }
  if (topicManageFoldNode) topicManageFoldNode.open = false;
});
latestFoldNode?.addEventListener("toggle", () => {
  if (latestFoldNode.open) closeTopicFold();
});
documentFilterButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    currentDocumentFilter = button.dataset.documentFilter || "formal";
    await refreshDocuments();
  });
});
document.querySelector("#recoverLatest").addEventListener("click", recoverLatestResult);
document.querySelector("#generateOpenings").addEventListener("click", generateOpenings);
document.querySelector("#generateDraft").addEventListener("click", generateFullDraft);
cancelGenerateButton?.addEventListener("click", () => {
  if (activeGenerateController) {
    activeGenerateController.abort();
  } else {
    failGenerateProgress({ name: "AbortError" });
  }
});
buildCowritePlanButton?.addEventListener("click", async () => {
  try {
    await buildCowritePlan();
  } catch (error) {
    cowriteStateNode.textContent = `定主线失败：${error.message}`;
  }
});
writeCowriteSectionButton?.addEventListener("click", async () => {
  try {
    await writeCowriteSection();
  } catch (error) {
    cowriteStateNode.textContent = `写段落失败：${error.message}`;
    setCowriteDraftText("", "没有生成段落。");
  }
});
insertCowriteSectionButton?.addEventListener("click", insertCowriteSection);
saveCowriteSectionButton?.addEventListener("click", saveCurrentCowriteSection);
clearCowriteSectionButton?.addEventListener("click", clearCurrentCowriteSection);
cowriteSectionDraftNode?.addEventListener("input", () => {
  latestCowriteSection = cowriteDraftText();
});
composeCowriteDraftButton?.addEventListener("click", composeCowriteDraft);
runPreflightButton?.addEventListener("click", async () => {
  try {
    await runWritingPreflight();
  } catch (error) {
    if (preflightPreviewNode) preflightPreviewNode.textContent = `预检失败：${error.message}`;
  }
});
refreshStyleCardButton?.addEventListener("click", async () => {
  try {
    await refreshSessionStyleCard();
  } catch (error) {
    if (sessionStyleCardNode) sessionStyleCardNode.textContent = `读取失败：${error.message}`;
  }
});
document.querySelector("#loadGenerated").addEventListener("click", loadGeneratedIntoEditor);
document.querySelector("#clearReview").addEventListener("click", () => {
  resetRewritePanel();
});
document.querySelector("#newDraft").addEventListener("click", newDraft);
newTopicDraftButton?.addEventListener("click", newDraft);
document.querySelector("#saveWorkspace").addEventListener("click", saveToWorkspace);
document.querySelector("#exportMd").addEventListener("click", () => exportDraft("md"));
presentDraftButton?.addEventListener("click", enterPresentationMode);
presentationPlayButton?.addEventListener("click", () => setPresentationPlaying(!presentationPlaying));
presentationResetButton?.addEventListener("click", resetPresentationScroll);
presentationCloseButton?.addEventListener("click", exitPresentationMode);
presentationFontSizeInput?.addEventListener("input", updatePresentationSettings);
presentationSpeedInput?.addEventListener("input", () => {
  savePresentationPrefs();
  updatePresentationStats();
  if (presentationPlaying) presentationLastFrameAt = performance.now();
});
presentationFontSizeInput?.addEventListener("input", savePresentationPrefs);
quickAuditButton?.addEventListener("click", runHardCheckWithProof);
finalReviewButton?.addEventListener("click", runFinalReview);
rerunAuditButton?.addEventListener("click", runQuickAudit);
tasteAuditButton?.addEventListener("click", runTasteAuditWithProof);
refreshWorkbenchContextButton?.addEventListener("click", async () => {
  try {
    await refreshWorkbenchContext();
  } catch (error) {
    if (contextStyleNode) contextStyleNode.textContent = `读取失败：${error.message}`;
  }
});
nextAuditIssueButton.addEventListener("click", jumpToNextAuditIssue);
document.querySelector("#loadSample").addEventListener("click", () => {
  currentDocumentId = "";
  currentWorkspaceUpdatedAt = "";
  currentDocumentType = "experiment";
  currentDocumentMetadata = {};
  window.localStorage.removeItem(currentDocumentKey);
  editor.innerHTML = sampleHtml;
  resetEditorUndoHistory();
  titleInput.value = sampleTitle;
  persistCurrentDraft({ dirty: true, workspaceUpdatedAt: "" });
  resetRewritePanel();
  saveStateNode.textContent = "已载入样稿";
  setDocumentMeta({ state: "样稿未保存", path: "尚未写入工作区", documentType: currentDocumentType, metadata: currentDocumentMetadata });
  documentPathNode.textContent = "尚未写入工作区";
  setBodySource("sample");
  markDraftChanged();
});
editor.addEventListener("input", () => {
  if (isRestoringEditorUndo) return;
  captureCaret();
  const activeAssistSlot = activePromptParagraph?.isAssistSlot ? activePromptParagraph.block : null;
  if (activeAssistSlot && activeAssistSlot.dataset.runState && activeAssistSlot.dataset.runState !== "running") {
    clearParagraphAssistSlotRunState(activeAssistSlot);
  }
  syncAllParagraphAssistSlots();
  syncHeadingFromTitle();
  markDraftChanged({
    rewriteMessage: "暂无候选。",
    clearSelection: true,
    notifyInvalidated: true,
  });
  scheduleSave();
  window.setTimeout(captureCaret, 20);
  scheduleParagraphAssistInlineBarSync();
});
titleInput.addEventListener("input", () => {
  syncHeadingFromTitle();
  markDraftChanged();
  scheduleSave();
  renderWorkflowState();
});

window.addEventListener("pagehide", flushAutosave);
window.addEventListener("beforeunload", flushAutosave);
window.addEventListener("keydown", handlePresentationKeydown);
window.addEventListener("keydown", handleWorkspaceSaveShortcut);
window.addEventListener("resize", scheduleParagraphAssistInlineBarSync);
window.addEventListener("scroll", scheduleParagraphAssistInlineBarSync, { passive: true });
document.addEventListener("fullscreenchange", () => {
  if (!presentationModeNode || presentationModeNode.hidden) return;
  if (!document.fullscreenElement) exitPresentationMode();
});
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushAutosave();
});

async function bootDocument() {
  setDocumentHydrating(true);
  const requestedDocumentId = resolveDocumentAlias(new URLSearchParams(window.location.search).get("documentId") || "");
  const documentIdToOpen = requestedDocumentId || resolveDocumentAlias(currentDocumentId);
  if (documentIdToOpen) {
    try {
      await openDocument(documentIdToOpen, { preferRemote: Boolean(requestedDocumentId) });
      canonicalizeWorkbenchUrl();
    } catch (error) {
      console.warn("openDocument failed", error);
      documentStateNode.textContent = "工作区文档打开失败";
      documentPathNode.textContent = error?.message || String(error);
      currentDocumentId = "";
      window.localStorage.removeItem(currentDocumentKey);
      canonicalizeWorkbenchUrl();
    }
  }
  if (!currentDocumentId) {
    if (restoreDraft()) {
      syncHeadingFromTitle();
      setDocumentMeta({ state: "已恢复本地草稿", path: "尚未写入工作区" });
      draftNoticeNode.textContent = "已恢复本地未保存改动。";
      renderWorkflowState();
      canonicalizeWorkbenchUrl();
      setDocumentHydrating(false);
      return;
    }
    const latest = await loadLatestGeneratedDraft({ apply: true });
    if (latest) {
      enterLiteMode();
      generateStateNode.textContent = "最新";
      saveStateNode.textContent = "已载入最新";
      setDocumentMeta({ state: "最新全文", path: latest.title || "最新生成稿", showType: false });
      draftNoticeNode.textContent = "已载入全文；可直接划选改句。";
      renderWorkflowState();
      canonicalizeWorkbenchUrl();
      setDocumentHydrating(false);
      return;
    }
    setDocumentMeta({ state: "新稿未保存", path: "尚未写入工作区" });
    draftNoticeNode.textContent = "没有最新生成稿。";
  }
  const latest = await loadLatestGeneratedDraft({ apply: false });
  if (!latest) {
    if (currentDocumentId) {
      setDocumentMeta({ state: "已打开工作区文档", path: `当前文档：${currentDocumentId}` });
    } else {
      setDocumentMeta({ state: "新稿未保存", path: "尚未写入工作区" });
    }
    draftNoticeNode.textContent = currentDocumentId ? "已打开工作区文档" : "没有最新生成稿。";
  }
  renderWorkflowState();
  canonicalizeWorkbenchUrl();
  setDocumentHydrating(false);
}

syncHeadingFromTitle();
setDocumentMeta({ state: "加载中", path: "正在恢复当前稿", showType: false });
renderWorkflowState();
renderAuditResult(null);
enterLiteMode();
restorePresentationPrefs();
updatePresentationSettings();
draftBriefInput.value = "";
draftClaimInput.value = "";
draftSourcesInput.value = "";
if (draftReaderObjectionInput) draftReaderObjectionInput.value = "";
if (draftAvoidShapeInput) draftAvoidShapeInput.value = "";
if (draftAuthorTakeInput) draftAuthorTakeInput.value = "";
draftNoInventInput.value = "";
if (draftPromptModeInput) {
  draftPromptModeInput.value = window.localStorage.getItem(promptModeKey) || "guided";
  draftPromptModeInput.addEventListener("change", () => {
    window.localStorage.setItem(promptModeKey, draftPromptModeInput.value);
  });
}
if (draftProviderInput) {
  draftProviderInput.value = normalizeDraftProvider(window.localStorage.getItem(draftProviderKey));
  draftProviderInput.addEventListener("change", () => {
    providerEngine = normalizeDraftProvider(draftProviderInput.value);
    window.localStorage.setItem(draftProviderKey, providerEngine);
    loadHealth();
  });
}
loadHealth();
refreshMemory();
refreshDocuments();
restoreGeneratedDraft();
restoreOpeningPack();
restoreCowritePlan();
updateParagraphAssistState();
setDocumentHydrating(true);
bootDocument().finally(() => {
  sanitizeVisibleModelDom();
  refreshWorkbenchContext().catch((error) => {
    if (contextStyleNode) contextStyleNode.textContent = `读取失败：${error.message}`;
  });
});

showRawDraftButton.addEventListener("click", () => {
  generatedDraftView = "raw";
  const raw = window.localStorage.getItem(generatedDraftKey);
  if (raw) renderGeneratedDraft(JSON.parse(raw));
});

showCleanDraftButton.addEventListener("click", () => {
  generatedDraftView = "clean";
  const raw = window.localStorage.getItem(generatedDraftKey);
  if (raw) renderGeneratedDraft(JSON.parse(raw));
});

syncLatestButton.addEventListener("click", refreshLatestGeneratedDraft);
loadGeneratedTopButton.addEventListener("click", loadGeneratedIntoEditor);
if (openInObsidianButton) openInObsidianButton.addEventListener("click", openCurrentTopicInObsidian);
if (refreshTopicArchiveButton) refreshTopicArchiveButton.addEventListener("click", refreshTopicArchive);
document.addEventListener("click", (event) => {
  if (latestFoldNode?.open && !latestFoldNode.contains(event.target)) closeLatestFold();
  if (topicFoldNode?.open && !topicFoldNode.contains(event.target)) closeTopicFold();
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  closeLatestFold();
  closeTopicFold();
});
