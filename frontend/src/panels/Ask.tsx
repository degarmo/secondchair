import { useState } from 'react'

import { api } from '../api'
import { Provenance, MarginEmpty } from '../Margin'
import type { Answer, Audience } from '../types'

const AUDIENCES: { value: Audience; label: string }[] = [
  { value: 'public', label: 'Public' },
  { value: 'recruiter', label: 'Recruiter' },
  { value: 'owner', label: 'Candidate' },
]

export function Ask({
  lit, onHover,
}: {
  lit: number | null
  onHover: (id: number | null) => void
}) {
  const [question, setQuestion] = useState('')
  const [audience, setAudience] = useState<Audience>('recruiter')
  const [result, setResult] = useState<Answer | null>(null)
  const [asked, setAsked] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    if (!question.trim()) return
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      setAsked(question.trim())
      setResult(await api.ask(question.trim(), audience))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <section className="record">
        <div className="panel-head">
          <div className="eyebrow">Ask about the candidate</div>
          <h2>Answers, and where they came from</h2>
          <p>
            Switch who is asking to see the same question answered against a
            different slice of the file.
          </p>
        </div>

        <div className="stack">
          <textarea
            className="field"
            rows={3}
            value={question}
            disabled={busy}
            placeholder="Have they led a team through a migration?"
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) void submit()
            }}
          />
          <div className="btn-row">
            <button className="btn" onClick={submit} disabled={busy || !question.trim()}>
              Ask
            </button>
            <select
              className="select"
              value={audience}
              aria-label="Who is asking"
              onChange={(e) => setAudience(e.target.value as Audience)}
            >
              {AUDIENCES.map((option) => (
                <option key={option.value} value={option.value}>
                  Asking as {option.label}
                </option>
              ))}
            </select>
            {busy && <span className="working">Checking the record</span>}
          </div>
        </div>

        {error && (
          <div className="notice" style={{ marginTop: '2rem' }}>{error}</div>
        )}

        {result && (
          <div style={{ marginTop: '2.75rem' }}>
            <div className="eyebrow" style={{ marginBottom: '0.75rem' }}>
              {asked}
            </div>

            <div className={result.answered ? undefined : 'declined'}>
              {!result.answered && (
                <div className="eyebrow" style={{ marginBottom: '0.5rem' }}>
                  Not in the record
                </div>
              )}
              <p className="answer">{result.answer}</p>
            </div>

            {result.citations.length > 0 && (
              <div style={{ marginTop: '1.5rem' }}>
                <span className="eyebrow">Drawn from</span>{' '}
                {result.citations.map((citation, index) => (
                  <button
                    className="cite"
                    key={citation.claim_id}
                    data-cite-id={citation.claim_id}
                    onMouseEnter={() => onHover(citation.claim_id)}
                    onMouseLeave={() => onHover(null)}
                    onFocus={() => onHover(citation.claim_id)}
                    onBlur={() => onHover(null)}
                  >
                    [{index + 1}]
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      <aside className="margin">
        <div className="eyebrow" style={{ marginBottom: '1rem' }}>
          {result?.citations.length ? 'Citations' : 'Sources'}
        </div>

        {!result?.citations.length ? (
          <MarginEmpty lines={
            result && !result.answered
              ? ['No sources, so no answer.', 'That is the intended behaviour.']
              : ['Sources appear here', 'alongside every answer.']
          } />
        ) : (
          result.citations.map((citation, index) => (
            <div key={citation.claim_id}>
              <Provenance
                id={citation.claim_id}
                marker={`${index + 1}`}
                source={citation.source}
                lit={lit === citation.claim_id}
                onHover={onHover}
              />
              <p className="claim-text" style={{ margin: '0.5rem 0 1.25rem' }}>
                {citation.claim_text}
              </p>
            </div>
          ))
        )}
      </aside>
    </>
  )
}
