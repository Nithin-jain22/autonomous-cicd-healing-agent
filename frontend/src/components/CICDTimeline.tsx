import type { ResultsPayload } from '../types'

interface CICDTimelineProps {
  results: ResultsPayload | null
}

function badgeClass(status: string) {
  if (status === 'PASSED') return 'bg-green-500/20 text-green-400 border border-green-400/30'
  if (status === 'FAILED') return 'bg-red-500/20 text-red-400 border border-red-400/30'
  return 'bg-yellow-500/20 text-yellow-400 border border-yellow-400/30'
}

export function CICDTimeline({ results }: CICDTimelineProps) {
  const timeline = results?.ci_timeline ?? []
  const retryLimit = results?.retry_limit ?? 5

  return (
    <section className="rounded-card border border-white/5 bg-bgsurface p-6 shadow-card">
      <h2 className="text-xl font-semibold text-text-primary">CI/CD Timeline</h2>

      <div className="relative mt-4 space-y-4 pl-2">
        <div className="absolute bottom-0 left-4 top-0 w-px bg-white/10" />
        {timeline.length === 0 ? (
          <p className="ml-10 text-sm text-text-muted">No CI iterations yet.</p>
        ) : (
          timeline.map((item) => (
            <article
              key={`${item.iteration}-${item.timestamp}`}
              className="ml-10 rounded-xl border border-white/5 bg-bgsurface p-4"
            >
              <div className="absolute left-[11px] mt-1 h-3 w-3 rounded-full bg-primary shadow-lg shadow-primary/40" />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm text-text-primary">Iteration {item.iteration}</p>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${badgeClass(item.status)}`}>
                  {item.status}
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">{new Date(item.timestamp).toLocaleString()}</p>
              <p className="mt-1 text-xs text-text-secondary">Usage: {item.iteration}/{retryLimit}</p>
            </article>
          ))
        )}
      </div>
    </section>
  )
}
