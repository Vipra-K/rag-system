const state = {
  documents: [],
  selected: new Set(),
  messages: [],
  busy: false,
  dragging: 0,
};

const elements = {
  sidebar: document.querySelector("#sidebar"),
  sidebarScrim: document.querySelector("#sidebarScrim"),
  documentList: document.querySelector("#documentList"),
  fileInput: document.querySelector("#fileInput"),
  uploadButton: document.querySelector("#uploadButton"),
  selectAllButton: document.querySelector("#selectAllButton"),
  newChatButton: document.querySelector("#newChatButton"),
  clearChatButton: document.querySelector("#clearChatButton"),
  openSidebar: document.querySelector("#openSidebar"),
  closeSidebar: document.querySelector("#closeSidebar"),
  scopeLabel: document.querySelector("#scopeLabel"),
  composerScope: document.querySelector("#composerScope"),
  conversation: document.querySelector("#conversation"),
  welcome: document.querySelector("#welcome"),
  messageStream: document.querySelector("#messageStream"),
  questionInput: document.querySelector("#questionInput"),
  sendButton: document.querySelector("#sendButton"),
  dropOverlay: document.querySelector("#dropOverlay"),
  toastRegion: document.querySelector("#toastRegion"),
};

const icons = {
  file: '<svg viewBox="0 0 24 24"><path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M5 7h14M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5M14 11v5"/></svg>',
  check: '<svg viewBox="0 0 24 24"><path d="m6 12 4 4 8-9"/></svg>',
  assistant: '<svg viewBox="0 0 24 24"><path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15h5"/></svg>',
  source: '<svg viewBox="0 0 24 24"><path d="M7 3.5h7l4 4v13H7zM14 3.5v4h4"/></svg>',
  success: '<svg viewBox="0 0 24 24"><path d="m5 12 4.5 4.5L19 7"/></svg>',
  error: '<svg viewBox="0 0 24 24"><path d="M12 8v5m0 3.5v.01M12 3.5 21 20H3z"/></svg>',
};

function loadSavedChat() {
  try {
    const saved = JSON.parse(localStorage.getItem("docchat.messages") || "[]");
    if (Array.isArray(saved)) state.messages = saved.slice(-50);
  } catch (_) {
    state.messages = [];
  }
}

function saveChat() {
  localStorage.setItem("docchat.messages", JSON.stringify(state.messages.slice(-50)));
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (response.ok) return response.status === 204 ? null : response.json();

  let message = `Request failed (${response.status})`;
  try {
    const body = await response.json();
    if (typeof body.detail === "string") message = body.detail;
    else if (Array.isArray(body.detail)) message = body.detail[0]?.msg || message;
  } catch (_) {}
  throw new Error(message);
}

async function loadDocuments({ selectNew = [] } = {}) {
  const previousSelection = new Set(state.selected);
  try {
    state.documents = await api("/documents");
    const validIds = new Set(state.documents.map((item) => item.document_id));
    state.selected = new Set(
      [...previousSelection].filter((documentId) => validIds.has(documentId))
    );
    selectNew.forEach((documentId) => {
      if (validIds.has(documentId)) state.selected.add(documentId);
    });

    if (!previousSelection.size && !selectNew.length) {
      state.documents.forEach((item) => state.selected.add(item.document_id));
    }
    renderDocuments();
    updateScope();
  } catch (error) {
    elements.documentList.innerHTML = '<div class="empty-library">Could not load your document library.</div>';
    showToast(error.message, "error");
  }
}

function renderDocuments() {
  elements.documentList.replaceChildren();
  if (!state.documents.length) {
    const empty = document.createElement("div");
    empty.className = "empty-library";
    empty.textContent = "Your uploaded PDFs will appear here.";
    elements.documentList.append(empty);
    return;
  }

  state.documents.forEach((documentItem) => {
    const item = document.createElement("div");
    item.className = `document-item${state.selected.has(documentItem.document_id) ? " selected" : ""}`;
    item.tabIndex = 0;
    item.setAttribute("role", "checkbox");
    item.setAttribute("aria-checked", String(state.selected.has(documentItem.document_id)));
    item.title = documentItem.filename;

    const check = document.createElement("span");
    check.className = "document-check";
    check.innerHTML = icons.check;

    const copy = document.createElement("span");
    copy.className = "document-copy";
    const name = document.createElement("span");
    name.className = "document-name";
    name.textContent = documentItem.filename;
    const meta = document.createElement("span");
    meta.className = "document-meta";
    meta.textContent = `${documentItem.total_pages} page${documentItem.total_pages === 1 ? "" : "s"} · ${documentItem.total_chunks} chunks`;
    copy.append(name, meta);

    const remove = document.createElement("button");
    remove.className = "delete-document";
    remove.type = "button";
    remove.title = `Delete ${documentItem.filename}`;
    remove.setAttribute("aria-label", `Delete ${documentItem.filename}`);
    remove.innerHTML = icons.trash;
    remove.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteDocument(documentItem);
    });

    const toggle = () => toggleDocument(documentItem.document_id);
    item.addEventListener("click", toggle);
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    });
    item.append(check, copy, remove);
    elements.documentList.append(item);
  });
}

function toggleDocument(documentId) {
  if (state.selected.has(documentId)) state.selected.delete(documentId);
  else state.selected.add(documentId);
  renderDocuments();
  updateScope();
}

function updateScope() {
  const count = state.selected.size;
  const total = state.documents.length;
  let label = "No documents selected";

  if (count === 1) {
    label = state.documents.find((item) => state.selected.has(item.document_id))?.filename || "1 document selected";
  } else if (count > 1 && count === total) {
    label = `All ${count} documents`;
  } else if (count > 1) {
    label = `${count} documents selected`;
  }

  elements.scopeLabel.textContent = total ? label : "Upload a PDF to begin";
  elements.composerScope.textContent = label;
  elements.selectAllButton.textContent = count === total && total ? "Clear" : "Select all";
  updateSendButton();
}

function updateSendButton() {
  elements.sendButton.disabled = (
    state.busy ||
    !elements.questionInput.value.trim() ||
    !state.selected.size
  );
}

async function uploadFiles(files) {
  const pdfFiles = [...files].filter((file) => (
    file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
  ));
  if (!pdfFiles.length) {
    showToast("Please choose one or more PDF files.", "error");
    return;
  }

  const uploadedIds = [];
  for (const file of pdfFiles) {
    const data = new FormData();
    data.append("file", file);
    showToast(`Indexing ${file.name}…`);
    try {
      const result = await api("/documents/upload", { method: "POST", body: data });
      uploadedIds.push(result.document_id);
      showToast(`${file.name} is ready — ${result.total_chunks} chunks indexed.`);
    } catch (error) {
      showToast(`${file.name}: ${error.message}`, "error");
    }
  }
  elements.fileInput.value = "";
  await loadDocuments({ selectNew: uploadedIds });
}

async function deleteDocument(documentItem) {
  const confirmed = window.confirm(
    `Delete “${documentItem.filename}” from the knowledge base? This cannot be undone.`
  );
  if (!confirmed) return;

  try {
    await api(`/documents/${encodeURIComponent(documentItem.document_id)}`, { method: "DELETE" });
    state.selected.delete(documentItem.document_id);
    await loadDocuments();
    showToast(`${documentItem.filename} was deleted.`);
  } catch (error) {
    showToast(error.message, "error");
  }
}

function addMessage(message, { persist = true } = {}) {
  if (persist) {
    state.messages.push(message);
    saveChat();
  }
  elements.welcome.classList.add("hidden");
  elements.messageStream.append(createMessageElement(message));
  scrollToBottom();
}

function createMessageElement(message) {
  const row = document.createElement("article");
  row.className = `message-row ${message.role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.innerHTML = message.role === "assistant" ? icons.assistant : "You";

  const content = document.createElement("div");
  content.className = "message-content";
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = message.role === "assistant" ? "DocChat" : "You";
  const body = document.createElement("div");
  body.className = "answer-body";

  if (message.loading) {
    body.innerHTML = '<div class="thinking" aria-label="Thinking"><i></i><i></i><i></i></div>';
  } else if (message.role === "assistant") {
    renderRichText(message.content, body);
  } else {
    const paragraph = document.createElement("p");
    paragraph.textContent = message.content;
    body.append(paragraph);
  }
  content.append(label, body);

  if (message.sources?.length) {
    const sourceList = document.createElement("div");
    sourceList.className = "source-list";
    message.sources.forEach((source) => {
      const documentItem = state.documents.find((item) => item.document_id === source.document_id);
      const chip = document.createElement("span");
      chip.className = "source-chip";
      chip.innerHTML = icons.source;
      const text = document.createElement("span");
      text.textContent = `${documentItem?.filename || `Document ${source.document_id.slice(0, 8)}`} · page ${source.page_number}`;
      chip.title = text.textContent;
      chip.append(text);
      sourceList.append(chip);
    });
    content.append(sourceList);
  }

  row.append(avatar, content);
  return row;
}

function appendInlineText(container, text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  parts.forEach((part) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = part.slice(2, -2);
      container.append(strong);
    } else {
      container.append(document.createTextNode(part));
    }
  });
}

function renderRichText(text, container) {
  const lines = String(text || "").split(/\r?\n/);
  let list = null;
  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      list = null;
      return;
    }
    const bullet = line.match(/^[-*•]\s+(.+)/);
    const numbered = line.match(/^\d+[.)]\s+(.+)/);
    if (bullet || numbered) {
      const type = numbered ? "ol" : "ul";
      if (!list || list.tagName.toLowerCase() !== type) {
        list = document.createElement(type);
        container.append(list);
      }
      const item = document.createElement("li");
      appendInlineText(item, (bullet || numbered)[1]);
      list.append(item);
      return;
    }
    list = null;
    if (/^#{1,3}\s+/.test(line)) {
      const heading = document.createElement("h3");
      appendInlineText(heading, line.replace(/^#{1,3}\s+/, ""));
      container.append(heading);
    } else {
      const paragraph = document.createElement("p");
      appendInlineText(paragraph, line);
      container.append(paragraph);
    }
  });
}

async function sendQuestion(question = elements.questionInput.value) {
  question = question.trim();
  if (!question || state.busy) return;
  if (!state.selected.size) {
    showToast("Select at least one PDF first.", "error");
    return;
  }

  state.busy = true;
  elements.questionInput.value = "";
  resizeTextarea();
  updateSendButton();
  addMessage({ role: "user", content: question });

  const loading = createMessageElement({ role: "assistant", loading: true });
  loading.dataset.loading = "true";
  elements.messageStream.append(loading);
  scrollToBottom();

  try {
    const result = await api("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        document_ids: [...state.selected],
      }),
    });
    loading.remove();
    addMessage({ role: "assistant", content: result.answer, sources: result.sources });
  } catch (error) {
    loading.remove();
    addMessage({
      role: "assistant",
      content: `I couldn't complete that request. ${error.message}`,
      sources: [],
    });
    showToast(error.message, "error");
  } finally {
    state.busy = false;
    updateSendButton();
    elements.questionInput.focus();
  }
}

function renderSavedMessages() {
  elements.messageStream.replaceChildren();
  state.messages.forEach((message) => addMessage(message, { persist: false }));
  elements.welcome.classList.toggle("hidden", Boolean(state.messages.length));
}

function clearChat() {
  state.messages = [];
  saveChat();
  elements.messageStream.replaceChildren();
  elements.welcome.classList.remove("hidden");
  elements.questionInput.focus();
}

function resizeTextarea() {
  elements.questionInput.style.height = "auto";
  elements.questionInput.style.height = `${Math.min(elements.questionInput.scrollHeight, 160)}px`;
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    elements.conversation.scrollTop = elements.conversation.scrollHeight;
  });
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "error" : ""}`;
  toast.innerHTML = type === "error" ? icons.error : icons.success;
  const text = document.createElement("span");
  text.textContent = message;
  toast.append(text);
  elements.toastRegion.append(toast);
  setTimeout(() => toast.remove(), 4400);
}

function openSidebar() {
  elements.sidebar.classList.add("open");
  elements.sidebarScrim.classList.add("visible");
}

function closeSidebar() {
  elements.sidebar.classList.remove("open");
  elements.sidebarScrim.classList.remove("visible");
}

elements.uploadButton.addEventListener("click", () => elements.fileInput.click());
elements.fileInput.addEventListener("change", () => uploadFiles(elements.fileInput.files));
elements.newChatButton.addEventListener("click", () => { clearChat(); closeSidebar(); });
elements.clearChatButton.addEventListener("click", clearChat);
elements.openSidebar.addEventListener("click", openSidebar);
elements.closeSidebar.addEventListener("click", closeSidebar);
elements.sidebarScrim.addEventListener("click", closeSidebar);
elements.selectAllButton.addEventListener("click", () => {
  if (state.selected.size === state.documents.length) state.selected.clear();
  else state.documents.forEach((item) => state.selected.add(item.document_id));
  renderDocuments();
  updateScope();
});
elements.questionInput.addEventListener("input", () => {
  resizeTextarea();
  updateSendButton();
});
elements.questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    sendQuestion();
  }
});
elements.sendButton.addEventListener("click", () => sendQuestion());
document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    elements.questionInput.value = button.dataset.question;
    resizeTextarea();
    updateSendButton();
    elements.questionInput.focus();
  });
});

window.addEventListener("dragenter", (event) => {
  event.preventDefault();
  state.dragging += 1;
  elements.dropOverlay.classList.add("visible");
});
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("dragleave", (event) => {
  event.preventDefault();
  state.dragging = Math.max(0, state.dragging - 1);
  if (!state.dragging) elements.dropOverlay.classList.remove("visible");
});
window.addEventListener("drop", (event) => {
  event.preventDefault();
  state.dragging = 0;
  elements.dropOverlay.classList.remove("visible");
  uploadFiles(event.dataTransfer.files);
});

loadSavedChat();
renderSavedMessages();
elements.documentList.innerHTML = '<div class="library-loader"><div class="skeleton"></div><div class="skeleton"></div></div>';
loadDocuments();
