import type { ResultsPayload } from '../types'

interface FixesTableProps {
  results: ResultsPayload | null
}

const rowColor: Record<string, string> = {
  FIXED: 'text-green-300',
  FAILED: 'text-red-300',
}

export function FixesTable({ results }: FixesTableProps) {
  const fixes = results?.fixes ?? []
  
  // PHASE 3: Validation - Log strict_output to verify data arrives
  if (fixes.length > 0) {
    console.log('✅ FixesTable renders with strict_output:', fixes.map(f => ({ 
      file: f.file, 
      strict_output: f.strict_output 
    })))
  }

  return (
    <section className="rounded-card border border-white/5 bg-bgsurface p-6 shadow-card">
      <h2 className="text-xl font-semibold text-text-primary">Fixes Applied</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-[#0F172A]">
            <tr className="text-left text-sm font-semibold uppercase tracking-wide text-text-secondary">
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Bug Type</th>
              <th className="px-4 py-3">Line Number</th>
              <th className="px-4 py-3">Commit Message</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Strict Output</th>
            </tr>
          </thead>
          <tbody>
            {fixes.length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-sm text-text-muted" colSpan={6}>
                  No fixes yet.
                </td>
              </tr>
            ) : (
              fixes.map((fix, index) => (
                <tr
                  key={`${fix.file}-${fix.line_number}-${index}`}
                  className="border-b border-white/5 even:bg-[#0F1625] hover:bg-[#1A2235]"
                >
                  <td className="px-4 py-3 text-sm text-text-primary">{fix.file}</td>
                  <td className="px-4 py-3 text-sm text-text-primary">{fix.bug_type}</td>
                  <td className="px-4 py-3 text-sm text-text-primary">{fix.line_number}</td>
                  <td className="px-4 py-3 text-sm text-text-primary">{fix.commit_message}</td>
                  <td className={`px-4 py-3 text-sm font-medium ${rowColor[fix.status]}`}>{fix.status}</td>
                  <td className="px-4 py-3 font-mono text-xs text-text-primary break-words max-w-xs" title={fix.strict_output}>
                    {fix.strict_output}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
