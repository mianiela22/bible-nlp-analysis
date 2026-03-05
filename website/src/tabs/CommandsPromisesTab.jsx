import { useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

// ── Verse card ─────────────────────────────────────────────────────────────

function VerseCard({ entry, categoryMeta }) {
  const meta = categoryMeta.find(c => c.id === entry.category) || {}
  const ref = `${entry.book} ${entry.chapter}:${entry.verse}`
  const confPct = Math.round(entry.confidence * 100)

  return (
    <div className="cp-verse-card" style={{ borderLeftColor: meta.color || '#888' }}>
      <div className="cp-verse-header">
        <span className="cp-category-badge" style={{ background: meta.color + '22', color: meta.color, borderColor: meta.color + '55' }}>
          {meta.icon} {meta.label}
        </span>
        <span className="cp-verse-ref">{ref}</span>
        <span className="cp-conf-badge" title={`Pattern confidence: ${confPct}%`} style={{ opacity: entry.confidence >= 0.90 ? 1 : 0.65 }}>
          {confPct}%
        </span>
      </div>
      <p className="cp-verse-text">{entry.text}</p>
    </div>
  )
}

// ── Category filter pills ─────────────────────────────────────────────────

function CategoryPills({ categories, selected, onToggle }) {
  return (
    <div className="cp-pills">
      <button
        className={'cp-pill cp-pill-all ' + (selected.length === 0 ? 'cp-pill-active' : '')}
        onClick={() => onToggle(null)}
      >
        All
      </button>
      {categories.map(cat => (
        <button
          key={cat.id}
          className={'cp-pill ' + (selected.includes(cat.id) ? 'cp-pill-active' : '')}
          style={selected.includes(cat.id) ? { background: cat.color, borderColor: cat.color, color: '#fff' } : { borderColor: cat.color + '88', color: cat.color }}
          onClick={() => onToggle(cat.id)}
        >
          {cat.icon} {cat.label}
        </button>
      ))}
    </div>
  )
}

// ── Book chart ─────────────────────────────────────────────────────────────

function BookChart({ byBook, bookOrder, mode }) {
  const data = bookOrder
    .filter(b => (byBook[b]?.commands || 0) + (byBook[b]?.promises || 0) > 0)
    .map(b => ({
      book: b.replace('1 ', '1').replace('2 ', '2').replace('3 ', '3'),
      commands: byBook[b]?.commands || 0,
      promises: byBook[b]?.promises || 0,
    }))
    .filter(d => (mode === 'commands' ? d.commands : d.promises) > 0)
    .sort((a, b) => (mode === 'commands' ? b.commands - a.commands : b.promises - a.promises))
    .slice(0, 20)

  const color = mode === 'commands' ? '#e74c3c' : '#2980b9'
  const key = mode === 'commands' ? 'commands' : 'promises'
  const label = mode === 'commands' ? 'Commands' : 'Promises'

  return (
    <div className="cp-chart-wrap">
      <div className="cp-chart-title">Top 20 books — {label}</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 4, right: 10, bottom: 60, left: 10 }}>
          <CartesianGrid strokeDasharray="2 4" vertical={false} opacity={0.4} />
          <XAxis
            dataKey="book"
            tick={{ fontSize: 11 }}
            angle={-55}
            textAnchor="end"
            interval={0}
          />
          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload?.length) {
                const d = payload[0].payload
                return (
                  <div className="custom-tooltip">
                    <strong>{d.book}</strong><br />
                    Commands: {d.commands}<br />
                    Promises: {d.promises}
                  </div>
                )
              }
              return null
            }}
          />
          <Bar dataKey={key} fill={color} radius={[3, 3, 0, 0]} name={label} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

function CommandsPromisesTab({ data }) {
  const [mode, setMode] = useState('commands')      // 'commands' | 'promises'
  const [selectedCats, setSelectedCats] = useState([])
  const [selectedBook, setSelectedBook] = useState('All Books')
  const [minConf, setMinConf] = useState(0.80)
  const [search, setSearch] = useState('')
  const [view, setView] = useState('browse')         // 'browse' | 'chart'
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 30

  if (!data) return <p style={{ padding: 20 }}>Could not load commands and promises data.</p>

  const { commands, promises, stats, categories, book_order: bookOrder } = data
  const entries = mode === 'commands' ? commands : promises
  const catMeta = mode === 'commands' ? categories.commands : categories.promises

  // Toggle category filter
  function toggleCat(id) {
    if (id === null) {
      setSelectedCats([])
    } else {
      setSelectedCats(prev =>
        prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
      )
    }
    setPage(0)
  }

  // Filtered entries
  const filtered = useMemo(() => {
    let result = entries.filter(e => e.confidence >= minConf)
    if (selectedCats.length > 0) {
      result = result.filter(e => selectedCats.includes(e.category))
    }
    if (selectedBook !== 'All Books') {
      result = result.filter(e => e.book === selectedBook)
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(e =>
        e.text.toLowerCase().includes(q) ||
        e.book.toLowerCase().includes(q)
      )
    }
    return result
  }, [entries, minConf, selectedCats, selectedBook, search])

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE)
  const pageEntries = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  // Books that appear in the current set
  const availableBooks = ['All Books', ...bookOrder.filter(b =>
    entries.some(e => e.book === b)
  )]

  const cmdCount = stats.unique_command_verses
  const promCount = stats.unique_promise_verses

  return (
    <div className="tab-content">

      {/* ── Intro ──────────────────────────────────────────────────────── */}
      <div className="insight-box" style={{ marginBottom: 20 }}>
        <h4>📜 What God Asks of Us — and What God Promises Us</h4>
        <p>
          The Bible contains two complementary voices: <strong>commands</strong> (what God asks of us —
          love, pray, trust, pursue justice) and <strong>promises</strong> (what God pledges to us —
          protection, provision, salvation, hope). This tool uses pattern recognition across all
          31,102 KJV verses to surface {cmdCount.toLocaleString()} command verses and {promCount.toLocaleString()} promise
          verses. Filter by category or book to explore what Scripture emphasizes.
        </p>
        <p style={{ fontSize: '0.85rem', color: '#888', marginTop: 8 }}>
          Note: Pattern matching works on text alone — a few verses may be misclassified when
          a human speaker uses a divine-sounding phrase. High-confidence entries (90%+) are most reliable.
        </p>
      </div>

      {/* ── Mode toggle ────────────────────────────────────────────────── */}
      <div className="cp-mode-toggle">
        <button
          className={'cp-mode-btn ' + (mode === 'commands' ? 'cp-mode-active-cmd' : '')}
          onClick={() => { setMode('commands'); setSelectedCats([]); setPage(0) }}
        >
          📜 Commands
          <span className="cp-mode-count">{cmdCount.toLocaleString()} verses</span>
        </button>
        <button
          className={'cp-mode-btn ' + (mode === 'promises' ? 'cp-mode-active-prom' : '')}
          onClick={() => { setMode('promises'); setSelectedCats([]); setPage(0) }}
        >
          ✨ Promises
          <span className="cp-mode-count">{promCount.toLocaleString()} verses</span>
        </button>
      </div>

      {/* ── View toggle ────────────────────────────────────────────────── */}
      <div className="cp-view-row">
        <button className={'cp-view-btn ' + (view === 'browse' ? 'active' : '')} onClick={() => setView('browse')}>Browse Verses</button>
        <button className={'cp-view-btn ' + (view === 'chart' ? 'active' : '')} onClick={() => setView('chart')}>Book Chart</button>
      </div>

      {view === 'chart' && (
        <BookChart byBook={stats.by_book} bookOrder={bookOrder} mode={mode} />
      )}

      {view === 'browse' && (
        <>
          {/* ── Category pills ────────────────────────────────────────── */}
          <CategoryPills categories={catMeta} selected={selectedCats} onToggle={toggleCat} />

          {/* ── Filters ───────────────────────────────────────────────── */}
          <div className="cp-filters">
            <select
              className="select-input"
              value={selectedBook}
              onChange={e => { setSelectedBook(e.target.value); setPage(0) }}
            >
              {availableBooks.map(b => <option key={b} value={b}>{b}</option>)}
            </select>

            <select
              className="select-input"
              value={minConf}
              onChange={e => { setMinConf(Number(e.target.value)); setPage(0) }}
            >
              <option value={0.70}>All (70%+ confidence)</option>
              <option value={0.80}>High (80%+ confidence)</option>
              <option value={0.90}>Very high (90%+ confidence)</option>
              <option value={0.95}>Best only (95%+ confidence)</option>
            </select>

            <input
              type="text"
              className="search-input"
              placeholder="Search verse text…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(0) }}
            />

            <span className="cp-result-count">
              {filtered.length.toLocaleString()} verse{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* ── Category summary cards ────────────────────────────────── */}
          {selectedCats.length === 0 && selectedBook === 'All Books' && !search && (
            <div className="cp-summary-grid">
              {catMeta.map(cat => {
                const n = stats.by_category[mode === 'commands' ? 'commands' : 'promises'][cat.id] || 0
                return (
                  <button
                    key={cat.id}
                    className="cp-summary-card"
                    style={{ borderTopColor: cat.color }}
                    onClick={() => { setSelectedCats([cat.id]); setPage(0) }}
                    title={cat.description}
                  >
                    <div className="cp-summary-icon">{cat.icon}</div>
                    <div className="cp-summary-count" style={{ color: cat.color }}>{n}</div>
                    <div className="cp-summary-label">{cat.label}</div>
                  </button>
                )
              })}
            </div>
          )}

          {/* ── Verse list ────────────────────────────────────────────── */}
          <div className="cp-verse-list">
            {pageEntries.length === 0 && (
              <p style={{ color: '#888', padding: '20px 0' }}>
                No verses match the current filters.
              </p>
            )}
            {pageEntries.map((entry, i) => (
              <VerseCard
                key={`${entry.book}-${entry.chapter}-${entry.verse}-${entry.category}-${i}`}
                entry={entry}
                categoryMeta={catMeta}
              />
            ))}
          </div>

          {/* ── Pagination ────────────────────────────────────────────── */}
          {pageCount > 1 && (
            <div className="cp-pagination">
              <button
                className="chapter-nav-btn"
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
              >←</button>
              <span style={{ fontSize: '0.9rem' }}>
                Page {page + 1} of {pageCount} — showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
              </span>
              <button
                className="chapter-nav-btn"
                onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
                disabled={page >= pageCount - 1}
              >→</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default CommandsPromisesTab
