(() => {
  "use strict";

  const STORAGE_KEY = "quickboard.cards.v1";
  const STATUSES = ["todo", "in-progress", "done"];
  const STATUS_LABELS = {
    todo: "待办",
    "in-progress": "进行中",
    done: "已完成",
  };

  const newTaskButton = document.querySelector("#new-task-button");
  const dialog = document.querySelector("#task-dialog");
  const form = document.querySelector("#task-form");
  const dialogTitle = document.querySelector("#dialog-title");
  const closeButton = document.querySelector("#dialog-close");
  const cancelButton = document.querySelector("#dialog-cancel");
  const idField = document.querySelector("#task-id");
  const titleField = document.querySelector("#task-title");
  const descriptionField = document.querySelector("#task-description");
  const statusField = document.querySelector("#task-status");
  const titleError = document.querySelector("#title-error");
  const announcer = document.querySelector("#board-announcer");

  let cards = loadCards();
  renderBoard();

  newTaskButton?.addEventListener("click", () => openEditor());
  closeButton?.addEventListener("click", closeEditor);
  cancelButton?.addEventListener("click", closeEditor);

  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) {
      closeEditor();
    }
  });

  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    saveFromForm();
  });

  titleField?.addEventListener("input", () => {
    if (titleField.value.trim()) {
      clearTitleError();
    }
  });

  function loadCards() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.map(normalizeCard).filter(Boolean);
    } catch (error) {
      console.warn("QuickBoard could not load saved data.", error);
      return [];
    }
  }

  function persistCards() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cards));
      return true;
    } catch (error) {
      console.warn("QuickBoard could not save data.", error);
      announce("浏览器无法保存当前更改；页面仍可继续使用。", true);
      return false;
    }
  }

  function normalizeCard(value) {
    if (!value || typeof value !== "object") return null;
    const title = typeof value.title === "string" ? value.title.trim().slice(0, 120) : "";
    if (!title) return null;
    const description = typeof value.description === "string"
      ? value.description.slice(0, 1000)
      : "";
    const status = STATUSES.includes(value.status) ? value.status : "todo";
    const createdAt = validTimestamp(value.createdAt) ? value.createdAt : new Date().toISOString();
    const updatedAt = validTimestamp(value.updatedAt) ? value.updatedAt : createdAt;
    const id = typeof value.id === "string" && value.id.trim()
      ? value.id.trim().slice(0, 160)
      : createId();
    return { id, title, description, status, createdAt, updatedAt };
  }

  function validTimestamp(value) {
    return typeof value === "string" && !Number.isNaN(Date.parse(value));
  }

  function createId() {
    if (globalThis.crypto?.randomUUID) {
      return globalThis.crypto.randomUUID();
    }
    return `qb-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  }

  function renderBoard() {
    for (const status of STATUSES) {
      const container = document.querySelector(`[data-column="${status}"]`);
      if (!container) continue;
      container.replaceChildren();

      const matching = cards.filter((card) => card.status === status);
      for (const card of matching) {
        container.append(createCardElement(card));
      }

      document.querySelectorAll(`[data-count="${status}"]`).forEach((node) => {
        node.textContent = String(matching.length);
      });

      const empty = document.querySelector(`[data-empty="${status}"]`);
      if (empty) empty.hidden = matching.length > 0;
    }
  }

  function createCardElement(card) {
    const article = document.createElement("article");
    article.className = "task-card";
    article.dataset.status = card.status;
    article.dataset.cardId = card.id;

    const heading = document.createElement("h3");
    heading.textContent = card.title;
    article.append(heading);

    if (card.description) {
      const description = document.createElement("p");
      description.textContent = card.description;
      article.append(description);
    }

    const meta = document.createElement("div");
    meta.className = "card-meta";

    const statusLabel = document.createElement("label");
    statusLabel.className = "status-label";
    const selectId = `status-${card.id.replace(/[^A-Za-z0-9_-]/g, "-")}`;
    statusLabel.htmlFor = selectId;
    statusLabel.textContent = "状态";

    const select = document.createElement("select");
    select.className = "status-select";
    select.id = selectId;
    select.setAttribute("aria-label", `${card.title} 的状态`);
    for (const status of STATUSES) {
      const option = document.createElement("option");
      option.value = status;
      option.textContent = STATUS_LABELS[status];
      option.selected = card.status === status;
      select.append(option);
    }
    select.addEventListener("change", () => moveCard(card.id, select.value));

    meta.append(statusLabel, select);
    article.append(meta);

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "card-action";
    edit.textContent = "编辑";
    edit.setAttribute("aria-label", `编辑任务：${card.title}`);
    edit.addEventListener("click", () => openEditor(card));

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "card-action card-action-danger";
    remove.textContent = "删除";
    remove.setAttribute("aria-label", `删除任务：${card.title}`);
    remove.addEventListener("click", () => deleteCard(card.id));

    actions.append(edit, remove);
    article.append(actions);
    return article;
  }

  function openEditor(card = null) {
    clearTitleError();
    form?.reset();

    if (card) {
      dialogTitle.textContent = "编辑任务";
      idField.value = card.id;
      titleField.value = card.title;
      descriptionField.value = card.description;
      statusField.value = card.status;
    } else {
      dialogTitle.textContent = "新建任务";
      idField.value = "";
      titleField.value = "";
      descriptionField.value = "";
      statusField.value = "todo";
    }

    if (typeof dialog?.showModal === "function") {
      dialog.showModal();
      requestAnimationFrame(() => titleField?.focus());
    }
  }

  function closeEditor() {
    if (dialog?.open) dialog.close();
    clearTitleError();
  }

  function saveFromForm() {
    const title = (titleField?.value || "").trim().slice(0, 120);
    const description = (descriptionField?.value || "").slice(0, 1000);
    const status = STATUSES.includes(statusField?.value) ? statusField.value : "todo";
    if (!title) {
      showTitleError("请输入任务标题。", titleField);
      return;
    }

    const now = new Date().toISOString();
    const existingId = idField?.value || "";
    const existingIndex = cards.findIndex((card) => card.id === existingId);

    if (existingIndex >= 0) {
      const existing = cards[existingIndex];
      cards[existingIndex] = {
        ...existing,
        title,
        description,
        status,
        updatedAt: now,
      };
      persistCards();
      renderBoard();
      closeEditor();
      announce(`已更新任务：${title}`);
      return;
    }

    cards.push({
      id: createId(),
      title,
      description,
      status,
      createdAt: now,
      updatedAt: now,
    });
    persistCards();
    renderBoard();
    closeEditor();
    announce(`已创建任务：${title}`);
  }

  function moveCard(cardId, nextStatus) {
    if (!STATUSES.includes(nextStatus)) return;
    const card = cards.find((item) => item.id === cardId);
    if (!card || card.status === nextStatus) return;
    card.status = nextStatus;
    card.updatedAt = new Date().toISOString();
    persistCards();
    renderBoard();
    announce(`已将“${card.title}”移动到${STATUS_LABELS[nextStatus]}。`);
  }

  function deleteCard(cardId) {
    const card = cards.find((item) => item.id === cardId);
    if (!card) return;
    if (!globalThis.confirm(`确定删除“${card.title}”吗？`)) return;
    cards = cards.filter((item) => item.id !== cardId);
    persistCards();
    renderBoard();
    announce(`已删除任务：${card.title}`);
  }

  function showTitleError(message, field) {
    if (titleError) titleError.textContent = message;
    field?.setAttribute("aria-invalid", "true");
    field?.focus();
  }

  function clearTitleError() {
    if (titleError) titleError.textContent = "";
    titleField?.removeAttribute("aria-invalid");
  }

  function announce(message, urgent = false) {
    if (!announcer) return;
    if (urgent) announcer.setAttribute("aria-live", "assertive");
    else announcer.setAttribute("aria-live", "polite");
    announcer.textContent = "";
    requestAnimationFrame(() => {
      announcer.textContent = message;
    });
  }
})();
