import axios from 'axios'
import type { RunAgentRequest, RunAgentResponse, RunStatusResponse } from '../types'

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim()
const isProduction = import.meta.env.PROD
const missingProductionApiUrl = isProduction && !configuredApiUrl
const API_BASE_URL = configuredApiUrl || (isProduction ? '' : 'http://localhost:8000')

const missingApiUrlMessage =
  'VITE_API_URL is not configured for production. Set it in Vercel: Project Settings → Environment Variables → VITE_API_URL, then redeploy.'

console.log('🔌 API Configuration:')
console.log(`   Base URL: ${API_BASE_URL}`)
console.log(`   Environment: ${import.meta.env.MODE}`)

if (missingProductionApiUrl) {
  console.error(`❌ ${missingApiUrlMessage}`)
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Network error or backend unreachable
      const helpText = `
        ❌ Network Error: Cannot reach backend API at ${API_BASE_URL}
        
        📋 Troubleshooting:
        1. Verify VITE_API_URL environment variable is set correctly
        2. Check if backend is running: curl ${API_BASE_URL}/health
        3. Ensure AWS EC2 security group allows port 8000
        4. On Vercel: Settings → Environment Variables → Set VITE_API_URL
        
        💻 For local development:
        - Backend should run at http://localhost:8000
        - Frontend should run at http://localhost:5174
      `
      console.error(helpText)
      error.message = `Network Error: Backend unreachable at ${API_BASE_URL}. Check console for details.`
    } else if (error.response?.status === 401 || error.response?.status === 403) {
      error.message = `Authorization Error: ${error.response.data?.detail || 'Check GITHUB_TOKEN'}`
    } else if (error.response?.status === 400) {
      error.message = `Bad Request: ${error.response.data?.detail || 'Invalid input'}`
    } else if (error.response?.status === 503) {
      error.message = `Service Unavailable: ${error.response.data?.detail || 'Backend not ready. Check server configuration.'}`
    }
    return Promise.reject(error)
  }
)

export async function runAgent(payload: RunAgentRequest): Promise<RunAgentResponse> {
  if (missingProductionApiUrl) {
    throw new Error(missingApiUrlMessage)
  }
  const { data } = await api.post<RunAgentResponse>('/run-agent', payload)
  return data
}

export async function getRunStatus(runId: string): Promise<RunStatusResponse> {
  if (missingProductionApiUrl) {
    throw new Error(missingApiUrlMessage)
  }
  const { data } = await api.get<RunStatusResponse>(`/run-status/${runId}`)
  return data
}
