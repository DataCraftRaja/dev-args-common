const api = window.orbitBrowser;
const standalone = !api;
const tabsElement = document.querySelector("#tabs");
const address = document.querySelector("#address");
const home = document.querySelector("#home");
const bookmarkButton = document.querySelector("#bookmark");
const savedBookmarksElement = document.querySelector("#saved-bookmarks");
const menu = document.querySelector("#menu");
const toast = document.querySelector("#toast");
let currentState = standalone
  ? { activeTabId: 1, tabs: [{ id: 1, title: "Orbit Browser", url: "", loading: false }] }
  : { activeTabId: null, tabs: [] };
let savedBookmarks = [];
let toastTimer;

function activeTab() {
  return currentState.tabs.find((tab) => tab.id === currentState.activeTabId);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 5000);
}

function renderBookmarks() {
  savedBookmarksElement.replaceChildren();
  for (const bookmark of savedBookmarks) {
    const button = document.createElement("button");
    button.className = "bookmark-link";
    button.type = "button";
    button.title = bookmark.url;
    button.textContent = bookmark.title;
    button.addEventListener("click", () => navigate(bookmark.url));
    savedBookmarksElement.append(button);
  }
}

function renderTabs() {
  tabsElement.replaceChildren();
  for (const tab of currentState.tabs) {
    const button = document.createElement("button");
    button.className = `tab${tab.id === currentState.activeTabId ? " active" : ""}`;
    button.type = "button";
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", String(tab.id === currentState.activeTabId));
    if (api) button.addEventListener("click", () => runAction(() => api.selectTab(tab.id)));

    const favicon = document.createElement("span");
    favicon.className = tab.loading ? "tab-loading" : "tab-favicon";
    favicon.textContent = tab.loading ? "" : "o";

    const title = document.createElement("span");
    title.className = "tab-title";
    title.textContent = tab.title;

    const close = document.createElement("span");
    close.className = "tab-close";
    close.setAttribute("role", "button");
    close.setAttribute("aria-label", `Close ${tab.title}`);
    close.textContent = "×";
    close.addEventListener("click", (event) => {
      event.stopPropagation();
      if (api) runAction(() => api.closeTab(tab.id));
      else showToast("Close this page using your browser's tab controls.");
    });

    button.append(favicon, title, close);
    tabsElement.append(button);
  }
}

function render(state) {
  currentState = state;
  renderTabs();
  renderBookmarks();

  const tab = activeTab();
  if (!tab) return;
  address.value = tab.url;
  home.style.display = tab.url ? "none" : "flex";
  bookmarkButton.classList.toggle("saved", savedBookmarks.some((item) => item.url === tab.url && tab.url));
  bookmarkButton.textContent = bookmarkButton.classList.contains("saved") ? "★" : "☆";
  document.querySelector("#back").disabled = !tab.canGoBack;
  document.querySelector("#forward").disabled = !tab.canGoForward;
}

async function runAction(action) {
  try {
    const state = await action();
    if (state?.tabs) render(state);
  } catch (error) {
    showToast(error.message || "That action could not be completed.");
  }
}

function navigate(input) {
  const value = input.trim();
  if (!value) return;
  if (api) {
    runAction(() => api.navigate(value));
    return;
  }

  const url = resolveInput(value);
  const opened = window.open(url, "_blank");
  if (!opened) {
    showToast("Your browser blocked the new tab. Allow pop-ups for this page.");
    return;
  }
  opened.opener = null;
  showToast("Opened in a new browser tab.");
}

function resolveInput(input) {
  const text = input.trim();
  if (/^https?:\/\//i.test(text)) return text;
  if (/^(localhost|(?:\d{1,3}\.){3}\d{1,3}|(?:[\w-]+\.)+[a-z]{2,})(:\d+)?([/?#].*)?$/i.test(text)) {
    return `https://${text}`;
  }
  return `https://www.google.com/search?q=${encodeURIComponent(text)}`;
}

function openStandaloneTab() {
  const opened = window.open(window.location.href, "_blank");
  if (!opened) {
    showToast("Your browser blocked the new tab. Allow pop-ups for this page.");
    return;
  }
  opened.opener = null;
}

document.querySelector("#new-tab").addEventListener("click", () => {
  if (api) runAction(() => api.newTab());
  else openStandaloneTab();
});
document.querySelector("#menu-new-tab").addEventListener("click", () => {
  menu.classList.remove("open");
  if (api) runAction(() => api.newTab());
  else openStandaloneTab();
});
document.querySelector("#back").addEventListener("click", () => {
  if (api) runAction(() => api.back());
});
document.querySelector("#forward").addEventListener("click", () => {
  if (api) runAction(() => api.forward());
});
document.querySelector("#reload").addEventListener("click", () => {
  if (api) runAction(() => api.reload());
  else window.location.reload();
});
document.querySelector("#address-form").addEventListener("submit", (event) => {
  event.preventDefault();
  navigate(address.value);
});
document.querySelector("#home-search").addEventListener("submit", (event) => {
  event.preventDefault();
  navigate(document.querySelector("#home-query").value);
});

bookmarkButton.addEventListener("click", () => {
  const tab = activeTab();
  if (!tab?.url) return;
  const existingIndex = savedBookmarks.findIndex((bookmark) => bookmark.url === tab.url);
  if (existingIndex >= 0) savedBookmarks.splice(existingIndex, 1);
  else savedBookmarks.push({ url: tab.url, title: tab.title });
  render(currentState);
});

document.querySelectorAll(".shortcut, .bookmark-link[data-url]").forEach((button) => {
  button.addEventListener("click", () => navigate(button.dataset.url));
});

document.querySelector("#menu-button").addEventListener("click", () => menu.classList.toggle("open"));
document.addEventListener("click", (event) => {
  if (!menu.contains(event.target) && !document.querySelector("#menu-button").contains(event.target)) {
    menu.classList.remove("open");
  }
});
document.querySelector("#menu-toggle-bookmarks").addEventListener("click", () => {
  const bar = document.querySelector("#bookmarks-bar");
  bar.hidden = !bar.hidden;
  menu.classList.remove("open");
});
document.querySelector("#menu-about").addEventListener("click", () => {
  showToast(standalone
    ? "Standalone mode opens websites in separate tabs in your regular browser."
    : "Orbit Browser uses Electron and Chromium to load websites in isolated tabs.");
  menu.classList.remove("open");
});
document.querySelector("#menu-quit").addEventListener("click", () => {
  showToast(standalone
    ? "Close this page using your browser's tab controls."
    : "Close this window to quit Orbit Browser.");
  menu.classList.remove("open");
});

document.addEventListener("keydown", (event) => {
  if (!api) return;
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "t") {
    event.preventDefault();
    runAction(() => api.newTab());
  } else if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "l") {
    event.preventDefault();
    address.focus();
    address.select();
  } else if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "w") {
    event.preventDefault();
    const tab = activeTab();
    if (tab) runAction(() => api.closeTab(tab.id));
  }
});

if (api) {
  api.onState(render);
  api.onTabError(({ message }) => showToast(message));
  runAction(() => api.getState());
} else {
  document.querySelector("#back").disabled = true;
  document.querySelector("#forward").disabled = true;
  document.querySelector("#welcome-message").textContent =
    "Standalone webpage mode: searches and websites open in separate tabs in your regular browser.";
  render(currentState);
}
