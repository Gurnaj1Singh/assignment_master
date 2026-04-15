import { useState, useEffect } from 'react'
import { parseISO } from 'date-fns'
import { Clock, AlertTriangle } from 'lucide-react'

/**
 * Live countdown to a due date. Updates every second.
 * Shows "Deadline passed" once the date is in the past.
 */
export default function DeadlineCountdown({ dueDate }) {
  const [timeLeft, setTimeLeft] = useState(null)

  useEffect(() => {
    if (!dueDate) return

    function update() {
      const now = Date.now()
      const due = (typeof dueDate === 'string' ? parseISO(dueDate) : dueDate).getTime()
      setTimeLeft(Math.floor((due - now) / 1000))
    }

    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [dueDate])

  if (timeLeft === null) return null

  if (timeLeft <= 0) {
    return (
      <span className="inline-flex items-center gap-1.5 text-sm font-medium text-destructive">
        <AlertTriangle className="h-4 w-4" />
        Deadline passed
      </span>
    )
  }

  const days    = Math.floor(timeLeft / 86400)
  const hours   = Math.floor((timeLeft % 86400) / 3600)
  const minutes = Math.floor((timeLeft % 3600) / 60)
  const seconds = timeLeft % 60
  const isUrgent = timeLeft < 86400 // < 24 hours

  const parts = []
  if (days > 0)  parts.push(`${days}d`)
  if (hours > 0) parts.push(`${hours}h`)
  parts.push(`${String(minutes).padStart(2, '0')}m`)
  parts.push(`${String(seconds).padStart(2, '0')}s`)

  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium tabular-nums ${
      isUrgent ? 'text-orange-500' : 'text-muted-foreground'
    }`}>
      <Clock className="h-4 w-4 shrink-0" />
      {parts.join(' ')} remaining
    </span>
  )
}
