import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ResultsPayload } from '../types'

interface ScorePanelProps {
  results: ResultsPayload | null
}

export function ScorePanel({ results }: ScorePanelProps) {
  const base = results?.score_base ?? 100
  const bonus = results?.score_time_bonus ?? 0
  const penalty = results?.score_commit_penalty ?? 0
  const finalScore = results?.score ?? 0

  const chartData = [
    { name: 'Base', value: base },
    { name: 'Bonus', value: bonus },
    { name: 'Penalty', value: penalty },
    { name: 'Final', value: finalScore },
  ]

  const progress = Math.max(0, Math.min(100, finalScore))

  return (
    <section className="rounded-card border border-white/5 bg-bgsurface p-6 shadow-card hover:bg-bghover transition duration-300">
      <h2 className="text-xl font-semibold text-text-primary">Score Breakdown</h2>

      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-sm text-text-secondary">Final Score</p>
          <p className="text-4xl font-bold text-accent">{finalScore}</p>
        </div>
        <div className="text-xs text-text-muted">
          <p>Base: {base}</p>
          <p>Bonus: +{bonus}</p>
          <p>Penalty: -{penalty}</p>
        </div>
      </div>

      <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-primary transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>

      <div className="mt-5 h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
            <Tooltip />
            <Bar dataKey="value" fill="#7C5CFF" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
