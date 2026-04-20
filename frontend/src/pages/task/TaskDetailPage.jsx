import { useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  ArrowLeft,
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  BookOpen,
  Sparkles,
  Users,
  Hash,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react'
import { format, parseISO } from 'date-fns'

import DeadlineCountdown from '@/components/shared/DeadlineCountdown'

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

import client from '@/api/client'
import {
  getTaskDetail,
  publishTask,
  uploadTaskPdf,
  getSubmissionStatus,
  getMySubmissions,
  getSubmissionDetail,
} from '@/api/assignments'
import {
  uploadReference,
  listReferences,
  deleteReference,
} from '@/api/references'
import {
  generateQuestions,
  listQuestions,
  selectQuestions,
  distributeQuestions,
  getMyQuestions,
} from '@/api/questions'
import useAuthStore from '@/stores/authStore'
import CollusionHeatmap from '@/components/analytics/CollusionHeatmap'
import SimilarityMatrix from '@/components/analytics/SimilarityMatrix'
import CollusionGroups from '@/components/analytics/CollusionGroups'
import PlagiarismReport from '@/components/analytics/PlagiarismReport'
import MatchViewer from '@/components/submission/MatchViewer'

// ── Helpers ──────────────────────────────────────────────────────────────────
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
    completed:      { label: 'Completed',      variant: 'default',     icon: CheckCircle2 },
    processing:     { label: 'Processing',     variant: 'secondary',   icon: Loader2 },
    failed:         { label: 'Failed',         variant: 'destructive', icon: XCircle },
    not_submitted:  { label: 'Not Submitted',  variant: 'outline',     icon: Clock },
  }
  const { label, variant, icon: Icon } = map[status] ?? map.not_submitted
  return (
    <Badge variant={variant} className="text-xs gap-1">
      <Icon className={`h-3 w-3 ${status === 'processing' ? 'animate-spin' : ''}`} />
      {label}
    </Badge>
  )
}

// ── Publish Toggle ───────────────────────────────────────────────────────────
function PublishToggle({ taskId, isPublished }) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (val) => publishTask(taskId, val),
    onSuccess: (_, val) => {
      toast.success(val ? 'Task published — students can now see it.' : 'Task unpublished.')
      qc.invalidateQueries({ queryKey: ['task', taskId] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail ?? 'Failed to update publish status')
    },
  })

  return (
    <Button
      variant={isPublished ? 'destructive' : 'default'}
      size="sm"
      disabled={mutation.isPending}
      onClick={() => mutation.mutate(!isPublished)}
    >
      {mutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
      {isPublished ? 'Unpublish' : 'Publish'}
    </Button>
  )
}

// ── PDF Upload Card ──────────────────────────────────────────────────────────
function PdfUploadCard({ label, existingFile, onUpload, uploading }) {
  const inputRef = useRef(null)

  function handleChange(e) {
    const file = e.target.files?.[0]
    if (file) onUpload(file)
    // Reset so same file can be re-uploaded if needed
    e.target.value = ''
  }

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-muted-foreground">
            {existingFile ? 'Uploaded — click to replace' : 'No file uploaded yet'}
          </p>
        </div>
        {existingFile && (
          <Badge variant="secondary" className="text-xs gap-1">
            <FileText className="h-3 w-3" />
            PDF
          </Badge>
        )}
      </div>
      <Button
        variant="outline"
        size="sm"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
      >
        {uploading ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Upload className="h-4 w-4 mr-2" />
        )}
        {existingFile ? 'Replace PDF' : 'Upload PDF'}
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleChange}
      />
    </div>
  )
}

// ── Reference Corpus Section ─────────────────────────────────────────────────
function ReferenceCorpus({ taskId }) {
  const qc = useQueryClient()
  const inputRef = useRef(null)
  const [uploading, setUploading] = useState(false)

  const { data: references = [] } = useQuery({
    queryKey: ['references', taskId],
    queryFn: async () => {
      const res = await listReferences(taskId)
      return res.data
    },
  })

  async function handleUpload(file) {
    setUploading(true)
    try {
      await uploadReference(taskId, file)
      toast.success(`Reference "${file.name}" uploaded.`)
      qc.invalidateQueries({ queryKey: ['references', taskId] })
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteReference(id),
    onSuccess: () => {
      toast.success('Reference removed.')
      qc.invalidateQueries({ queryKey: ['references', taskId] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail ?? 'Delete failed')
    },
  })

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Reference Corpus</p>
          <p className="text-xs text-muted-foreground">
            Upload source PDFs for plagiarism comparison and question generation.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Upload className="h-4 w-4 mr-2" />
          )}
          Add PDF
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handleUpload(f)
            e.target.value = ''
          }}
        />
      </div>

      {references.length > 0 && (
        <div className="space-y-1.5 pt-1">
          {references.map((r) => (
            <div
              key={r.reference_id ?? r.id}
              className="flex items-center justify-between text-xs bg-muted/50 rounded px-3 py-2"
            >
              <span className="flex items-center gap-1.5 truncate">
                <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="truncate">{r.original_filename ?? r.file_path}</span>
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-destructive hover:text-destructive"
                onClick={() => deleteMutation.mutate(r.reference_id ?? r.id)}
                disabled={deleteMutation.isPending}
              >
                <XCircle className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Overview Tab ─────────────────────────────────────────────────────────────
function OverviewTab({ task, taskId }) {
  const qc = useQueryClient()
  const [uploading, setUploading] = useState(false)

  async function handleTaskPdfUpload(file) {
    setUploading(true)
    try {
      await uploadTaskPdf(taskId, file)
      toast.success('Question paper uploaded.')
      qc.invalidateQueries({ queryKey: ['task', taskId] })
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6 mt-4">
      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Submissions</p>
            <p className="text-2xl font-bold mt-0.5">{task.submission_count ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Avg. Similarity</p>
            <p className="text-2xl font-bold mt-0.5">{fmtScore(task.average_score)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Due Date</p>
            <p className="text-sm font-semibold mt-0.5">{fmtDate(task.due_date)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {task.description && (
        <div>
          <h3 className="text-sm font-medium mb-1">Instructions</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {task.description}
          </p>
        </div>
      )}

      <Separator />

      {/* File uploads */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Files</h3>
        <PdfUploadCard
          label="Question Paper PDF"
          existingFile={task.has_pdf}
          onUpload={handleTaskPdfUpload}
          uploading={uploading}
        />
        <ReferenceCorpus taskId={taskId} />
      </div>
    </div>
  )
}

// ── Submissions Tab ──────────────────────────────────────────────────────────
function SubmissionsTab({ taskId }) {
  const [selectedSubmission, setSelectedSubmission] = useState(null)

  const { data: submissions = [], isLoading } = useQuery({
    queryKey: ['submission-status', taskId],
    queryFn: async () => {
      const res = await getSubmissionStatus(taskId)
      return res.data
    },
  })

  // Show detail view for a specific submission
  if (selectedSubmission) {
    return (
      <MatchViewer
        submissionId={selectedSubmission.submission_id}
        studentName={selectedSubmission.student_name}
        onBack={() => setSelectedSubmission(null)}
      />
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  const submitted = submissions.filter((s) => s.status !== 'not_submitted').length

  return (
    <div className="space-y-4 mt-4">
      <p className="text-sm text-muted-foreground">
        {submitted} / {submissions.length} submitted
      </p>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Student</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Submitted At</TableHead>
              <TableHead className="text-right">Similarity Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {submissions.map((s) => (
              <TableRow
                key={s.student_id}
                className={
                  s.submission_id && s.status === 'completed'
                    ? 'cursor-pointer hover:bg-muted/50'
                    : ''
                }
                onClick={() => {
                  if (s.submission_id && s.status === 'completed') {
                    setSelectedSubmission(s)
                  }
                }}
              >
                <TableCell className="font-medium">{s.student_name}</TableCell>
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
    </div>
  )
}

// ── Questions Tab ─────────────────────────────────────────────────────────────
function QuestionsTab({ taskId }) {
  const qc = useQueryClient()
  const [generating, setGenerating] = useState(false)
  const [selected, setSelected] = useState(new Set())
  const [distributeOpen, setDistributeOpen] = useState(false)
  const [numPerStudent, setNumPerStudent] = useState(5)
  const [llmProvider, setLlmProvider] = useState('ollama')

  const { data: questions = [], isLoading: loadingQ } = useQuery({
    queryKey: ['questions', taskId],
    queryFn: async () => {
      const res = await listQuestions(taskId)
      // Seed selected from is_selected flag
      const initialSelected = new Set(
        res.data.filter((q) => q.is_selected).map((q) => q.question_id)
      )
      setSelected(initialSelected)
      return res.data
    },
  })

  async function handleGenerate() {
    setGenerating(true)
    try {
      const res = await generateQuestions(taskId, llmProvider)
      toast.success(`${res.data.length} questions generated.`)
      const initialSelected = new Set(
        res.data.filter((q) => q.is_selected).map((q) => q.question_id)
      )
      setSelected(initialSelected)
      qc.setQueryData(['questions', taskId], res.data)
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  const saveMutation = useMutation({
    mutationFn: () => selectQuestions(taskId, Array.from(selected)),
    onSuccess: (res) => {
      toast.success(res.data?.message ?? 'Selection saved.')
      qc.invalidateQueries({ queryKey: ['questions', taskId] })
    },
    onError: (err) => toast.error(err.response?.data?.detail ?? 'Failed to save'),
  })

  const distributeMutation = useMutation({
    mutationFn: () => distributeQuestions(taskId, numPerStudent),
    onSuccess: (res) => {
      toast.success(
        res.data?.message ?? `Questions distributed (${numPerStudent} per student).`
      )
      setDistributeOpen(false)
    },
    onError: (err) => toast.error(err.response?.data?.detail ?? 'Distribution failed'),
  })

  function toggleQuestion(id) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === questions.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(questions.map((q) => q.question_id)))
    }
  }

  const difficultyColor = {
    easy:   'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard:   'bg-red-100 text-red-700',
  }

  return (
    <div className="space-y-4 mt-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <Select value={llmProvider} onValueChange={setLlmProvider}>
          <SelectTrigger size="sm" className="w-[130px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ollama">Ollama (Local)</SelectItem>
            <SelectItem value="openai">OpenAI</SelectItem>
          </SelectContent>
        </Select>

        <Button
          onClick={handleGenerate}
          disabled={generating}
          variant="outline"
          size="sm"
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Questions
            </>
          )}
        </Button>

        {questions.length > 0 && (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={toggleAll}
            >
              {selected.size === questions.length ? 'Deselect All' : 'Select All'}
            </Button>
            <Button
              size="sm"
              disabled={saveMutation.isPending}
              onClick={() => saveMutation.mutate()}
            >
              {saveMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Save Selection ({selected.size})
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setDistributeOpen(true)}
              disabled={selected.size === 0}
            >
              <Users className="h-4 w-4 mr-2" />
              Distribute
            </Button>
          </>
        )}
      </div>

      {/* Question pool */}
      {loadingQ ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
        </div>
      ) : questions.length === 0 ? (
        <div className="rounded-lg border border-dashed py-16 text-center">
          <Sparkles className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-medium">No questions yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Upload a reference corpus PDF first, then click Generate Questions.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {questions.map((q, idx) => {
            const isSelected = selected.has(q.question_id)
            return (
              <div
                key={q.question_id}
                onClick={() => toggleQuestion(q.question_id)}
                className={`flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                  isSelected
                    ? 'border-primary bg-primary/5'
                    : 'hover:bg-muted/50'
                }`}
              >
                {/* Checkbox */}
                <div
                  className={`mt-0.5 h-4 w-4 shrink-0 rounded border-2 flex items-center justify-center ${
                    isSelected ? 'border-primary bg-primary' : 'border-muted-foreground'
                  }`}
                >
                  {isSelected && (
                    <svg className="h-2.5 w-2.5 text-primary-foreground" viewBox="0 0 10 10">
                      <path d="M1.5 5L4 7.5L8.5 2.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
                    </svg>
                  )}
                </div>
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-snug">{idx + 1}. {q.question_text}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {q.difficulty && (
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${difficultyColor[q.difficulty] ?? 'bg-muted text-muted-foreground'}`}>
                        {q.difficulty}
                      </span>
                    )}
                    {q.bloom_level && (
                      <span className="text-xs text-muted-foreground capitalize">
                        {q.bloom_level}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Distribute Dialog */}
      <Dialog open={distributeOpen} onOpenChange={setDistributeOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Distribute Questions</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <p className="text-sm text-muted-foreground">
              Randomly assign questions from your selected pool ({selected.size} selected)
              to each student in the classroom.
            </p>
            <div className="space-y-1.5">
              <Label htmlFor="num_per_student">Questions per student</Label>
              <Input
                id="num_per_student"
                type="number"
                min={1}
                max={selected.size}
                value={numPerStudent}
                onChange={(e) => setNumPerStudent(Number(e.target.value))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDistributeOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => distributeMutation.mutate()}
              disabled={distributeMutation.isPending || numPerStudent < 1}
            >
              {distributeMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Distribute
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ── Analytics Tab ────────────────────────────────────────────────────────────
function AnalyticsTab({ taskId }) {
  return (
    <div className="space-y-8 mt-4">
      {/* Plagiarism Report */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Plagiarism Report
        </h3>
        <PlagiarismReport taskId={taskId} />
      </section>

      <Separator />

      {/* Collusion Heatmap */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Collusion Heatmap
        </h3>
        <CollusionHeatmap taskId={taskId} />
      </section>

      <Separator />

      {/* Similarity Matrix */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Similarity Matrix
        </h3>
        <SimilarityMatrix taskId={taskId} />
      </section>

      <Separator />

      {/* Collusion Groups */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Collusion Groups
        </h3>
        <CollusionGroups taskId={taskId} />
      </section>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function TaskDetailPage() {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const isProfessor = user?.role === 'professor'

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const res = await getTaskDetail(taskId)
      return res.data
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    )
  }

  if (error || !task) {
    return (
      <div className="text-center py-20">
        <p className="text-destructive font-medium">Task not found.</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(isProfessor ? '/professor' : '/student')}
        >
          Go to Dashboard
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 text-muted-foreground"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back
      </Button>

      {/* Title + Meta + Actions */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">{task.title}</h1>
          <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
            <span className="font-mono flex items-center gap-1">
              <Hash className="h-3.5 w-3.5" />
              {task.assignment_code}
            </span>
            <Badge variant={task.is_published ? 'default' : 'secondary'} className="text-xs">
              {task.is_published ? (
                <><CheckCircle2 className="h-3 w-3 mr-1" />Published</>
              ) : (
                <><Clock className="h-3 w-3 mr-1" />Draft</>
              )}
            </Badge>
          </div>
        </div>
        {isProfessor && (
          <PublishToggle taskId={taskId} isPublished={task.is_published} />
        )}
      </div>

      {/* Tabs */}
      {isProfessor ? (
        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="submissions">
              Submissions
              {task.submission_count > 0 && (
                <span className="ml-1.5 rounded-full bg-primary/20 px-1.5 py-0.5 text-xs font-medium">
                  {task.submission_count}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="questions">Questions</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab task={task} taskId={taskId} />
          </TabsContent>
          <TabsContent value="submissions">
            <SubmissionsTab taskId={taskId} />
          </TabsContent>
          <TabsContent value="questions">
            <QuestionsTab taskId={taskId} />
          </TabsContent>
          <TabsContent value="analytics">
            <AnalyticsTab taskId={taskId} />
          </TabsContent>
        </Tabs>
      ) : (
        // Student view — Session 3
        <StudentTaskView task={task} taskId={taskId} />
      )}
    </div>
  )
}

// ── Student Task View ─────────────────────────────────────────────────────────
function StudentTaskView({ task, taskId }) {
  const qc = useQueryClient()
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  // All of the student's submissions — find the one for this task
  const { data: mySubmissions = [] } = useQuery({
    queryKey: ['my-submissions'],
    queryFn: async () => {
      const res = await getMySubmissions()
      return res.data
    },
  })

  const mySubmission = mySubmissions.find(
    (s) => String(s.task_id) === String(taskId)
  )

  // Full plagiarism detail once processing is complete
  const { data: submissionDetail } = useQuery({
    queryKey: ['submission-detail', mySubmission?.submission_id],
    queryFn: async () => {
      const res = await getSubmissionDetail(mySubmission.submission_id)
      return res.data
    },
    enabled: !!(mySubmission?.submission_id && mySubmission?.status === 'completed'),
    // Poll while processing
    refetchInterval: mySubmission?.status === 'processing' ? 5000 : false,
  })

  // Assigned questions for this student
  const { data: myQuestions = [] } = useQuery({
    queryKey: ['my-questions', taskId],
    queryFn: async () => {
      const res = await getMyQuestions(taskId)
      return res.data
    },
    retry: false,
  })

  // Drag-and-drop handlers
  function handleDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    setDragging(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file?.type === 'application/pdf') {
      setSelectedFile(file)
    } else {
      toast.error('Only PDF files are accepted.')
    }
  }

  async function handleSubmit() {
    if (!selectedFile || submitting) return
    setSubmitting(true)
    setUploadProgress(0)
    const form = new FormData()
    form.append('file', selectedFile)
    try {
      await client.post(`/assignments/submit/${taskId}`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) setUploadProgress(Math.round((e.loaded * 100) / e.total))
        },
      })
      toast.success('Assignment submitted — plagiarism check will run shortly.')
      setSelectedFile(null)
      qc.invalidateQueries({ queryKey: ['my-submissions'] })
      qc.invalidateQueries({ queryKey: ['task', taskId] })
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  const isPastDue = task.due_date && new Date(task.due_date) < new Date()
  const hasSubmission = !!mySubmission

  const difficultyColor = {
    easy:   'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard:   'bg-red-100 text-red-700',
  }

  // Active poll badge — re-query every 5 s while processing
  const isProcessing = mySubmission?.status === 'processing'

  return (
    <div className="space-y-6 mt-2">
      {/* Task info card */}
      <Card>
        <CardContent className="pt-4 space-y-3">
          {task.due_date && (
            <div className="flex items-center justify-between flex-wrap gap-2">
              <p className="text-xs text-muted-foreground">
                Due: {fmtDate(task.due_date)}
              </p>
              <DeadlineCountdown dueDate={task.due_date} />
            </div>
          )}
          {task.description && (
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {task.description}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Tabs: Submit + My Questions */}
      <Tabs defaultValue="submit">
        <TabsList>
          <TabsTrigger value="submit">Submit</TabsTrigger>
          {myQuestions.length > 0 && (
            <TabsTrigger value="questions">
              My Questions
              <span className="ml-1.5 rounded-full bg-primary/20 px-1.5 py-0.5 text-xs font-medium">
                {myQuestions.length}
              </span>
            </TabsTrigger>
          )}
        </TabsList>

        {/* ── Submit Tab ─────────────────────────────── */}
        <TabsContent value="submit" className="space-y-5 mt-4">

          {/* Existing submission card */}
          {mySubmission && (
            <div className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <p className="text-sm font-medium">Your Submission</p>
                <StatusBadge status={mySubmission.status} />
              </div>
              {mySubmission.submitted_at && (
                <p className="text-xs text-muted-foreground">
                  Submitted: {fmtDate(mySubmission.submitted_at)}
                </p>
              )}

              {/* Processing notice */}
              {isProcessing && (
                <p className="text-xs text-muted-foreground">
                  Plagiarism check in progress — results will appear here when done.
                </p>
              )}

              {/* Results */}
              {submissionDetail && submissionDetail.plagiarism_score != null && (
                <div className="space-y-4 pt-1">
                  {/* Score */}
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Similarity Score</p>
                    <p className={`text-3xl font-bold tabular-nums ${
                      submissionDetail.plagiarism_score > 70
                        ? 'text-destructive'
                        : submissionDetail.plagiarism_score > 40
                        ? 'text-orange-500'
                        : 'text-green-600'
                    }`}>
                      {fmtScore(submissionDetail.plagiarism_score)}
                    </p>
                  </div>

                  {/* Verbatim matches */}
                  {submissionDetail.verbatim_matches?.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Verbatim Matches
                      </p>
                      {submissionDetail.verbatim_matches.map((m, i) => (
                        <div
                          key={i}
                          className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs"
                        >
                          <p className="text-muted-foreground mb-1">
                            Matched with:{' '}
                            <span className="font-medium">{m.matched_with ?? 'corpus'}</span>
                            {m.similarity != null && <> — {fmtScore(m.similarity)}</>}
                          </p>
                          <p className="font-mono break-all leading-relaxed">
                            "{m.text ?? m.excerpt}"
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Top matches */}
                  {submissionDetail.match_details?.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Top Matches
                      </p>
                      {submissionDetail.match_details.slice(0, 5).map((m, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between text-xs bg-muted/50 rounded px-3 py-2"
                        >
                          <span className="truncate text-muted-foreground">
                            {m.source ?? m.reference_file ?? `Source ${i + 1}`}
                          </span>
                          <span className="font-mono font-medium ml-2 shrink-0">
                            {fmtScore(m.score ?? m.similarity)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Upload zone */}
          {!isPastDue ? (
            <div className="space-y-3">
              <p className="text-sm font-medium">
                {hasSubmission ? 'Resubmit Assignment' : 'Submit Assignment'}
              </p>

              {/* Drop zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !submitting && inputRef.current?.click()}
                className={`rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
                  submitting
                    ? 'cursor-default opacity-60'
                    : dragging
                    ? 'border-primary bg-primary/5 cursor-copy'
                    : selectedFile
                    ? 'border-primary/60 bg-primary/5 cursor-pointer'
                    : 'border-muted-foreground/30 hover:border-muted-foreground/50 hover:bg-muted/30 cursor-pointer'
                }`}
              >
                <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                {selectedFile ? (
                  <>
                    <p className="text-sm font-medium">{selectedFile.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB — click to change
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-medium">Drag & drop your PDF here</p>
                    <p className="text-xs text-muted-foreground mt-1">or click to browse</p>
                  </>
                )}
                <input
                  ref={inputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) setSelectedFile(f)
                    e.target.value = ''
                  }}
                />
              </div>

              {/* Upload progress */}
              {submitting && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Uploading…</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-1.5" />
                </div>
              )}

              {selectedFile && !submitting && (
                <Button onClick={handleSubmit} className="w-full">
                  <Upload className="h-4 w-4 mr-2" />
                  {hasSubmission ? 'Resubmit Assignment' : 'Submit Assignment'}
                </Button>
              )}
            </div>
          ) : (
            !hasSubmission && (
              <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-center">
                <AlertTriangle className="h-6 w-6 text-destructive mx-auto mb-2" />
                <p className="text-sm font-medium text-destructive">Deadline has passed</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Submissions are no longer accepted for this assignment.
                </p>
              </div>
            )
          )}
        </TabsContent>

        {/* ── Questions Tab ───────────────────────────── */}
        {myQuestions.length > 0 && (
          <TabsContent value="questions" className="space-y-3 mt-4">
            <p className="text-xs text-muted-foreground">
              These questions have been assigned to you for this task.
            </p>
            {myQuestions.map((q, idx) => (
              <div
                key={q.question_id ?? idx}
                className="rounded-lg border p-4 space-y-2"
              >
                <p className="text-sm leading-snug">
                  {idx + 1}. {q.question_text}
                </p>
                <div className="flex items-center gap-2">
                  {q.difficulty && (
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      difficultyColor[q.difficulty] ?? 'bg-muted text-muted-foreground'
                    }`}>
                      {q.difficulty}
                    </span>
                  )}
                  {q.bloom_level && (
                    <span className="text-xs text-muted-foreground capitalize">
                      {q.bloom_level}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}
