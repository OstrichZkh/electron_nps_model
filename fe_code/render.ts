const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  createNewProject: (title) => ipcRenderer.invoke('createNewProject', title),
  requireProjectInfo: (info) => ipcRenderer.invoke('requireProjectInfo', info),
  deleteProject: (name) => ipcRenderer.invoke('deleteProject', name),
  updateProjectInfo: (payload) => ipcRenderer.invoke('updateProjectInfo', payload),
  uploadFile: (payload) => ipcRenderer.invoke('uploadFile', payload),
  rusleCal: (payload) => ipcRenderer.invoke('rusleCal', payload),
  requireRusle: (payload) => ipcRenderer.invoke('requireRusle', payload),
  requireParas: (payload) => ipcRenderer.invoke('requireParas', payload),
  updateParas: (payload) => ipcRenderer.invoke('updateParas', payload),
  deleteFile: (payload) => ipcRenderer.invoke('deleteFile', payload),
})