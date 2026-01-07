/* global ANNOTATION_DATA */

const STORAGE_KEY = "issue-annotation-v2";

const elements = {
  annotatorName: document.getElementById("annotatorName"),
  paperSelect: document.getElementById("paperSelect"),
  unjournalLink: document.getElementById("unjournalLink"),
  humanIssueSelect: document.getElementById("humanIssueSelect"),
  prevIssue: document.getElementById("prevIssue"),
  nextIssue: document.getElementById("nextIssue"),
  selectedIssueText: document.getElementById("selectedIssueText"),
  formattedCritique: document.getElementById("formattedCritique"),
  humanIssues: document.getElementById("humanIssues"),
  llmIssues: document.getElementById("llmIssues"),
  llmReport: document.getElementById("llmReport"),
  addIssue: document.getElementById("addIssue"),
  downloadJson: document.getElementById("downloadJson"),
  downloadCsv: document.getElementById("downloadCsv"),
  clearPaper: document.getElementById("clearPaper"),
  saveStatus: document.getElementById("saveStatus"),
};

const state = {
  annotator: "",
  paperId: null,
  selectedIssueId: null,
  annotations: {},
};

function loadState() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    return;
  }
  try {
    const parsed = JSON.parse(stored);
    state.annotator = parsed.annotator || "";
    state.annotations = parsed.annotations || {};
    Object.keys(state.annotations).forEach((paperId) => {
      const normalized = normalizeIssueList(state.annotations[paperId].issues || []);
      state.annotations[paperId].issues = normalized;
    });
  } catch (err) {
    console.warn("Failed to load stored annotations", err);
  }
}

function saveState() {
  const payload = {
    annotator: state.annotator,
    annotations: state.annotations,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  elements.saveStatus.textContent = `Saved ${new Date().toLocaleTimeString()}`;
}

function buildDefaultIssues(paper) {
  const suggestions = paper.human_issue_suggestions || [];
  const filtered = suggestions.filter((item) => item.text && item.text.trim().length > 0);
  return filtered.map((item, index) => ({
    id: `H${index + 1}`,
    text: item.text || "",
    severity: normalizeSeverity(item.severity || ""),
    match_score: 0,
    match_confidence: 0,
    match_llm_issue_ids: [],
    discussion: "",
    context_not_shared: false,
  }));
}

function normalizeIssueList(issues) {
  const filtered = issues.filter((issue) => {
    const text = issue.text ? issue.text.trim() : "";
    return text.length > 0 && text.toLowerCase() !== "(empty)";
  });
  return filtered.map((issue, index) => ({
    ...issue,
    severity: normalizeSeverity(issue.severity),
    id: `H${index + 1}`,
  }));
}

function normalizeSeverity(value) {
  if (!value) return "";
  const lowered = String(value).toLowerCase();
  if (lowered.includes("necessary")) return "necessary";
  if (lowered.includes("optional")) return "optional";
  if (lowered.includes("unsure")) return "unsure";
  if (lowered.includes("possibly") || lowered.includes("probably") || lowered.includes("less")) {
    return "unsure";
  }
  return lowered;
}

function ensurePaperAnnotations(paper) {
  if (!state.annotations[paper.paper_id]) {
    state.annotations[paper.paper_id] = {
      issues: buildDefaultIssues(paper),
    };
  } else {
    state.annotations[paper.paper_id].issues = normalizeIssueList(
      state.annotations[paper.paper_id].issues || []
    );
  }
}

function renderPaperSelect() {
  elements.paperSelect.innerHTML = "";
  ANNOTATION_DATA.papers.forEach((paper, index) => {
    const option = document.createElement("option");
    option.value = paper.paper_id;
    option.textContent = `${paper.paper_title} (${paper.paper_id})`;
    if (index === 0) {
      option.selected = true;
    }
    elements.paperSelect.appendChild(option);
  });
  state.paperId = elements.paperSelect.value;
}

function getCurrentPaper() {
  return ANNOTATION_DATA.papers.find((paper) => paper.paper_id === state.paperId);
}

function renderLLMIssues(paper) {
  elements.llmIssues.innerHTML = "";
  const issues = paper.llm_key_issues || [];
  issues.forEach((issue, idx) => {
    const li = document.createElement("li");
    li.textContent = `L${idx + 1}. ${issue}`;
    elements.llmIssues.appendChild(li);
  });
}

function renderLLMReport(paper) {
  elements.llmReport.innerHTML = "";
  const text = paper.llm_assessment_summary || "";
  const parts = text.split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean);
  if (!parts.length) {
    elements.llmReport.textContent = "";
    return;
  }
  parts.forEach((part) => {
    const p = document.createElement("p");
    p.textContent = part;
    elements.llmReport.appendChild(p);
  });
}

function renderIssueCard(issue, llmIssues, onUpdate, onRemove) {
  const card = document.createElement("div");
  card.className = "issue-card";

  const header = document.createElement("header");
  header.textContent = issue.id;
  if (issue.severity) {
    const badge = document.createElement("span");
    badge.className = "severity-badge";
    badge.textContent = issue.severity;
    header.appendChild(badge);
  }
  card.appendChild(header);

  const issueText = document.createElement("textarea");
  issueText.value = issue.text;
  issueText.addEventListener("input", (event) => {
    issue.text = event.target.value;
    onUpdate();
  });
  card.appendChild(issueText);

  const row = document.createElement("div");
  row.className = "row";

  const severityWrap = document.createElement("label");
  severityWrap.textContent = "Severity";
  const severitySelect = document.createElement("select");
  ["", "necessary", "optional", "unsure"].forEach((label) => {
    const option = document.createElement("option");
    option.value = label;
    option.textContent = label === "" ? "--" : label;
    if (label === issue.severity) {
      option.selected = true;
    }
    severitySelect.appendChild(option);
  });
  severitySelect.addEventListener("change", (event) => {
    issue.severity = event.target.value;
    onUpdate();
    renderHumanIssueSelect(getCurrentPaper());
    renderFormattedCritique(getCurrentPaper());
  });
  severityWrap.appendChild(severitySelect);
  row.appendChild(severityWrap);

  const scoreWrap = document.createElement("label");
  scoreWrap.textContent = "Match score (0-1)";
  const scoreRange = document.createElement("input");
  scoreRange.type = "range";
  scoreRange.min = 0;
  scoreRange.max = 1;
  scoreRange.step = 0.05;
  scoreRange.value = issue.match_score || 0;
  const scoreNumber = document.createElement("input");
  scoreNumber.type = "number";
  scoreNumber.min = 0;
  scoreNumber.max = 1;
  scoreNumber.step = 0.05;
  scoreNumber.value = issue.match_score || 0;

  const syncScore = (value) => {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
      return;
    }
    issue.match_score = parsed;
    scoreRange.value = parsed;
    scoreNumber.value = parsed;
    onUpdate();
  };

  scoreRange.addEventListener("input", (event) => syncScore(event.target.value));
  scoreNumber.addEventListener("input", (event) => syncScore(event.target.value));
  scoreWrap.appendChild(scoreRange);
  scoreWrap.appendChild(scoreNumber);
  row.appendChild(scoreWrap);

  const confidenceWrap = document.createElement("label");
  confidenceWrap.textContent = "Confidence (0-1)";
  const confidenceRange = document.createElement("input");
  confidenceRange.type = "range";
  confidenceRange.min = 0;
  confidenceRange.max = 1;
  confidenceRange.step = 0.05;
  confidenceRange.value = issue.match_confidence || 0;
  const confidenceNumber = document.createElement("input");
  confidenceNumber.type = "number";
  confidenceNumber.min = 0;
  confidenceNumber.max = 1;
  confidenceNumber.step = 0.05;
  confidenceNumber.value = issue.match_confidence || 0;

  const syncConfidence = (value) => {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
      return;
    }
    issue.match_confidence = parsed;
    confidenceRange.value = parsed;
    confidenceNumber.value = parsed;
    onUpdate();
  };

  confidenceRange.addEventListener("input", (event) =>
    syncConfidence(event.target.value)
  );
  confidenceNumber.addEventListener("input", (event) =>
    syncConfidence(event.target.value)
  );
  confidenceWrap.appendChild(confidenceRange);
  confidenceWrap.appendChild(confidenceNumber);
  row.appendChild(confidenceWrap);

  const contextWrap = document.createElement("label");
  contextWrap.textContent = "Context not shared with LLM";
  const contextCheck = document.createElement("input");
  contextCheck.type = "checkbox";
  contextCheck.checked = Boolean(issue.context_not_shared);
  contextCheck.addEventListener("change", (event) => {
    issue.context_not_shared = event.target.checked;
    onUpdate();
  });
  contextWrap.appendChild(contextCheck);
  row.appendChild(contextWrap);

  const discussionWrap = document.createElement("label");
  discussionWrap.textContent = "Discussion";
  const discussion = document.createElement("textarea");
  discussion.value = issue.discussion || "";
  discussion.addEventListener("input", (event) => {
    issue.discussion = event.target.value;
    onUpdate();
  });
  discussionWrap.appendChild(discussion);
  row.appendChild(discussionWrap);

  card.appendChild(row);

  const matchDetails = document.createElement("details");
  matchDetails.open = true;
  matchDetails.className = "match-details";
  const matchSummary = document.createElement("summary");
  matchSummary.textContent = "Link to LLM issues";
  matchDetails.appendChild(matchSummary);

  const matchList = document.createElement("div");
  matchList.className = "match-list";

  llmIssues.forEach((issueText, idx) => {
    const llmId = `L${idx + 1}`;
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = issue.match_llm_issue_ids.includes(llmId);
    checkbox.addEventListener("change", (event) => {
      if (event.target.checked) {
        issue.match_llm_issue_ids.push(llmId);
      } else {
        issue.match_llm_issue_ids = issue.match_llm_issue_ids.filter(
          (value) => value !== llmId
        );
      }
      onUpdate();
    });
    const text = document.createElement("span");
    text.textContent = `${llmId}. ${issueText}`;
    label.appendChild(checkbox);
    label.appendChild(text);
    matchList.appendChild(label);
  });

  matchDetails.appendChild(matchList);
  card.appendChild(matchDetails);

  const actions = document.createElement("div");
  actions.className = "actions";
  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.textContent = "Remove";
  removeButton.addEventListener("click", () => onRemove(issue.id));
  actions.appendChild(removeButton);
  card.appendChild(actions);

  return card;
}

function renderHumanIssues(paper) {
  elements.humanIssues.innerHTML = "";
  const annotations = state.annotations[paper.paper_id];
  const llmIssues = paper.llm_key_issues || [];

  const issue = annotations.issues.find((item) => item.id === state.selectedIssueId);
  if (!issue && annotations.issues.length) {
    state.selectedIssueId = annotations.issues[0].id;
  }

  const selected = annotations.issues.find(
    (item) => item.id === state.selectedIssueId
  );
  if (selected) {
    elements.selectedIssueText.textContent = selected.text || "";
    const card = renderIssueCard(
      selected,
      llmIssues,
      () => saveState(),
      (issueId) => removeIssue(paper.paper_id, issueId)
    );
    elements.humanIssues.appendChild(card);
  } else {
    elements.selectedIssueText.textContent = "";
  }
}

function renderPaper() {
  const paper = getCurrentPaper();
  if (!paper) {
    return;
  }
  ensurePaperAnnotations(paper);
  state.selectedIssueId = state.annotations[paper.paper_id].issues[0]?.id || null;
  renderHumanIssueSelect(paper);
  renderFormattedCritique(paper);
  renderUnjournalLink(paper);
  renderLLMIssues(paper);
  renderLLMReport(paper);
  renderHumanIssues(paper);
}

function addIssue() {
  const paper = getCurrentPaper();
  const annotations = state.annotations[paper.paper_id];
  const newId = `H${annotations.issues.length + 1}`;
  annotations.issues.push({
    id: newId,
    text: "",
    severity: "",
    match_score: 0,
    match_confidence: 0,
    match_llm_issue_ids: [],
    discussion: "",
    context_not_shared: false,
  });
  saveState();
  state.selectedIssueId = newId;
  renderHumanIssueSelect(paper);
  renderFormattedCritique(paper);
  renderHumanIssues(paper);
}

function removeIssue(paperId, issueId) {
  const annotations = state.annotations[paperId];
  annotations.issues = annotations.issues.filter((issue) => issue.id !== issueId);
  saveState();
  const paper = getCurrentPaper();
  state.selectedIssueId = annotations.issues[0]?.id || null;
  renderHumanIssueSelect(paper);
  renderFormattedCritique(paper);
  renderHumanIssues(paper);
}

function clearPaperAnnotations() {
  const paper = getCurrentPaper();
  if (!paper) {
    return;
  }
  state.annotations[paper.paper_id] = {
    issues: buildDefaultIssues(paper),
  };
  state.selectedIssueId = state.annotations[paper.paper_id].issues[0]?.id || null;
  saveState();
  renderHumanIssueSelect(paper);
  renderFormattedCritique(paper);
  renderHumanIssues(paper);
}

function renderHumanIssueSelect(paper) {
  const annotations = state.annotations[paper.paper_id];
  elements.humanIssueSelect.innerHTML = "";
  annotations.issues.forEach((issue) => {
    const option = document.createElement("option");
    option.value = issue.id;
    const snippet = issue.text ? issue.text.slice(0, 80) : "";
    option.textContent = `${issue.id}: ${snippet}`;
    option.title = issue.text || "";
    if (issue.id === state.selectedIssueId) {
      option.selected = true;
    }
    elements.humanIssueSelect.appendChild(option);
  });
}

function renderFormattedCritique(paper) {
  const annotations = state.annotations[paper.paper_id];
  elements.formattedCritique.innerHTML = "";

  const grouped = { necessary: [], optional: [], unsure: [] };
  annotations.issues.forEach((issue) => {
    const key = issue.severity || "unsure";
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(issue);
  });

  ["necessary", "optional", "unsure"].forEach((tier) => {
    if (!grouped[tier] || grouped[tier].length === 0) {
      return;
    }
    const section = document.createElement("div");
    section.className = "critique-section";
    const header = document.createElement("h3");
    header.textContent = tier;
    section.appendChild(header);

    const list = document.createElement("ol");
    grouped[tier].forEach((issue) => {
      const li = document.createElement("li");
      li.textContent = issue.text || "";
      list.appendChild(li);
    });
    section.appendChild(list);
    elements.formattedCritique.appendChild(section);
  });
}

function renderUnjournalLink(paper) {
  if (!paper.unjournal_search_url) {
    elements.unjournalLink.href = "#";
    elements.unjournalLink.textContent = "Open evaluation summary";
    return;
  }
  elements.unjournalLink.href = paper.unjournal_search_url;
}

function buildExportRows() {
  const rows = [];
  ANNOTATION_DATA.papers.forEach((paper) => {
    const annotations = state.annotations[paper.paper_id] || { issues: [] };
    const llmIssueMap = (paper.llm_key_issues || []).reduce((acc, text, idx) => {
      acc[`L${idx + 1}`] = text;
      return acc;
    }, {});

    annotations.issues.forEach((issue) => {
      const llmTexts = (issue.match_llm_issue_ids || []).map(
        (id) => llmIssueMap[id] || ""
      );
      rows.push({
        annotator: state.annotator,
        paper_id: paper.paper_id,
        paper_title: paper.paper_title,
        human_issue_id: issue.id,
        human_issue_text: issue.text,
        human_issue_severity: issue.severity,
        match_score: issue.match_score,
        match_confidence: issue.match_confidence,
        context_not_shared: issue.context_not_shared,
        llm_issue_ids: (issue.match_llm_issue_ids || []).join(";"),
        llm_issue_texts: llmTexts.join(";"),
        discussion: issue.discussion,
      });
    });
  });
  return rows;
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function exportJson() {
  const rows = buildExportRows();
  const payload = {
    annotator: state.annotator,
    exported_at: new Date().toISOString(),
    rows,
  };
  downloadFile("issue_annotations.json", JSON.stringify(payload, null, 2), "application/json");
}

function exportCsv() {
  const rows = buildExportRows();
  const headers = [
    "annotator",
    "paper_id",
    "paper_title",
    "human_issue_id",
    "human_issue_text",
    "human_issue_severity",
    "match_score",
    "match_confidence",
    "context_not_shared",
    "llm_issue_ids",
    "llm_issue_texts",
    "discussion",
  ];

  const escapeValue = (value) => {
    const text = value === null || value === undefined ? "" : String(value);
    return `"${text.replace(/"/g, '""')}"`;
  };

  const lines = [headers.join(",")];
  rows.forEach((row) => {
    const line = headers.map((header) => escapeValue(row[header])).join(",");
    lines.push(line);
  });
  downloadFile("issue_annotations.csv", lines.join("\n"), "text/csv");
}

function bindEvents() {
  elements.annotatorName.addEventListener("input", (event) => {
    state.annotator = event.target.value;
    saveState();
  });

  elements.paperSelect.addEventListener("change", (event) => {
    state.paperId = event.target.value;
    renderPaper();
  });

  elements.humanIssueSelect.addEventListener("change", (event) => {
    state.selectedIssueId = event.target.value;
    renderHumanIssues(getCurrentPaper());
  });

  elements.prevIssue.addEventListener("click", () => {
    const paper = getCurrentPaper();
    const issues = state.annotations[paper.paper_id].issues;
    const idx = issues.findIndex((issue) => issue.id === state.selectedIssueId);
    if (idx > 0) {
      state.selectedIssueId = issues[idx - 1].id;
      renderHumanIssueSelect(paper);
      renderHumanIssues(paper);
    }
  });

  elements.nextIssue.addEventListener("click", () => {
    const paper = getCurrentPaper();
    const issues = state.annotations[paper.paper_id].issues;
    const idx = issues.findIndex((issue) => issue.id === state.selectedIssueId);
    if (idx >= 0 && idx < issues.length - 1) {
      state.selectedIssueId = issues[idx + 1].id;
      renderHumanIssueSelect(paper);
      renderHumanIssues(paper);
    }
  });

  elements.addIssue.addEventListener("click", addIssue);
  elements.downloadJson.addEventListener("click", exportJson);
  elements.downloadCsv.addEventListener("click", exportCsv);
  elements.clearPaper.addEventListener("click", clearPaperAnnotations);
}

function init() {
  loadState();
  elements.annotatorName.value = state.annotator;
  renderPaperSelect();
  const paper = getCurrentPaper();
  if (paper) {
    ensurePaperAnnotations(paper);
  }
  renderPaper();
  bindEvents();
  saveState();
}

init();
