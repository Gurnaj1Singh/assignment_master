import client from './client'

// Login uses OAuth2PasswordRequestForm — must be multipart/form-data
export const login = ({ email, password }) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

export const signup = (data) => client.post('/auth/signup', data)

export const verifyOtp = (data) => client.post('/auth/verify-otp', data)

export const forgotPassword = (data) => client.post('/auth/forgot-password', data)

export const resetPassword = (data) => client.post('/auth/reset-password', data)
