import { useState, useEffect, useMemo, useRef } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

// ── Color mapping ─────────────────────────────────────────────────────────────
// Compound score: -1 (very negative) to +1 (very positive)
// Returns a light background tint — always readable

function sentimentBg(compound) {
  const c = Math.max(-1, Math.min(1, compound))
  // Threshold bands
  if (c <= -0.5)  return { bg: 'hsl(0,  65%, 87%)', label: 'Very Negative' }
  if (c <= -0.2)  return { bg: 'hsl(5,  55%, 92%)', label: 'Negative' }
  if (c <= -0.05) return { bg: 'hsl(12, 40%, 95%)', label: 'Slightly Negative' }
  if (c <   0.05) return { bg: 'hsl(45, 20%, 97%)', label: 'Neutral' }
  if (c <   0.2)  return { bg: 'hsl(95, 38%, 94%)', label: 'Slightly Positive' }
  if (c <   0.4)  return { bg: 'hsl(110,48%, 90%)', label: 'Positive' }
  if (c <   0.6)  return { bg: 'hsl(118,55%, 86%)', label: 'Very Positive' }
  return           { bg: 'hsl(120,60%, 82%)', label: 'Joyful' }
}

// Solid dot color for chapter arc (more vivid)
function sentimentDot(compound) {
  const c = Math.max(-1, Math.min(1, compound))
  if (c <= -0.3)  return '#e74c3c'
  if (c <= -0.05) return '#e67e73'
  if (c <   0.05) return '#d4c9a0'
  if (c <   0.2)  return '#a8d8a8'
  if (c <   0.4)  return '#5cb85c'
  return '#27ae60'
}

// ── Chapter Arc — colored squares showing each chapter's sentiment ─────────────

function BookArc({ chapterAvg, currentChapter, onSelect }) {
  const chapters = Object.entries(chapterAvg)
    .map(([ch, avg]) => ({ ch: parseInt(ch), avg }))
    .sort((a, b) => a.ch - b.ch)

  return (
    <div className="book-arc">
      <div className="arc-label">Book arc — click any chapter</div>
      <div className="arc-squares">
        {chapters.map(({ ch, avg }) => (
          <button
            key={ch}
            className={'arc-square ' + (ch === currentChapter ? 'arc-active' : '')}
            style={{ background: sentimentDot(avg) }}
            onClick={() => onSelect(ch)}
            title={`Ch. ${ch}  avg sentiment: ${avg > 0 ? '+' : ''}${avg.toFixed(3)}`}
          />
        ))}
      </div>
      <div className="arc-legend">
        {[[-0.5,'Very Negative','#e74c3c'],[-0.15,'Negative','#e67e73'],[0,'Neutral','#d4c9a0'],[0.15,'Positive','#5cb85c'],[0.5,'Very Positive','#27ae60']].map(([,label,color]) => (
          <span key={label} className="arc-legend-item">
            <span className="arc-legend-dot" style={{ background: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}

// ── Chapter line mini-chart ───────────────────────────────────────────────────

function ChapterSparkline({ verses }) {
  const data = verses.map(([vnum, , compound]) => ({ v: vnum, score: compound }))
  return (
    <div className="chapter-sparkline">
      <div className="sparkline-label">Verse-by-verse emotional arc this chapter</div>
      <ResponsiveContainer width="100%" height={80}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 20 }}>
          <defs>
            <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#27ae60" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#e74c3c" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 2" vertical={false} opacity={0.3} />
          <XAxis dataKey="v" hide />
          <YAxis domain={[-1, 1]} hide />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload?.length) {
                const d = payload[0].payload
                const score = d.score
                const { label } = sentimentBg(score)
                return (
                  <div className="custom-tooltip" style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
                    v.{d.v}: {score > 0 ? '+' : ''}{score.toFixed(3)} — {label}
                  </div>
                )
              }
              return null
            }}
          />
          <ReferenceLine y={0} stroke="#999" strokeDasharray="3 3" />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#555"
            strokeWidth={1.5}
            fill="url(#scoreGrad)"
            dot={(props) => {
              const { cx, cy, payload } = props
              return <circle key={payload.v} cx={cx} cy={cy} r={2} fill={sentimentDot(payload.score)} />
            }}
            activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Verse display ─────────────────────────────────────────────────────────────

function VerseRow({ vnum, text, compound, highlight }) {
  const { bg, label } = sentimentBg(compound)
  return (
    <div
      className={'verse-row ' + (highlight ? 'verse-highlight' : '')}
      style={{ background: bg }}
      title={`${label} — score: ${compound > 0 ? '+' : ''}${compound.toFixed(4)}`}
    >
      <span className="verse-number" style={{ background: sentimentDot(compound) }}>
        {vnum}
      </span>
      <span className="verse-body">{text}</span>
      <span className="verse-score-badge">{compound > 0 ? '+' : ''}{compound.toFixed(2)}</span>
    </div>
  )
}

// ── Global search result row ──────────────────────────────────────────────────

function GlobalVerseRow({ book, chapter, vnum, text, compound, query, onJump }) {
  const { bg, label } = sentimentBg(compound)
  // Highlight the search term in the text
  const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
  return (
    <div
      className="verse-row"
      style={{ background: bg, cursor: 'pointer' }}
      title={`${label} — score: ${compound > 0 ? '+' : ''}${compound.toFixed(4)} — click to open chapter`}
      onClick={onJump}
    >
      <span className="verse-number" style={{ background: sentimentDot(compound) }}>{vnum}</span>
      <span className="verse-body">
        <span className="global-ref" style={{ color: '#888', fontSize: '0.8rem', marginRight: 6 }}>
          {book} {chapter}:
        </span>
        {parts.map((part, i) =>
          part.toLowerCase() === query.toLowerCase()
            ? <mark key={i} style={{ background: '#fff3cd', padding: '0 2px', borderRadius: 2 }}>{part}</mark>
            : part
        )}
      </span>
      <span className="verse-score-badge">{compound > 0 ? '+' : ''}{compound.toFixed(2)}</span>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

function VerseSentimentTab() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState('read')             // 'read' | 'search'
  const [selectedBook, setSelectedBook] = useState('Psalms')
  const [selectedChapter, setSelectedChapter] = useState(22)
  const [searchQuery, setSearchQuery] = useState('')
  const [globalQuery, setGlobalQuery] = useState('')
  const topRef = useRef(null)

  // Flatten all verses once for global search
  const allVerses = useMemo(() => {
    if (!data) return []
    const out = []
    for (const book of data.book_order) {
      const chaps = data.verses?.[book] || {}
      for (const [ch, verses] of Object.entries(chaps)) {
        for (const [vnum, text, compound] of verses) {
          out.push({ book, chapter: parseInt(ch), verse: vnum, text, compound })
        }
      }
    }
    return out
  }, [data])

  const MAX_RESULTS = 250
  const globalResults = useMemo(() => {
    const q = globalQuery.trim()
    if (q.length < 2) return []
    const lower = q.toLowerCase()
    return allVerses.filter(v => v.text.toLowerCase().includes(lower))
  }, [allVerses, globalQuery])

  // Lazy-load the large JSON only when this tab is visited
  useEffect(() => {
    fetch('/data/verse_sentiment.json')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const verses = useMemo(() => {
    if (!data) return []
    return data.verses?.[selectedBook]?.[String(selectedChapter)] || []
  }, [data, selectedBook, selectedChapter])

  const chapterAvg = useMemo(() => {
    if (!data) return {}
    return data.chapter_avg?.[selectedBook] || {}
  }, [data, selectedBook])

  const totalChapters = useMemo(() => {
    if (!data) return 0
    return data.chapter_counts?.[selectedBook] || 0
  }, [data, selectedBook])

  const chapterSentiment = useMemo(() => {
    return chapterAvg[String(selectedChapter)] ?? null
  }, [chapterAvg, selectedChapter])

  // When book changes, go to chapter 1
  function selectBook(book) {
    setSelectedBook(book)
    setSelectedChapter(1)
    topRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  function goChapter(n) {
    if (n >= 1 && n <= totalChapters) {
      setSelectedChapter(n)
      topRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  // Search filtering
  const filteredVerses = useMemo(() => {
    if (!searchQuery.trim()) return verses
    const q = searchQuery.toLowerCase()
    return verses.filter(([, text]) => text.toLowerCase().includes(q))
  }, [verses, searchQuery])

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: 300 }}>
        <h3>Loading 31,102 verses…</h3>
        <p style={{ color: '#888', marginTop: 8 }}>This tab loads the complete Bible with sentiment scores.</p>
      </div>
    )
  }

  if (!data) return <p>Could not load verse sentiment data.</p>

  const bookOrder = data.book_order

  // Chapter avg sentiment bar data for selected chapter
  const { bg: chBg, label: chLabel } = chapterSentiment !== null
    ? sentimentBg(chapterSentiment)
    : { bg: '#f5f5dc', label: 'Neutral' }

  return (
    <div className="tab-content" ref={topRef}>

      {/* ── Intro ──────────────────────────────────────────────────────────── */}
      <div className="insight-box" style={{ marginBottom: 20 }}>
        <h4>🎨 Color-Coded Bible — Read the Emotional Texture of Scripture</h4>
        <p>
          Every verse is colored by its VADER sentiment score. This isn't interpretation — it's the
          machine reading the words and asking: positive or negative? The results are theologically
          striking. <strong>Lamentations</strong> is uniformly dark. <strong>Philippians</strong> glows.
          <strong> Romans 7</strong> bottoms out ("O wretched man that I am!") then
          <strong> Romans 8</strong> blazes green ("nothing can separate us from the love of God").
          Hover any verse to see its exact score.
        </p>
      </div>

      {/* ── Mode toggle ──────────────────────────────────────────────────── */}
      <div className="cp-view-row" style={{ marginBottom: 20 }}>
        <button className={'cp-view-btn ' + (mode === 'read' ? 'active' : '')} onClick={() => setMode('read')}>
          📖 Read by Chapter
        </button>
        <button className={'cp-view-btn ' + (mode === 'search' ? 'active' : '')} onClick={() => setMode('search')}>
          🔍 Search All Verses
        </button>
      </div>

      {/* ══ GLOBAL SEARCH MODE ══════════════════════════════════════════════ */}
      {mode === 'search' && (
        <div>
          <div className="verse-search-row" style={{ marginBottom: 12 }}>
            <input
              type="text"
              className="search-input"
              placeholder="Search all 31,102 verses (e.g. fear not, grace, rejoice)…"
              value={globalQuery}
              onChange={e => setGlobalQuery(e.target.value)}
              autoFocus
              style={{ maxWidth: 420 }}
            />
            {globalQuery.trim().length >= 2 && (
              <span style={{ marginLeft: 12, fontSize: '0.85rem', color: '#888' }}>
                {globalResults.length > MAX_RESULTS
                  ? `Showing first ${MAX_RESULTS} of ${globalResults.length.toLocaleString()} matches`
                  : `${globalResults.length.toLocaleString()} verse${globalResults.length !== 1 ? 's' : ''} matching`}
              </span>
            )}
          </div>

          {globalQuery.trim().length < 2 && (
            <p style={{ color: '#aaa', fontStyle: 'italic', padding: '12px 0' }}>
              Type at least 2 characters to search.
            </p>
          )}

          <div className="verse-display">
            {globalResults.slice(0, MAX_RESULTS).map(v => (
              <GlobalVerseRow
                key={`${v.book}-${v.chapter}-${v.verse}`}
                book={v.book}
                chapter={v.chapter}
                vnum={v.verse}
                text={v.text}
                compound={v.compound}
                query={globalQuery.trim()}
                onJump={() => {
                  setMode('read')
                  setSelectedBook(v.book)
                  setSelectedChapter(v.chapter)
                  topRef.current?.scrollIntoView({ behavior: 'smooth' })
                }}
              />
            ))}
          </div>

          {/* Color legend */}
          <div className="verse-legend" style={{ marginTop: 16 }}>
            {[[-0.6,'Very Negative'],[-0.2,'Negative'],[0,'Neutral'],[0.25,'Positive'],[0.55,'Very Positive']].map(([score, label]) => (
              <div key={label} className="legend-item">
                <div className="legend-swatch" style={{ background: sentimentBg(score).bg }} />
                <span>{label}</span>
              </div>
            ))}
            <span className="legend-note">Click any verse to open its chapter</span>
          </div>
        </div>
      )}

      {/* ══ READ BY CHAPTER MODE ════════════════════════════════════════════ */}
      {mode === 'read' && (<>

      {/* ── Book + Chapter nav ─────────────────────────────────────────────── */}
      <div className="verse-nav-row">
        <div className="verse-nav-book">
          <label>Book</label>
          <select
            value={selectedBook}
            onChange={e => selectBook(e.target.value)}
            className="select-input"
          >
            {bookOrder.map(b => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>

        <div className="verse-nav-chapter">
          <button className="chapter-nav-btn" onClick={() => goChapter(selectedChapter - 1)} disabled={selectedChapter <= 1}>←</button>
          <span className="chapter-nav-label">
            Chapter {selectedChapter} of {totalChapters}
            {chapterSentiment !== null && (
              <span
                className="chapter-sentiment-pill"
                style={{ background: chBg, marginLeft: 10 }}
              >
                {chapterSentiment > 0 ? '+' : ''}{chapterSentiment.toFixed(3)} — {chLabel}
              </span>
            )}
          </span>
          <button className="chapter-nav-btn" onClick={() => goChapter(selectedChapter + 1)} disabled={selectedChapter >= totalChapters}>→</button>
        </div>

        {/* Quick picks */}
        <div className="verse-quick-picks">
          {[['Psalms',22],['Romans',7],['Romans',8],['Job',3],['Lam',1,'Lamentations'],['Phil',4,'Philippians'],['Isa',61,'Isaiah'],['Rev',21,'Revelation']].map(([label, ch, book]) => (
            <button
              key={label + ch}
              className="quick-pick"
              style={{ fontSize: '0.78rem' }}
              onClick={() => { selectBook(book || label); setSelectedChapter(ch) }}
            >
              {label} {ch}
            </button>
          ))}
        </div>
      </div>

      {/* ── Book arc (heat map of all chapters) ──────────────────────────────── */}
      <BookArc
        chapterAvg={chapterAvg}
        currentChapter={selectedChapter}
        onSelect={ch => { setSelectedChapter(ch); topRef.current?.scrollIntoView({ behavior: 'smooth' }) }}
      />

      {/* ── Chapter sparkline ─────────────────────────────────────────────── */}
      {verses.length > 0 && <ChapterSparkline verses={verses} />}

      {/* ── Search within chapter ─────────────────────────────────────────── */}
      <div className="verse-search-row">
        <input
          type="text"
          className="search-input"
          placeholder={`Search within ${selectedBook} ${selectedChapter}…`}
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{ maxWidth: 320 }}
        />
        {searchQuery && (
          <span style={{ marginLeft: 10, fontSize: '0.85rem', color: '#888' }}>
            {filteredVerses.length} verse{filteredVerses.length !== 1 ? 's' : ''} matching
          </span>
        )}
      </div>

      {/* ── Verse text ────────────────────────────────────────────────────── */}
      <div className="verse-display">
        <h3 className="verse-chapter-title">
          {selectedBook} — Chapter {selectedChapter}
        </h3>

        {filteredVerses.length === 0 && (
          <p style={{ color: '#888', padding: '20px 0' }}>
            {searchQuery ? `No verses matching "${searchQuery}"` : 'No verse data available.'}
          </p>
        )}

        {filteredVerses.map(([vnum, text, compound]) => (
          <VerseRow
            key={vnum}
            vnum={vnum}
            text={text}
            compound={compound}
            highlight={searchQuery && text.toLowerCase().includes(searchQuery.toLowerCase())}
          />
        ))}
      </div>

      {/* ── Color legend ──────────────────────────────────────────────────── */}
      <div className="verse-legend">
        {[
          [-0.6, 'Very Negative'],
          [-0.2, 'Negative'],
          [0,    'Neutral'],
          [0.25, 'Positive'],
          [0.55, 'Very Positive'],
        ].map(([score, label]) => (
          <div key={label} className="legend-item">
            <div className="legend-swatch" style={{ background: sentimentBg(score).bg }} />
            <span>{label}</span>
          </div>
        ))}
        <span className="legend-note">Hover any verse for exact score</span>
      </div>

      </>)}

    </div>
  )
}

export default VerseSentimentTab
