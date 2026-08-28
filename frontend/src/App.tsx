import { useCallback, useEffect, useState } from 'react'

import { api } from './api'
import { Ask } from './panels/Ask'
import { Interview } from './panels/Interview'
import { Review } from './panels/Review'

type Station = 'interview' | 'review' | 'ask'

const STATIONS: { id: Station; label: string }[] = [
  { id: 'interview', label: 'Interview' },
  { id: 'review', label: 'Review' },
  { id: 'ask', label: 'Ask' },
]

export default function App() {
  const [station, setStation] = useState<Station>('interview')
  const [lit, setLit] = useState<number | null>(null)
  const [counts, setCounts] = useState({ proposed: 0, onRecord: 0 })

  const refreshCounts = useCallback(async () => {
    try {
      const [proposed, approved] = await Promise.all([
        api.claims('proposed'), api.claims('approved'),
      ])
      setCounts({ proposed: proposed.length, onRecord: approved.length })
    } catch {
      // The docket is informational; a failure here must not block the page.
    }
  }, [])

  useEffect(() => { void refreshCounts() }, [refreshCounts])

  // Highlighted sources belong to the station that rendered them.
  useEffect(() => { setLit(null) }, [station])

  return (
    <>
      <header className="masthead">
        <div className="masthead-top">
          <h1 className="wordmark">second<em>chair</em></h1>
          <div className="docket">
            <div className="docket-item">
              <b>{counts.onRecord}</b>
              <span className="eyebrow">On record</span>
            </div>
            <div className="docket-item">
              <b>{counts.proposed}</b>
              <span className="eyebrow">Awaiting review</span>
            </div>
          </div>
        </div>

        <nav className="stations">
          {STATIONS.map(({ id, label }) => (
            <button
              key={id}
              className="station"
              aria-current={station === id}
              onClick={() => setStation(id)}
            >
              {label}
              {id === 'review' && counts.proposed > 0 && (
                <span className="count">{counts.proposed}</span>
              )}
            </button>
          ))}
        </nav>
      </header>

      <main className="sheet">
        {station === 'interview' && (
          <Interview lit={lit} onHover={setLit} onChange={refreshCounts} />
        )}
        {station === 'review' && (
          <Review lit={lit} onHover={setLit} onChange={refreshCounts} />
        )}
        {station === 'ask' && <Ask lit={lit} onHover={setLit} />}
      </main>
    </>
  )
}
