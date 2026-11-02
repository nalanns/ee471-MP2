// All data and rules come from the Flask API; this file only renders responses and sends requests.

const API = "/api/items";

const state = {
  availableOnly: false,
  type: "",          // "" | "book" | "dvd"
  editingItem: null, // the item being edited, or null when adding
};

const TYPE_INFO = {
  book: { label: "Book", icon: "#icon-book", metaIcon: "#icon-pages", field: "page_count",
          numberLabel: "Page count", hint: "Enter the total number of pages.", placeholder: "e.g. 180",
          titlePlaceholder: "e.g. The Great Gatsby", authorPlaceholder: "e.g. F. Scott Fitzgerald" },
  dvd:  { label: "DVD", icon: "#icon-disc", metaIcon: "#icon-clock", field: "duration",
          numberLabel: "Duration (min)", hint: "Enter the running time in minutes.", placeholder: "e.g. 148",
          titlePlaceholder: "e.g. Inception", authorPlaceholder: "e.g. Christopher Nolan" },
};

const $ = (id) => document.getElementById(id);

// ---------- API ----------

class ApiError extends Error {}

async function request(method, url, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new ApiError("Could not reach the server.");
  }
  if (response.status === 204) return null; // DELETE: empty body
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.error || `Request failed (${response.status}).`);
  }
  return data;
}

// ---------- Alerts (error and success) ----------

function showAlert(box, message) {
  box.querySelector(".alert-message").textContent = message;
  box.hidden = false;
}

function hideAlert(box) {
  box.hidden = true;
}

document.querySelectorAll(".alert-close").forEach((button) => {
  button.addEventListener("click", () => hideAlert(button.closest(".alert")));
});

// ---------- List ----------

async function loadItems() {
  const params = new URLSearchParams();
  if (state.availableOnly) params.set("available", "true");
  if (state.type) params.set("type", state.type);
  const query = params.toString();
  try {
    const items = await request("GET", query ? `${API}?${query}` : API);
    renderItems(items);
  } catch (error) {
    showAlert($("error"), error.message);
  }
}

function renderItems(items) {
  const filtered = state.availableOnly || state.type;
  const count = items.length;
  const noun = count === 1 ? "item" : "items";
  const verb = count === 1 ? "matches" : "match";
  $("item-count").textContent = filtered ? `${count} ${noun} ${verb} your filters` : `${count} ${noun} in your library`;

  $("list-section").hidden = count === 0;
  $("empty").hidden = count !== 0;

  if (count === 0) {
    $("empty-title").textContent = filtered ? "No matching items" : "No items yet";
    $("empty-text").textContent = filtered
      ? "Nothing matches these filters. Try a different type or turn off “Available only”."
      : "Good stories deserve a place. Add your first book or DVD to start building your library.";
    $("grid").replaceChildren();
    return;
  }

  const typeLabel = { "": "items", book: "books", dvd: "DVDs" }[state.type];
  $("list-title").textContent = state.availableOnly ? `Available ${typeLabel}` : `All ${typeLabel}`;

  // Only meaningful for the full list; a filtered list would give misleading counts.
  $("status-summary").hidden = Boolean(filtered);
  if (!filtered) {
    const availableCount = items.filter((item) => item.is_available).length;
    $("available-count").textContent = `${availableCount} available`;
    $("checked-out-count").textContent = `${count - availableCount} checked out`;
  }
  $("footer-text").textContent = `You’re all caught up. ${count === 1 ? "1 item is" : `All ${count} items are`} shown.`;

  $("grid").replaceChildren(...items.map(renderCard));
}

function renderCard(item) {
  const info = TYPE_INFO[item.type];
  const card = $("card-template").content.firstElementChild.cloneNode(true);

  card.querySelector(".card-icon use").setAttribute("href", info.icon);
  card.querySelector(".type-badge").textContent = info.label;
  card.querySelector(".card-title").textContent = item.title;
  card.querySelector(".card-author").textContent = item.author;
  card.querySelector(".card-meta use").setAttribute("href", info.metaIcon);
  card.querySelector(".card-meta span").textContent =
    item.type === "book" ? `${item.page_count} pages` : `${item.duration} mins`;

  const status = card.querySelector(".status");
  status.textContent = item.is_available ? "Available" : "Checked out";
  status.classList.add(item.is_available ? "status-available" : "status-out");

  const toggle = card.querySelector(".toggle-btn");
  toggle.textContent = item.is_available ? "Checkout" : "Return";
  toggle.classList.add(item.is_available ? "btn-primary" : "btn-secondary");
  toggle.addEventListener("click", () =>
    runAction("POST", `${API}/${item.id}/${item.is_available ? "checkout" : "return"}`));

  card.querySelector(".edit-btn").addEventListener("click", () => openModal(item));
  card.querySelector(".delete-btn").addEventListener("click", () => {
    if (confirm(`Delete “${item.title}”?`)) runAction("DELETE", `${API}/${item.id}`);
  });

  return card;
}

async function runAction(method, url) {
  hideAlert($("error"));
  hideAlert($("success"));
  try {
    const result = await request(method, url);
    if (result?.message) showAlert($("success"), result.message);
  } catch (error) {
    showAlert($("error"), error.message);
  }
  await loadItems();
}

// ---------- Filters ----------

$("available-only").addEventListener("change", (event) => {
  state.availableOnly = event.target.checked;
  loadItems();
});

document.querySelectorAll(".segmented button").forEach((button) => {
  button.addEventListener("click", () => {
    state.type = button.dataset.type;
    document.querySelectorAll(".segmented button").forEach((b) => b.classList.toggle("active", b === button));
    loadItems();
  });
});

// ---------- Modal ----------

function updateTypeFields() {
  const info = TYPE_INFO[$("field-type").value];
  $("modal-eyebrow").textContent = `${info.label} details`;
  $("modal-eyebrow-icon").setAttribute("href", info.icon);
  $("number-label").textContent = info.numberLabel;
  $("number-hint").textContent = info.hint;
  $("field-number").placeholder = info.placeholder;
  $("field-title").placeholder = info.titlePlaceholder;
  $("field-author").placeholder = info.authorPlaceholder;
}

function openModal(item = null) {
  state.editingItem = item;
  hideAlert($("form-error"));
  $("modal-title").textContent = item ? "Edit Item" : "Add Item";
  $("field-title").value = item ? item.title : "";
  $("field-author").value = item ? item.author : "";
  $("field-type").value = item ? item.type : "book";
  $("field-type").disabled = Boolean(item);
  $("field-number").value = item ? item[TYPE_INFO[item.type].field] : "";
  updateTypeFields();
  $("modal").hidden = false;
  $("field-title").focus();
}

function closeModal() {
  $("modal").hidden = true;
  state.editingItem = null;
}

$("field-type").addEventListener("change", updateTypeFields);

document.querySelectorAll('[data-action="add"]').forEach((button) =>
  button.addEventListener("click", () => openModal()));
document.querySelectorAll('[data-action="close"]').forEach((button) =>
  button.addEventListener("click", closeModal));

$("modal").addEventListener("click", (event) => {
  if (event.target === $("modal")) closeModal();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("modal").hidden) closeModal();
});

$("item-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert($("form-error"));

  const type = $("field-type").value;
  const number = $("field-number").value.trim();
  // Send what the user typed; the API decides whether it is valid.
  const body = {
    title: $("field-title").value,
    author: $("field-author").value,
    [TYPE_INFO[type].field]: number === "" ? null : Number(number),
  };

  try {
    if (state.editingItem) {
      await request("PATCH", `${API}/${state.editingItem.id}`, body);
    } else {
      await request("POST", API, { type, ...body });
    }
    closeModal();
    await loadItems();
  } catch (error) {
    showAlert($("form-error"), error.message);
  }
});

loadItems();
