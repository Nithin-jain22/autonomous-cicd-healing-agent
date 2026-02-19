export type RunStatus = 'running' | 'PASSED' | 'FAILED'

export type BugType = 'LINTING' | 'SYNTAX' | 'LOGIC' | 'TYPE_ERROR' | 'IMPORT' | 'INDENTATION'

export type FixStatus = 'FIXED' | 'FAILED'

export interface FixRecord {
  file: string
  bug_type: BugType
  line_number: number
  commit_message: string
  status: FixStatus
  strict_output: string
}

export interface TimelineRecord {
  iteration: number
  status: RunStatus
  timestamp: string
}

export interface ResultsPayload {
  repository: string
  team_name: string
  leader_name: string
  branch_name: string
  total_failures: number
  total_fixes: number
  iterations_used: number
  retry_limit: number
  commits: number
  final_status: RunStatus
  execution_time_seconds: number
  score: number
  score_base: number
  score_time_bonus: number
  score_commit_penalty: number
  fixes: FixRecord[]
  ci_timeline: TimelineRecord[]
}

export interface RunStatusResponse {
  run_id: string
  status: RunStatus
  results: ResultsPayload
  score_breakdown: {
    base: number
    time_bonus: number
    commit_penalty: number
    final: number
  }
  started_at: string
  finished_at: string | null
}

export interface RunAgentRequest {
  repo_url: string
  team_name: string
  leader_name: string
}

export interface RunAgentResponse {
  run_id: string
  status: RunStatus
}
