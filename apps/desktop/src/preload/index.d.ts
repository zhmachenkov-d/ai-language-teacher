export {}

export interface TeacherStatus {
  state: 'starting' | 'running' | 'stopped' | 'error'
  base_url: string
  bearer: string | null
  message?: string
}

declare global {
  interface Window {
    desktop: {
      scaffold: string
      quit: () => Promise<void>
    }
    teacher: {
      getAuth: () => Promise<TeacherStatus>
      retry: () => Promise<TeacherStatus>
      onStatusChange: (callback: (status: TeacherStatus) => void) => () => void
    }
  }
}
