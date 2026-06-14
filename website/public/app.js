const els = {
  messages: document.querySelector("#messages"),
  form: document.querySelector("#chatForm"),
  prompt: document.querySelector("#prompt"),
  sendButton: document.querySelector("#sendButton"),
  model: document.querySelector("#model"),
  systemPrompt: document.querySelector("#systemPrompt"),
  maxTokens: document.querySelector("#maxTokens"),
  maxTokensValue: document.querySelector("#maxTokensValue"),
  temperature: document.querySelector("#temperature"),
  temperatureValue: document.querySelector("#temperatureValue"),
  thinking: document.querySelector("#thinking"),
  thinkingState: document.querySelector("#thinkingState"),
  sitePassword: document.querySelector("#sitePassword"),
  fileInput: document.querySelector("#fileInput"),
  fileStatus: document.querySelector("#fileStatus"),
  fileWarning: document.querySelector("#fileWarning"),
  clearChat: document.querySelector("#clearChat"),
  exportChat: document.querySelector("#exportChat"),
  checkConnection: document.querySelector("#checkConnection"),
  connectionDot: document.querySelector("#connectionDot"),
  connectionText: document.querySelector("#connectionText"),
  sessionTitle: document.querySelector("#sessionTitle"),
  messageCount: document.querySelector("#messageCount"),
  draftCount: document.querySelector("#draftCount"),
  template: document.querySelector("#messageTemplate"),
};

const state = {
  messages: [],
  fileContext: "",
  fileName: "",
  busy: false,
};

const CHAT_STORAGE_KEY = "chatMessages";
const MAX_SAVED_MESSAGES = 100;
const SYSTEM_PROMPT_VERSION = "rfid-rtl-v2";
const DEFAULT_SYSTEM_PROMPT = `You are an expert low-power digital IC RTL designer specializing in RFID tag/baseband logic.

Your task is to generate synthesizable SystemVerilog RTL optimized for passive or ultra-low-power RFID chips.

Optimization priority:
1. Functional correctness and synthesizability.
2. Minimize area.
3. Minimize dynamic and leakage power.
4. Meet only the required timing/throughput constraints.
5. Do not optimize for maximum speed unless explicitly required.

Important design philosophy:
- The chip is area- and power-constrained.
- Latency may be increased if this reduces area or power.
- Prefer serial, iterative, shared-resource, and FSM-based architectures over wide parallel datapaths.
- Prefer small counters, narrow registers, simple comparators, simple muxing, and reused datapath blocks.
- Avoid unnecessary arithmetic width.
- Avoid multipliers, dividers, large barrel shifters, large lookup tables, large FIFOs, and wide combinational logic unless required.
- Avoid unnecessary pipelining because it increases flip-flops and clock power.
- Avoid unnecessary resets, especially datapath resets, unless required for correctness.
- Prefer clock-enable style RTL so synthesis can infer integrated clock gating where appropriate.
- Do not manually instantiate technology-specific clock-gating cells unless a specific standard-cell library is provided.
- Minimize signal toggling by holding registers stable when idle.
- Use explicit valid/enable conditions to prevent unnecessary switching.
- Use one-hot FSM only if it likely reduces logic or timing risk; otherwise prefer compact binary or gray-style state encoding for area.
- Prefer ROM/table-free logic when the table would be large.
- Prefer LFSR or simple bitwise logic for lightweight pseudo-random behavior when acceptable.
- Prefer resource sharing when operations do not need to happen in the same cycle.

SystemVerilog requirements:
- Generate synthesizable SystemVerilog.
- Use always_ff for sequential logic.
- Use always_comb for combinational logic.
- Use nonblocking assignments in sequential logic.
- Use blocking assignments in combinational logic.
- Avoid inferred latches.
- Avoid unsynthesizable constructs.
- Avoid delays, initial blocks for hardware behavior, fork/join, dynamic arrays, classes, randomization, and simulation-only code.
- Parameterize widths when useful, but do not over-parameterize simple logic.
- Include clear reset behavior.
- Keep module interfaces simple and hardware-realistic.

Before writing RTL:
1. Restate the minimum required behavior.
2. List assumptions.
3. Propose at least two microarchitectures:
   - lowest-area/lowest-power architecture
   - faster but larger fallback architecture, only if useful
4. Compare the architectures qualitatively for area, power, latency, and timing risk.
5. Choose the architecture that best matches area and power priority.

When producing RTL:
- Output only one final chosen RTL implementation unless asked for alternatives.
- Include concise comments explaining area/power decisions.
- Do not claim exact area, power, or timing numbers unless synthesis reports are provided.
- If constraints are missing, make conservative assumptions and state them clearly.

After RTL:
1. Explain why the design is area-efficient.
2. Explain why the design is power-efficient.
3. List expected synthesis risks.
4. Suggest synthesis constraints or attributes only when appropriate.
5. Suggest testbench scenarios.

Interaction behavior:
- If the user gives a complete RTL task, follow the full design workflow.
- If the user only greets you or gives an unclear request, ask briefly for the missing block specification.
- Do not produce architecture analysis, RTL, or long explanations until a concrete design task is provided.
- Keep clarification responses short.`;

const storage = {
  get(key, fallback = "") {
    try {
      return localStorage.getItem(key) ?? fallback;
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Ignore storage failures in private browsing contexts.
    }
  },
  remove(key) {
    try {
      localStorage.removeItem(key);
    } catch {
      // Ignore storage failures in private browsing contexts.
    }
  },
};

function saveChat() {
  const messages = state.messages.slice(-MAX_SAVED_MESSAGES);
  storage.set(CHAT_STORAGE_KEY, JSON.stringify(messages));
}

function restoreChat() {
  const raw = storage.get(CHAT_STORAGE_KEY, "");
  if (!raw) return false;

  try {
    const saved = JSON.parse(raw);
    if (!Array.isArray(saved)) return false;

    state.messages = saved
      .filter((message) => message && ["user", "assistant"].includes(message.role))
      .map((message) => ({
        role: message.role,
        content: String(message.content || "").slice(0, 120000),
        attachmentName: message.role === "user" ? String(message.attachmentName || "").slice(0, 255) : "",
      }))
      .slice(-MAX_SAVED_MESSAGES);

    for (const message of state.messages) {
      renderMessage(message.role, message.content, message.attachmentName);
    }
    return state.messages.length > 0;
  } catch {
    storage.remove(CHAT_STORAGE_KEY);
    return false;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
}

function formatMarkdownBlocks(value) {
  const lines = String(value || "").split("\n");
  const blocks = [];
  let paragraph = [];
  let listType = "";
  let listItems = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    blocks.push(`<p>${paragraph.map(formatInlineMarkdown).join("<br>")}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(`<${listType}>${listItems.map((item) => `<li>${formatInlineMarkdown(item)}</li>`).join("")}</${listType}>`);
    listType = "";
    listItems = [];
  };

  for (const line of lines) {
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    const unordered = line.match(/^\s*[-*+]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    const quote = line.match(/^>\s?(.*)$/);

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      blocks.push(`<h${level}>${formatInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    if (unordered || ordered) {
      flushParagraph();
      const nextType = unordered ? "ul" : "ol";
      if (listType && listType !== nextType) flushList();
      listType = nextType;
      listItems.push((unordered || ordered)[1]);
      continue;
    }

    if (quote) {
      flushParagraph();
      flushList();
      blocks.push(`<blockquote>${formatInlineMarkdown(quote[1])}</blockquote>`);
      continue;
    }

    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();
  return blocks.join("");
}

function formatContent(content) {
  const parts = String(content || "").split(/```/g);
  return parts
    .map((part, index) => {
      if (index % 2 === 0) return formatMarkdownBlocks(part);
      const code = part.replace(/^[a-zA-Z0-9_-]+\n/, "");
      return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    })
    .join("");
}

function updateChrome() {
  const turns = state.messages.length;
  els.messageCount.textContent = `${turns} message${turns === 1 ? "" : "s"}`;
  els.thinkingState.textContent = els.thinking.checked ? "Thinking on" : "Thinking off";
  els.sessionTitle.textContent = els.model.value.trim() || "qwen36-27b";
  els.draftCount.textContent = `${els.prompt.value.length} chars`;
}

function resizePrompt() {
  els.prompt.style.height = "auto";
  els.prompt.style.height = `${Math.min(els.prompt.scrollHeight, 116)}px`;
}

function setRangePair(rangeEl, valueEl, rawValue) {
  const min = Number.parseFloat(rangeEl.min);
  const max = Number.parseFloat(rangeEl.max);
  const step = rangeEl.step.includes(".") ? 1 : 0;
  const parsed = Number.parseFloat(rawValue);
  if (Number.isNaN(parsed)) return "";

  const clamped = Math.min(Math.max(parsed, min), max);
  const value = step ? clamped.toFixed(step) : String(Math.round(clamped));
  rangeEl.value = value;
  valueEl.value = value;
  return value;
}

function bindRangePair(key, rangeEl, valueEl) {
  const sync = (source) => {
    const value = setRangePair(rangeEl, valueEl, source.value);
    if (!value) return;
    storage.set(key, value);
    updateChrome();
  };

  rangeEl.addEventListener("input", () => sync(rangeEl));
  valueEl.addEventListener("input", () => sync(valueEl));
}

function renderMessage(role, content, attachmentName = "") {
  const node = els.template.content.firstElementChild.cloneNode(true);
  const contentEl = node.querySelector(".message-text");
  const attachmentEl = node.querySelector(".message-attachment");
  const copyButton = node.querySelector(".copy-message");
  node.classList.add(role);
  node.querySelector(".role").textContent = role;
  if (role === "user" && attachmentName) {
    attachmentEl.textContent = `Attached ${attachmentName}`;
    attachmentEl.hidden = false;
  }
  contentEl.innerHTML = formatContent(content);
  node.dataset.rawContent = content;
  copyButton.addEventListener("click", async () => {
    await navigator.clipboard.writeText(node.dataset.rawContent || "");
  });
  els.messages.appendChild(node);
  els.messages.scrollTop = els.messages.scrollHeight;
  return node;
}

function updateMessage(node, content) {
  node.dataset.rawContent = content;
  node.querySelector(".message-text").innerHTML = formatContent(content);
  els.messages.scrollTop = els.messages.scrollHeight;
}

async function readStreamingAnswer(response, node) {
  if (!response.body) throw new Error("Streaming response body is unavailable");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let answer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (!payload || payload === "[DONE]") continue;

      let event;
      try {
        event = JSON.parse(payload);
      } catch {
        continue;
      }

      const delta = event.choices?.[0]?.delta?.content;
      if (typeof delta !== "string" || !delta) continue;
      answer += delta;
      updateMessage(node, answer);
    }

    if (done) break;
  }

  return answer;
}

function setBusy(busy) {
  state.busy = busy;
  els.sendButton.disabled = busy;
  els.sendButton.querySelector("span").textContent = busy ? "Sending" : "Send";
}

function setConnection(status, text) {
  els.connectionDot.classList.remove("online", "offline");
  if (status) els.connectionDot.classList.add(status);
  els.connectionText.textContent = text;
}

function setFileWarning(message = "") {
  els.fileWarning.textContent = message;
  els.fileWarning.classList.toggle("visible", Boolean(message));
}

function clearFileContext() {
  state.fileContext = "";
  state.fileName = "";
  els.fileInput.value = "";
  els.fileStatus.classList.remove("has-file");
  els.fileStatus.textContent = "";
  setFileWarning();
}

function renderFileBadge(file) {
  els.fileStatus.classList.add("has-file");
  els.fileStatus.innerHTML = `
    <span>File: ${escapeHtml(file.name)} (${Math.ceil(file.size / 1024)} KB)</span>
    <button type="button" aria-label="Remove attached file">&times;</button>
  `;
  els.fileStatus.querySelector("button").addEventListener("click", clearFileContext);
}

function buildMessages(userContent) {
  const messages = [];
  const systemPrompt = els.systemPrompt.value.trim();
  if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
  messages.push(...state.messages.slice(-24));
  messages.push({ role: "user", content: userContent });
  return messages;
}

async function sendChat(userContent) {
  const fileContext = state.fileContext;
  const attachmentName = state.fileName;
  setBusy(true);
  renderMessage("user", userContent, attachmentName);
  const assistantNode = renderMessage("assistant", "");
  assistantNode.classList.add("streaming");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-site-password": els.sitePassword.value,
      },
      body: JSON.stringify({
        model: els.model.value.trim() || "qwen36-27b",
        messages: buildMessages(userContent),
        max_tokens: Number.parseInt(els.maxTokens.value || "1024", 10),
        temperature: Number.parseFloat(els.temperature.value || "0.7"),
        thinking: els.thinking.checked,
        file_context: fileContext,
        stream: true,
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error ? `${data.error}: ${JSON.stringify(data.detail || "")}` : "Request failed");
    }

    const answer = await readStreamingAnswer(response, assistantNode);
    updateMessage(assistantNode, answer || "(empty response)");
    state.messages.push({ role: "user", content: userContent, attachmentName });
    state.messages.push({ role: "assistant", content: answer });
    saveChat();
    if (fileContext) clearFileContext();
    setConnection("online", "Gateway online");
  } catch (error) {
    updateMessage(assistantNode, `Error: ${error.message}`);
    setConnection("offline", "Gateway error");
  } finally {
    assistantNode.classList.remove("streaming");
    setBusy(false);
    updateChrome();
  }
}

async function checkConnection() {
  setConnection("", "Checking gateway");
  try {
    const modelsResponse = await fetch("/api/models", {
      headers: {
        "x-site-password": els.sitePassword.value,
      },
    });

    if (modelsResponse.ok) {
      const modelsData = await modelsResponse.json();
      const servedModel = modelsData?.data?.[0]?.id;
      if (servedModel && servedModel !== els.model.value.trim()) {
        els.model.value = servedModel;
        storage.set("model", servedModel);
        updateChrome();
      }
    }

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-site-password": els.sitePassword.value,
      },
      body: JSON.stringify({
        model: els.model.value.trim() || "qwen36-27b",
        messages: [{ role: "user", content: "Reply exactly: online" }],
        max_tokens: 8,
        temperature: 0,
        thinking: false,
      }),
    });

    if (!response.ok) throw new Error("offline");
    setConnection("online", "Gateway online");
  } catch {
    setConnection("offline", "Gateway offline");
  }
}

function restorePrefs() {
  els.sitePassword.value = storage.get("sitePassword", "");
  els.model.value = storage.get("model", els.model.value);
  const promptVersion = storage.get("systemPromptVersion", "");
  if (promptVersion !== SYSTEM_PROMPT_VERSION) {
    els.systemPrompt.value = DEFAULT_SYSTEM_PROMPT;
    storage.set("systemPrompt", DEFAULT_SYSTEM_PROMPT);
    storage.set("systemPromptVersion", SYSTEM_PROMPT_VERSION);
  } else {
    els.systemPrompt.value = storage.get("systemPrompt", DEFAULT_SYSTEM_PROMPT);
  }
  setRangePair(els.maxTokens, els.maxTokensValue, storage.get("maxTokens", els.maxTokens.value));
  setRangePair(els.temperature, els.temperatureValue, storage.get("temperature", els.temperature.value));
  els.thinking.checked = storage.get("thinking", "0") === "1";
}

function wirePrefs() {
  for (const [key, element] of [
    ["sitePassword", els.sitePassword],
    ["model", els.model],
    ["systemPrompt", els.systemPrompt],
  ]) {
    element.addEventListener("input", () => {
      storage.set(key, element.value);
      updateChrome();
    });
  }
  els.thinking.addEventListener("change", () => {
    storage.set("thinking", els.thinking.checked ? "1" : "0");
    updateChrome();
  });
  bindRangePair("maxTokens", els.maxTokens, els.maxTokensValue);
  bindRangePair("temperature", els.temperature, els.temperatureValue);
}

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy) return;
  const prompt = els.prompt.value.trim();
  if (!prompt) return;
  els.prompt.value = "";
  updateChrome();
  resizePrompt();
  await sendChat(prompt);
});

els.prompt.addEventListener("input", () => {
  updateChrome();
  resizePrompt();
});

els.prompt.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;

  if (event.ctrlKey || event.metaKey) {
    event.preventDefault();
    const start = els.prompt.selectionStart;
    const end = els.prompt.selectionEnd;
    els.prompt.setRangeText("\n", start, end, "end");
    updateChrome();
    resizePrompt();
    return;
  }

  event.preventDefault();
  els.form.requestSubmit();
});

els.clearChat.addEventListener("click", () => {
  state.messages = [];
  storage.remove(CHAT_STORAGE_KEY);
  els.messages.innerHTML = "";
  renderMessage("system", "Session cleared. Ask a new question when ready.");
  updateChrome();
});

els.exportChat.addEventListener("click", () => {
  const text = state.messages.map((message) => `${message.role.toUpperCase()}\n${message.content}`).join("\n\n");
  const blob = new Blob([text || "No chat messages yet."], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `llm-test-chat-${new Date().toISOString().slice(0, 19).replaceAll(":", "-")}.txt`;
  link.click();
  URL.revokeObjectURL(url);
});

els.checkConnection.addEventListener("click", checkConnection);

els.fileInput.addEventListener("change", async () => {
  const file = els.fileInput.files?.[0];
  if (!file) {
    clearFileContext();
    return;
  }

  const maxBytes = 220000;
  if (file.size > maxBytes) {
    clearFileContext();
    setFileWarning(`File too large. Limit: ${Math.round(maxBytes / 1000)} KB.`);
    return;
  }

  const text = await file.text();
  state.fileContext = `File: ${file.name}\n\n${text}`;
  state.fileName = file.name;
  setFileWarning();
  renderFileBadge(file);
});

restorePrefs();
wirePrefs();
if (!restoreChat()) {
  renderMessage("system", "Ready. Ask me something, or attach a small text file for context.");
}
updateChrome();
resizePrompt();
checkConnection();
