import { contextBridge } from 'electron'

// Lifecycle/host surface only — no domain traffic over IPC (Story 1.1 scaffold).
contextBridge.exposeInMainWorld('desktop', {
  scaffold: '1.1'
})
