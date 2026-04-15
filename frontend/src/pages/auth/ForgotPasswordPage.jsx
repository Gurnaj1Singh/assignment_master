import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { KeyRound, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { forgotPasswordSchema } from '@/lib/validators'
import { forgotPassword } from '@/api/auth'

export default function ForgotPasswordPage() {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(forgotPasswordSchema) })

  async function onSubmit({ email }) {
    try {
      await forgotPassword({ email })
      // Backend always returns 200 (prevents email enumeration)
      toast.success('If this email is registered, a reset OTP has been sent.')
      navigate('/reset-password', { state: { email } })
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Something went wrong. Please try again.'
      toast.error(msg)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <KeyRound className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-semibold">Reset your password</h1>
          <p className="text-sm text-muted-foreground">
            Enter your email and we&apos;ll send a reset code.
          </p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="you@example.com" {...register('email')} />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Send reset code
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground">
          <Link to="/login" className="font-medium text-foreground hover:underline">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
