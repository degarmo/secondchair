import { useEffect, useState } from 'react'

import { api } from '../api'
import { Provenance, MarginEmpty } from '../Margin'
import type { Claim, Prompt, Rejected } from '../types'
import { VISIBILITY_NAME } from '../types'

interface Turn { question: string; answer: string }

export function Interview({
  lit, onHover, onChange,
}: {
  lit: number | null
  onHover: (id: number | null) => void
  onChange: () => void
}) {
  const [prompt, setPrompt] = useState<Prompt | null>(null)
  const [draft, setDraft] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [proposed, setProposed] = useState<Claim[]>([])
  const [rejected, setRejected] = useState<Rejected[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadQuestion(history: Turn[]) {
    setBusy(true)
    setError(null)
    try {
      setPrompt(await api.nextQuestion(history))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { void loadQuestion([]) }, [])

  async function submit() {
    if (!prompt || !draft.trim()) return
    setBusy(true)
    setError(null)
    try {
      const result = await api.submitAnswer(prompt.question, draft.trim())
      setProposed(result.proposed)
      setRejected(result.rejected)
      const history = [...turns, { question: prompt.question, answer: draft }]
      setTurns(history)
      setDraft('')
      onChange()
      await loadQuestion(history)
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  return (
    <>
      <section className="record">
        <div className="panel-head">
          <div className="eyebrow">Interview &middot; turn {turns.length + 1}</div>
          <h2>Building the record</h2>
          <p>
            Answer in your own words. Everything extracted from what you say
            is quoted back to you for approval before it enters the file.
          </p>
        </div>

        {error && <div className="notice">{error}</div>}

        {prompt && (
          <>
            <p className="question">{prompt.question}</p>
            <p className="rationale">{prompt.rationale}</p>
          </>
        )}

        {busy && !prompt && <div className="working">Preparing the question</div>}

        <div className="stack">
          <textarea
            className="field"
            rows={6}
            value={draft}
            disabled={busy || !prompt}
            placeholder="Take your time. Specifics travel further than adjectives."
            onChange={(e) => setDraft(e.target.value)}
          />
          <div className="btn-row">
            <button className="btn" onClick={submit} disabled={busy || !draft.trim()}>
              Submit answer
            </button>
            <button
              className="btn btn-quiet"
              disabled={busy || !prompt}
              onClick={() => void loadQuestion(turns)}
            >
              Ask me something else
            </button>
            {busy && <span className="working">Working</span>}
          </div>
        </div>

        {rejected.length > 0 && (
          <div className="stack" style={{ marginTop: '2.5rem' }}>
            <div className="eyebrow">Not carried forward</div>
            {rejected.map((item) => (
              <div className="notice" key={item.text}>
                &ldquo;{item.text}&rdquo; &mdash; {item.reason}
              </div>
            ))}
          </div>
        )}
      </section>

      <aside className="margin">
        <div className="eyebrow" style={{ marginBottom: '1rem' }}>
          {proposed.length > 0
            ? `Proposed from that answer · ${proposed.length}`
            : 'Extracted'}
        </div>
        {proposed.length === 0 ? (
          <MarginEmpty lines={[
            'Nothing extracted yet.',
            'What you say will appear here,',
            'quoted, before it is filed.',
          ]} />
        ) : (
          proposed.map((claim) => (
            <div key={claim.id}>
              <Provenance
                id={claim.id}
                marker={VISIBILITY_NAME[claim.visibility]}
                source={claim.source}
                lit={lit === claim.id}
                onHover={onHover}
              />
              <p className="claim-text" style={{ margin: '0.5rem 0 1.25rem' }}>
                {claim.text}
              </p>
            </div>
          ))
        )}
      </aside>
    </>
  )
}
