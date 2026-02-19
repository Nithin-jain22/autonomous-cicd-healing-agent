import { useState } from 'react'

interface InputFormProps {
  onSubmit: (repoUrl: string, teamName: string, leaderName: string) => Promise<void>
  loading: boolean
}

export function InputForm({ onSubmit, loading }: InputFormProps) {
  const [repoUrl, setRepoUrl] = useState('')
  const [teamName, setTeamName] = useState('')
  const [leaderName, setLeaderName] = useState('')

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await onSubmit(repoUrl, teamName, leaderName)
  }

  return (
    <section className="rounded-card border border-white/5 bg-bgsurface p-6 shadow-card">
      <h2 className="text-xl font-semibold text-text-primary">Run Agent</h2>
      <form className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-2 text-sm text-text-secondary">
          GitHub Repository URL
          <input
            aria-label="GitHub Repository URL"
            value={repoUrl}
            onChange={(event) => setRepoUrl(event.target.value)}
            className="h-11 rounded-xl border border-white/10 bg-bgelevated px-3 text-text-primary outline-none focus:ring-2 focus:ring-primary"
            placeholder="https://github.com/org/repo"
            required
          />
        </label>

        <label className="flex flex-col gap-2 text-sm text-text-secondary">
          Team Name
          <input
            aria-label="Team Name"
            value={teamName}
            onChange={(event) => setTeamName(event.target.value)}
            className="h-11 rounded-xl border border-white/10 bg-bgelevated px-3 text-text-primary outline-none focus:ring-2 focus:ring-primary"
            placeholder="RIFT ORGANISERS"
            required
          />
        </label>

        <label className="flex flex-col gap-2 text-sm text-text-secondary">
          Team Leader Name
          <input
            aria-label="Team Leader Name"
            value={leaderName}
            onChange={(event) => setLeaderName(event.target.value)}
            className="h-11 rounded-xl border border-white/10 bg-bgelevated px-3 text-text-primary outline-none focus:ring-2 focus:ring-primary"
            placeholder="Saiyam Kumar"
            required
          />
        </label>

        <div className="md:col-span-3">
          <button
            type="submit"
            disabled={loading}
            aria-label="Run Agent"
            className="h-11 min-w-44 rounded-xl bg-primary px-6 text-sm font-semibold text-white transition duration-300 ease-out hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/30 active:scale-95 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? 'Running...' : 'Run Agent'}
          </button>
        </div>
      </form>
    </section>
  )
}
