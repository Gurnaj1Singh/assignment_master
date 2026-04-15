import { WifiOff, RotateCcw, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function QueryError({ error, onRetry }) {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  // Rate limit detection
  if (status === 429) {
    const retryAfter = error?.response?.headers?.['retry-after']
    return (
      <div className="rounded-lg border border-orange-300 bg-orange-50 dark:bg-orange-950/20 p-6 text-center">
        <ShieldAlert className="h-8 w-8 text-orange-500 mx-auto mb-3" />
        <p className="text-sm font-medium text-orange-700 dark:text-orange-400">
          Too many requests
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {detail ?? 'You've hit the rate limit.'}{' '}
          {retryAfter
            ? `Please wait ${retryAfter} seconds.`
            : 'Please wait a moment before trying again.'}
        </p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </div>
    )
  }

  // Network error (no response)
  if (!error?.response) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center">
        <WifiOff className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm font-medium">Network error</p>
        <p className="text-xs text-muted-foreground mt-1">
          Could not connect to the server. Check your internet connection.
        </p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </div>
    )
  }

  // Generic error
  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
      <p className="text-sm font-medium text-destructive">
        {detail ?? 'Something went wrong'}
      </p>
      {status && (
        <p className="text-xs text-muted-foreground mt-1">
          Error {status}
        </p>
      )}
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      )}
    </div>
  )
}
