import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { PlusCircle, BookOpen, Users, Hash, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { getMyClassrooms, joinClassroom } from '@/api/classrooms'

export default function StudentDashboard() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [joinOpen, setJoinOpen] = useState(false)
  const [code, setCode] = useState('')

  const { data: classrooms = [], isLoading } = useQuery({
    queryKey: ['classrooms', 'my'],
    queryFn: async () => {
      const res = await getMyClassrooms()
      return res.data
    },
  })

  const joinMutation = useMutation({
    mutationFn: () => joinClassroom(code.trim()),
    onSuccess: () => {
      toast.success('Joined classroom!')
      qc.invalidateQueries({ queryKey: ['classrooms', 'my'] })
      setJoinOpen(false)
      setCode('')
    },
    onError: (err) =>
      toast.error(err.response?.data?.detail ?? 'Could not join classroom'),
  })

  function openJoin() {
    setCode('')
    setJoinOpen(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Classrooms</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {classrooms.length} classroom{classrooms.length !== 1 ? 's' : ''} joined
          </p>
        </div>
        <Button onClick={openJoin}>
          <PlusCircle className="h-4 w-4 mr-2" />
          Join Classroom
        </Button>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))}
        </div>
      ) : classrooms.length === 0 ? (
        <div className="rounded-xl border border-dashed py-20 text-center">
          <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm font-medium">No classrooms yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Join a classroom using the code your professor gave you.
          </p>
          <Button className="mt-4" variant="outline" onClick={openJoin}>
            Join Classroom
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {classrooms.map((c) => (
            <Card
              key={c.classroom_id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/student/classroom/${c.classroom_id}`)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-base leading-snug">{c.class_name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Hash className="h-3.5 w-3.5" />
                  <span className="font-mono">{c.class_code}</span>
                </div>
                {c.member_count != null && (
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Users className="h-3.5 w-3.5" />
                    {c.member_count} student{c.member_count !== 1 ? 's' : ''}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Join Dialog */}
      <Dialog open={joinOpen} onOpenChange={setJoinOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Join a Classroom</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="class_code">Classroom Code</Label>
              <Input
                id="class_code"
                placeholder="e.g. ABC123"
                value={code}
                autoFocus
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                onKeyDown={(e) =>
                  e.key === 'Enter' && code.trim() && joinMutation.mutate()
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setJoinOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!code.trim() || joinMutation.isPending}
              onClick={() => joinMutation.mutate()}
            >
              {joinMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Join
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
