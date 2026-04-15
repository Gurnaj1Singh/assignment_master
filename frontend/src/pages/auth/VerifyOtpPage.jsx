import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { toast } from 'sonner'
import { ShieldCheck, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { verifyOtpSchema } from '@/lib/validators'
import { verifyOtp, signup } from '@/api/auth'

export default function VerifyOtpPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const prefillEmail = location.state?.email ?? ''
  const signupData = location.state?.signupData
  const [resending, setResending] = useState(false)

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(verifyOtpSchema),
    defaultValues: { email: prefillEmail, code: '' },
  })

  async function onSubmit(values) {
    try {
      await verifyOtp(values)
      toast.success('Email verified! You can now sign in.')
      navigate('/login')
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Invalid or expired OTP.'
      toast.error(msg)
    }
  }

  async function handleResend() {
    if (!signupData) {
      toast.error('Please sign up again to receive a new OTP.')
      navigate('/signup')
      return
    }
    setResending(true)
    try {
      await signup(signupData)
      toast.success('A new OTP has been sent to your email.')
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Failed to resend OTP.'
      toast.error(msg)
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-semibold">Verify your email</h1>
          <p className="text-sm text-muted-foreground">
            Enter the 6-digit code sent to{' '}
            {prefillEmail ? <strong>{prefillEmail}</strong> : 'your email'}
          </p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" {...register('email')} />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="code">OTP Code</Label>
                <Input
                  id="code"
                  placeholder="123456"
                  maxLength={6}
                  inputMode="numeric"
                  className="text-center text-xl tracking-widest"
                  {...register('code')}
                />
                {errors.code && <p className="text-xs text-destructive">{errors.code.message}</p>}
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Verify
              </Button>

              <Button
                type="button"
                variant="ghost"
                className="w-full"
                disabled={resending}
                onClick={handleResend}
              >
                {resending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Resend OTP
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
