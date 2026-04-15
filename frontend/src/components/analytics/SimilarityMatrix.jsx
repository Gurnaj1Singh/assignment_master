import { useQuery } from '@tanstack/react-query'
import { ArrowUpDown } from 'lucide-react'
import { useState } from 'react'
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
import { getSimilarityMatrix } from '@/api/assignments'

function scoreBadge(score) {
  if (score >= 70) return 'destructive'
  if (score >= 40) return 'secondary'
  return 'outline'
}

export default function SimilarityMatrix({ taskId }) {
  const [sortField, setSortField] = useState('avg_similarity')
  const [sortAsc, setSortAsc] = useState(false)

  const { data: matrix = [], isLoading } = useQuery({
    queryKey: ['similarity-matrix', taskId],
    queryFn: async () => {
      const res = await getSimilarityMatrix(taskId)
      return res.data
    },
  })

  function toggleSort(field) {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  const sorted = [...matrix].sort((a, b) => {
    const mul = sortAsc ? 1 : -1
    if (sortField === 'pair') return mul * a.pair.localeCompare(b.pair)
    return mul * (a[sortField] - b[sortField])
  })

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (matrix.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No similarity data available yet.
      </p>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead
              className="cursor-pointer select-none"
              onClick={() => toggleSort('pair')}
            >
              <span className="flex items-center gap-1">
                Student Pair <ArrowUpDown className="h-3 w-3" />
              </span>
            </TableHead>
            <TableHead
              className="cursor-pointer select-none text-right"
              onClick={() => toggleSort('avg_similarity')}
            >
              <span className="flex items-center justify-end gap-1">
                Avg Similarity <ArrowUpDown className="h-3 w-3" />
              </span>
            </TableHead>
            <TableHead
              className="cursor-pointer select-none text-right"
              onClick={() => toggleSort('shared_sentences')}
            >
              <span className="flex items-center justify-end gap-1">
                Shared Sentences <ArrowUpDown className="h-3 w-3" />
              </span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((row) => (
            <TableRow key={row.pair}>
              <TableCell className="font-medium">{row.pair}</TableCell>
              <TableCell className="text-right">
                <Badge variant={scoreBadge(row.avg_similarity)} className="font-mono text-xs">
                  {row.avg_similarity.toFixed(1)}%
                </Badge>
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {row.shared_sentences}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
