import type { ResultsPayload, RunStatus } from '../types'

interface RunSummaryCardProps {
  status: RunStatus | 'idle'
  results: ResultsPayload | null
  startedAt: string | null
  finishedAt: string | null
}

function statusClass(status: RunStatus | 'idle') {
  if (status === 'PASSED') return 'bg-green-500/20 text-green-400 border border-green-400/30'
  if (status === 'FAILED') return 'bg-red-500/20 text-red-400 border border-red-400/30'
  return 'bg-yellow-500/20 text-yellow-400 border border-yellow-400/30'
}

export function RunSummaryCard({ status, results, startedAt, finishedAt }: RunSummaryCardProps) {
  return (
    <section className="rounded-card border border-white/5 bg-bgsurface p-6 shadow-card hover:bg-bghover transition duration-300">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-text-primary">Run Summary</h2>
        {status !== 'idle' && (
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass(status)}`}>{status}</span>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
        <div>
          <dt className="text-text-muted">Repository URL</dt>
          <dd className="truncate text-text-primary">{results?.repository ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Team Name</dt>
          <dd className="text-text-primary">{results?.team_name ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Team Leader Name</dt>
          <dd className="text-text-primary">{results?.leader_name ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Generated Branch</dt>
          <dd className="text-text-primary">{results?.branch_name ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Total Failures</dt>
          <dd className="text-text-primary">{results?.total_failures ?? 0}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Total Fixes Applied</dt>
          <dd className="text-text-primary">{results?.total_fixes ?? 0}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Total Time</dt>
          <dd className="text-text-primary">
            {results ? `${results.execution_time_seconds}s` : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-text-muted">Start / End</dt>
          <dd className="text-text-primary text-xs">
            {startedAt ? new Date(startedAt).toLocaleString() : '—'}
            {'  '}→{'  '}
            {finishedAt ? new Date(finishedAt).toLocaleString() : '—'}
          </dd>
        </div>
      </dl>
    </section>
  )
}
