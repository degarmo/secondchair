import type { Source } from './types'

/** A source card in the margin. `id` pairs it with a citation marker in
 *  the record column; hovering either lights both. */
export function Provenance({
  id, marker, source, lit, onHover,
}: {
  id: number
  marker: string
  source: Source
  lit: boolean
  onHover: (id: number | null) => void
}) {
  return (
    <div
      className="provenance"
      data-prov-id={id}
      data-lit={lit}
      onMouseEnter={() => onHover(id)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="provenance-head">
        <span className="marker">{marker}</span>
        <span className="provenance-label">{source.label}</span>
      </div>
      <blockquote className="excerpt">{source.excerpt}</blockquote>
    </div>
  )
}

export function MarginEmpty({ lines }: { lines: string[] }) {
  return (
    <div className="margin-empty">
      {lines.map((line) => <div key={line}>{line}</div>)}
    </div>
  )
}
