import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { getHeatmap } from '@/api/assignments'

function colorForSimilarity(value) {
  if (value >= 80) return 'bg-red-600 text-white'
  if (value >= 60) return 'bg-red-400 text-white'
  if (value >= 40) return 'bg-orange-400 text-white'
  if (value >= 20) return 'bg-yellow-300 text-foreground'
  return 'bg-green-200 text-foreground'
}

export default function CollusionHeatmap({ taskId }) {
  const { data: heatmapData = [], isLoading } = useQuery({
    queryKey: ['heatmap', taskId],
    queryFn: async () => {
      const res = await getHeatmap(taskId)
      return res.data
    },
  })

  // Build a unique list of students and a lookup map
  const { students, matrix } = useMemo(() => {
    const nameSet = new Set()
    heatmapData.forEach((e) => {
      nameSet.add(e.student_a)
      nameSet.add(e.student_b)
    })
    const students = [...nameSet].sort()

    const lookup = {}
    heatmapData.forEach((e) => {
      const key = `${e.student_a}|${e.student_b}`
      const keyR = `${e.student_b}|${e.student_a}`
      lookup[key] = e
      lookup[keyR] = e
    })

    return { students, matrix: lookup }
  }, [heatmapData])

  if (isLoading) {
    return <Skeleton className="h-64 w-full rounded-lg" />
  }

  if (students.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        Not enough submissions to generate a heatmap.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-2" />
            {students.map((s) => (
              <th
                key={s}
                className="p-2 font-medium text-muted-foreground max-w-[80px] truncate"
                title={s}
              >
                {s.split(' ')[0]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {students.map((rowStudent) => (
            <tr key={rowStudent}>
              <td
                className="p-2 font-medium text-muted-foreground text-right max-w-[100px] truncate"
                title={rowStudent}
              >
                {rowStudent.split(' ')[0]}
              </td>
              {students.map((colStudent) => {
                if (rowStudent === colStudent) {
                  return (
                    <td key={colStudent} className="p-1">
                      <div className="h-8 w-8 rounded bg-muted flex items-center justify-center text-muted-foreground">
                        —
                      </div>
                    </td>
                  )
                }

                const entry = matrix[`${rowStudent}|${colStudent}`]
                const sim = entry ? entry.similarity : 0

                return (
                  <td key={colStudent} className="p-1">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div
                          className={`h-8 w-8 rounded flex items-center justify-center font-mono font-medium cursor-default transition-transform hover:scale-110 ${colorForSimilarity(sim)}`}
                        >
                          {Math.round(sim)}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs">
                        <p className="font-semibold">
                          {rowStudent} & {colStudent}
                        </p>
                        <p>Similarity: {sim.toFixed(1)}%</p>
                        {entry && (
                          <p>
                            Shared sentences: {entry.shared_sentences}
                          </p>
                        )}
                      </TooltipContent>
                    </Tooltip>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-4 text-xs text-muted-foreground">
        <span>Low</span>
        <div className="flex gap-0.5">
          <div className="h-3 w-6 rounded-sm bg-green-200" />
          <div className="h-3 w-6 rounded-sm bg-yellow-300" />
          <div className="h-3 w-6 rounded-sm bg-orange-400" />
          <div className="h-3 w-6 rounded-sm bg-red-400" />
          <div className="h-3 w-6 rounded-sm bg-red-600" />
        </div>
        <span>High</span>
      </div>
    </div>
  )
}
