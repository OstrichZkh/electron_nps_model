const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  createNewProject: (title) => ipcRenderer.invoke('createNewProject', title),
  requireProjectInfo: (info) => ipcRenderer.invoke('requireProjectInfo', info)

})