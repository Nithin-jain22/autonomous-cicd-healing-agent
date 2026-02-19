import { create } from 'zustand'
import { getRunStatus, runAgent } from '../services/api'
import type { ResultsPayload, RunStatus } from '../types'

interface RunStore {
  runId: string
  status: RunStatus | 'idle'
  loading: boolean
  error: string
  results: ResultsPayload | null
  startedAt: string | null
  finishedAt: string | null
  pollTimer: number | null
  startRun: (repoUrl: string, teamName: string, leaderName: string) => Promise<void>
  pollStatus: () => Promise<void>
  stopPolling: () => void
  reset: () => void
}

export const useRunStore = create<RunStore>((set, get) => ({
  runId: '',
  status: 'idle',
  loading: false,
  error: '',
  results: null,
  startedAt: null,
  finishedAt: null,
  pollTimer: null,
  startRun: async (repoUrl, teamName, leaderName) => {
    get().stopPolling()
    set({ loading: true, error: '', status: 'running', results: null, startedAt: null, finishedAt: null })
    try {
      const response = await runAgent({
        repo_url: repoUrl,
        team_name: teamName,
        leader_name: leaderName,
      })
      set({ runId: response.run_id, status: response.status })
      await get().pollStatus()
      const timer = window.setInterval(() => {
        void get().pollStatus()
      }, 5000)
      set({ pollTimer: timer })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start run'
      set({ error: message, loading: false, status: 'FAILED' })
    }
  },
  pollStatus: async () => {
    const { runId } = get()
    if (!runId) return

    try {
      const response = await getRunStatus(runId)
      set({
        status: response.status,
        results: response.results,
        startedAt: response.started_at,
        finishedAt: response.finished_at,
        loading: response.status === 'running',
      })

      if (response.status !== 'running') {
        get().stopPolling()
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch run status'
      set({ error: message, loading: false })
      get().stopPolling()
    }
  },
  stopPolling: () => {
    const timer = get().pollTimer
    if (timer !== null) {
      window.clearInterval(timer)
      set({ pollTimer: null })
    }
  },
  reset: () => {
    get().stopPolling()
    set({
      runId: '',
      status: 'idle',
      loading: false,
      error: '',
      results: null,
      startedAt: null,
      finishedAt: null,
    })
  },
}))
