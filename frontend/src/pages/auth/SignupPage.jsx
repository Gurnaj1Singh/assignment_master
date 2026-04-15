import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { BookOpen, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { signupSchema } from '@/lib/validators'
import { signup } from '@/api/auth'

export default function SignupPage() {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: { role: 'student' },
  })

  const password = watch('password', '')

  // Visual password strength checker
  const checks = [
    { label: '8+ characters', pass: password.length >= 8 },
    { label: 'Uppercase letter', pass: /[A-Z]/.test(password) },
    { label: 'Number', pass: /\d/.test(password) },
    { label: 'Special character', pass: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
  ]
  const strength = checks.filter((c) => c.pass).length

  async function onSubmit(values) {
    try {
      await signup(values)
      toast.success('Account created! Check your email for the OTP.')
      navigate('/verify-otp', { state: { email: values.email, signupData: values } })
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Signup failed. Try again.'
      toast.error(msg)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <BookOpen className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-semibold">Create an account</h1>
          <p className="text-sm text-muted-foreground">Join Assignment Master</p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Name */}
              <div className="space-y-1.5">
                <Label htmlFor="name">Full name</Label>
                <Input id="name" placeholder="Gurnaj Singh" {...register('name')} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>

              {/* Email */}
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="you@example.com" {...register('email')} />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>

              {/* Role toggle */}
              <div className="space-y-1.5">
                <Label>I am a</Label>
                <div className="grid grid-cols-2 gap-2">
                  {['student', 'professor'].map((r) => (
                    <label
                      key={r}
                      className="relative flex cursor-pointer items-center justify-center rounded-lg border p-3 text-sm font-medium transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5"
                    >
                      <input
                        type="radio"
                        value={r}
                        className="sr-only"
                        {...register('role')}
                      />
                      <span className="capitalize">{r}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" placeholder="••••••••" {...register('password')} />
                {/* Strength meter */}
                {password.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <div className="flex gap-1">
                      {[...Array(4)].map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded-full transition-colors ${
                            i < strength
                              ? strength <= 1 ? 'bg-destructive'
                              : strength <= 2 ? 'bg-amber-400'
                              : strength <= 3 ? 'bg-yellow-400'
                              : 'bg-emerald-500'
                              : 'bg-border'
                          }`}
                        />
                      ))}
                    </div>
                    <ul className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                      {checks.map((c) => (
                        <li
                          key={c.label}
                          className={`flex items-center gap-1 text-xs ${c.pass ? 'text-emerald-600' : 'text-muted-foreground'}`}
                        >
                          <span>{c.pass ? '✓' : '○'}</span> {c.label}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create account
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-foreground hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
