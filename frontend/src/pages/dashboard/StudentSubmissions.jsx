import { useQuery } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { FileText, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getMySubmissions } from '@/api/assignments'

function fmtDate(iso) {
  if (!iso) return '—'
  try { return format(parseISO(iso), 'dd MMM yyyy, HH:mm') } catch { return iso }
}

function fmtScore(score) {
  if (score == null) return '—'
  return `${score.toFixed(1)}%`
}

function StatusBadge({ status }) {
  const map = {
    completed:     { label: 'Completed',     variant: 'default',     icon: CheckCircle2 },
    processing:    { label: 'Processing',    variant: 'secondary',   icon: Loader2 },
    failed:        { label: 'Failed',        variant: 'destructive', icon: XCircle },
    not_submitted: { label: 'Not Submitted', variant: 'outline',     icon: Clock },
  }
  const { label, variant, icon: Icon } = map[status] ?? map.not_submitted
  return (
    <Badge variant={variant} className="text-xs gap-1">
      <Icon className={`h-3 w-3 ${status === 'processing' ? 'animate-spin' : ''}`} />
      {label}
    </Badge>
  )
}

export default function StudentSubmissions() {
  const { data: submissions = [], isLoading } = useQuery({
    queryKey: ['my-submissions'],
    queryFn: async () => {
      const res = await getMySubmissions()
      return res.data
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Submissions</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          All your assignment submissions across classrooms.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : submissions.length === 0 ? (
        <div className="rounded-xl border border-dashed py-20 text-center">
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm font-medium">No submissions yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Your submitted assignments will appear here.
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Assignment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Submitted At</TableHead>
                <TableHead className="text-right">Similarity Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {submissions.map((s) => (
                <TableRow key={s.submission_id ?? s.id}>
                  <TableCell className="font-medium">
                    {s.task_title ?? s.title ?? `Task ${s.task_id}`}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={s.status} />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {fmtDate(s.submitted_at)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {fmtScore(s.plagiarism_score)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
