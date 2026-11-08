type Method = 'GET' | 'POST' | 'PUT' | 'DELETE'

export class ApiError extends Error {
  status: number
  fields: Record<string, string>
  data: Record<string, any>

  constructor(
    message: string,
    status: number,
    fields: Record<string, string> = {},
    data: Record<string, any> = {},
  ) {
    super(message)
    this.status = status
    this.fields = fields
    this.data = data
  }
}

// Read the CSRF cookie fresh on every request: Flask replaces it on login,
// so a value cached at setup time would go stale.
function readCsrfCookie(): string | undefined {
  if (import.meta.server) return undefined
  const match = document.cookie.match(/(?:^|;\s*)csrf_access_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]!) : undefined
}

export function useApi() {
  // During server rendering, pass the browser's cookies on to Flask.
  const forwarded = import.meta.server ? useRequestHeaders(['cookie']) : {}

  async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { ...forwarded }
    if (method !== 'GET') {
      const token = readCsrfCookie()
      if (token) headers['X-CSRF-TOKEN'] = token
    }

    try {
      return await $fetch<T>(`/api${path}`, {
        method,
        body: body as Record<string, unknown> | undefined,
        headers,
        credentials: 'include',
      })
    } catch (err: any) {
      const data = err?.data
      const message =
        (data && typeof data.message === 'string' && data.message) ||
        'Could not reach the server. Please try again.'
      throw new ApiError(message, err?.statusCode ?? 0, data?.fields ?? {}, data ?? {})
    }
  }

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
    del: <T>(path: string) => request<T>('DELETE', path),
  }
}
