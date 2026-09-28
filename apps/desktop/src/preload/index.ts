import { contextBridge, ipcRenderer } from 'electron'
import {
  DESKTOP_QUIT_CHANNEL,
  TEACHER_GET_AUTH_CHANNEL,
  TEACHER_RETRY_CHANNEL,
  TEACHER_STATUS_CHANNEL
} from '../shared/ipcChannels'

// Lifecycle/host surface only — no domain traffic over IPC (Story 1.1 scaffold;
// teacher lifecycle + auth bridge added in Story 1.6/AUTH_BRIDGE). Vue calls the
// teacher HTTP API directly with `base_url` + `bearer` obtained here.
contextBridge.exposeInMainWorld('desktop', {
  scaffold: '1.1',
  quit: (): Promise<void> => ipcRenderer.invoke(DESKTOP_QUIT_CHANNEL)
})

export interface TeacherStatus {
  state: 'starting' | 'running' | 'stopped' | 'error'
  base_url: string
  bearer: string | null
  message?: string
}

contextBridge.exposeInMainWorld('teacher', {
  getAuth: (): Promise<TeacherStatus> => ipcRenderer.invoke(TEACHER_GET_AUTH_CHANNEL),
  retry: (): Promise<TeacherStatus> => ipcRenderer.invoke(TEACHER_RETRY_CHANNEL),
  onStatusChange: (callback: (status: TeacherStatus) => void): (() => void) => {
    const listener = (_event: Electron.IpcRendererEvent, status: TeacherStatus): void =>
      callback(status)
    ipcRenderer.on(TEACHER_STATUS_CHANNEL, listener)
    return () => ipcRenderer.removeListener(TEACHER_STATUS_CHANNEL, listener)
  }
})
