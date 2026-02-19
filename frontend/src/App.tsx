import { useRunStore } from './store/runStore'
import { InputForm } from './components/InputForm'
import { RunSummaryCard } from './components/RunSummaryCard'
import { ScorePanel } from './components/ScorePanel'
import { FixesTable } from './components/FixesTable'
import { CICDTimeline } from './components/CICDTimeline'
import { LoadingOverlay } from './components/LoadingOverlay'

export default function App() {
  const { status, loading, error, results, startedAt, finishedAt, startRun } = useRunStore()

  return (
    <div className="min-h-screen bg-bgmain text-text-primary">
      {loading && <LoadingOverlay message="Agent is running and monitoring CI/CD..." />}

      <header className="border-b border-white/5 bg-bgsurface/60">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <h1 className="text-4xl font-bold">Autonomous CI/CD Healing Agent</h1>
          <p className="mt-2 text-sm text-text-secondary">AI-driven failure detection, fixing, and CI validation loop</p>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-12 gap-6 px-6 py-12">
        <div className="col-span-12">
          <InputForm onSubmit={startRun} loading={loading} />
        </div>

        {error ? (
          <div className="col-span-12 rounded-card border border-danger/30 bg-danger/10 p-4 text-sm text-danger">{error}</div>
        ) : null}

        <div className="col-span-12 lg:col-span-6">
          <RunSummaryCard status={status} results={results} startedAt={startedAt} finishedAt={finishedAt} />
        </div>
        <div className="col-span-12 lg:col-span-6">
          <ScorePanel results={results} />
        </div>

        <div className="col-span-12">
          <FixesTable results={results} />
        </div>

        <div className="col-span-12">
          <CICDTimeline results={results} />
        </div>
      </main>

      <footer className="border-t border-white/5 py-6">
        <div className="mx-auto max-w-7xl px-6 text-xs text-text-muted">Autonomous CI/CD Healing Agent • Dark-first dashboard</div>
      </footer>
    </div>
  )
}
