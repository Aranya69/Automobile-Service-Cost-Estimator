// Same rules as backend/app/validators.py. The server always checks again;
// these just give quicker feedback while typing.

export const PASSWORD_MIN = 8
export const PASSWORD_MAX = 128
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function nameError(raw: string) {
  const name = raw.trim().replace(/\s+/g, ' ')
  if (!name) return 'Name is required.'
  if (name.length < 2 || name.length > 60) return 'Name must be 2 to 60 characters.'
  if (!/\p{L}/u.test(name)) return 'Name must contain letters.'
  return ''
}

export function emailError(raw: string) {
  const email = raw.trim()
  if (!email) return 'Email is required.'
  if (email.length > 254 || !EMAIL_PATTERN.test(email)) return 'Enter a valid email address.'
  return ''
}

export function passwordChecks(password: string) {
  return [
    { label: `At least ${PASSWORD_MIN} characters`, ok: password.length >= PASSWORD_MIN },
    { label: 'At least one letter', ok: /[A-Za-z]/.test(password) },
    { label: 'At least one number', ok: /\d/.test(password) },
  ]
}

export function passwordError(password: string, email = '') {
  if (!password) return 'Password is required.'
  if (password.length > PASSWORD_MAX) return `Password must be at most ${PASSWORD_MAX} characters.`
  if (passwordChecks(password).some((c) => !c.ok)) {
    return 'Password must be 8+ characters with at least one letter and one number.'
  }
  if (email && password.toLowerCase() === email.trim().toLowerCase()) {
    return 'Password must not be the same as your email.'
  }
  return ''
}

export function confirmError(password: string, confirm: string) {
  if (!confirm) return 'Please confirm your password.'
  if (confirm !== password) return 'Passwords do not match.'
  return ''
}
