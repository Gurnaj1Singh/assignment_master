import { useQuery } from '@tanstack/react-query'
import { Users, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getCollusionGroups } from '@/api/assignments'

export default function CollusionGroups({ taskId }) {
  const { data, isLoading } = useQuery({
    queryKey: ['collusion-groups', taskId],
    queryFn: async () => {
      const res = await getCollusionGroups(taskId)
      return res.data
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(2)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (!data || data.total_groups === 0) {
    return (
      <div className="rounded-lg border border-dashed py-12 text-center">
        <Users className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm font-medium">No collusion groups detected</p>
        <p className="text-xs text-muted-foreground mt-1">
          Students with high mutual similarity will appear here.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-destructive" />
        <p className="text-sm font-medium">
          {data.total_groups} collusion group{data.total_groups !== 1 ? 's' : ''} detected
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {data.groups.map((group, idx) => (
          <Card key={idx} className="border-destructive/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Users className="h-4 w-4 text-destructive" />
                Group {idx + 1}
                <Badge variant="destructive" className="text-xs ml-auto">
                  {group.length} students
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {group.map((student) => (
                  <Badge key={student} variant="secondary" className="text-xs">
                    {student}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
