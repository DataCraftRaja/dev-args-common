const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("orbitBrowser", {
  getState: () => ipcRenderer.invoke("browser:get-state"),
  newTab: () => ipcRenderer.invoke("browser:new-tab"),
  selectTab: (id) => ipcRenderer.invoke("browser:select-tab", id),
  closeTab: (id) => ipcRenderer.invoke("browser:close-tab", id),
  navigate: (input) => ipcRenderer.invoke("browser:navigate", input),
  back: () => ipcRenderer.invoke("browser:back"),
  forward: () => ipcRenderer.invoke("browser:forward"),
  reload: () => ipcRenderer.invoke("browser:reload"),
  onState: (callback) => {
    const listener = (_event, state) => callback(state);
    ipcRenderer.on("browser:state", listener);
    return () => ipcRenderer.removeListener("browser:state", listener);
  },
  onTabError: (callback) => {
    const listener = (_event, error) => callback(error);
    ipcRenderer.on("browser:tab-error", listener);
    return () => ipcRenderer.removeListener("browser:tab-error", listener);
  }
});
