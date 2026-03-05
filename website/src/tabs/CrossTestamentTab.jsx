import { useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

// ── Confidence badge ────────────────────────────────────────────────────────

function ConfBadge({ confidence, method }) {
  const pct = Math.round(confidence * 100)
  const color = confidence >= 0.80 ? '#27ae60' : confidence >= 0.55 ? '#f39c12' : '#95a5a6'
  const label = method === 'phrase' ? `${pct}% phrase` : `${pct}% tfidf`
  return (
    <span className="ct-conf-badge" style={{ background: color + '22', color, borderColor: color + '55' }}>
      {label}
    </span>
  )
}

// ── Highlight shared phrase in verse text ──────────────────────────────────

function HighlightText({ text, phrase }) {
  if (!phrase || !text) return <>{text}</>
  const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = new RegExp(`(${escaped})`, 'gi')
  const parts = text.split(pattern)
  return (
    <>
      {parts.map((part, i) =>
        pattern.test(part)
          ? <mark key={i} className="ct-bridge-word">{part}</mark>
          : part
      )}
    </>
  )
}

// ── Citation card ───────────────────────────────────────────────────────────

function CitationCard({ cit, expanded, onToggle }) {
  const bm = cit.best_match
  const ntRef = `${cit.nt_book} ${cit.nt_chapter}:${cit.nt_verse}`
  const otRef = bm ? `${bm.book} ${bm.chapter}:${bm.verse}` : null

  return (
    <div className={'ct-card ' + (expanded ? 'ct-card-open' : '')}
         style={{ borderLeftColor: bm ? (bm.confidence >= 0.80 ? '#27ae60' : bm.confidence >= 0.55 ? '#f39c12' : '#95a5a6') : '#ddd' }}>

      <button className="ct-card-header" onClick={onToggle}>
        <span className="ct-formula-badge">{cit.formula}</span>
        <span className="ct-card-title">{ntRef}</span>
        {otRef && <span className="ct-card-refs">→ {otRef}</span>}
        {bm && <ConfBadge confidence={bm.confidence} method={bm.method} />}
        <span className="ct-card-chevron">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className="ct-card-body">
          {/* Two-panel: NT cite + OT source */}
          <div className="ct-panels">

            {/* NT panel */}
            <div className="ct-verse-panel" style={{ background: '#f0f4ff', borderTopColor: '#4169E1' }}>
              <div className="ct-panel-label" style={{ color: '#4169E1' }}>✝️ NT — {ntRef}</div>
              <div className="ct-formula-tag">"{cit.formula}"</div>
              <blockquote className="ct-panel-text">{cit.nt_text}</blockquote>
              {cit.quoted_text && (
                <div className="ct-extracted-quote">
                  <span className="ct-extracted-label">Extracted quote:</span> {cit.quoted_text}
                </div>
              )}
            </div>

            <div className="ct-arrow">→</div>

            {/* OT panel */}
            {bm ? (
              <div className="ct-verse-panel" style={{ background: '#fdf7f0', borderTopColor: '#8B4513' }}>
                <div className="ct-panel-label" style={{ color: '#8B4513' }}>📜 OT — {otRef}</div>
                <div className="ct-method-tag">
                  {bm.method === 'phrase'
                    ? `Matched by phrase: "${bm.matched_phrase}"`
                    : `Matched by TF-IDF (cosine = ${(bm.similarity).toFixed(2)})`}
                </div>
                <blockquote className="ct-panel-text">
                  <HighlightText text={bm.text} phrase={bm.matched_phrase} />
                </blockquote>
              </div>
            ) : (
              <div className="ct-verse-panel" style={{ background: '#f5f5f5', borderTopColor: '#ccc' }}>
                <p style={{ color: '#aaa', fontStyle: 'italic', fontSize: '0.9rem' }}>No OT source identified</p>
              </div>
            )}
          </div>

          {/* Alternate matches */}
          {cit.alternates?.length > 0 && (
            <div className="ct-alternates">
              <div className="ct-alt-label">Other possible OT sources:</div>
              {cit.alternates.map((alt, i) => (
                <div key={i} className="ct-alt-row">
                  <span className="ct-alt-ref">{alt.book} {alt.chapter}:{alt.verse}</span>
                  <ConfBadge confidence={alt.confidence} method={alt.method} />
                  <span className="ct-alt-text">{alt.text.slice(0, 80)}…</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Stats panel ─────────────────────────────────────────────────────────────

function StatsPanel({ stats, otBooks, ntBooks }) {
  // Top NT books
  const ntData = ntBooks
    .filter(b => stats.by_nt_book[b])
    .map(b => ({ book: b.replace(/\d /, n => n), count: stats.by_nt_book[b] }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  // Top OT books cited
  const otData = otBooks
    .filter(b => stats.by_ot_book[b])
    .map(b => ({ book: b, count: stats.by_ot_book[b] }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  // Formula breakdown
  const formulaData = Object.entries(stats.by_formula)
    .map(([f, n]) => ({ formula: f, count: n }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8)

  const { high, medium, low } = stats.confidence_distribution

  return (
    <div className="ct-stats">
      {/* Headline numbers */}
      <div className="ct-stat-cards">
        <div className="ct-stat-card">
          <div className="ct-stat-num">{stats.total_citations}</div>
          <div className="ct-stat-label">NT citation verses<br/>detected</div>
        </div>
        <div className="ct-stat-card">
          <div className="ct-stat-num" style={{ color: '#27ae60' }}>{high}</div>
          <div className="ct-stat-label">High-confidence<br/>phrase matches</div>
        </div>
        <div className="ct-stat-card">
          <div className="ct-stat-num" style={{ color: '#f39c12' }}>{medium}</div>
          <div className="ct-stat-label">Medium-confidence<br/>TF-IDF matches</div>
        </div>
        <div className="ct-stat-card">
          <div className="ct-stat-num" style={{ color: '#9b59b6' }}>
            {Object.keys(stats.by_ot_book).length}
          </div>
          <div className="ct-stat-label">Distinct OT books<br/>quoted</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="ct-charts-row">
        <div className="cp-chart-wrap" style={{ flex: 1 }}>
          <div className="cp-chart-title">Which NT books cite OT most?</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={ntData} margin={{ top: 4, right: 8, bottom: 50, left: 0 }}>
              <CartesianGrid strokeDasharray="2 4" vertical={false} opacity={0.4} />
              <XAxis dataKey="book" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" interval={0} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [v, 'citations']} />
              <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                {ntData.map((_, i) => <Cell key={i} fill="#4169E1" opacity={0.75 + 0.05 * (ntData.length - i) / ntData.length} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="cp-chart-wrap" style={{ flex: 1 }}>
          <div className="cp-chart-title">Which OT books are cited most?</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={otData} margin={{ top: 4, right: 8, bottom: 50, left: 0 }}>
              <CartesianGrid strokeDasharray="2 4" vertical={false} opacity={0.4} />
              <XAxis dataKey="book" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" interval={0} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [v, 'times cited']} />
              <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                {otData.map((_, i) => <Cell key={i} fill="#8B4513" opacity={0.75 + 0.05 * (otData.length - i) / otData.length} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Formula breakdown */}
      <div className="cp-chart-wrap">
        <div className="cp-chart-title">Citation formulas used by NT authors</div>
        <div className="ct-formula-bars">
          {formulaData.map(({ formula, count }) => {
            const max = formulaData[0].count
            return (
              <div key={formula} className="ct-formula-row">
                <span className="ct-formula-name">"{formula}"</span>
                <div className="ct-formula-track">
                  <div className="ct-formula-fill" style={{ width: `${(count / max) * 100}%` }} />
                </div>
                <span className="ct-formula-count">{count}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Main component ──────────────────────────────────────────────────────────

function CrossTestamentTab({ data }) {
  const [view, setView] = useState('citations')
  const [filterFormula, setFilterFormula] = useState('All')
  const [filterNtBook, setFilterNtBook] = useState('All NT Books')
  const [filterOtBook, setFilterOtBook] = useState('All OT Books')
  const [filterConf, setFilterConf] = useState('all')
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  if (!data) return <p style={{ padding: 20 }}>Could not load cross-testament data.</p>

  const { citations, stats, ot_books, nt_books } = data

  // Unique formulas that appear in the data
  const formulas = ['All', ...Object.keys(stats.by_formula)]
  const ntBooksWithData = ['All NT Books', ...nt_books.filter(b => stats.by_nt_book[b])]
  const otBooksWithData = ['All OT Books', ...ot_books.filter(b => stats.by_ot_book[b])]

  const filtered = useMemo(() => {
    let r = citations
    if (filterFormula !== 'All') r = r.filter(c => c.formula === filterFormula)
    if (filterNtBook !== 'All NT Books') r = r.filter(c => c.nt_book === filterNtBook)
    if (filterOtBook !== 'All OT Books') r = r.filter(c => c.best_match?.book === filterOtBook)
    if (filterConf === 'high') r = r.filter(c => c.best_match?.confidence >= 0.80)
    if (filterConf === 'phrase') r = r.filter(c => c.best_match?.method === 'phrase')
    if (search.trim()) {
      const q = search.toLowerCase()
      r = r.filter(c =>
        c.nt_text.toLowerCase().includes(q) ||
        c.best_match?.text.toLowerCase().includes(q) ||
        c.nt_book.toLowerCase().includes(q) ||
        c.best_match?.book.toLowerCase().includes(q)
      )
    }
    return r
  }, [citations, filterFormula, filterNtBook, filterOtBook, filterConf, search])

  return (
    <div className="tab-content">

      {/* ── Intro ──────────────────────────────────────────────────── */}
      <div className="insight-box" style={{ marginBottom: 20 }}>
        <h4>🔗 Machine-Detected OT Quotations in the NT</h4>
        <p>
          NT authors regularly signal they are quoting the OT with phrases like
          <em> "as it is written"</em> or <em>"that it might be fulfilled."</em> This
          analysis scanned all 7,957 NT verses for {Object.keys(stats.by_formula).length} such
          citation formulas, found <strong>{stats.total_citations} citation verses</strong>, extracted
          the quoted text, and then searched all 23,145 OT verses using two methods:
        </p>
        <ul style={{ margin: '8px 0 0 20px', lineHeight: 1.8 }}>
          <li><strong>Phrase matching</strong> — finds exact 4-6 word sequences shared between NT and OT
            ({stats.confidence_distribution.high} high-confidence hits)</li>
          <li><strong>TF-IDF cosine similarity</strong> — finds the most textually similar OT verse even
            when the NT author paraphrases ({stats.confidence_distribution.medium} medium-confidence hits)</li>
        </ul>
        <p style={{ marginTop: 8, color: '#888', fontSize: '0.85rem' }}>
          The algorithm has no theological knowledge — it discovers these connections from text alone.
          The top cited OT books (Psalms, Isaiah) are exactly what scholars have identified for centuries.
        </p>
      </div>

      {/* ── View toggle ────────────────────────────────────────────── */}
      <div className="cp-view-row" style={{ marginBottom: 20 }}>
        <button className={'cp-view-btn ' + (view === 'citations' ? 'active' : '')} onClick={() => setView('citations')}>
          Browse Citations ({citations.length})
        </button>
        <button className={'cp-view-btn ' + (view === 'stats' ? 'active' : '')} onClick={() => setView('stats')}>
          Statistics & Charts
        </button>
      </div>

      {/* ══ STATS VIEW ══════════════════════════════════════════════ */}
      {view === 'stats' && (
        <StatsPanel stats={stats} otBooks={ot_books} ntBooks={nt_books} />
      )}

      {/* ══ CITATIONS VIEW ══════════════════════════════════════════ */}
      {view === 'citations' && (
        <>
          {/* Filters */}
          <div className="cp-filters" style={{ flexWrap: 'wrap', marginBottom: 16 }}>
            <select className="select-input" value={filterFormula} onChange={e => setFilterFormula(e.target.value)}>
              {formulas.map(f => <option key={f} value={f}>{f === 'All' ? 'All formulas' : `"${f}"`}</option>)}
            </select>
            <select className="select-input" value={filterNtBook} onChange={e => setFilterNtBook(e.target.value)}>
              {ntBooksWithData.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
            <select className="select-input" value={filterOtBook} onChange={e => setFilterOtBook(e.target.value)}>
              {otBooksWithData.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
            <select className="select-input" value={filterConf} onChange={e => setFilterConf(e.target.value)}>
              <option value="all">All confidence</option>
              <option value="high">High confidence (80%+)</option>
              <option value="phrase">Phrase matches only</option>
            </select>
            <input
              type="text"
              className="search-input"
              placeholder="Search verse text…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <span className="cp-result-count">{filtered.length} citation{filtered.length !== 1 ? 's' : ''}</span>
          </div>

          {/* Confidence legend */}
          <div className="ct-conf-legend">
            <span className="ct-conf-item"><span style={{ background: '#27ae60' }} className="ct-conf-dot" />High (80%+) — phrase match</span>
            <span className="ct-conf-item"><span style={{ background: '#f39c12' }} className="ct-conf-dot" />Medium (55–79%) — TF-IDF</span>
            <span className="ct-conf-item"><span style={{ background: '#95a5a6' }} className="ct-conf-dot" />Low (&lt;55%) — weak match</span>
          </div>

          {/* Citation cards */}
          <div className="ct-connection-list">
            {filtered.map(cit => (
              <CitationCard
                key={cit.id}
                cit={cit}
                expanded={expandedId === cit.id}
                onToggle={() => setExpandedId(expandedId === cit.id ? null : cit.id)}
              />
            ))}
            {filtered.length === 0 && (
              <p style={{ color: '#888', padding: '20px 0' }}>No citations match the current filters.</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default CrossTestamentTab
