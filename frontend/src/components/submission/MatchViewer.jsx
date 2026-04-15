import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, FileSearch, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { getSubmissionDetail } from '@/api/assignments'

function similarityColor(score) {
  if (score >= 80) return 'text-red-600 bg-red-50 dark:bg-red-950/30'
  if (score >= 60) return 'text-orange-600 bg-orange-50 dark:bg-orange-950/30'
  return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950/30'
}

function highlightOverlap(original, matched) {
  // Simple word-level highlighting: mark words that appear in both
  const matchedWords = new Set(matched.toLowerCase().split(/\s+/))
  return original.split(/(\s+)/).map((token, i) => {
    if (/^\s+$/.test(token)) return token
    const isMatch = matchedWords.has(token.toLowerCase().replace(/[^\w]/g, ''))
    return isMatch ? (
      <mark key={i} className="bg-destructive/20 text-destructive rounded px-0.5">
        {token}
      </mark>
    ) : (
      <span key={i}>{token}</span>
    )
  })
}

export default function MatchViewer({ submissionId, studentName, onBack }) {
  const { data: matches = [], isLoading, error } = useQuery({
    queryKey: ['submission-detail', submissionId],
    queryFn: async () => {
      const res = await getSubmissionDetail(submissionId)
      return res.data
    },
    enabled: !!submissionId,
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-40 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-3" />
        <p className="text-sm text-destructive font-medium">
          Failed to load submission details.
        </p>
        <Button variant="outline" size="sm" className="mt-3" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to submissions
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-5 mt-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <h3 className="text-sm font-semibold">{studentName}'s Matches</h3>
          <Badge variant="secondary" className="text-xs">
            {matches.length} match{matches.length !== 1 ? 'es' : ''}
          </Badge>
        </div>
      </div>

      {matches.length === 0 ? (
        <div className="rounded-lg border border-dashed py-12 text-center">
          <FileSearch className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-medium">No plagiarism matches found</p>
          <p className="text-xs text-muted-foreground mt-1">
            This submission didn't trigger any similarity flags.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {matches.map((match, idx) => (
            <Card key={idx} className={similarityColor(match.similarity)}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    Match #{idx + 1}
                    <span className="text-xs font-normal text-muted-foreground">
                      vs. {match.source_student}
                    </span>
                  </CardTitle>
                  <Badge
                    variant={match.similarity >= 80 ? 'destructive' : 'secondary'}
                    className="font-mono text-xs"
                  >
                    {match.similarity.toFixed(1)}%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  {/* Original text */}
                  <div className="space-y-1.5">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {studentName}'s Text
                    </p>
                    <div className="rounded-md border bg-background p-3 text-sm leading-relaxed">
                      {highlightOverlap(match.original, match.matched)}
                    </div>
                  </div>

                  {/* Matched text */}
                  <div className="space-y-1.5">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {match.source_student}'s Text
                    </p>
                    <div className="rounded-md border bg-background p-3 text-sm leading-relaxed">
                      {highlightOverlap(match.matched, match.original)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
