import axios from 'axios'
import type { RunAgentRequest, RunAgentResponse, RunStatusResponse } from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 30000,
})

export async function runAgent(payload: RunAgentRequest): Promise<RunAgentResponse> {
  const { data } = await api.post<RunAgentResponse>('/run-agent', payload)
  return data
}

export async function getRunStatus(runId: string): Promise<RunStatusResponse> {
  const { data } = await api.get<RunStatusResponse>(`/run-status/${runId}`)
  return data
}
