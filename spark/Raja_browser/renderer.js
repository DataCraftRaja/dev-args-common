const api = window.orbitBrowser;
const tabsElement = document.querySelector("#tabs");
const address = document.querySelector("#address");
const home = document.querySelector("#home");
const bookmarkButton = document.querySelector("#bookmark");
const savedBookmarksElement = document.querySelector("#saved-bookmarks");
const menu = document.querySelector("#menu");
const toast = document.querySelector("#toast");
let currentState = { activeTabId: null, tabs: [] };
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
    button.addEventListener("click", () => runAction(() => api.navigate(bookmark.url)));
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
    button.addEventListener("click", () => runAction(() => api.selectTab(tab.id)));

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
      runAction(() => api.closeTab(tab.id));
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
  runAction(() => api.navigate(value));
}

document.querySelector("#new-tab").addEventListener("click", () => runAction(() => api.newTab()));
document.querySelector("#menu-new-tab").addEventListener("click", () => {
  menu.classList.remove("open");
  runAction(() => api.newTab());
});
document.querySelector("#back").addEventListener("click", () => runAction(() => api.back()));
document.querySelector("#forward").addEventListener("click", () => runAction(() => api.forward()));
document.querySelector("#reload").addEventListener("click", () => runAction(() => api.reload()));
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
  showToast("Orbit Browser uses Electron and Chromium to load websites in isolated tabs.");
  menu.classList.remove("open");
});
document.querySelector("#menu-quit").addEventListener("click", () => {
  showToast("Close this window to quit Orbit Browser.");
  menu.classList.remove("open");
});

document.addEventListener("keydown", (event) => {
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

api.onState(render);
api.onTabError(({ message }) => showToast(message));
runAction(() => api.getState());
