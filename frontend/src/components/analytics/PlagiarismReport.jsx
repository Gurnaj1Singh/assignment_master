import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getReport } from '@/api/assignments'
import { format, parseISO } from 'date-fns'

function barColor(score) {
  if (score >= 70) return '#ef4444'  // red-500
  if (score >= 40) return '#f97316'  // orange-500
  return '#22c55e'                   // green-500
}

function scoreBadgeVariant(score) {
  if (score >= 70) return 'destructive'
  if (score >= 40) return 'secondary'
  return 'outline'
}

export default function PlagiarismReport({ taskId }) {
  const { data: report = [], isLoading } = useQuery({
    queryKey: ['report', taskId],
    queryFn: async () => {
      const res = await getReport(taskId)
      return res.data
    },
  })

  // Build histogram buckets
  const distribution = useMemo(() => {
    const buckets = [
      { range: '0-20%', min: 0, max: 20, count: 0 },
      { range: '20-40%', min: 20, max: 40, count: 0 },
      { range: '40-60%', min: 40, max: 60, count: 0 },
      { range: '60-80%', min: 60, max: 80, count: 0 },
      { range: '80-100%', min: 80, max: 100, count: 0 },
    ]
    report.forEach((r) => {
      const s = r.score ?? 0
      const bucket = buckets.find((b) => s >= b.min && (s < b.max || (b.max === 100 && s <= 100)))
      if (bucket) bucket.count++
    })
    return buckets
  }, [report])

  // Summary stats
  const stats = useMemo(() => {
    if (report.length === 0) return null
    const scores = report.map((r) => r.score ?? 0)
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length
    const max = Math.max(...scores)
    const flagged = scores.filter((s) => s >= 60).length
    return { avg, max, flagged, total: scores.length }
  }, [report])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-48 w-full rounded-lg" />
      </div>
    )
  }

  if (report.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No submissions to report on yet.
      </p>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Average Score</p>
              <p className="text-2xl font-bold mt-0.5">{stats.avg.toFixed(1)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Highest Score</p>
              <p className="text-2xl font-bold mt-0.5 text-destructive">
                {stats.max.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Flagged (&ge;60%)</p>
              <p className="text-2xl font-bold mt-0.5">
                {stats.flagged}
                <span className="text-sm font-normal text-muted-foreground ml-1">
                  / {stats.total}
                </span>
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Score distribution chart */}
      <div>
        <h3 className="text-sm font-medium mb-3">Score Distribution</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={distribution} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis dataKey="range" tick={{ fontSize: 11 }} className="fill-muted-foreground" />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} className="fill-muted-foreground" />
            <RechartsTooltip
              contentStyle={{
                backgroundColor: 'var(--popover)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                color: 'var(--popover-foreground)',
                fontSize: '12px',
              }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {distribution.map((entry) => (
                <Cell key={entry.range} fill={barColor(entry.min + 10)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detail table */}
      <div>
        <h3 className="text-sm font-medium mb-3">All Submissions</h3>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                <TableHead className="text-right">Similarity Score</TableHead>
                <TableHead className="text-right">Submitted</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {report.map((r, i) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">{r.student}</TableCell>
                  <TableCell className="text-right">
                    <Badge
                      variant={scoreBadgeVariant(r.score)}
                      className="font-mono text-xs"
                    >
                      {(r.score ?? 0).toFixed(1)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-xs text-muted-foreground">
                    {r.time
                      ? format(parseISO(r.time), 'dd MMM, HH:mm')
                      : '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}
