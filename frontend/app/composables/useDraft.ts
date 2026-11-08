// What a visitor typed on the landing page, kept through sign-up so they do
// not have to type it again. Stored per browser tab only.

export interface Draft {
  model: string
  year: number
  problem: string
}

const KEY = 'asce-draft'

export function useDraft() {
  function save(draft: Draft) {
    try {
      sessionStorage.setItem(KEY, JSON.stringify(draft))
    } catch {
      // Private mode or storage blocked: the visitor just retypes it.
    }
  }

  function load(): Draft | null {
    if (import.meta.server) return null
    try {
      const raw = sessionStorage.getItem(KEY)
      return raw ? (JSON.parse(raw) as Draft) : null
    } catch {
      return null
    }
  }

  function clear() {
    try {
      sessionStorage.removeItem(KEY)
    } catch {
      // nothing to clear
    }
  }

  return { save, load, clear }
}
