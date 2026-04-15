import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod/v4'
import { toast } from 'sonner'
import { Plus, BookOpen, Users, Hash, ArrowRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'

import { getMyClassrooms, createClassroom } from '@/api/classrooms'

const schema = z.object({
  class_name: z.string().min(2, 'At least 2 characters').max(200, 'Max 200 characters'),
})

function ClassroomCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-24 mt-1" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-32" />
      </CardContent>
    </Card>
  )
}

function EmptyState({ onOpenCreate }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-20 text-center">
      <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold">No classrooms yet</h3>
      <p className="text-sm text-muted-foreground mt-1 mb-6">
        Create your first classroom to get started.
      </p>
      <Button onClick={onOpenCreate}>
        <Plus className="h-4 w-4 mr-2" />
        Create Classroom
      </Button>
    </div>
  )
}

export default function ProfessorDashboard() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)

  const { data: classrooms = [], isLoading } = useQuery({
    queryKey: ['classrooms', 'my'],
    queryFn: async () => {
      const res = await getMyClassrooms()
      return res.data
    },
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ resolver: zodResolver(schema) })

  const mutation = useMutation({
    mutationFn: (data) => createClassroom(data),
    onSuccess: (res) => {
      toast.success(
        `"${res.data.class_name}" created — join code: ${res.data.class_code}`
      )
      qc.invalidateQueries({ queryKey: ['classrooms', 'my'] })
      setOpen(false)
      reset()
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail ?? 'Failed to create classroom')
    },
  })

  function onSubmit(data) {
    mutation.mutate(data)
  }

  function handleClose(val) {
    setOpen(val)
    if (!val) reset()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Classrooms</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isLoading
              ? 'Loading…'
              : `${classrooms.length} classroom${classrooms.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <Dialog open={open} onOpenChange={handleClose}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Classroom
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Create Classroom</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label htmlFor="class_name">Classroom Name</Label>
                <Input
                  id="class_name"
                  placeholder="e.g. Robotics & AI — Batch 2026"
                  {...register('class_name')}
                />
                {errors.class_name && (
                  <p className="text-xs text-destructive">{errors.class_name.message}</p>
                )}
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleClose(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  Create
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <ClassroomCardSkeleton key={i} />
          ))}
        </div>
      ) : classrooms.length === 0 ? (
        <EmptyState onOpenCreate={() => setOpen(true)} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {classrooms.map((c) => (
            <Card
              key={c.class_id}
              className="cursor-pointer hover:shadow-md transition-shadow group"
              onClick={() => navigate(`/professor/classroom/${c.class_id}`)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-base leading-snug">{c.class_name}</CardTitle>
                <CardDescription className="flex items-center gap-1 font-mono text-xs">
                  <Hash className="h-3 w-3" />
                  {c.class_code}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Users className="h-4 w-4" />
                  {c.student_count ?? 0} student{c.student_count !== 1 ? 's' : ''}
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
