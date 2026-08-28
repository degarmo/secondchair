import type {
  Answer, Audience, Claim, Prompt, Rejected, Visibility,
} from './types'

/** Every response body is JSON; a non-2xx carries a `detail` string. */
async function request<T>(
  path: string, body?: unknown, method?: string,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: method ?? (body === undefined ? 'GET' : 'POST'),
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.detail ?? `Request failed (${response.status})`)
  }
  return data as T
}

export const api = {
  nextQuestion: (recent: { question: string; answer: string }[]) =>
    request<Prompt>('/interview/next/', { recent }),

  submitAnswer: (question: string, answer: string) =>
    request<{ proposed: Claim[]; rejected: Rejected[] }>(
      '/interview/answer/', { question, answer },
    ),

  claims: (status?: string) =>
    request<Claim[]>(`/claims/${status ? `?status=${status}` : ''}`),

  setVisibility: (id: number, visibility: Visibility) =>
    request<Claim>(`/claims/${id}/`, { visibility }, 'PATCH'),

  approve: (id: number) => request<Claim>(`/claims/${id}/approve/`, {}),
  reject: (id: number) => request<Claim>(`/claims/${id}/reject/`, {}),

  approveAll: (ids: number[]) =>
    request<{ approved: number }>('/claims/approve_all/', { ids }),

  ask: (question: string, audience: Audience) =>
    request<Answer>('/ask/', { question, audience }),
}
