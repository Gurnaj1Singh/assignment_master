import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod/v4'
import { toast } from 'sonner'
import {
  ArrowLeft,
  Plus,
  Loader2,
  Users,
  ClipboardList,
  Hash,
  FileText,
  CheckCircle2,
  Clock,
  ChevronRight,
} from 'lucide-react'
import { format, parseISO } from 'date-fns'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

import {
  getClassroomMembers,
  getClassroomTasks,
  createTask,
} from '@/api/classrooms'
import useAuthStore from '@/stores/authStore'

// ── Zod schema ─────────────────────────────────────────────────────────────
const taskSchema = z.object({
  title: z.string().min(2, 'At least 2 characters').max(300, 'Max 300 characters'),
  description: z.string().optional(),
  due_date: z.string().optional(), // datetime-local string, converted before send
})

// ── Helpers ─────────────────────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), 'dd MMM yyyy, HH:mm')
  } catch {
    return iso
  }
}

function TaskBadge({ isPublished }) {
  return isPublished ? (
    <Badge variant="default" className="text-xs">
      <CheckCircle2 className="h-3 w-3 mr-1" />
      Published
    </Badge>
  ) : (
    <Badge variant="secondary" className="text-xs">
      <Clock className="h-3 w-3 mr-1" />
      Draft
    </Badge>
  )
}

// ── Create Task Dialog ───────────────────────────────────────────────────────
function CreateTaskDialog({ classroomId, open, onOpenChange }) {
  const qc = useQueryClient()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ resolver: zodResolver(taskSchema) })

  const mutation = useMutation({
    mutationFn: (payload) => createTask(classroomId, payload),
    onSuccess: (res) => {
      toast.success(`Task "${res.data.title}" created — code: ${res.data.task_code}`)
      qc.invalidateQueries({ queryKey: ['classroom-tasks', classroomId] })
      onOpenChange(false)
      reset()
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail ?? 'Failed to create task')
    },
  })

  function onSubmit({ title, description, due_date }) {
    const payload = {
      title,
      description: description || undefined,
      // Convert datetime-local value to ISO string with local timezone offset
      due_date: due_date ? new Date(due_date).toISOString() : undefined,
    }
    mutation.mutate(payload)
  }

  function handleClose(val) {
    onOpenChange(val)
    if (!val) reset()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Create Assignment Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
          {/* Title */}
          <div className="space-y-1.5">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              placeholder="e.g. NLP Research Paper"
              {...register('title')}
            />
            {errors.title && (
              <p className="text-xs text-destructive">{errors.title.message}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label htmlFor="description">Instructions (optional)</Label>
            <Textarea
              id="description"
              placeholder="Rubric, guidelines, or additional context for students…"
              rows={3}
              {...register('description')}
            />
          </div>

          {/* Due date */}
          <div className="space-y-1.5">
            <Label htmlFor="due_date">Due Date (optional)</Label>
            <Input
              id="due_date"
              type="datetime-local"
              {...register('due_date')}
            />
            <p className="text-xs text-muted-foreground">
              Time is interpreted in your local timezone. Leave blank for no deadline.
            </p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Create Task
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── Member Tab ───────────────────────────────────────────────────────────────
function MembersTab({ classroomId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['classroom-members', classroomId],
    queryFn: async () => {
      const res = await getClassroomMembers(classroomId)
      return res.data
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <p className="text-sm text-destructive mt-4">
        {error.response?.data?.detail ?? 'Failed to load members.'}
      </p>
    )
  }

  const { total_students, students = [] } = data ?? {}

  return (
    <div className="space-y-4 mt-4">
      <p className="text-sm text-muted-foreground">
        {total_students ?? students.length} enrolled student
        {students.length !== 1 ? 's' : ''}
      </p>
      {students.length === 0 ? (
        <div className="rounded-lg border border-dashed py-12 text-center text-sm text-muted-foreground">
          No students have joined yet. Share the classroom code to invite them.
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Joined</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {students.map((s) => (
                <TableRow key={s.student_id}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell className="text-muted-foreground">{s.email}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">
                    {fmtDate(s.joined_at)}
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

// ── Tasks Tab ────────────────────────────────────────────────────────────────
function TasksTab({ classroomId, isProfessor }) {
  const navigate = useNavigate()
  const [createOpen, setCreateOpen] = useState(false)

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['classroom-tasks', classroomId],
    queryFn: async () => {
      const res = await getClassroomTasks(classroomId)
      return res.data
    },
  })

  const basePath = isProfessor ? '/professor' : '/student'

  if (isLoading) {
    return (
      <div className="space-y-3 mt-4">
        {[...Array(2)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4 mt-4">
      {isProfessor && (
        <div className="flex justify-end">
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Task
          </Button>
        </div>
      )}

      {tasks.length === 0 ? (
        <div className="rounded-lg border border-dashed py-12 text-center text-sm text-muted-foreground">
          {isProfessor
            ? 'No tasks yet. Create your first assignment task.'
            : 'No published tasks yet.'}
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((t) => (
            <Card
              key={t.task_id}
              className="cursor-pointer hover:shadow-sm transition-shadow group"
              onClick={() => navigate(`${basePath}/task/${t.task_id}`)}
            >
              <CardContent className="flex items-start justify-between gap-4 py-4">
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm truncate">{t.title}</span>
                    <TaskBadge isPublished={t.is_published} />
                    {t.has_pdf && (
                      <Badge variant="outline" className="text-xs">
                        <FileText className="h-3 w-3 mr-1" />
                        PDF
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="font-mono">
                      <Hash className="h-3 w-3 inline mr-0.5" />
                      {t.assignment_code}
                    </span>
                    {t.due_date && (
                      <span>Due: {fmtDate(t.due_date)}</span>
                    )}
                    {isProfessor && (
                      <span>{t.submission_count} submission{t.submission_count !== 1 ? 's' : ''}</span>
                    )}
                  </div>
                  {t.description && (
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {t.description}
                    </p>
                  )}
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {isProfessor && (
        <CreateTaskDialog
          classroomId={classroomId}
          open={createOpen}
          onOpenChange={setCreateOpen}
        />
      )}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function ClassroomDetailPage() {
  const { classroomId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const isProfessor = user?.role === 'professor'

  // Fetch member data for the header (professor only)
  const { data: memberData } = useQuery({
    queryKey: ['classroom-members', classroomId],
    queryFn: async () => {
      const res = await getClassroomMembers(classroomId)
      return res.data
    },
    enabled: isProfessor,
  })

  // Fetch tasks for basic header info when not professor
  const { data: tasks = [] } = useQuery({
    queryKey: ['classroom-tasks', classroomId],
    queryFn: async () => {
      const res = await getClassroomTasks(classroomId)
      return res.data
    },
  })

  const backPath = isProfessor ? '/professor' : '/student'
  const classroomName = memberData?.class_name
    ?? (tasks.length > 0 ? undefined : undefined)
    ?? 'Classroom'
  const classCode = memberData?.class_code

  return (
    <div className="space-y-6">
      {/* Back + Header */}
      <div>
        <Button
          variant="ghost"
          size="sm"
          className="mb-3 -ml-2 text-muted-foreground"
          onClick={() => navigate(backPath)}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{classroomName}</h1>
            {classCode && (
              <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
                <Hash className="h-3.5 w-3.5" />
                Join code:&nbsp;<span className="font-mono font-medium">{classCode}</span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="tasks">
        <TabsList>
          <TabsTrigger value="tasks" className="gap-1.5">
            <ClipboardList className="h-4 w-4" />
            Tasks
          </TabsTrigger>
          {isProfessor && (
            <TabsTrigger value="members" className="gap-1.5">
              <Users className="h-4 w-4" />
              Members
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="tasks">
          <TasksTab classroomId={classroomId} isProfessor={isProfessor} />
        </TabsContent>

        {isProfessor && (
          <TabsContent value="members">
            <MembersTab classroomId={classroomId} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}
