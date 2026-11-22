const path = require("node:path");
const { app, BrowserWindow, WebContentsView, ipcMain, shell, session } = require("electron");

const CHROME_HEIGHT = 124;
const tabs = new Map();
let tabOrder = [];
let activeTabId = null;
let attachedTabId = null;
let nextTabId = 1;
let mainWindow = null;

function isHttpUrl(value) {
  try {
    const url = new URL(value);
    return (url.protocol === "http:" || url.protocol === "https:") &&
      !url.username && !url.password;
  } catch {
    return false;
  }
}

function normalizeInput(input) {
  const text = String(input).trim();
  if (!text) return null;

  if (/^https?:\/\//i.test(text)) {
    return isHttpUrl(text) ? new URL(text).href : null;
  }

  if (/^(localhost|(?:\d{1,3}\.){3}\d{1,3}|(?:[\w-]+\.)+[a-z]{2,})(:\d+)?([/?#].*)?$/i.test(text)) {
    const url = `https://${text}`;
    return isHttpUrl(url) ? new URL(url).href : null;
  }

  return `https://www.google.com/search?q=${encodeURIComponent(text)}`;
}

function getSnapshot() {
  return {
    activeTabId,
    tabs: tabOrder
      .map((id) => tabs.get(id))
      .filter(Boolean)
      .map((tab) => ({
        id: tab.id,
        title: tab.title,
        url: tab.url,
        loading: tab.loading,
        canGoBack: Boolean(tab.view?.webContents.navigationHistory.canGoBack()),
        canGoForward: Boolean(tab.view?.webContents.navigationHistory.canGoForward())
      }))
  };
}

function sendState() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send("browser:state", getSnapshot());
}

function updateViewBounds() {
  if (!mainWindow || !attachedTabId) return;
  const tab = tabs.get(attachedTabId);
  if (!tab?.view) return;

  const [width, height] = mainWindow.getContentSize();
  tab.view.setBounds({
    x: 0,
    y: CHROME_HEIGHT,
    width,
    height: Math.max(0, height - CHROME_HEIGHT)
  });
}

function attachActiveView() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  if (attachedTabId === activeTabId) {
    updateViewBounds();
    return;
  }

  if (attachedTabId) {
    const previous = tabs.get(attachedTabId);
    if (previous?.view) mainWindow.contentView.removeChildView(previous.view);
  }
  attachedTabId = null;

  const active = tabs.get(activeTabId);
  if (active?.view) {
    mainWindow.contentView.addChildView(active.view);
    attachedTabId = active.id;
    updateViewBounds();
  }
}

function reportTabError(tab, message) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send("browser:tab-error", {
    tabId: tab.id,
    message
  });
}

function createWebContentsView(tab) {
  const view = new WebContentsView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      partition: "persist:orbit-browser"
    }
  });
  tab.view = view;

  view.webContents.setWindowOpenHandler(({ url }) => {
    if (isHttpUrl(url)) createTab(url);
    return { action: "deny" };
  });

  view.webContents.on("will-navigate", (event, url) => {
    if (isHttpUrl(url)) return;
    event.preventDefault();
    if (url.startsWith("mailto:")) {
      shell.openExternal(url).catch((error) => {
        reportTabError(tab, `Could not open mail link: ${error.message}`);
      });
    }
  });
  view.webContents.on("will-redirect", (event, url) => {
    if (!isHttpUrl(url)) event.preventDefault();
  });

  const updateTab = () => {
    if (tab.view) {
      tab.url = tab.view.webContents.getURL();
      tab.loading = tab.view.webContents.isLoading();
      if (tab.url) tab.title = tab.view.webContents.getTitle() || new URL(tab.url).hostname;
    }
    sendState();
  };

  view.webContents.on("page-title-updated", (_event, title) => {
    tab.title = title || tab.title;
    sendState();
  });
  view.webContents.on("did-navigate", updateTab);
  view.webContents.on("did-navigate-in-page", updateTab);
  view.webContents.on("did-start-loading", () => {
    tab.loading = true;
    sendState();
  });
  view.webContents.on("did-stop-loading", () => {
    tab.loading = false;
    updateTab();
  });
  view.webContents.on("did-fail-load", (_event, errorCode, description, validatedURL, isMainFrame) => {
    if (!isMainFrame || errorCode === -3) return;
    tab.loading = false;
    reportTabError(tab, `Could not load ${validatedURL}: ${description}`);
    sendState();
  });

  return view;
}

async function loadTab(tab, url) {
  if (!tab.view) createWebContentsView(tab);
  tab.url = url;
  tab.title = new URL(url).hostname;
  tab.loading = true;
  attachActiveView();
  sendState();

  try {
    await tab.view.webContents.loadURL(url);
  } catch (error) {
    tab.loading = false;
    reportTabError(tab, `Could not load ${url}: ${error.message}`);
    sendState();
  }
}

function createTab(initialUrl = null) {
  const id = nextTabId++;
  const tab = {
    id,
    title: initialUrl ? new URL(initialUrl).hostname : "New tab",
    url: initialUrl || "",
    loading: false,
    view: null
  };
  tabs.set(id, tab);
  tabOrder.push(id);
  activeTabId = id;
  attachActiveView();
  sendState();
  if (initialUrl) void loadTab(tab, initialUrl);
  return tab;
}

function closeTab(id) {
  const tab = tabs.get(id);
  if (!tab) return;
  const closingIndex = tabOrder.indexOf(id);

  if (attachedTabId === id) {
    mainWindow.contentView.removeChildView(tab.view);
    attachedTabId = null;
  }
  tab.view?.webContents.close();
  tabs.delete(id);
  tabOrder = tabOrder.filter((tabId) => tabId !== id);

  if (tabOrder.length === 0) {
    createTab();
    return;
  }
  if (activeTabId === id) activeTabId = tabOrder[Math.min(closingIndex, tabOrder.length - 1)];
  attachActiveView();
  sendState();
}

function requireUi(event) {
  if (!mainWindow || event.sender !== mainWindow.webContents) {
    throw new Error("This action is only available to the browser interface.");
  }
}

function registerIpc() {
  ipcMain.handle("browser:get-state", (event) => {
    requireUi(event);
    return getSnapshot();
  });
  ipcMain.handle("browser:new-tab", (event) => {
    requireUi(event);
    createTab();
    return getSnapshot();
  });
  ipcMain.handle("browser:select-tab", (event, id) => {
    requireUi(event);
    if (!tabs.has(id)) throw new Error("That tab no longer exists.");
    activeTabId = id;
    attachActiveView();
    sendState();
    return getSnapshot();
  });
  ipcMain.handle("browser:close-tab", (event, id) => {
    requireUi(event);
    closeTab(id);
    return getSnapshot();
  });
  ipcMain.handle("browser:navigate", async (event, input) => {
    requireUi(event);
    const url = normalizeInput(input);
    if (!url) throw new Error("Enter a valid website address or search term.");
    const tab = tabs.get(activeTabId);
    if (!tab) throw new Error("No active tab is available.");
    await loadTab(tab, url);
    return getSnapshot();
  });
  ipcMain.handle("browser:back", (event) => {
    requireUi(event);
    const history = tabs.get(activeTabId)?.view?.webContents.navigationHistory;
    if (history?.canGoBack()) history.goBack();
  });
  ipcMain.handle("browser:forward", (event) => {
    requireUi(event);
    const history = tabs.get(activeTabId)?.view?.webContents.navigationHistory;
    if (history?.canGoForward()) history.goForward();
  });
  ipcMain.handle("browser:reload", (event) => {
    requireUi(event);
    tabs.get(activeTabId)?.view?.webContents.reload();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 760,
    minHeight: 540,
    backgroundColor: "#202124",
    title: "Orbit Browser",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (url !== `file://${path.join(__dirname, "index.html")}`) event.preventDefault();
  });
  mainWindow.on("resize", updateViewBounds);
  mainWindow.on("closed", () => {
    for (const tab of tabs.values()) tab.view?.webContents.close();
    tabs.clear();
    tabOrder = [];
    activeTabId = null;
    attachedTabId = null;
    mainWindow = null;
  });
  mainWindow.webContents.on("did-finish-load", () => {
    if (tabOrder.length === 0) createTab();
    attachActiveView();
    sendState();
  });

  void mainWindow.loadFile(path.join(__dirname, "index.html"));
}

app.whenReady().then(() => {
  session.fromPartition("persist:orbit-browser")
    .setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
  registerIpc();
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
