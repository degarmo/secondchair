import { useEffect, useState } from 'react'

import { api } from '../api'
import { Provenance, MarginEmpty } from '../Margin'
import type { Claim, Visibility } from '../types'
import { VISIBILITY_NAME } from '../types'

export function Review({
  lit, onHover, onChange,
}: {
  lit: number | null
  onHover: (id: number | null) => void
  onChange: () => void
}) {
  const [claims, setClaims] = useState<Claim[]>([])
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setBusy(true)
    try {
      setClaims(await api.claims('proposed'))
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { void load() }, [])

  async function decide(id: number, verdict: 'approve' | 'reject') {
    setClaims((current) => current.filter((c) => c.id !== id))
    try {
      await (verdict === 'approve' ? api.approve(id) : api.reject(id))
      onChange()
    } catch (e) {
      setError((e as Error).message)
      void load()
    }
  }

  async function approveAll() {
    const ids = claims.map((c) => c.id)
    setClaims([])
    try {
      await api.approveAll(ids)
      onChange()
    } catch (e) {
      setError((e as Error).message)
      void load()
    }
  }

  const lifted = claims.find((c) => c.id === lit)

  return (
    <>
      <section className="record">
        <div className="panel-head">
          <div className="eyebrow">Review queue</div>
          <h2>Nothing is filed until you say so</h2>
          <p>
            Each proposal is shown with the words it came from. Set who can
            see it, then approve or discard.
          </p>
        </div>

        {error && <div className="notice">{error}</div>}
        {busy && <div className="working">Loading the queue</div>}

        {!busy && claims.length === 0 && (
          <p className="record-text" style={{ color: 'var(--graphite)' }}>
            The queue is clear. Run another interview turn to add to the file.
          </p>
        )}

        {claims.length > 0 && (
          <>
            <div className="btn-row" style={{ marginBottom: '1.5rem' }}>
              <button className="btn" onClick={approveAll}>
                Approve all {claims.length}
              </button>
            </div>

            {claims.map((claim) => (
              <article
                className="claim"
                key={claim.id}
                data-lit={lit === claim.id}
                onMouseEnter={() => onHover(claim.id)}
                onMouseLeave={() => onHover(null)}
              >
                <div>
                  <p className="claim-text">{claim.text}</p>
                  <div className="claim-meta">
                    {claim.entity && <span>{claim.entity.title} &middot; {claim.entity.org}</span>}
                    <span>confidence {claim.confidence.toFixed(2)}</span>
                  </div>
                </div>

                <div className="claim-actions">
                  <select
                    className="select"
                    value={claim.visibility}
                    aria-label="Who can see this claim"
                    onChange={(e) => {
                      const visibility = Number(e.target.value) as Visibility
                      setClaims((current) => current.map(
                        (c) => (c.id === claim.id ? { ...c, visibility } : c),
                      ))
                      api.setVisibility(claim.id, visibility)
                        .catch((err) => setError((err as Error).message))
                    }}
                  >
                    {([10, 20, 30] as Visibility[]).map((level) => (
                      <option key={level} value={level}>
                        {VISIBILITY_NAME[level]}
                      </option>
                    ))}
                  </select>
                  <button
                    className="icon-btn"
                    data-kind="approve"
                    onClick={() => decide(claim.id, 'approve')}
                  >
                    Approve
                  </button>
                  <button
                    className="icon-btn"
                    data-kind="reject"
                    onClick={() => decide(claim.id, 'reject')}
                  >
                    Discard
                  </button>
                </div>
              </article>
            ))}
          </>
        )}
      </section>

      <aside className="margin">
        <div className="eyebrow" style={{ marginBottom: '1rem' }}>Source</div>
        {lifted ? (
          <Provenance
            id={lifted.id}
            marker={`#${lifted.id}`}
            source={lifted.source}
            lit
            onHover={onHover}
          />
        ) : (
          <MarginEmpty lines={[
            'Point at a proposal to see',
            'the words it was drawn from.',
          ]} />
        )}
      </aside>
    </>
  )
}
