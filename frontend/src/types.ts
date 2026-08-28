export type Visibility = 10 | 20 | 30
export type Audience = 'public' | 'recruiter' | 'owner'

export const VISIBILITY_NAME: Record<Visibility, string> = {
  10: 'Public',
  20: 'Recruiter',
  30: 'Private',
}

export interface Source {
  id: number
  kind: string
  label: string
  excerpt: string
}

export interface Entity {
  id: number
  kind: string
  title: string
  org: string
  period: string
}

export interface Claim {
  id: number
  text: string
  entity: Entity | null
  source: Source
  visibility: Visibility
  status: 'proposed' | 'approved' | 'rejected'
  confidence: number
}

export interface Citation {
  claim_id: number
  claim_text: string
  source: Source
}

export interface Answer {
  answered: boolean
  answer: string
  citations: Citation[]
}

export interface Prompt {
  question: string
  rationale: string
  targets: 'gap' | 'depth' | 'coverage'
}

export interface Rejected {
  text: string
  excerpt: string
  reason: string
}
