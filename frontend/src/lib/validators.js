import { z } from 'zod'

const passwordSchema = z
  .string()
  .min(8, 'Minimum 8 characters')
  .regex(/\d/, 'Must contain at least one digit')
  .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
  .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Must contain at least one special character')

export const signupSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  password: passwordSchema,
  role: z.enum(['student', 'professor']),
})

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, 'Password is required'),
})

export const verifyOtpSchema = z.object({
  email: z.string().email(),
  code: z.string().length(6, 'OTP must be 6 digits'),
})

export const forgotPasswordSchema = z.object({
  email: z.string().email(),
})

export const resetPasswordSchema = z.object({
  email: z.string().email(),
  code: z.string().length(6, 'OTP must be 6 digits'),
  new_password: passwordSchema,
})

export const createClassroomSchema = z.object({
  class_name: z.string().min(2).max(200),
})

export const joinClassroomSchema = z.object({
  class_code: z.string().min(1, 'Class code is required'),
})

export const createTaskSchema = z.object({
  title: z.string().min(2).max(300),
  description: z.string().optional(),
  due_date: z.string().optional().nullable(),
})

export const distributeQuestionsSchema = z.object({
  num_per_student: z.coerce.number().int().min(1),
})
