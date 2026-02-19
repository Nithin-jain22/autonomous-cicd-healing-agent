interface LoadingOverlayProps {
  message?: string
}

export function LoadingOverlay({ message = 'Running autonomous healing agent...' }: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bgmain/80 backdrop-blur-sm">
      <div className="rounded-2xl border border-white/5 bg-bgsurface p-6 shadow-card">
        <div className="flex items-center gap-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-text-secondary">{message}</p>
        </div>
      </div>
    </div>
  )
}
